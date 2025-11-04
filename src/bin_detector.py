"""
Object detection module using YOLOv8 to detect garbage bins specifically
"""
import os
from ultralytics import YOLO
import cv2
import numpy as np
from typing import List, Dict, Tuple
import config


class BinDetector:
    """Detects garbage bins in video frames using YOLOv8"""
    
    def __init__(self, model_path: str = None, confidence_threshold: float = None):
        """
        Initialize the bin detector.
        
        Args:
            model_path: Path to custom YOLO bin detection model (None uses default YOLOv8n)
            confidence_threshold: Minimum confidence for detections (default: from config)
        """
        self.confidence_threshold = confidence_threshold or config.DETECTION_CONFIDENCE_THRESHOLD
        
        # Load YOLO model
        # TODO: Replace with bin-specific model from Vision_Based_Smart_Bins when available
        if model_path and os.path.exists(model_path):
            self.model = YOLO(model_path)
        else:
            # Use YOLOv8n for now - will be replaced with bin-specific model
            # For now, we'll detect all objects and filter for container-like objects
            self.model = YOLO('yolov8n.pt')
        
        # Container-like object classes that might be bins
        # COCO classes: bottle=39, cup=41, bowl=45
        # We'll use a broader approach and filter with VLM confirmation
        self.container_classes = {39, 41, 45}  # bottle, cup, bowl
    
    def detect_in_frame(self, frame_path: str) -> List[Dict]:
        """
        Detect objects (potentially bins) in a single frame.
        
        Args:
            frame_path: Path to the frame image
            
        Returns:
            List of detections, each with bbox, confidence, class_id, class_name
        """
        results = self.model(frame_path, conf=self.confidence_threshold)
        
        detections = []
        
        for result in results:
            boxes = result.boxes
            for i, box in enumerate(boxes):
                # Get bounding box coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0].cpu().numpy())
                class_id = int(box.cls[0].cpu().numpy())
                class_name = self.model.names[class_id]
                
                # Calculate bbox properties for filtering
                width = x2 - x1
                height = y2 - y1
                area = width * height
                aspect_ratio = height / width if width > 0 else 0
                
                detections.append({
                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                    'confidence': confidence,
                    'class_id': class_id,
                    'class_name': class_name,
                    'width': float(width),
                    'height': float(height),
                    'area': float(area),
                    'aspect_ratio': float(aspect_ratio),
                    'is_container_like': class_id in self.container_classes
                })
        
        return detections
    
    def detect_bins_in_frames(self, frame_paths: List[Dict]) -> List[Dict]:
        """
        Detect bins in multiple frames.
        Uses container-like object detection and filters by size/position.
        
        Args:
            frame_paths: List of frame dictionaries with 'path', 'timestamp', etc.
            
        Returns:
            List of frames with bin detections, including frame metadata and detected bins
        """
        results = []
        
        for frame_info in frame_paths:
            frame_path = frame_info['path']
            detections = self.detect_in_frame(frame_path)
            
            # Filter for potential bins
            # Criteria: container-like objects OR large objects that might be bins
            potential_bins = []
            for det in detections:
                # Filter for container-like objects or large objects
                is_large_object = det['area'] > 5000  # Threshold for large objects (bins are usually big)
                is_container = det['is_container_like']
                is_tall_object = det['aspect_ratio'] > 0.8 and det['aspect_ratio'] < 2.0  # Reasonable bin aspect ratio
                
                if is_container or (is_large_object and is_tall_object):
                    potential_bins.append(det)
            
            has_bin = len(potential_bins) > 0
            
            results.append({
                **frame_info,
                'detections': detections,
                'bin_detections': potential_bins,
                'has_bin': has_bin,
                'detection_count': len(detections),
                'bin_count': len(potential_bins)
            })
        
        return results
    
    def filter_bin_detections(self, frames_with_detections: List[Dict]) -> List[Dict]:
        """
        Filter frames to only those that likely contain bins.
        
        Args:
            frames_with_detections: List of frames with detection results
            
        Returns:
            Filtered list of frames that likely contain bins
        """
        return [f for f in frames_with_detections if f['has_bin']]


def format_timestamp(seconds: float) -> str:
    """
    Format seconds as HH:MM:SS.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
