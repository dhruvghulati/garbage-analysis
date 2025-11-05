# Quick Start Guide - Using Cookies

## Step-by-Step Instructions

### 1. Export YouTube Cookies

**Easiest Method (Chrome/Edge):**
1. Install extension: "Get cookies.txt LOCALLY" from Chrome Web Store
   - Link: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
2. Go to https://www.youtube.com and **log in**
3. Click the extension icon
4. Click "Export" 
5. Save as `cookies.txt` in your project folder

**For Firefox:**
1. Install "cookies.txt" extension from Firefox Add-ons
2. Follow same steps as above

### 2. Run the System

Once you have `cookies.txt` in your project directory:

```bash
cd /workspace
python3 main.py --url "https://www.youtube.com/watch?v=O3fAVQ8Wm60&list=PLwv5VAcVPWTAOxC3DtsIANSrfBThdeUGw&index=71" --cookies cookies.txt --sample-size 10
```

### 3. View Results

After processing completes, launch the dashboard:

```bash
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## What Happens

1. ✅ Downloads video from YouTube (using your cookies for authentication)
2. ✅ Extracts frames at 1 FPS
3. ✅ Detects garbage bins using YOLOv8
4. ✅ Clusters detections into events
5. ✅ Extracts 10-second clips around each event
6. ✅ Analyzes 10 random events with GPT-4 Vision (cost-effective)
7. ✅ Generates JSON and Markdown reports
8. ✅ Creates interactive dashboard

## Output Files

After running, check:
- `outputs/reports/` - JSON and Markdown reports
- `outputs/clips/` - Video clips for each event
- `outputs/frames/` - Extracted frames
- `outputs/videos/` - Downloaded video

## Troubleshooting

**Cookies not working?**
- Make sure you exported cookies while logged into YouTube
- Check that `cookies.txt` is in the same directory or provide full path
- Try re-exporting cookies (they expire after some time)

**Still getting bot detection?**
- Make sure cookies file is in Netscape format (extensions do this automatically)
- Try updating yt-dlp: `pip install --upgrade yt-dlp`

**Need more help?**
- See `COOKIES_GUIDE.md` for detailed instructions
- See `README.md` for full system documentation
