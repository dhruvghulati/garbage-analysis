# YouTube Cookies Extraction Guide

This guide shows you how to extract YouTube cookies from your browser to use with yt-dlp for downloading videos.

## Why Do You Need Cookies?

YouTube sometimes requires authentication to download videos. By exporting your browser cookies (which contain your login session), yt-dlp can authenticate as you and download videos that would otherwise be blocked.

## Method 1: Using Browser Extension (Easiest)

### Chrome/Edge/Brave (Chromium-based browsers)

1. **Install the "Get cookies.txt LOCALLY" extension:**
   - Chrome Web Store: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
   - Or search for "Get cookies.txt LOCALLY" in Chrome Web Store

2. **Export cookies:**
   - Go to https://www.youtube.com
   - Make sure you're logged in
   - Click the extension icon
   - Click "Export" button
   - Save the file as `cookies.txt` in your project directory

### Firefox

1. **Install the "cookies.txt" extension:**
   - Firefox Add-ons: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/
   - Or search for "cookies.txt" in Firefox Add-ons

2. **Export cookies:**
   - Go to https://www.youtube.com
   - Make sure you're logged in
   - Click the extension icon
   - Click "Export" button
   - Save the file as `cookies.txt` in your project directory

## Method 2: Using Browser Developer Tools (Manual)

### Chrome/Edge

1. **Open YouTube:**
   - Go to https://www.youtube.com
   - Make sure you're logged in

2. **Open Developer Tools:**
   - Press `F12` or `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Option+I` (Mac)
   - Go to the "Application" tab (Chrome) or "Storage" tab (Edge)

3. **Export cookies:**
   - In the left sidebar, expand "Cookies"
   - Click on `https://www.youtube.com`
   - Right-click on the cookies table
   - Select "Copy" or use a cookie export tool

4. **Convert to Netscape format:**
   - Use an online converter or browser extension
   - The format should be Netscape cookies format

### Firefox

1. **Open YouTube:**
   - Go to https://www.youtube.com
   - Make sure you're logged in

2. **Open Developer Tools:**
   - Press `F12` or `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Option+I` (Mac)
   - Go to the "Storage" tab

3. **Export cookies:**
   - In the left sidebar, expand "Cookies"
   - Click on `https://www.youtube.com`
   - Use the "cookies.txt" extension (recommended) or manually export

## Method 3: Using Command Line Tools

### Using yt-dlp's built-in cookie extraction

yt-dlp can extract cookies directly from your browser:

```bash
# For Chrome/Edge/Brave
yt-dlp --cookies-from-browser chrome https://www.youtube.com/watch?v=VIDEO_ID

# For Firefox
yt-dlp --cookies-from-browser firefox https://www.youtube.com/watch?v=VIDEO_ID

# For Safari (Mac)
yt-dlp --cookies-from-browser safari https://www.youtube.com/watch?v=VIDEO_ID
```

However, this method doesn't save cookies to a file, so you'll need to use the extension method for our use case.

## Method 4: Using Python Script (Alternative)

If you prefer, you can use a Python script to extract cookies. Install the required package:

```bash
pip install browser-cookie3
```

Then create a script to export cookies (this is a more advanced method).

## Using Cookies with the System

Once you have your `cookies.txt` file:

1. **Save the cookies file:**
   - Place `cookies.txt` in your project directory (`/workspace/`)
   - Or save it anywhere and note the path

2. **Run the system with cookies:**
   ```bash
   python3 main.py --url "https://www.youtube.com/watch?v=O3fAVQ8Wm60" --cookies cookies.txt --sample-size 10
   ```

3. **Or specify full path:**
   ```bash
   python3 main.py --url "https://www.youtube.com/watch?v=O3fAVQ8Wm60" --cookies /path/to/cookies.txt --sample-size 10
   ```

## Cookie File Format

The cookies file should be in **Netscape format** (also called cookies.txt format). It should look like this:

```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	FALSE	1234567890	SESSION_ID	value123
.youtube.com	TRUE	/	FALSE	1234567890	VISITOR_INFO1_LIVE	value456
```

The browser extensions mentioned above will automatically create this format.

## Troubleshooting

### Cookies not working?
- Make sure you're logged into YouTube in your browser
- Make sure you exported cookies from the correct domain (youtube.com)
- Check that the cookies file path is correct
- Try re-exporting cookies (they expire after some time)

### Cookies expired?
Cookies expire after a certain period. If you get authentication errors, re-export your cookies.

### Still getting bot detection?
- Try using `--cookies-from-browser` flag directly with yt-dlp
- Make sure you're using the latest version of yt-dlp: `pip install --upgrade yt-dlp`
- Some videos may still be restricted even with cookies

## Security Note

⚠️ **Important**: Your cookies file contains authentication information. Keep it secure:
- Don't commit `cookies.txt` to git (add it to `.gitignore`)
- Don't share your cookies file with others
- Delete cookies file if you no longer need it

## Quick Start (Recommended Method)

1. Install "Get cookies.txt LOCALLY" extension in Chrome/Edge
2. Go to https://www.youtube.com and log in
3. Click the extension icon and export cookies
4. Save as `cookies.txt` in your project directory
5. Run: `python3 main.py --url "YOUR_URL" --cookies cookies.txt --sample-size 10`

That's it! The system will use your cookies to authenticate with YouTube.
