# System Usage Guide

## Code Updates Completed ✅

The system has been updated to support:

1. **Local Video Files**: You can now process local MP4 files directly
2. **Playlist URL Handling**: URLs with playlist parameters are automatically cleaned to extract just the video
3. **Better Error Handling**: Improved handling of local vs. remote video sources

## Usage Options

### Option 1: Process a YouTube Video (requires authentication if blocked)

```bash
python3 main.py --url "https://www.youtube.com/watch?v=VIDEO_ID" --sample-size 10
```

### Option 2: Process a Local Video File (NEW!)

```bash
python3 main.py --url "/path/to/your/video.mp4" --sample-size 10
```

Or with a relative path:

```bash
python3 main.py --url "videos/my_garbage_truck_video.mp4" --sample-size 10
```

## YouTube Download Issue

If you encounter YouTube bot detection errors, you have these options:

### Solution 1: Use Browser Cookies

1. Export cookies from your browser (Chrome/Firefox)
2. Use the cookies file with yt-dlp

### Solution 2: Use Local Video Files

Download the video manually and use the local file path:

```bash
# Download video manually first
# Then process it:
python3 main.py --url "outputs/videos/O3fAVQ8Wm60.mp4" --sample-size 10
```

### Solution 3: Try Different Video

Some videos may be less restricted than others.

## What the System Does

1. **Downloads/loads video** from URL or local file
2. **Extracts frames** at 1 FPS
3. **Detects garbage bins** using YOLOv8
4. **Clusters events** - groups detections into discrete events
5. **Extracts clips** - creates 10-second clips around each event
6. **Analyzes events** - Uses GPT-4 Vision to classify event types:
   - Bin missed / not collected
   - Contamination detected
   - Overflowing bin or spillage
   - Blocked access
7. **Generates reports** - JSON and Markdown reports
8. **Dashboard** - Streamlit visualization

## Output Files

After processing, check:

- **Reports**: `outputs/reports/report_*.json` and `report_*.md`
- **Clips**: `outputs/clips/{video_id}/event_*.mp4`
- **Frames**: `outputs/frames/{video_id}/frame_*.jpg`
- **Videos**: `outputs/videos/{video_id}.mp4`

## View Results

Launch the Streamlit dashboard:

```bash
streamlit run app.py
```

Then open `http://localhost:8501` in your browser.
