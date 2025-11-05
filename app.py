"""
Streamlit dashboard for visualizing garbage bin event detection results
"""
import streamlit as st
import json
import os
import plotly.graph_objects as go
from pathlib import Path
from PIL import Image
import sys

# Load .env file BEFORE importing config
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

import config

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.vlm_analyzer import VLMAnalyzer
from src.video_processor import get_video_info
from analyze_clip import extract_clip_frames


def display_video(clip_path: str):
    """
    Display video in Streamlit with proper error handling.
    Uses bytes method for better compatibility with Streamlit's media server.
    
    Note: Videos created with 'mp4v' codec may not play in all browsers.
    For best compatibility, videos should be encoded with H.264 (avc1) codec.
    """
    if not clip_path or not os.path.exists(clip_path):
        return False
    
    # Convert to absolute path
    abs_path = os.path.abspath(clip_path)
    
    try:
        # Read video as bytes - this bypasses Streamlit's file path resolution
        # which can have issues with certain codecs
        with open(abs_path, 'rb') as video_file:
            video_bytes = video_file.read()
            
        # Check file size - warn if very large (might cause performance issues)
        file_size_mb = len(video_bytes) / (1024 * 1024)
        if file_size_mb > 50:
            st.warning(f"⚠️ Large video file ({file_size_mb:.1f} MB). Loading may take a moment...")
        
        # Use bytes directly - Streamlit will serve it through its media endpoint
        # format parameter helps browser understand the video type
        st.video(video_bytes, format='video/mp4')
        
        # Add download link as fallback and note about codec compatibility
        st.caption("💡 If video doesn't play, download it using the link below.")
        st.download_button(
            label="⬇️ Download Video",
            data=video_bytes,
            file_name=os.path.basename(abs_path),
            mime='video/mp4'
        )
        
        return True
    except Exception as e:
        # If bytes method fails, try path method as fallback
        try:
            st.video(abs_path)
            return True
        except Exception as e2:
            st.warning(f"⚠️ Could not load video. The video file may use an unsupported codec.")
            with st.expander("🔍 Video loading error details"):
                st.write(f"**Path:** `{abs_path}`")
                st.write(f"**File exists:** {os.path.exists(abs_path)}")
                if os.path.exists(abs_path):
                    file_size = os.path.getsize(abs_path)
                    st.write(f"**File size:** {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
                st.write(f"**Error:** {str(e2)}")
                st.info("💡 **Tip:** Videos created with 'mp4v' codec may not play in all browsers. Consider re-encoding with H.264 codec for better compatibility.")
            return False


def load_report_data(report_dir: str = None):
    """Load the most recent JSON report"""
    if report_dir is None:
        report_dir = config.REPORTS_DIR
    
    if not os.path.exists(report_dir):
        return None
    
    # Find most recent JSON report
    json_files = list(Path(report_dir).glob("*.json"))
    if not json_files:
        return None
    
    # Sort by modification time
    json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    latest_report = json_files[0]
    
    with open(latest_report, 'r') as f:
        return json.load(f)


def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def create_timeline_figure(events: list, video_duration: float):
    """Create a timeline visualization of events"""
    fig = go.Figure()
    
    # Add video duration bar
    fig.add_trace(go.Scatter(
        x=[0, video_duration],
        y=[0, 0],
        mode='lines',
        line=dict(color='lightgray', width=20),
        name='Video Duration',
        hoverinfo='skip'
    ))
    
    # Add event markers
    for event in events:
        timestamp = event['timestamp']
        event_type = event.get('event_type', 'Unknown')
        confidence = event.get('confidence', 'medium')
        
        # Color based on confidence
        color_map = {
            'high': 'green',
            'medium': 'orange',
            'low': 'red'
        }
        color = color_map.get(confidence.lower(), 'gray')
        
        fig.add_trace(go.Scatter(
            x=[timestamp],
            y=[0],
            mode='markers',
            marker=dict(
                size=15,
                color=color,
                symbol='diamond'
            ),
            name=f"Event {event['event_id']}: {event_type}",
            text=f"Event {event['event_id']}: {event_type}<br>{format_timestamp(timestamp)}",
            hovertemplate='<b>%{text}</b><extra></extra>'
        ))
    
    fig.update_layout(
        title="Event Timeline",
        xaxis_title="Time (seconds)",
        yaxis=dict(showticklabels=False, range=[-0.5, 0.5]),
        height=200,
        showlegend=False,
        hovermode='closest'
    )
    
    return fig


def analyze_clip_page():
    """Page for analyzing individual event clips"""
    st.header("🎬 Analyze Individual Event Clip")
    st.markdown("Analyze a single event clip using GPT-4 Vision to get a detailed narrative description.")
    
    st.markdown("---")
    
    # Find available clips
    clips_dir = config.CLIPS_DIR
    available_clips = []
    
    if os.path.exists(clips_dir):
        for root, dirs, files in os.walk(clips_dir):
            for file in files:
                if file.endswith('.mp4'):
                    clip_path = os.path.join(root, file)
                    available_clips.append(clip_path)
    
    if not available_clips:
        st.warning("No event clips found. Please run the analysis first using:")
        st.code("python main.py --url 'YOUR_YOUTUBE_URL'")
        return
    
    # Clip selection
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Display clips by relative path
        clip_display_names = [os.path.relpath(c, clips_dir) for c in available_clips]
        selected_display = st.selectbox("Select a clip to analyze", clip_display_names)
        selected_clip = os.path.join(clips_dir, selected_display)
    
    with col2:
        num_frames = st.number_input("Frames to analyze", min_value=3, max_value=10, value=5, step=1)
        max_cost = st.number_input("Max cost (USD)", min_value=0.1, max_value=5.0, value=0.5, step=0.1)
    
    # Get clip info
    clip_info = None
    if os.path.exists(selected_clip):
        # Convert to absolute path for Streamlit
        if not os.path.isabs(selected_clip):
            selected_clip = os.path.abspath(selected_clip)
        
        display_video(selected_clip)
        
        try:
            clip_info = get_video_info(selected_clip)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Duration", f"{clip_info['duration']:.2f}s")
            with col2:
                st.metric("Resolution", f"{clip_info['width']}x{clip_info['height']}")
            with col3:
                st.metric("FPS", f"{clip_info['fps']:.2f}")
            with col4:
                st.metric("Frames", clip_info['frame_count'])
        except Exception as e:
            st.error(f"Error getting clip info: {str(e)}")
    
    st.markdown("---")
    
    # Analyze button
    if st.button("🤖 Analyze Clip with GPT-4 Vision", type="primary"):
        if not os.path.exists(selected_clip):
            st.error(f"Clip file not found: {selected_clip}")
            return
        
        if clip_info is None:
            try:
                clip_info = get_video_info(selected_clip)
            except Exception as e:
                st.error(f"Error getting clip info: {str(e)}")
                return
        
        # Check for API key
        # Also check environment variable directly as fallback
        api_key = config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        
        if not api_key:
            st.error("OpenAI API key not found. Please:")
            st.markdown("""
            1. Create a `.env` file in the project root (you can copy from `.env.example`)
            2. Add your API key: `OPENAI_API_KEY=sk-your-key-here`
            3. Restart the Streamlit app (click the hamburger menu → "Rerun" or restart the server)
            
            Or set it as an environment variable:
            ```bash
            export OPENAI_API_KEY="your-key-here"
            ```
            """)
            
            # Debug info
            with st.expander("🔍 Debug Information"):
                st.write(f"Config file path: {Path(__file__).parent / 'config.py'}")
                st.write(f".env file path: {Path(__file__).parent / '.env'}")
                st.write(f".env exists: {(Path(__file__).parent / '.env').exists()}")
                st.write(f"config.OPENAI_API_KEY: {'SET' if config.OPENAI_API_KEY else 'NOT SET'}")
                st.write(f"os.getenv('OPENAI_API_KEY'): {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
            return
        
        # Update config if we got it from environment
        if not config.OPENAI_API_KEY and api_key:
            config.OPENAI_API_KEY = api_key
        
        with st.spinner("Analyzing clip..."):
            try:
                # Extract timestamp from filename
                clip_name = Path(selected_clip).stem
                timestamp = 0.0
                if '_t' in clip_name:
                    try:
                        timestamp = float(clip_name.split('_t')[1].replace('s', ''))
                    except:
                        pass
                
                # Extract frames
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Extracting frames...")
                frame_paths = extract_clip_frames(selected_clip, num_frames)
                progress_bar.progress(30)
                
                if not frame_paths:
                    st.error("Failed to extract frames from clip")
                    return
                
                # Analyze with VLM
                status_text.text(f"Analyzing {len(frame_paths)} frames with GPT-4 Vision...")
                analyzer = VLMAnalyzer(max_cost=max_cost)
                
                clip_info_dict = {
                    'timestamp': timestamp,
                    'duration': clip_info['duration'],
                    'clip_path': selected_clip
                }
                
                analysis = analyzer.analyze_clip_sequence(frame_paths, clip_info_dict)
                progress_bar.progress(100)
                status_text.text("Analysis complete!")
                
                # Display results
                st.markdown("---")
                st.header("📊 Analysis Results")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    event_type = analysis.get('event_type', 'Unknown')
                    st.metric("Event Type", event_type)
                
                with col2:
                    confidence = analysis.get('confidence', 'medium').upper()
                    confidence_colors = {
                        'HIGH': '🟢',
                        'MEDIUM': '🟡',
                        'LOW': '🔴'
                    }
                    st.metric("Confidence", f"{confidence_colors.get(confidence, '⚪')} {confidence}")
                
                with col3:
                    detection_method = analysis.get('method', 'vlm').upper()
                    st.metric("Detection Method", f"GPT-4 Vision ({detection_method})")
                
                st.markdown("---")
                
                # Description
                st.subheader("📝 Description")
                st.write(analysis.get('description', 'No description available'))
                
                # Narrative
                narrative = analysis.get('narrative', '')
                if narrative:
                    st.markdown("---")
                    st.subheader("📖 Narrative (What happened in the clip)")
                    st.write(narrative)
                
                # Cost and stats
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Cost", f"${analysis.get('cost', 0):.4f}")
                
                with col2:
                    st.metric("Frames Analyzed", analysis.get('frames_analyzed', 0))
                
                with col3:
                    cost_summary = analyzer.get_cost_summary()
                    st.metric("Budget Used", f"${cost_summary['total_cost']:.2f} / ${max_cost:.2f}")
                
                # Raw response (expandable)
                if 'raw_response' in analysis and analysis['raw_response']:
                    with st.expander("📄 View Raw VLM Response"):
                        st.text(analysis['raw_response'])
                
                # Display extracted frames
                if frame_paths:
                    st.markdown("---")
                    st.subheader("🎞️ Extracted Frames")
                    frame_cols = st.columns(min(3, len(frame_paths)))
                    for idx, frame_path in enumerate(frame_paths[:3]):
                        if os.path.exists(frame_path):
                            with frame_cols[idx % len(frame_cols)]:
                                img = Image.open(frame_path)
                                st.image(img, caption=f"Frame {idx+1}", use_container_width=True)
                
            except Exception as e:
                st.error(f"Error analyzing clip: {str(e)}")
                import traceback
                with st.expander("Error Details"):
                    st.code(traceback.format_exc())


def main():
    st.set_page_config(
        page_title="Garbage Bin Event Detection",
        page_icon="🗑️",
        layout="wide"
    )
    
    st.title("🗑️ Garbage Bin Event Detection Dashboard")
    
    # Create tabs
    tab1, tab2 = st.tabs(["📊 Event Reports", "🎬 Analyze Clip"])
    
    with tab1:
        st.markdown("---")
        
        # Load report data
        report_data = load_report_data()
        
        if report_data is None:
            st.warning("No report data found. Please run the analysis first using:")
            st.code("python main.py --url 'YOUR_YOUTUBE_URL'")
        else:
            display_report_view(report_data)
    
    with tab2:
        analyze_clip_page()


def display_report_view(report_data):
    """Display the main report view"""
    metadata = report_data.get('metadata', {})
    events = report_data.get('events', [])
    
    # Sidebar with video info
    with st.sidebar:
        st.header("Video Information")
        st.write(f"**URL:** {metadata.get('video_url', 'N/A')}")
        st.write(f"**Duration:** {metadata.get('video_duration_formatted', 'N/A')}")
        st.write(f"**Resolution:** {metadata.get('video_resolution', {}).get('width', 0)}x{metadata.get('video_resolution', {}).get('height', 0)}")
        st.write(f"**FPS:** {metadata.get('video_fps', 0):.2f}")
        st.write(f"**Total Events:** {len(events)}")
        
        # Show sampling info if present
        if 'sampling_info' in metadata:
            st.markdown("---")
            st.header("Sampling Information")
            sampling_info = metadata['sampling_info']
            st.write(f"**Total Events:** {sampling_info.get('total_events', len(events))}")
            st.write(f"**Analyzed:** {sampling_info.get('sampled_events', len(events))}")
            st.write(f"**Sample Size:** {sampling_info.get('sample_size', 'N/A')}")
            st.info("⚠️ Only sampled events were analyzed with VLM")
        
        st.markdown("---")
        
        # Filter options
        st.header("Filters")
        
        # Show sampled events filter if sampling was used
        if 'sampling_info' in metadata:
            show_filter = st.radio(
                "Show Events",
                ["All Events", "Sampled Only", "Unsampled Only"],
                index=0
            )
        else:
            show_filter = "All Events"
        
        event_types = ['All'] + list(set([e.get('event_type', 'Unknown') for e in events]))
        selected_event_type = st.selectbox("Event Type", event_types)
        
        confidence_levels = ['All', 'High', 'Medium', 'Low']
        selected_confidence = st.selectbox("Confidence", confidence_levels)
        
        # Apply filters
        filtered_events = events
        
        # Apply sampling filter first
        if show_filter == "Sampled Only":
            # Only show events that were actually analyzed (have real VLM analysis)
            filtered_events = [
                e for e in filtered_events 
                if e.get('vlm_analysis', {}).get('sampled', True) != False 
                and e.get('description', '') != 'Not analyzed (not in sample)'
            ]
        elif show_filter == "Unsampled Only":
            filtered_events = [
                e for e in filtered_events 
                if e.get('vlm_analysis', {}).get('sampled', True) == False 
                or e.get('description', '') == 'Not analyzed (not in sample)'
            ]
        
        if selected_event_type != 'All':
            filtered_events = [e for e in filtered_events if e.get('event_type') == selected_event_type]
        
        if selected_confidence != 'All':
            filtered_events = [e for e in filtered_events if e.get('confidence', '').lower() == selected_confidence.lower()]
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Event Timeline")
        if events:
            timeline_fig = create_timeline_figure(events, metadata.get('video_duration', 0))
            st.plotly_chart(timeline_fig, use_container_width=True)
        else:
            st.info("No events to display")
    
    with col2:
        st.subheader("Event Summary")
        st.metric("Total Events", len(events))
        st.metric("Filtered Events", len(filtered_events))
        
        # Event type distribution
        if events:
            event_type_counts = {}
            for event in events:
                event_type = event.get('event_type', 'Unknown')
                event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
            
            st.markdown("**By Event Type:**")
            for event_type, count in sorted(event_type_counts.items()):
                st.write(f"- {event_type}: {count}")
    
    st.markdown("---")
    
    # Events list
    st.subheader(f"Events ({len(filtered_events)} found)")
    
    if not filtered_events:
        st.info("No events match the selected filters.")
    else:
        for event in filtered_events:
            # Determine if event was sampled
            is_sampled = True
            vlm_analysis = event.get('vlm_analysis', {})
            if vlm_analysis.get('sampled', True) == False or event.get('description', '') == 'Not analyzed (not in sample)':
                is_sampled = False
            
            # Create title with sampled indicator
            title_parts = [f"Event #{event['event_id']}: {event.get('event_type', 'Unknown')}"]
            if 'sampling_info' in metadata:
                if is_sampled:
                    title_parts.append("🎲 SAMPLED")
                else:
                    title_parts.append("⏭️ NOT ANALYZED")
            
            with st.expander(
                f"{' | '.join(title_parts)} at {event.get('timestamp_formatted', 'N/A')}",
                expanded=False
            ):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Description:** {event.get('description', 'No description available')}")
                    st.write(f"**Timestamp:** {event.get('timestamp_formatted', 'N/A')} ({event.get('timestamp', 0):.2f}s)")
                    st.write(f"**Duration:** {event.get('duration', 0):.2f} seconds")
                    st.write(f"**Frames:** {event.get('frame_count', 0)}")
                    st.write(f"**Detections:** {event.get('detection_count', 0)}")
                    
                    # Show detection method and model info
                    vlm_analysis = event.get('vlm_analysis', {})
                    detection_method = vlm_analysis.get('method', 'vlm')
                    
                    if detection_method == 'yolo':
                        st.info("🤖 **Detected by:** YOLOv8 Overflow Classifier")
                        overflow_class = event.get('overflow_classification', {})
                        if overflow_class:
                            st.write(f"   - Overflow Confidence: {overflow_class.get('confidence', 0):.2%}")
                            st.write(f"   - Votes: {overflow_class.get('overflowing_votes', 0)}/{overflow_class.get('total_votes', 0)}")
                    else:
                        st.info("🤖 **Detected by:** GPT-4 Vision (VLM)")
                        frames_analyzed = vlm_analysis.get('frames_analyzed', 0)
                        if frames_analyzed:
                            st.write(f"   - Frames Analyzed: {frames_analyzed}")
                    
                    # Show overflow classification details if available
                    overflow_class = event.get('overflow_classification', {})
                    if overflow_class and event.get('event_type') == 'Overflowing bin or spillage':
                        st.markdown("---")
                        st.subheader("Overflow Detection Details")
                        st.write(f"**Method:** {overflow_class.get('method', 'yolo').upper()}")
                        st.write(f"**Confidence:** {overflow_class.get('confidence', 0):.2%}")
                        st.write(f"**Votes:** {overflow_class.get('overflowing_votes', 0)}/{overflow_class.get('total_votes', 0)} frames detected overflow")
                
                with col2:
                    confidence = event.get('confidence', 'medium').lower()
                    confidence_colors = {
                        'high': '🟢',
                        'medium': '🟡',
                        'low': '🔴'
                    }
                    st.write(f"**Confidence:** {confidence_colors.get(confidence, '⚪')} {confidence.capitalize()}")
                    
                    # Show analyzed frame if available
                    analyzed_frame = event.get('analyzed_frame', '')
                    if analyzed_frame and os.path.exists(analyzed_frame):
                        try:
                            img = Image.open(analyzed_frame)
                            st.image(img, caption="Analyzed Frame", use_container_width=True)
                        except Exception as e:
                            st.write(f"Could not load image: {str(e)}")
                
                with col3:
                    # Clip path info
                    clip_path = event.get('clip_path', '')
                    if clip_path:
                        st.write(f"**Clip:** `{os.path.basename(clip_path)}`")
                        if not display_video(clip_path):
                            st.warning(f"Clip file not found or could not be loaded: `{clip_path}`")
                    else:
                        st.info("No clip available")
                
                st.markdown("---")


# Streamlit entry point
if __name__ == '__main__':
    # Streamlit will run this when launched with 'streamlit run app.py'
    pass
# For streamlit, code at module level runs, so we call main() here
# But wrap in try-except to handle reloads gracefully
try:
    main()
except Exception as e:
    st.error(f"Error loading dashboard: {str(e)}")
    st.info("Make sure you have run the analysis first with: python main.py --url 'YOUR_URL'")
