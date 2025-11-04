"""
Streamlit dashboard for visualizing garbage bin event detection results
"""
import streamlit as st
import json
import os
import plotly.graph_objects as go
from pathlib import Path
from PIL import Image
import config


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


def main():
    st.set_page_config(
        page_title="Garbage Bin Event Detection",
        page_icon="🗑️",
        layout="wide"
    )
    
    st.title("🗑️ Garbage Bin Event Detection Dashboard")
    st.markdown("---")
    
    # Load report data
    report_data = load_report_data()
    
    if report_data is None:
        st.warning("No report data found. Please run the analysis first using:")
        st.code("python main.py --url 'YOUR_YOUTUBE_URL'")
        return
    
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
                        if os.path.exists(clip_path):
                            st.video(clip_path)
                        else:
                            st.warning("Clip file not found")
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
