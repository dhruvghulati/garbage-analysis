#!/usr/bin/env python3
"""
Analyze a single event clip using VLM to get a narrative description
"""
import argparse
import sys
import os
import cv2
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.vlm_analyzer import VLMAnalyzer
from src.video_processor import get_video_info
import config


def extract_clip_frames(clip_path: str, num_frames: int = 5) -> List[str]:
    """
    Extract sample frames from a clip.
    
    Args:
        clip_path: Path to the video clip
        num_frames: Number of frames to extract (default: 5)
        
    Returns:
        List of frame file paths
    """
    # Create temporary directory for frames
    clip_name = Path(clip_path).stem
    temp_frame_dir = os.path.join(config.FRAMES_DIR, f"clip_{clip_name}")
    os.makedirs(temp_frame_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(clip_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open clip: {clip_path}")
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / video_fps if video_fps > 0 else 0
    
    frame_paths = []
    
    # Extract frames at evenly spaced intervals
    if frame_count > 0:
        step = max(1, frame_count // num_frames)
        for i in range(0, frame_count, step):
            if len(frame_paths) >= num_frames:
                break
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                timestamp = i / video_fps if video_fps > 0 else 0
                frame_filename = f"frame_{i:06d}_t{timestamp:.2f}.jpg"
                frame_path = os.path.join(temp_frame_dir, frame_filename)
                cv2.imwrite(frame_path, frame)
                frame_paths.append(frame_path)
    
    # Always include the last frame if we haven't already
    if frame_count > 0 and len(frame_paths) < num_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count - 1)
        ret, frame = cap.read()
        if ret:
            timestamp = (frame_count - 1) / video_fps if video_fps > 0 else 0
            frame_filename = f"frame_{frame_count-1:06d}_t{timestamp:.2f}.jpg"
            frame_path = os.path.join(temp_frame_dir, frame_filename)
            cv2.imwrite(frame_path, frame)
            if frame_path not in frame_paths:
                frame_paths.append(frame_path)
    
    cap.release()
    
    return frame_paths


def main():
    parser = argparse.ArgumentParser(
        description='Analyze a single event clip using VLM to get a narrative description'
    )
    parser.add_argument(
        '--clip',
        type=str,
        required=True,
        help='Path to the event clip file (e.g., outputs/clips/O3fAVQ8Wm60/event_007_t217.50s.mp4)'
    )
    parser.add_argument(
        '--max-cost',
        type=float,
        default=1.0,
        help='Maximum cost in USD for VLM analysis (default: 1.0)'
    )
    parser.add_argument(
        '--num-frames',
        type=int,
        default=5,
        help='Number of frames to extract from clip (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Check if clip exists
    if not os.path.exists(args.clip):
        print(f"❌ Error: Clip file not found: {args.clip}")
        sys.exit(1)
    
    print("=" * 60)
    print("Event Clip Analysis")
    print("=" * 60)
    print(f"\nClip: {args.clip}\n")
    
    try:
        # Get clip info
        print("📹 Getting clip information...")
        clip_info = get_video_info(args.clip)
        print(f"✅ Duration: {clip_info['duration']:.2f}s, {clip_info['width']}x{clip_info['height']}, {clip_info['fps']:.2f} FPS\n")
        
        # Extract frames
        print(f"🎞️  Extracting {args.num_frames} frames from clip...")
        frame_paths = extract_clip_frames(args.clip, args.num_frames)
        print(f"✅ Extracted {len(frame_paths)} frames\n")
        
        if not frame_paths:
            print("❌ Error: No frames extracted from clip")
            sys.exit(1)
        
        # Analyze with VLM
        print("🤖 Analyzing clip with GPT-4 Vision...")
        print(f"   💰 Budget: ${args.max_cost:.2f}\n")
        
        analyzer = VLMAnalyzer(max_cost=args.max_cost)
        
        # Extract timestamp from filename if possible
        clip_name = Path(args.clip).stem
        timestamp = 0.0
        if '_t' in clip_name:
            try:
                timestamp = float(clip_name.split('_t')[1].replace('s', ''))
            except:
                pass
        
        clip_info_dict = {
            'timestamp': timestamp,
            'duration': clip_info['duration'],
            'clip_path': args.clip
        }
        
        analysis = analyzer.analyze_clip_sequence(frame_paths, clip_info_dict)
        
        # Print results
        print("\n" + "=" * 60)
        print("ANALYSIS RESULTS")
        print("=" * 60)
        print(f"\n📋 Event Type: {analysis.get('event_type', 'Unknown')}")
        print(f"🎯 Confidence: {analysis.get('confidence', 'Unknown').upper()}")
        print(f"🤖 Detection Method: {analysis.get('method', 'vlm').upper()}")
        print(f"\n📝 Description:")
        print(f"   {analysis.get('description', 'No description available')}")
        
        narrative = analysis.get('narrative', '')
        if narrative:
            print(f"\n📖 Narrative (What happened in the clip):")
            print(f"   {narrative}")
        
        print(f"\n💰 Cost: ${analysis.get('cost', 0):.4f}")
        print(f"📸 Frames Analyzed: {analysis.get('frames_analyzed', 0)}")
        
        cost_summary = analyzer.get_cost_summary()
        print(f"\n📊 Total Budget Used: ${cost_summary['total_cost']:.2f} / ${args.max_cost:.2f} ({cost_summary['budget_utilization']})")
        
        # Show raw response if available
        if 'raw_response' in analysis and analysis['raw_response']:
            print(f"\n📄 Raw Response:")
            print("-" * 60)
            print(analysis['raw_response'])
        
        print("\n" + "=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n❌ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

