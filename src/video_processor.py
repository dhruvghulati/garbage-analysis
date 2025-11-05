"""
Video processing module for downloading YouTube videos and extracting frames
"""
import os
import cv2
import yt_dlp
from typing import Tuple, List
from pathlib import Path
import config


def download_video(url_or_path: str, output_dir: str = None) -> str:
    """
    Download a YouTube video or use a local video file.
    Checks if video already exists and skips download if found.
    
    Args:
        url_or_path: YouTube video URL or local file path
        output_dir: Directory to save the video (default: outputs/videos)
        
    Returns:
        Path to the video file (local file or downloaded file)
    """
    # Check if input is a local file path
    if os.path.isfile(url_or_path):
        print(f"   📁 Using local video file: {url_or_path}")
        return url_or_path
    
    # Check if input looks like a URL (starts with http:// or https://)
    if not url_or_path.startswith(('http://', 'https://')):
        # Treat as local file path even if it doesn't exist (will raise error later)
        if os.path.exists(url_or_path):
            print(f"   📁 Using local video file: {url_or_path}")
            return url_or_path
        else:
            raise FileNotFoundError(f"Video file not found: {url_or_path}")
    
    # It's a URL, proceed with YouTube download
    url = url_or_path
    
    # Extract video ID from URL (handle playlist parameters)
    if 'v=' in url:
        video_id = url.split('v=')[-1].split('&')[0].split('#')[0]
        # Clean up URL to remove playlist parameters to download just the video
        if '&list=' in url or '&index=' in url:
            # Extract just the video ID part
            base_url = url.split('&')[0] if '&' in url else url
            if '?' in base_url and 'v=' in base_url:
                url = f"{base_url.split('?')[0]}?v={video_id}"
            else:
                url = f"https://www.youtube.com/watch?v={video_id}"
    else:
        video_id = 'video'
    
    if output_dir is None:
        output_dir = config.VIDEOS_DIR
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract video ID to get correct ID (may differ from URL parsing)
    ext = 'mp4'
    with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'noplaylist': True}) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            video_id = info.get('id', video_id)
            ext = info.get('ext', 'mp4')
        except Exception:
            # Fallback: use extracted ID from URL parsing
            pass
    
    # Check if video already exists
    video_path = os.path.join(output_dir, f"{video_id}.{ext}")
    if os.path.exists(video_path):
        print(f"   📁 Using existing video: {video_path}")
        return video_path
    
    # Video doesn't exist, proceed with download
    # Configure yt-dlp options
    # Use 'best' format which typically includes audio and doesn't require ffmpeg merging
    # If that's not available, fall back to mp4 formats
    ydl_opts = {
        'format': 'best[ext=mp4]/best[height<=720]/best',  # Prefer mp4, or best quality up to 720p, or best available
        'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'noplaylist': True,  # Download only the video, not the entire playlist
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'extractor_args': {'youtube': {'skip': ['dash', 'hls']}},
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Extract video info and download
        info = ydl.extract_info(url, download=True)
        video_id = info.get('id', 'video')
        ext = info.get('ext', 'mp4')
        video_path = os.path.join(output_dir, f"{video_id}.{ext}")
    
    return video_path


def extract_frames(video_path: str, output_dir: str = None, fps: int = None) -> List[str]:
    """
    Extract frames from a video at specified FPS.
    Checks if frames already exist and loads them instead of re-extracting.
    
    Args:
        video_path: Path to the video file
        output_dir: Directory to save frames (default: outputs/frames)
        fps: Frames per second to extract (default: from config)
        
    Returns:
        List of frame dictionaries with paths and metadata
    """
    if output_dir is None:
        output_dir = config.FRAMES_DIR
    if fps is None:
        fps = config.FRAME_SAMPLING_RATE
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a subdirectory for this video's frames
    video_name = Path(video_path).stem
    frame_dir = os.path.join(output_dir, video_name)
    os.makedirs(frame_dir, exist_ok=True)
    
    # Check if frames already exist
    existing_frames = sorted(Path(frame_dir).glob("frame_*.jpg"))
    if existing_frames:
        print(f"   📁 Found {len(existing_frames)} existing frames, loading from cache...")
        frame_paths = []
        for frame_file in existing_frames:
            # Extract timestamp from filename: frame_000001_t123.45.jpg
            filename = frame_file.stem
            try:
                parts = filename.split('_t')
                if len(parts) == 2:
                    timestamp = float(parts[1])
                    # Extract frame number
                    frame_num_part = parts[0].replace('frame_', '')
                    frame_number = int(frame_num_part) if frame_num_part.isdigit() else 0
                    extracted_index = int(frame_num_part) if frame_num_part.isdigit() else 0
                else:
                    timestamp = 0.0
                    frame_number = 0
                    extracted_index = 0
            except Exception:
                timestamp = 0.0
                frame_number = 0
                extracted_index = 0
            
            frame_paths.append({
                'path': str(frame_file),
                'frame_number': frame_number,
                'timestamp': timestamp,
                'extracted_index': extracted_index
            })
        
        return frame_paths
    
    # Frames don't exist, extract them
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(video_fps / fps)  # Extract every Nth frame
    
    frame_paths = []
    frame_count = 0
    extracted_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Extract frame at specified interval
        if frame_count % frame_interval == 0:
            timestamp = frame_count / video_fps
            frame_filename = f"frame_{extracted_count:06d}_t{timestamp:.2f}.jpg"
            frame_path = os.path.join(frame_dir, frame_filename)
            cv2.imwrite(frame_path, frame)
            frame_paths.append({
                'path': frame_path,
                'frame_number': frame_count,
                'timestamp': timestamp,
                'extracted_index': extracted_count
            })
            extracted_count += 1
        
        frame_count += 1
    
    cap.release()
    return frame_paths


def get_video_info(video_path: str) -> dict:
    """
    Get video metadata (duration, FPS, resolution, etc.)
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Dictionary with video information
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    cap.release()
    
    return {
        'fps': fps,
        'frame_count': frame_count,
        'duration': duration,
        'width': width,
        'height': height
    }
