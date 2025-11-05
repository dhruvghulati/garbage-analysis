"""
Report generation module for JSON and markdown outputs
"""
import os
import json
from typing import List, Dict
from datetime import datetime
import config


def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class ReportGenerator:
    """Generates JSON and markdown reports from event analysis"""
    
    def __init__(self, output_dir: str = None):
        """
        Initialize the report generator.
        
        Args:
            output_dir: Directory to save reports (default: outputs/reports)
        """
        self.output_dir = output_dir or config.REPORTS_DIR
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_json_report(self, video_url: str, video_info: Dict, 
                            events: List[Dict], output_filename: str = None) -> str:
        """
        Generate a JSON report with all event data.
        
        Args:
            video_url: Original YouTube URL
            video_info: Video metadata
            events: List of analyzed events
            output_filename: Output filename (default: auto-generated)
            
        Returns:
            Path to the generated JSON file
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"report_{timestamp}.json"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Build report structure
        report = {
            'metadata': {
                'video_url': video_url,
                'generated_at': datetime.now().isoformat(),
                'video_duration': video_info.get('duration', 0),
                'video_duration_formatted': format_timestamp(video_info.get('duration', 0)),
                'video_resolution': {
                    'width': video_info.get('width', 0),
                    'height': video_info.get('height', 0)
                },
                'video_fps': video_info.get('fps', 0),
                'total_events_detected': len(events)
            },
            'events': []
        }
        
        # Add sampling info if present
        if 'sampling_info' in video_info:
            report['metadata']['sampling_info'] = video_info['sampling_info']
        
        # Add events
        for event in events:
            vlm_analysis = event.get('vlm_analysis', {})
            
            event_data = {
                'event_id': event.get('event_id', 0),
                'timestamp': event.get('center_time', 0),
                'timestamp_formatted': format_timestamp(event.get('center_time', 0)),
                'start_time': event.get('start_time', 0),
                'start_time_formatted': format_timestamp(event.get('start_time', 0)),
                'end_time': event.get('end_time', 0),
                'end_time_formatted': format_timestamp(event.get('end_time', 0)),
                'duration': event.get('duration', 0),
                'frame_count': event.get('frame_count', 0),
                'detection_count': event.get('detections', 0),
                'event_type': vlm_analysis.get('event_type', 'No event detected'),
                'description': vlm_analysis.get('description', ''),
                'confidence': vlm_analysis.get('confidence', 'medium'),
                'detection_method': vlm_analysis.get('method', 'vlm'),  # Add this
                'clip_path': event.get('clip_path', ''),
                'analyzed_frame': event.get('analyzed_frame', '')
            }
            
            # Add overflow classification details if available
            overflow_class = event.get('overflow_classification', {})
            if overflow_class:
                event_data['overflow_detection'] = {
                    'method': overflow_class.get('method', 'yolo'),
                    'confidence': overflow_class.get('confidence', 0),
                    'overflowing_votes': overflow_class.get('overflowing_votes', 0),
                    'total_votes': overflow_class.get('total_votes', 0)
                }
            
            report['events'].append(event_data)
        
        # Write JSON file
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return output_path
    
    def generate_markdown_report(self, video_url: str, video_info: Dict,
                                 events: List[Dict], output_filename: str = None) -> str:
        """
        Generate a human-readable markdown report.
        
        Args:
            video_url: Original YouTube URL
            video_info: Video metadata
            events: List of analyzed events
            output_filename: Output filename (default: auto-generated)
            
        Returns:
            Path to the generated markdown file
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"report_{timestamp}.md"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Build markdown content
        lines = [
            "# Garbage Bin Event Detection Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Video Information",
            "",
            f"- **URL:** {video_url}",
            f"- **Duration:** {format_timestamp(video_info.get('duration', 0))}",
            f"- **Resolution:** {video_info.get('width', 0)}x{video_info.get('height', 0)}",
            f"- **FPS:** {video_info.get('fps', 0):.2f}",
            f"- **Total Events Detected:** {len(events)}",
            "",
            "---",
            ""
        ]
        
        # Add sampling info if present
        if 'sampling_info' in video_info:
            sampling_info = video_info['sampling_info']
            lines.extend([
                "## Sampling Information",
                "",
                f"- **Total Events:** {sampling_info.get('total_events', len(events))}",
                f"- **Events Analyzed with VLM:** {sampling_info.get('sampled_events', len(events))}",
                f"- **Sample Size:** {sampling_info.get('sample_size', 'N/A')}",
                f"- **Sampling Method:** {sampling_info.get('sampling_method', 'N/A')}",
                "",
                "---",
                ""
            ])
        
        lines.extend([
            "## Events Detected",
            ""
        ])
        
        if not events:
            lines.extend([
                "No events detected in this video.",
                ""
            ])
        else:
            for event in events:
                vlm_analysis = event.get('vlm_analysis', {})
                event_id = event.get('event_id', 0)
                timestamp = format_timestamp(event.get('center_time', 0))
                event_type = vlm_analysis.get('event_type', 'No event detected')
                description = vlm_analysis.get('description', 'No description available')
                confidence = vlm_analysis.get('confidence', 'medium')
                
                lines.extend([
                    f"### Event #{event_id} - {event_type}",
                    "",
                    f"**Timestamp:** {timestamp} ({event.get('center_time', 0):.2f}s)",
                    f"**Duration:** {event.get('duration', 0):.2f} seconds",
                    f"**Confidence:** {confidence.capitalize()}",
                    f"**Frames with Detections:** {event.get('frame_count', 0)}",
                    "",
                    f"**Description:**",
                    f"{description}",
                    "",
                    f"**Details:**",
                    f"- Start Time: {format_timestamp(event.get('start_time', 0))}",
                    f"- End Time: {format_timestamp(event.get('end_time', 0))}",
                    f"- Clip Path: `{event.get('clip_path', 'N/A')}`",
                    "",
                    "---",
                    ""
                ])
        
        # Write markdown file
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
        
        return output_path
    
    def generate_reports(self, video_url: str, video_info: Dict,
                        events: List[Dict], base_filename: str = None) -> Dict[str, str]:
        """
        Generate both JSON and markdown reports.
        
        Args:
            video_url: Original YouTube URL
            video_info: Video metadata
            events: List of analyzed events
            base_filename: Base filename (without extension)
            
        Returns:
            Dictionary with 'json' and 'markdown' keys containing file paths
        """
        if base_filename:
            json_filename = f"{base_filename}.json"
            md_filename = f"{base_filename}.md"
        else:
            json_filename = None
            md_filename = None
        
        json_path = self.generate_json_report(video_url, video_info, events, json_filename)
        md_path = self.generate_markdown_report(video_url, video_info, events, md_filename)
        
        return {
            'json': json_path,
            'markdown': md_path
        }
