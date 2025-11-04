"""
Event segmentation module to cluster detections and extract video clips
"""
import os
import cv2
from typing import List, Dict
from pathlib import Path
import config


class EventSegmenter:
    """Segments video into events and extracts clips"""
    
    def __init__(self, clip_duration: int = None, gap_threshold: float = 2.0):
        """
        Initialize the event segmenter.
        
        Args:
            clip_duration: Total clip duration in seconds (default: from config)
            gap_threshold: Maximum gap in seconds between detections to consider same event
        """
        self.clip_duration = clip_duration or config.CLIP_DURATION_SECONDS
        self.gap_threshold = gap_threshold
        self.clip_half_duration = self.clip_duration / 2  # 5 seconds before/after
    
    def cluster_detections(self, frames_with_detections: List[Dict]) -> List[Dict]:
        """
        Cluster consecutive detections into discrete events.
        
        Args:
            frames_with_detections: List of frames with detection results
            
        Returns:
            List of event clusters, each containing frame info and timestamps
        """
        if not frames_with_detections:
            return []
        
        events = []
        current_event = []
        event_id_counter = 1
        
        for i, frame in enumerate(frames_with_detections):
            if not frame.get('has_bin', False):
                # End current event if gap is too large
                if current_event:
                    # Check gap from last frame in current event
                    last_timestamp = current_event[-1]['timestamp']
                    current_timestamp = frame['timestamp']
                    if current_timestamp - last_timestamp > self.gap_threshold:
                        # Save event and start new one
                        events.append(self._create_event(current_event, event_id_counter))
                        event_id_counter += 1
                        current_event = []
                continue
            
            # Check if this frame continues current event or starts new one
            if current_event:
                last_timestamp = current_event[-1]['timestamp']
                current_timestamp = frame['timestamp']
                
                if current_timestamp - last_timestamp <= self.gap_threshold:
                    # Continue current event
                    current_event.append(frame)
                else:
                    # Gap too large, start new event
                    events.append(self._create_event(current_event, event_id_counter))
                    event_id_counter += 1
                    current_event = [frame]
            else:
                # Start new event
                current_event = [frame]
        
        # Don't forget the last event
        if current_event:
            events.append(self._create_event(current_event, event_id_counter))
        
        return events
    
    def _create_event(self, frames: List[Dict], event_id: int) -> Dict:
        """
        Create an event dictionary from a list of frames.
        
        Args:
            frames: List of frames belonging to the event
            event_id: Unique identifier for this event
            
        Returns:
            Event dictionary with metadata
        """
        if not frames:
            return None
        
        timestamps = [f['timestamp'] for f in frames]
        start_time = min(timestamps)
        end_time = max(timestamps)
        center_time = (start_time + end_time) / 2
        
        # Get representative frame (middle frame)
        mid_index = len(frames) // 2
        representative_frame = frames[mid_index]
        
        return {
            'event_id': event_id,
            'frames': frames,
            'start_time': start_time,
            'end_time': end_time,
            'center_time': center_time,
            'duration': end_time - start_time,
            'frame_count': len(frames),
            'representative_frame': representative_frame,
            'detections': sum(f['detection_count'] for f in frames)
        }
    
    def extract_clips(self, video_path: str, events: List[Dict], output_dir: str = None) -> List[Dict]:
        """
        Extract video clips around each event.
        Checks if clips already exist and skips extraction if found.
        
        Args:
            video_path: Path to the source video
            events: List of event dictionaries
            output_dir: Directory to save clips (default: outputs/clips)
            
        Returns:
            List of events with added clip_path information
        """
        if output_dir is None:
            output_dir = config.CLIPS_DIR
        
        os.makedirs(output_dir, exist_ok=True)
        
        video_name = Path(video_path).stem
        clip_dir = os.path.join(output_dir, video_name)
        os.makedirs(clip_dir, exist_ok=True)
        
        # Get video properties first
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        events_with_clips = []
        clips_loaded = 0
        clips_extracted = 0
        
        for event_idx, event in enumerate(events):
            # Get event_id, defaulting to index+1 if not present (backwards compatibility)
            event_id = event.get('event_id', event_idx + 1)
            center_time = event.get('center_time', 0)
            
            # Generate clip filename
            clip_filename = f"event_{event_id:03d}_t{center_time:.2f}s.mp4"
            clip_path = os.path.join(clip_dir, clip_filename)
            
            # Check if clip already exists
            if os.path.exists(clip_path):
                # Clip exists, just add the path and ensure event_id is preserved
                event_with_clip = {
                    **event,
                    'event_id': event_id,  # Explicitly preserve event_id
                    'clip_path': clip_path
                }
                clips_loaded += 1
            else:
                # Clip doesn't exist, extract it
                center_frame = int(center_time * video_fps)
                clip_duration_frames = int(config.CLIP_DURATION_SECONDS * video_fps)
                clip_start_frame = max(0, center_frame - clip_duration_frames // 2)
                clip_end_frame = center_frame + clip_duration_frames // 2
                
                self._extract_clip_opencv(
                    video_path, video_fps, width, height, clip_start_frame, clip_end_frame, clip_path
                )
                
                event_with_clip = {
                    **event,
                    'event_id': event_id,  # Explicitly preserve event_id
                    'clip_path': clip_path
                }
                clips_extracted += 1
            
            events_with_clips.append(event_with_clip)
        
        if clips_loaded > 0:
            print(f"   📁 Loaded {clips_loaded} existing clips from cache")
        if clips_extracted > 0:
            print(f"   ✂️  Extracted {clips_extracted} new clips")
        
        return events_with_clips
    
    def _extract_clip_opencv(self, video_path: str, fps: float, width: int, height: int,
                             start_frame: int, end_frame: int, output_path: str):
        """
        Extract a clip from video using OpenCV.
        
        Args:
            video_path: Path to source video
            fps: Video frame rate
            width: Video width
            height: Video height
            start_frame: Starting frame number
            end_frame: Ending frame number
            output_path: Path to save the clip
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Seek to start frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Read and write frames
        current_frame = start_frame
        while current_frame <= end_frame:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
            current_frame += 1
        
        out.release()
        cap.release()


def format_timestamp(seconds: float) -> str:
    """
    Format seconds as HH:MM:SS.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
