# 🍪 YouTube Cookies Setup - Complete Guide

## ✅ Code Updated Successfully!

The system now supports cookie-based authentication. Here's everything you need to know.

## 🚀 Quick Start (3 Steps)

### Step 1: Export Cookies from Your Browser

**Recommended: Chrome/Edge Extension**

1. **Install Extension:**
   - Go to: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
   - Click "Add to Chrome"
   - Or search for "Get cookies.txt LOCALLY" in Chrome Web Store

2. **Export Cookies:**
   - Open https://www.youtube.com in your browser
   - **Make sure you're logged in** to your YouTube account
   - Click the extension icon (usually in the toolbar)
   - Click the "Export" button
   - Save the file as `cookies.txt` in your project directory (`/workspace/`)

### Step 2: Run the System

```bash
cd /workspace
python3 main.py --url "https://www.youtube.com/watch?v=O3fAVQ8Wm60&list=PLwv5VAcVPWTAOxC3DtsIANSrfBThdeUGw&index=71" --cookies cookies.txt --sample-size 10
```

### Step 3: View Results

```bash
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## 📋 Alternative Methods

### Firefox Users

1. Install "cookies.txt" extension: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/
2. Follow the same export steps as above

### Command Line (Advanced)

You can also use yt-dlp directly with browser cookies:

```bash
yt-dlp --cookies-from-browser chrome "https://www.youtube.com/watch?v=O3fAVQ8Wm60"
```

But for our system, the extension method is recommended.

## 🔍 What Changed in the Code

1. **Added `--cookies` argument** to `main.py`
2. **Updated `download_video()` function** to accept and use cookies file
3. **Automatic cookie detection** - system checks if cookies file exists before using it

## 📁 File Structure

After exporting cookies, your project should look like:

```
/workspace/
├── cookies.txt          ← Your exported cookies (don't commit to git!)
├── main.py
├── src/
├── COOKIES_GUIDE.md     ← Detailed guide
├── QUICK_START.md       ← Quick reference
└── ...
```

## 🛡️ Security Notes

⚠️ **Important Security Tips:**

1. **Don't commit cookies.txt to git**
   - Add to `.gitignore`: `echo "cookies.txt" >> .gitignore`

2. **Keep cookies private**
   - Don't share your cookies file
   - Cookies contain your authentication session

3. **Cookies expire**
   - Re-export cookies if they stop working
   - Cookies typically expire after days/weeks

## 🐛 Troubleshooting

### "Cookies file not found"
- Make sure `cookies.txt` is in the current directory
- Or provide full path: `--cookies /full/path/to/cookies.txt`

### "Still getting bot detection errors"
- Make sure you exported cookies while **logged in** to YouTube
- Try re-exporting cookies (old ones may have expired)
- Check that cookies file is in Netscape format (extensions do this automatically)

### "Cookies not working"
- Verify you're logged into YouTube in your browser
- Make sure you exported from `youtube.com` domain
- Try updating yt-dlp: `pip install --upgrade yt-dlp`

## 📚 More Information

- **Detailed Guide**: See `COOKIES_GUIDE.md` for all methods and troubleshooting
- **Quick Reference**: See `QUICK_START.md` for step-by-step instructions
- **Full Documentation**: See `README.md` for system overview

## ✅ Testing

Once you have cookies set up, test with:

```bash
python3 main.py --url "https://www.youtube.com/watch?v=O3fAVQ8Wm60" --cookies cookies.txt --sample-size 5
```

This will:
- ✅ Download the video using your cookies
- ✅ Process 5 sample events (fast & cost-effective)
- ✅ Generate reports
- ✅ Show you the system in action!

## 🎯 Next Steps

1. Export your cookies using the extension
2. Save as `cookies.txt` in `/workspace/`
3. Run the command above
4. View results in Streamlit dashboard

You're all set! 🎉
