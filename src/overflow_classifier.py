"""
Overflow classification module using YOLOv8 to detect overflowing bins
"""
import os
from ultralytics import YOLO
from typing import Dict, Optional, List
import config


class OverflowClassifier:
    """Classifies bins as overflowing or not using YOLOv8 classification model"""
    
    def __init__(self, model_path: str = None):
        """
        Initialize the overflow classifier.
        
        Args:
            model_path: Path to YOLOv8 classification model (Full/Not Full)
                       If None, will try to use model from Vision_Based_Smart_Bins repo
        """
        self.model_path = model_path
        self.model = None
        
        # Try to load model if path provided
        if model_path and os.path.exists(model_path):
            try:
                self.model = YOLO(model_path)
            except Exception as e:
                print(f"Warning: Could not load overflow classification model from {model_path}: {e}")
        
        # If no model loaded, we'll use VLM for overflow detection instead
        self.has_model = self.model is not None
    
    def classify_frame(self, frame_path: str) -> Dict:
        """
        Classify a frame to determine if bin is overflowing.
        
        Args:
            frame_path: Path to the frame image
            
        Returns:
            Dictionary with classification results:
            {
                'is_overflowing': bool,
                'confidence': float,
                'method': 'yolo' or 'vlm_fallback'
            }
        """
        if not self.has_model:
            return {
                'is_overflowing': False,
                'confidence': 0.0,
                'method': 'no_model',
                'message': 'YOLOv8 overflow model not available, will use VLM'
            }
        
        try:
            results = self.model(frame_path)
            
            # YOLOv8 classification returns class probabilities
            # Assuming model has 2 classes: 'not_full' (0) and 'full' (1)
            if results and len(results) > 0:
                probs = results[0].probs
                if probs is not None:
                    # Get probability for 'full' class (class 1)
                    full_prob = float(probs.data[1] if len(probs.data) > 1 else 0.0)
                    not_full_prob = float(probs.data[0] if len(probs.data) > 0 else 0.0)
                    
                    is_overflowing = full_prob > 0.5
                    confidence = max(full_prob, not_full_prob)
                    
                    return {
                        'is_overflowing': is_overflowing,
                        'confidence': confidence,
                        'full_probability': full_prob,
                        'not_full_probability': not_full_prob,
                        'method': 'yolo'
                    }
            
            return {
                'is_overflowing': False,
                'confidence': 0.0,
                'method': 'yolo',
                'message': 'No classification results'
            }
        
        except Exception as e:
            return {
                'is_overflowing': False,
                'confidence': 0.0,
                'method': 'yolo',
                'error': str(e)
            }
    
    def classify_clip_frames(self, frame_paths: List[str], sample_count: int = 3) -> Dict:
        """
        Classify multiple frames from a clip and return consensus.
        
        Args:
            frame_paths: List of frame paths from the clip
            sample_count: Number of frames to sample (default: 3)
            
        Returns:
            Dictionary with classification results
        """
        if not frame_paths:
            return {
                'is_overflowing': False,
                'confidence': 0.0,
                'method': 'yolo'
            }
        
        # Sample frames (start, middle, end)
        sample_indices = [
            0,
            len(frame_paths) // 2,
            len(frame_paths) - 1
        ][:sample_count]
        
        sample_frames = [frame_paths[i] for i in sample_indices if i < len(frame_paths)]
        
        classifications = []
        for frame_path in sample_frames:
            if os.path.exists(frame_path):
                result = self.classify_frame(frame_path)
                if result.get('method') == 'yolo' and 'error' not in result:
                    classifications.append(result)
        
        if not classifications:
            return {
                'is_overflowing': False,
                'confidence': 0.0,
                'method': 'yolo',
                'message': 'No valid classifications'
            }
        
        # Consensus: if majority say overflowing, mark as overflowing
        overflowing_count = sum(1 for c in classifications if c.get('is_overflowing', False))
        avg_confidence = sum(c.get('confidence', 0) for c in classifications) / len(classifications)
        
        is_overflowing = overflowing_count > len(classifications) / 2
        
        return {
            'is_overflowing': is_overflowing,
            'confidence': avg_confidence,
            'overflowing_votes': overflowing_count,
            'total_votes': len(classifications),
            'method': 'yolo'
        }
