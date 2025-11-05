# YouTube Garbage Bin Event Detection System

An AI-powered system that detects and analyzes garbage bin events in YouTube videos using object detection (YOLOv8) and vision language models (GPT-4 Vision).

## Features

- **Automatic Video Processing**: Downloads YouTube videos directly from URLs
- **Bin Detection**: Uses YOLOv8 to specifically detect garbage bins in video frames
- **Two-Stage Pipeline**: Separates bin detection from event classification for better accuracy
- **Hybrid Classification**: Uses YOLOv8 for overflow detection + GPT-4 Vision for complex events
- **Event Types**: Detects 4 specific operational events (missed collection, contamination, overflow, blocked access)
- **Event Detection Flags**: Clear indicators showing which ML model detected each event
- **Interactive Dashboard**: Streamlit app for visualizing detections and events with model attribution
- **Comprehensive Reports**: Generates JSON data and human-readable markdown reports

## Machine Learning Models

This system uses a **hybrid ML approach** combining multiple models for optimal accuracy:

### 1. YOLOv8n (Object Detection)
- **Purpose**: Initial bin detection in video frames
- **Model**: `yolov8n.pt` (YOLOv8 nano - pre-trained on COCO dataset)
- **Usage**: Detects all objects in frames, filters for container-like objects (bottles, cups, bowls) and large objects that could be bins
- **Location**: `src/bin_detector.py`
- **Output**: Bounding boxes and confidence scores for potential bins
- **Note**: Currently uses general object detection; can be replaced with a bin-specific trained model

### 2. YOLOv8 Classification Model (Optional)
- **Purpose**: Overflow detection (bin full/not full classification)
- **Model**: Custom classification model (2 classes: "not_full" and "full")
- **Usage**: Classifies frames from events to determine if bins are overflowing
- **Location**: `src/overflow_classifier.py`
- **Status**: Optional - if not available, falls back to GPT-4 Vision for overflow detection
- **Output**: Overflow probability and confidence scores
- **Method**: Consensus-based voting across multiple frames (start, middle, end)

### 3. GPT-4 Vision (gpt-4o)
- **Purpose**: Complex event classification and narrative description
- **Model**: OpenAI GPT-4o with vision capabilities
- **Usage**: Analyzes event clips to classify:
  - Bin missed / not collected
  - Contamination detected
  - Overflowing bin or spillage (if YOLO classifier unavailable)
  - Blocked access
- **Location**: `src/vlm_analyzer.py`
- **Input**: Multiple frames from event clips (typically 2-5 frames per event)
- **Output**: Event type, detailed description, confidence level, and narrative
- **Cost**: ~$0.01-0.03 per image depending on resolution

### Detection Pipeline

1. **Stage 1 - Bin Detection** (YOLOv8n):
   - Extracts frames at 1 FPS
   - Detects objects using YOLOv8n
   - Filters for potential bins (container-like objects, large objects)
   - Clusters detections into discrete events

2. **Stage 2 - Event Classification** (Hybrid):
   - **YOLO Overflow Classifier** (if available):
     - Analyzes frames from events
     - Returns overflow probability
     - If overflow detected → marks event as "Overflowing bin or spillage"
   - **GPT-4 Vision** (for remaining events):
     - Analyzes frames for complex events
     - Provides detailed descriptions and narratives
     - Returns event type and confidence

### Event Detection Flags

Each detected event includes:
- **Event Type**: One of the 4 operational events or "No event detected"
- **Detection Method**: `yolo` (YOLO overflow classifier) or `vlm` (GPT-4 Vision)
- **Confidence Level**: `high`, `medium`, or `low`
- **Model-Specific Details**:
  - YOLO: Overflow probability, votes, classification confidence
  - VLM: Raw response, frames analyzed, consensus votes

All detection flags are visible in:
- Streamlit dashboard (event details panel)
- JSON reports (`outputs/reports/*.json`)
- Markdown reports (`outputs/reports/*.md`)

## Setup

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (for GPT-4 Vision)
- (Optional) YOLOv8 classification model for overflow detection

### Installation

1. Clone the repository and navigate to the project directory:
```bash
cd /Users/dhruvghulati/Documents/Coding/projects/garbage-analysis
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set your OpenAI API key:

   **Option 1: Using .env file (Recommended)**
   
   Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` and add your API key:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```
   
   The `.env` file is automatically loaded by the application. Make sure it's in `.gitignore` (it already is).

   **Option 2: Environment variable**
   
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
   
   Get your API key from: https://platform.openai.com/api-keys
