"""
Vision Language Model analyzer using GPT-4 Vision API
"""
import os
import base64
from typing import List, Dict, Optional
from openai import OpenAI
from PIL import Image
import config


class VLMAnalyzer:
    """Analyzes video events using GPT-4 Vision API"""
    
    # GPT-4o Vision pricing (as of 2024)
    # Standard resolution (<=1024x1024): $0.01 per image
    # High detail (>1024x1024): $0.03 per image
    COST_PER_STANDARD_IMAGE = 0.01  # USD
    COST_PER_HIGH_DETAIL_IMAGE = 0.03  # USD
    
    def __init__(self, api_key: str = None, model: str = None, max_cost: float = 1.0):
        """
        Initialize the VLM analyzer.
        
        Args:
            api_key: OpenAI API key (default: from config)
            model: Model name (default: from config)
            max_cost: Maximum cost in USD to spend (default: 1.0)
        """
        self.api_key = api_key or config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or in config.py")
        
        self.model = model or config.OPENAI_MODEL
        self.client = OpenAI(api_key=self.api_key)
        self.event_types = config.EVENT_TYPES
        self.max_cost = max_cost
        self.total_cost = 0.0
        self.images_analyzed = 0
        self.cost_exceeded = False
    
    def encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 for API.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _calculate_image_cost(self, image_path: str) -> float:
        """Calculate cost for analyzing an image based on resolution."""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                max_dimension = max(width, height)
                return self.COST_PER_STANDARD_IMAGE if max_dimension <= 1024 else self.COST_PER_HIGH_DETAIL_IMAGE
        except Exception:
            return self.COST_PER_STANDARD_IMAGE
    
    def _can_afford_analysis(self, image_path: str) -> tuple:
        """Check if we can afford to analyze an image."""
        if self.cost_exceeded:
            return False, 0.0
        cost = self._calculate_image_cost(image_path)
        return (self.total_cost + cost) <= self.max_cost, cost
    
    def get_cost_summary(self) -> Dict:
        """Get current cost tracking summary."""
        return {
            'total_cost': self.total_cost,
            'images_analyzed': self.images_analyzed,
            'max_cost': self.max_cost,
            'remaining_budget': max(0, self.max_cost - self.total_cost),
            'cost_exceeded': self.cost_exceeded,
            'budget_utilization': f"{(self.total_cost / self.max_cost * 100):.1f}%" if self.max_cost > 0 else "N/A"
        }
    
    def analyze_frame(self, frame_path: str, context: str = None) -> Dict:
        """
        Analyze a single frame using GPT-4 Vision.
        
        Args:
            frame_path: Path to the frame image
            context: Optional context about the video/event
            
        Returns:
            Dictionary with analysis results
        """
        # Check cost before proceeding
        can_afford, cost = self._can_afford_analysis(frame_path)
        if not can_afford:
            self.cost_exceeded = True
            return {
                'event_type': 'No event detected',
                'description': f'Cost limit reached (${self.max_cost:.2f}). Skipped analysis.',
                'confidence': 'low',
                'raw_response': None,
                'cost_exceeded': True
            }
        
        base64_image = self.encode_image(frame_path)
        
        # Build prompt
        # Filter out "No event detected" from the list shown to VLM
        # Filter out "No event detected" from the list shown to VLM
        event_types_filtered = [et for et in self.event_types if et != "No event detected"]
        event_types_list = "\n".join([f"- {et}" for et in event_types_filtered])
        
        prompt = f"""Analyze this image from a garbage collection video. You are looking at a clip where a garbage bin has been detected.

Identify if any of these specific events is occurring:
{event_types_list}

IMPORTANT: Focus on these specific scenarios:
- "Bin missed / not collected": The bin is visible but there is NO mechanical claw, arm, or collection equipment attached to or interacting with the bin
- "Contamination detected": You can see non-recyclable waste items mixed in with recyclable materials (e.g., plastic bottles in paper recycling, or vice versa)
- "Overflowing bin or spillage": The bin is filled to the brim and waste is protruding out or spilling over the edges
- "Blocked access": A car, vehicle, or obstacle is parked directly in front of the bin, preventing collection access

Please provide:
1. Which event type best matches what's happening (or "No event detected")
2. A detailed description of what you see and why this event is occurring
3. Confidence level (high/medium/low) that this is the detected event

Context: {context or "Garbage collection video - bin detected"}

Respond in the following format:
EVENT_TYPE: [event type from the list or "No event detected"]
DESCRIPTION: [detailed description]
CONFIDENCE: [high/medium/low]"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            # Track cost after successful API call
            self.total_cost += cost
            self.images_analyzed += 1
            
            result_text = response.choices[0].message.content
            
            # Parse response
            event_type = self._parse_event_type(result_text)
            description = self._parse_description(result_text)
            confidence = self._parse_confidence(result_text)
            
            return {
                'event_type': event_type,
                'description': description,
                'confidence': confidence,
                'raw_response': result_text,
                'cost': cost
            }
        
        except Exception as e:
            # Don't charge for failed requests
            return {
                'event_type': 'No event detected',
                'description': f'Error analyzing frame: {str(e)}',
                'confidence': 'low',
                'raw_response': None,
                'error': str(e),
                'cost': 0.0
            }
    
    def analyze_event(self, event: Dict, video_context: Dict = None) -> Dict:
        """
        Analyze an event using multiple frames from the clip for better context.
        
        Args:
            event: Event dictionary with frames and clip information
            video_context: Optional video metadata for context
            
        Returns:
            Event dictionary with added VLM analysis
        """
        # Stop if cost exceeded
        if self.cost_exceeded:
            return {
                **event,
                'vlm_analysis': {
                    'event_type': 'No event detected',
                    'description': f'Cost limit reached (${self.max_cost:.2f}). Skipped analysis.',
                    'confidence': 'low',
                    'cost_exceeded': True
                }
            }
        
        # Get all frames from the event
        event_frames = event.get('frames', [])
        
        if not event_frames:
            return {
                **event,
                'vlm_analysis': {
                    'event_type': 'No event detected',
                    'description': 'No frames available',
                    'confidence': 'low'
                }
            }
        
        # Sample 3-5 frames: start, middle, end
        sample_indices = [0, len(event_frames) // 2, len(event_frames) - 1]
        if len(event_frames) > 5:
            # Add more samples for longer events
            sample_indices = [
                0,
                len(event_frames) // 4,
                len(event_frames) // 2,
                3 * len(event_frames) // 4,
                len(event_frames) - 1
            ]
        
        sample_frames = [event_frames[i] for i in sample_indices if i < len(event_frames)]
        sample_frame_paths = [f.get('path') for f in sample_frames if f.get('path') and os.path.exists(f.get('path'))]
        
        if not sample_frame_paths:
            # Fallback to representative frame
            representative_frame = event.get('representative_frame', {})
            frame_path = representative_frame.get('path')
            if frame_path and os.path.exists(frame_path):
                sample_frame_paths = [frame_path]
            else:
                return {
                    **event,
                    'vlm_analysis': {
                        'event_type': 'No event detected',
                        'description': 'No valid frames found',
                        'confidence': 'low'
                    }
                }
        
        # Analyze multiple frames and get consensus
        # Limit to 1-2 frames per event to stay within budget
        max_frames_per_event = 2 if self.max_cost >= 1.0 else 1
        analyses = []
        
        for frame_path in sample_frame_paths[:max_frames_per_event]:
            # Check if we can afford this analysis
            if self.cost_exceeded:
                break
            
            context = f"Bin detected at timestamp {event.get('center_time', 0):.2f} seconds"
            if video_context:
                context += f" in a {video_context.get('duration', 0):.1f} second video"
            analysis = self.analyze_frame(frame_path, context)
            analyses.append(analysis)
            
            # Stop if cost exceeded after this frame
            if analysis.get('cost_exceeded', False):
                break
        
        # Get consensus - use the most confident event type
        if analyses:
            # Count event types
            event_type_counts = {}
            for analysis in analyses:
                event_type = analysis.get('event_type', 'No event detected')
                confidence = analysis.get('confidence', 'low')
                # Weight by confidence
                weight = {'high': 3, 'medium': 2, 'low': 1}.get(confidence, 1)
                event_type_counts[event_type] = event_type_counts.get(event_type, 0) + weight
            
            # Get most common event type
            if event_type_counts:
                consensus_event = max(event_type_counts.items(), key=lambda x: x[1])[0]
                # Get description from the analysis with this event type
                consensus_analysis = next((a for a in analyses if a.get('event_type') == consensus_event), analyses[0])
                
                total_event_cost = sum(a.get('cost', 0) for a in analyses)
                
                return {
                    **event,
                    'vlm_analysis': {
                        'event_type': consensus_event,
                        'description': consensus_analysis.get('description', ''),
                        'confidence': consensus_analysis.get('confidence', 'medium'),
                        'frames_analyzed': len([a for a in analyses if not a.get('cost_exceeded', False)]),
                        'consensus_votes': event_type_counts.get(consensus_event, 0),
                        'cost': total_event_cost,
                        'cost_exceeded': any(a.get('cost_exceeded', False) for a in analyses)
                    },
                    'analyzed_frames': sample_frame_paths[:len(analyses)]
                }
        
        # Fallback
        return {
            **event,
            'vlm_analysis': analyses[0] if analyses else {
                'event_type': 'No event detected',
                'description': 'Analysis failed',
                'confidence': 'low'
            }
        }
    
    def analyze_events(self, events: List[Dict], video_context: Dict = None) -> List[Dict]:
        """
        Analyze multiple events.
        
        Args:
            events: List of event dictionaries
            video_context: Optional video metadata
            
        Returns:
            List of events with VLM analysis added
        """
        analyzed_events = []
        
        print(f"   💰 Budget: ${self.max_cost:.2f} | Analyzing up to {len(events)} events...")
        
        for i, event in enumerate(events):
            if self.cost_exceeded:
                print(f"   ⚠️  Cost limit reached at event {i+1}/{len(events)}. Remaining events will be skipped.")
                # Mark remaining events as skipped
                for remaining_event in events[i:]:
                    analyzed_events.append({
                        **remaining_event,
                        'vlm_analysis': {
                            'event_type': 'No event detected',
                            'description': f'Cost limit reached. Skipped analysis.',
                            'confidence': 'low',
                            'cost_exceeded': True
                        }
                    })
                break
            
            analyzed_event = self.analyze_event(event, video_context)
            analyzed_events.append(analyzed_event)
            
            # Print progress periodically
            if (i + 1) % 10 == 0 or i == len(events) - 1:
                cost_summary = self.get_cost_summary()
                print(f"   📊 Progress: {i+1}/{len(events)} events | Cost: ${cost_summary['total_cost']:.2f} / ${self.max_cost:.2f} ({cost_summary['budget_utilization']})")
        
        # Final cost summary
        cost_summary = self.get_cost_summary()
        print(f"\n   💵 Final Cost: ${cost_summary['total_cost']:.2f} / ${self.max_cost:.2f}")
        print(f"   📸 Images Analyzed: {cost_summary['images_analyzed']}")
        print(f"   📊 Budget Utilization: {cost_summary['budget_utilization']}")
        
        return analyzed_events
    
    def analyze_clip_sequence(self, frame_paths: List[str], clip_info: Dict = None) -> Dict:
        """
        Analyze a video clip by examining multiple frames together to get a narrative description.
        
        Args:
            frame_paths: List of frame image paths from the clip
            clip_info: Optional information about the clip (duration, timestamp, etc.)
            
        Returns:
            Dictionary with analysis results including narrative description
        """
        if self.cost_exceeded:
            return {
                'event_type': 'No event detected',
                'description': f'Cost limit reached (${self.max_cost:.2f}). Skipped analysis.',
                'confidence': 'low',
                'narrative': '',
                'cost_exceeded': True
            }
        
        if not frame_paths:
            return {
                'event_type': 'No event detected',
                'description': 'No frames provided',
                'confidence': 'low',
                'narrative': ''
            }
        
        # Sample frames: start, 1/3, 2/3, end (or fewer if clip is short)
        num_frames = len(frame_paths)
        if num_frames <= 2:
            sample_indices = list(range(num_frames))
        elif num_frames <= 4:
            sample_indices = [0, num_frames - 1]
        else:
            sample_indices = [0, num_frames // 3, 2 * num_frames // 3, num_frames - 1]
        
        sample_frames = [frame_paths[i] for i in sample_indices if i < len(frame_paths)]
        
        # Limit to 3-5 frames to control cost
        max_frames = min(5, len(sample_frames))
        sample_frames = sample_frames[:max_frames]
        
        # Check if we can afford all frames
        total_cost_estimate = 0
        affordable_frames = []
        for frame_path in sample_frames:
            can_afford, cost = self._can_afford_analysis(frame_path)
            if not can_afford:
                break
            affordable_frames.append(frame_path)
            total_cost_estimate += cost
        
        if not affordable_frames:
            return {
                'event_type': 'No event detected',
                'description': 'Cost limit too low for analysis',
                'confidence': 'low',
                'narrative': ''
            }
        
        # Build prompt for sequence analysis
        event_types_filtered = [et for et in self.event_types if et != "No event detected"]
        event_types_list = "\n".join([f"- {et}" for et in event_types_filtered])
        
        context_info = ""
        if clip_info:
            timestamp = clip_info.get('timestamp', 0)
            duration = clip_info.get('duration', 0)
            context_info = f" This clip is from timestamp {timestamp:.2f}s and is {duration:.2f} seconds long."
        
        prompt = f"""You are analyzing a sequence of frames from a garbage collection video clip. These frames show what happened over time in a 10-second clip where a garbage bin was detected.

