#!/usr/bin/env python3
"""
Main CLI entry point for YouTube Bin Detection System
"""
import argparse
import sys
import random
import os
from pathlib import Path
import yt_dlp

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src import video_processor
from src.bin_detector import BinDetector
from src.event_segmenter import EventSegmenter
from src.vlm_analyzer import VLMAnalyzer
from src.overflow_classifier import OverflowClassifier
from src.report_generator import ReportGenerator
import config


def extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL"""
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('id', 'video')
    except Exception:
        # Fallback: try to extract ID from URL pattern
        if 'v=' in url:
            return url.split('v=')[-1].split('&')[0].split('#')[0]
        return 'video'


def main():
    parser = argparse.ArgumentParser(
        description='Detect and analyze garbage bin events in YouTube videos'
    )
    parser.add_argument(
        '--url',
        type=str,
        required=True,
        help='YouTube video URL or local video file path to process'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory (default: outputs)'
    )
    parser.add_argument(
        '--confidence',
        type=float,
        default=None,
        help=f'Detection confidence threshold (default: {config.DETECTION_CONFIDENCE_THRESHOLD})'
    )
    parser.add_argument(
        '--skip-download',
        action='store_true',
        help='Skip video download (use existing video file)'
    )
    parser.add_argument(
        '--skip-analysis',
        action='store_true',
        help='Skip VLM analysis (faster, but no event descriptions)'
    )
    parser.add_argument(
        '--sample-size',
        type=int,
        default=None,
        help='Sample size for VLM analysis (default: analyze all events)'
    )
    parser.add_argument(
        '--cookies',
        type=str,
        default=None,
        help='Path to cookies file (Netscape format) for YouTube authentication'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("YouTube Garbage Bin Event Detection System")
    print("=" * 60)
    
    # Determine if input is URL or local file
    is_local_file = os.path.isfile(args.url) if hasattr(os.path, 'isfile') else False
    if not is_local_file and not args.url.startswith(('http://', 'https://')):
        # Check if it's a relative path that exists
        is_local_file = os.path.exists(args.url)
    
    if is_local_file:
        print(f"\nProcessing local video file: {args.url}\n")
        video_id = Path(args.url).stem
    else:
        print(f"\nProcessing video: {args.url}\n")
        # Extract video ID for checking existing files
        video_id = extract_video_id(args.url)
    
    try:
        # Step 1: Download video (or use existing/local file)
        print("📥 Step 1/7: Checking video...")
        video_path = video_processor.download_video(args.url, cookies_file=args.cookies)
        print(f"✅ Video ready: {video_path}\n")
        
        # Step 2: Get video info
        print("ℹ️  Step 2/7: Extracting video information...")
        video_info = video_processor.get_video_info(video_path)
        print(f"✅ Video info: {video_info['duration']:.1f}s, {video_info['width']}x{video_info['height']}, {video_info['fps']:.2f} FPS\n")
        
        # Step 3: Extract frames (or load existing)
        print("🎞️  Step 3/7: Checking frames...")
        frames = video_processor.extract_frames(video_path)
        print(f"✅ Ready: {len(frames)} frames\n")
        
        # ============================================================
        # STAGE 1: Bin Detection & Clip Extraction
        # ============================================================
        print("\n" + "=" * 60)
        print("STAGE 1: Bin Detection & Clip Extraction")
        print("=" * 60 + "\n")
        
        # Step 4: Detect bins
        print("🔍 Step 4/7: Detecting bins in frames...")
        detector = BinDetector(confidence_threshold=args.confidence)
        frames_with_detections = detector.detect_bins_in_frames(frames)
        frames_with_bins = detector.filter_bin_detections(frames_with_detections)
        print(f"✅ Found bins in {len(frames_with_bins)} frames\n")
        
        if not frames_with_bins:
            print("⚠️  No bins detected in video. Exiting.")
            sys.exit(0)
        
        # Step 5: Cluster bin appearances into events
        print("📦 Step 5/7: Clustering bin appearances into events...")
        segmenter = EventSegmenter()
        events = segmenter.cluster_detections(frames_with_bins)
        print(f"✅ Identified {len(events)} bin appearance events\n")
        
        if not events:
            print("⚠️  No bin events clustered. Exiting.")
            sys.exit(0)
        
        # Step 6: Extract clips (or load existing)
        print("✂️  Step 6/7: Checking event clips...")
        events_with_clips = segmenter.extract_clips(video_path, events)
        print(f"✅ Ready: {len(events_with_clips)} clips\n")
        
        # ============================================================
        # STAGE 2: Event Classification
        # ============================================================
        print("\n" + "=" * 60)
        print("STAGE 2: Event Classification")
        print("=" * 60 + "\n")
        
        # Determine which events to analyze with VLM
        events_to_analyze = events_with_clips
        sample_size = args.sample_size
        
        if sample_size and sample_size > 0 and sample_size < len(events_with_clips):
            # Sample random events that have bins
            events_with_bins = [e for e in events_with_clips if e.get('has_bin', True)]
            if len(events_with_bins) >= sample_size:
                print(f"🎲 Sampling {sample_size} random events from {len(events_with_bins)} events with bins...")
                events_to_analyze = random.sample(events_with_bins, sample_size)
                print(f"✅ Selected {len(events_to_analyze)} events for VLM analysis\n")
            else:
                print(f"⚠️  Only {len(events_with_bins)} events have bins, analyzing all of them\n")
                events_to_analyze = events_with_bins
        else:
            print(f"📊 Analyzing all {len(events_with_clips)} events\n")
        
        # Step 7: Classify events
        analyzed_events_full = events_with_clips.copy()  # Keep all events
        analyzed_sample = events_to_analyze.copy()  # Only analyzed subset
        
        if not args.skip_analysis:
            print("🤖 Step 7/7: Classifying events (YOLO + GPT-4 Vision)...")
            
            # First, check for overflow using YOLO (if available)
            overflow_classifier = OverflowClassifier()
            if overflow_classifier.has_model:
                print("   📊 Checking overflow using YOLOv8 classifier...")
                for i, event in enumerate(analyzed_sample):
                    event_frames = event.get('frames', [])
                    frame_paths = [f.get('path') for f in event_frames if f.get('path')]
                    if frame_paths:
                        overflow_result = overflow_classifier.classify_clip_frames(frame_paths)
                        if overflow_result.get('is_overflowing', False):
                            analyzed_sample[i] = {
                                **event,
                                'vlm_analysis': {
                                    'event_type': 'Overflowing bin or spillage',
                                    'description': f"Bin detected as overflowing (confidence: {overflow_result.get('confidence', 0):.2f})",
                                    'confidence': 'high' if overflow_result.get('confidence', 0) > 0.7 else 'medium',
                                    'method': 'yolo',
                                    'overflow_confidence': overflow_result.get('confidence', 0)
                                },
                                'overflow_classification': overflow_result
                            }
                            print(f"   ✅ Event {i+1}: Overflowing bin detected (YOLO)")
            
            # Use VLM for events not classified as overflow
            print("   🔍 Analyzing events with GPT-4 Vision...")
            analyzer = VLMAnalyzer(max_cost=config.MAX_VLM_COST_USD if hasattr(config, 'MAX_VLM_COST_USD') else 1.0)
            events_needing_vlm = [
                e for e in analyzed_sample 
                if 'vlm_analysis' not in e or e.get('vlm_analysis', {}).get('event_type') != 'Overflowing bin or spillage'
            ]
            
            if events_needing_vlm:
                vlm_analyzed = analyzer.analyze_events(events_needing_vlm, video_info)
                # Merge VLM results back
                vlm_dict = {e.get('event_id'): e for e in vlm_analyzed}
                for i, event in enumerate(analyzed_sample):
                    event_id = event.get('event_id')
                    if event_id in vlm_dict:
                        analyzed_sample[i] = vlm_dict[event_id]
            
            # Merge analyzed sample back into full list
            analyzed_dict = {e.get('event_id'): e for e in analyzed_sample}
            for i, event in enumerate(analyzed_events_full):
                event_id = event.get('event_id')
                if event_id in analyzed_dict:
                    analyzed_events_full[i] = analyzed_dict[event_id]
                else:
                    # Mark unanalyzed events
                    analyzed_events_full[i] = {
                        **event,
                        'vlm_analysis': {
                            'event_type': 'No event detected',
                            'description': 'Not analyzed (not in sample)',
                            'confidence': 'low',
                            'sampled': False
                        }
                    }
            
            print(f"✅ Classified {len(analyzed_sample)} events (out of {len(analyzed_events_full)} total)\n")
        else:
            print("⏭️  Skipping event classification...\n")
        
        # Generate reports
        print("📊 Generating reports...")
        report_gen = ReportGenerator()
        
        # Add sampling metadata to video_info for reports
        report_video_info = video_info.copy()
        if sample_size and len(analyzed_sample) < len(analyzed_events_full):
            report_video_info['sampling_info'] = {
                'total_events': len(analyzed_events_full),
                'sampled_events': len(analyzed_sample),
                'sample_size': sample_size,
                'sampling_method': 'random_bin_events'
            }
        
        reports = report_gen.generate_reports(args.url, report_video_info, analyzed_events_full)
        print(f"✅ JSON report: {reports['json']}")
        print(f"✅ Markdown report: {reports['markdown']}\n")
        
        print("=" * 60)
        print("✅ Processing complete!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  - Total events detected: {len(analyzed_events_full)}")
        if sample_size and len(analyzed_sample) < len(analyzed_events_full):
            print(f"  - Events analyzed with VLM: {len(analyzed_sample)}")
        print(f"  - Reports saved to: {config.REPORTS_DIR}")
        print(f"  - Clips saved to: {config.CLIPS_DIR}")
        print(f"\nRun 'streamlit run app.py' to visualize results\n")
        
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
