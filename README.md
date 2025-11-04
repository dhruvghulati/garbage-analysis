# YouTube Garbage Bin Event Detection System

An AI-powered system that detects and analyzes garbage bin events in YouTube videos using object detection (YOLOv8) and vision language models (GPT-4 Vision).

## Features

- **Automatic Video Processing**: Downloads YouTube videos directly from URLs
- **Bin Detection**: Uses YOLOv8 to specifically detect garbage bins in video frames
- **Two-Stage Pipeline**: Separates bin detection from event classification for better accuracy
- **Hybrid Classification**: Uses YOLOv8 for overflow detection + GPT-4 Vision for complex events
- **Event Types**: Detects 4 specific operational events (missed collection, contamination, overflow, blocked access)
- **Interactive Dashboard**: Streamlit app for visualizing detections and events
- **Comprehensive Reports**: Generates JSON data and human-readable markdown reports

## Setup

### Prerequisites

- Python 3.8 or higher
- OpenAI API key

### Installation

1. Clone the repository and navigate to the project directory:
```bash
cd /Users/dhruvghulati/Documents/Coding/projects/garbage
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or create a `.env` file with:
```
OPENAI_API_KEY=your-api-key-here
```

## Usage

### Command Line Interface

Process a YouTube video:
```bash
python main.py --url "https://www.youtube.com/watch?v=O3fAVQ8Wm60"
```

Optional arguments:
- `--url`: YouTube video URL (required)
- `--output-dir`: Output directory (default: outputs)
- `--confidence`: Detection confidence threshold (default: 0.5)

### Streamlit Dashboard

Launch the interactive dashboard:
```bash
streamlit run app.py
```

The dashboard will be available at `http://localhost:8501`

## Project Structure

```
garbage/
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── config.py             # Configuration settings
├── main.py               # CLI entry point
├── app.py                # Streamlit dashboard
├── src/
│   ├── __init__.py
│   ├── video_processor.py    # Video download and frame extraction
│   ├── bin_detector.py       # YOLO object detection
│   ├── event_segmenter.py    # Event clustering and clip extraction
│   ├── vlm_analyzer.py       # GPT-4 Vision API integration
│   └── report_generator.py   # Report generation
├── outputs/
│   ├── videos/          # Downloaded videos
│   ├── frames/          # Extracted frames
│   ├── clips/           # Event clips
│   └── reports/         # JSON and markdown reports
└── tests/               # Test files
```

## Workflow

### Stage 1: Bin Detection & Clip Extraction
1. **Video Download**: Downloads video from YouTube URL using yt-dlp
2. **Frame Extraction**: Extracts frames at 1 FPS for processing
3. **Bin Detection**: Runs YOLOv8 to detect garbage bins specifically in each frame
4. **Event Clustering**: Groups consecutive bin detections into discrete events
5. **Clip Extraction**: Creates 10-second clips around each bin appearance

### Stage 2: Event Classification
6. **Overflow Detection**: Uses YOLOv8 classification model (if available) to detect overflowing bins
7. **VLM Analysis**: Uses GPT-4 Vision to analyze clips for complex events:
   - Bin missed / not collected
   - Contamination detected
   - Blocked access
8. **Report Generation**: Creates JSON and markdown reports with all findings
9. **Visualization**: Streamlit dashboard displays results interactively

## Configuration

Edit `config.py` to customize:
- Detection confidence thresholds
- Frame sampling rates
- Clip durations
- Event types to detect
- Output directories

## License

MIT
