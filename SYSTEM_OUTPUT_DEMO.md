# System Output Demonstration

## Overview

The YouTube Garbage Bin Event Detection System processes videos and generates comprehensive reports on detected garbage bin events. Here's what the system outputs:

## Output Structure

When you run the system on a video, it generates the following outputs:

### 1. **Video File** (`outputs/videos/`)
- Downloaded video file saved as `{video_id}.mp4`
- Used as the source for all analysis

### 2. **Extracted Frames** (`outputs/frames/{video_id}/`)
- Frames extracted at 1 FPS (configurable)
- Named: `frame_000001_t123.45.jpg` (frame number and timestamp)
- Used for bin detection and analysis

### 3. **Event Clips** (`outputs/clips/{video_id}/`)
- 10-second video clips around each detected bin event
- Named: `event_001_t123.45s.mp4`
- Used for VLM analysis and visualization

### 4. **JSON Report** (`outputs/reports/report_YYYYMMDD_HHMMSS.json`)
- Structured data with all detected events
- Contains metadata, event details, and analysis results

### 5. **Markdown Report** (`outputs/reports/report_YYYYMMDD_HHMMSS.md`)
- Human-readable report with event summaries
- Includes timestamps, descriptions, and confidence levels

## Sample JSON Report Structure

```json
{
  "metadata": {
    "video_url": "https://www.youtube.com/watch?v=O3fAVQ8Wm60",
    "generated_at": "2025-01-XX XX:XX:XX",
    "video_duration": 1234.56,
    "video_duration_formatted": "00:20:34",
    "video_resolution": {
      "width": 1920,
      "height": 1080
    },
    "video_fps": 30.0,
    "total_events_detected": 15,
    "sampling_info": {
      "total_events": 15,
      "sampled_events": 10,
      "sample_size": 10,
      "sampling_method": "random_bin_events"
    }
  },
  "events": [
    {
      "event_id": 1,
      "timestamp": 45.23,
      "timestamp_formatted": "00:00:45",
      "start_time": 40.23,
      "start_time_formatted": "00:00:40",
      "end_time": 50.23,
      "end_time_formatted": "00:00:50",
      "duration": 10.0,
      "frame_count": 10,
      "detection_count": 8,
      "event_type": "Overflowing bin or spillage",
      "description": "A garbage bin is visible with waste overflowing from the top. The bin appears to be overfilled with multiple items extending beyond the rim.",
      "confidence": "high",
      "clip_path": "outputs/clips/O3fAVQ8Wm60/event_001_t45.23s.mp4",
      "analyzed_frame": "outputs/frames/O3fAVQ8Wm60/frame_000045_t45.23.jpg"
    },
    {
      "event_id": 2,
      "timestamp": 123.45,
      "timestamp_formatted": "00:02:03",
      "event_type": "Bin missed / not collected",
      "description": "A garbage bin is visible but no collection vehicle or mechanical arm is present in the frame.",
      "confidence": "medium",
      ...
    }
  ]
}
```

## Event Types Detected

The system detects 4 specific operational events:

1. **Bin missed / not collected** - Bin visible but no mechanical claw/arm interacting
2. **Contamination detected** - Non-recyclable items in recycling bin
3. **Overflowing bin or spillage** - Bin filled to brim with waste protruding
4. **Blocked access** - Car or vehicle obstructing bin access
5. **No event detected** - Bin visible but no operational event identified

## Sample Markdown Report

```markdown
# Garbage Bin Event Detection Report

**Generated:** 2025-01-XX XX:XX:XX

## Video Information

- **URL:** https://www.youtube.com/watch?v=O3fAVQ8Wm60
- **Duration:** 00:20:34
- **Resolution:** 1920x1080
- **FPS:** 30.00
- **Total Events Detected:** 15

## Sampling Information

- **Total Events:** 15
- **Events Analyzed with VLM:** 10
- **Sample Size:** 10
- **Sampling Method:** random_bin_events

## Events Detected

### Event #1 - Overflowing bin or spillage

**Timestamp:** 00:00:45 (45.23s)
**Duration:** 10.00 seconds
**Confidence:** High
**Frames with Detections:** 10

**Description:**
A garbage bin is visible with waste overflowing from the top. The bin appears to be overfilled with multiple items extending beyond the rim.

**Details:**
- Start Time: 00:00:40
- End Time: 00:00:50
- Clip Path: `outputs/clips/O3fAVQ8Wm60/event_001_t45.23s.mp4`

---
```

## Streamlit Dashboard

The system includes an interactive Streamlit dashboard that visualizes:

- **Event Timeline**: Visual timeline showing when events occur
- **Event Summary**: Statistics and distribution of event types
- **Filter Options**: Filter by event type, confidence level, and sampling status
- **Event Details**: Expandable sections showing:
  - Event description
  - Timestamp and duration
  - Frame count and detections
  - Confidence level
  - Video clip player
  - Analyzed frame image

## Current Issue

**YouTube Download Blocking**: The system is currently encountering YouTube's bot detection, which requires authentication. To work around this:

1. **Use cookies**: Export cookies from your browser and use `--cookies` option with yt-dlp
2. **Use local video**: Modify the code to accept local video file paths directly
3. **Try different video**: Some videos may be less restricted than others

## Next Steps

To see the system in action:

1. **Provide a video file locally** - We can modify the code to process local videos
2. **Set up cookies** - Export YouTube cookies to bypass bot detection
3. **Try a different video URL** - Some videos may work without authentication

## Running the System

```bash
# Process a video with sampling (10 events)
python3 main.py --url "YOUR_YOUTUBE_URL" --sample-size 10

# View results in Streamlit dashboard
streamlit run app.py
```

## Output Locations

- **Videos**: `outputs/videos/{video_id}.mp4`
- **Frames**: `outputs/frames/{video_id}/frame_*.jpg`
- **Clips**: `outputs/clips/{video_id}/event_*.mp4`
- **Reports**: `outputs/reports/report_*.json` and `report_*.md`
