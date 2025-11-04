"""
Configuration file for YouTube Bin Detection System
"""
import os
from typing import List

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o"  # Use gpt-4o or gpt-4-turbo for vision
MAX_VLM_COST_USD = float(os.getenv("MAX_VLM_COST_USD", "1.0"))  # Maximum cost in USD for VLM analysis per run

# Detection Configuration
DETECTION_CONFIDENCE_THRESHOLD = 0.5
# Note: YOLO COCO doesn't have a "trash can" class, so we detect all objects
# and let the VLM filter for actual bins

# Video Processing Configuration
FRAME_SAMPLING_RATE = 1  # Extract 1 frame per second
CLIP_DURATION_SECONDS = 10  # Total clip duration (5s before + 5s after event)

# Event Types to Detect
EVENT_TYPES: List[str] = [
    "Bin missed / not collected",  # Bin visible but no mechanical claw/arm interacting
    "Contamination detected",  # Non-recyclable items in recycling bin
    "Overflowing bin or spillage",  # Bin filled to brim with waste protruding
    "Blocked access",  # Car or vehicle obstructing bin access
    "No event detected"
]

# Output Directories
OUTPUT_DIR = "outputs"
VIDEOS_DIR = os.path.join(OUTPUT_DIR, "videos")
FRAMES_DIR = os.path.join(OUTPUT_DIR, "frames")
CLIPS_DIR = os.path.join(OUTPUT_DIR, "clips")
REPORTS_DIR = os.path.join(OUTPUT_DIR, "reports")

# Streamlit Configuration
STREAMLIT_PORT = 8501
STREAMLIT_HOST = "localhost"