Analyze the sequence of frames to understand what happened in this clip. Look for temporal patterns and changes between frames.

Possible events to identify:
{event_types_list}

IMPORTANT: Focus on these specific scenarios:
- "Bin missed / not collected": The bin is visible but there is NO mechanical claw, arm, or collection equipment attached to or interacting with the bin throughout the clip
- "Contamination detected": Non-recyclable waste items mixed with recyclable materials
- "Overflowing bin or spillage": The bin is filled to the brim with waste protruding or spilling
- "Blocked access": A car, vehicle, or obstacle is parked directly in front of the bin, preventing access

Provide:
1. EVENT_TYPE: Which event type best matches what happened (or "No event detected")
2. DESCRIPTION: A detailed description of what you see in the clip
3. NARRATIVE: A chronological narrative description of what happened in the sequence - describe the flow of events from start to end of the clip
4. CONFIDENCE: Your confidence level (high/medium/low)

Context:{context_info}

Respond in this format:
EVENT_TYPE: [event type or "No event detected"]
DESCRIPTION: [detailed description]
NARRATIVE: [chronological narrative of what happened in the clip]
CONFIDENCE: [high/medium/low]"""

        # Encode all sample frames
        image_contents = []
        for frame_path in affordable_frames:
            base64_image = self.encode_image(frame_path)
            image_contents.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })
        
        # Build messages with all frames
        messages_content = [{"type": "text", "text": prompt}] + image_contents
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": messages_content
                    }
                ],
                max_tokens=800  # More tokens for narrative
            )
            
            # Calculate and track cost
            total_cost = 0
            for frame_path in affordable_frames:
                cost = self._calculate_image_cost(frame_path)
                total_cost += cost
            
            self.total_cost += total_cost
            self.images_analyzed += len(affordable_frames)
            
            result_text = response.choices[0].message.content
            
            # Parse response
            event_type = self._parse_event_type(result_text)
            description = self._parse_description(result_text)
            confidence = self._parse_confidence(result_text)
            narrative = self._parse_narrative(result_text)
            
            return {
                'event_type': event_type,
                'description': description,
                'narrative': narrative,
                'confidence': confidence,
                'raw_response': result_text,
                'frames_analyzed': len(affordable_frames),
                'cost': total_cost,
                'method': 'vlm'
            }
        
        except Exception as e:
            return {
                'event_type': 'No event detected',
                'description': f'Error analyzing clip: {str(e)}',
                'narrative': '',
                'confidence': 'low',
                'error': str(e),
                'cost': 0.0
            }
    
    def _parse_event_type(self, text: str) -> str:
        """Extract event type from response text"""
        text_lower = text.lower()
        
        # Check each event type
        for event_type in self.event_types:
            if event_type.lower() in text_lower:
                return event_type
        
        return 'No event detected'
    
    def _parse_description(self, text: str) -> str:
        """Extract description from response text"""
        lines = text.split('\n')
        for line in lines:
            if 'description:' in line.lower():
                return line.split(':', 1)[1].strip()
        
        # Fallback: return first substantial line
        for line in lines:
            if len(line.strip()) > 20:
                return line.strip()
        
        return text[:200]  # Return first 200 chars as fallback
    
    def _parse_confidence(self, text: str) -> str:
        """Extract confidence from response text"""
        text_lower = text.lower()
        
        if 'confidence: high' in text_lower or 'high confidence' in text_lower:
            return 'high'
        elif 'confidence: medium' in text_lower or 'medium confidence' in text_lower:
            return 'medium'
        elif 'confidence: low' in text_lower or 'low confidence' in text_lower:
            return 'low'
        
        return 'medium'  # Default
    
    def _parse_narrative(self, text: str) -> str:
        """Extract narrative description from response text"""
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'narrative:' in line.lower():
                # Get the narrative text (might span multiple lines)
                narrative_parts = [line.split(':', 1)[1].strip()]
                # Check next lines for continuation
                for j in range(i + 1, min(i + 10, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and not any(keyword in next_line.lower() for keyword in ['event_type:', 'description:', 'confidence:', 'narrative:']):
                        narrative_parts.append(next_line)
                    else:
                        break
                return ' '.join(narrative_parts)
        
        return ''
