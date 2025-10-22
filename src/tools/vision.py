"""
Vision Tool for Memory Lane
Uses NVIDIA Nemotron Vision for image analysis and memory extraction
"""
import os
from typing import Dict, Any, Optional, List
from PIL import Image
import base64
from openai import OpenAI
from src.core.logging import get_logger
from src.core.rate_limiter import nvapi_rate_limiter

logger = get_logger(__name__)


class VisionTool:
    """Tool for processing images and extracting memories using NVIDIA Vision"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize vision tool with NVIDIA Nemotron Vision
        
        Args:
            api_key: NVIDIA API key (uses NVIDIA_API_KEY env var if not provided)
            base_url: NVIDIA API base URL
        """
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        self.base_url = base_url or os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        
        # Debug logging
        if self.api_key:
            logger.info(f"API key loaded: {self.api_key[:10]}...{self.api_key[-4:]}")
        else:
            logger.error("No API key found in environment!")
        
        if self.api_key:
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
                # NVIDIA Vision model - Nemotron Nano VL
                self.model_name = "nvidia/llama-3.1-nemotron-nano-vl-8b-v1"
                self.available = True
                logger.info(f"NVIDIA Vision Tool initialized with model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize NVIDIA Vision: {e}")
                self.client = None
                self.available = False
        else:
            logger.warning("NVIDIA API key not found, vision processing will be limited")
            self.client = None
            self.available = False
    
    def _encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 string
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze an image and extract memory information using NVIDIA Vision
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with analysis results
        """
        if not self.available:
            return self._fallback_analysis(image_path)
        
        try:
            logger.info(f"Analyzing image with NVIDIA Vision: {image_path}")
            nvapi_rate_limiter.wait()  # Wait before making the API call
            
            # Encode image to base64
            base64_image = self._encode_image(image_path)
            
            # Create prompt for memory extraction
            prompt = """Analyze this photo as if it's part of a personal memory collection for someone with dementia.

Please identify:
1. People in the photo (describe appearance, number visible, relationships)
2. Location or setting (indoor/outdoor, type of place)
3. Activity or event taking place
4. Important objects or details
5. Emotional context and atmosphere

Provide a warm, detailed description to help recall this memory."""
            
            # Call NVIDIA Vision API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.7,
                top_p=0.7,
                max_tokens=512
            )
            
            description = response.choices[0].message.content
            
            # Extract structured information
            result = {
                "success": True,
                "description": description,
                "people_detected": self._extract_people_count(description),
                "location": self._extract_location(description),
                "activity": self._extract_activity(description),
                "model": self.model_name
            }
            
            logger.info(f"Image analysis complete: {result['people_detected']} people detected")
            
            return result
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return self._fallback_analysis(image_path)
    
    def _fallback_analysis(self, image_path: str) -> Dict[str, Any]:
        """Fallback analysis when NVIDIA Vision is not available"""
        try:
            image = Image.open(image_path)
            
            return {
                "success": True,
                "description": f"Photo saved: {os.path.basename(image_path)} ({image.size[0]}x{image.size[1]})",
                "people_detected": 0,
                "location": "Unknown",
                "activity": "Unknown",
                "model": "basic"
            }
        except Exception as e:
            logger.error(f"Fallback analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_people_count(self, description: str) -> int:
        """Extract number of people from description"""
        description_lower = description.lower()
        
        for i in range(10, 0, -1):
            if f"{i} people" in description_lower or f"{i} person" in description_lower:
                return i
        
        if any(word in description_lower for word in ["group", "several people", "crowd"]):
            return 3
        elif any(word in description_lower for word in ["two people", "couple", "pair"]):
            return 2
        elif any(word in description_lower for word in ["person", "individual", "someone"]):
            return 1
        
        return 0
    
    def _extract_location(self, description: str) -> str:
        """Extract location from description"""
        description_lower = description.lower()
        
        locations = {
            "home": ["home", "house", "living room", "kitchen", "bedroom"],
            "outdoor": ["outdoor", "outside", "park", "garden", "beach"],
            "restaurant": ["restaurant", "cafe", "dining"],
            "office": ["office", "workplace", "desk"],
            "event": ["party", "celebration", "wedding", "birthday"]
        }
        
        for loc_type, keywords in locations.items():
            if any(kw in description_lower for kw in keywords):
                return loc_type
        
        return "Unknown"
    
    def _extract_activity(self, description: str) -> str:
        """Extract activity from description"""
        description_lower = description.lower()
        
        activities = {
            "celebration": ["birthday", "party", "celebration", "wedding"],
            "dining": ["eating", "dining", "meal", "dinner", "lunch"],
            "traveling": ["travel", "vacation", "trip", "tour"],
            "gathering": ["gathering", "meeting", "reunion", "visit"],
            "work": ["working", "meeting", "presentation"]
        }
        
        for activity_type, keywords in activities.items():
            if any(kw in description_lower for kw in keywords):
                return activity_type
        
        return "Unknown"
    
    def extract_faces(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Extract faces from image using NVIDIA Vision
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of detected faces with metadata
        """
        if not self.available:
            logger.warning("Face extraction not available without NVIDIA Vision")
            return []
        
        try:
            logger.info(f"Extracting faces from: {image_path}")
            
            base64_image = self._encode_image(image_path)
            
            prompt = "Describe each person visible in this photo. For each person, provide their appearance, position, and apparent relationship to others."
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.5,
                max_tokens=256
            )
            
            faces = [{
                "description": response.choices[0].message.content,
                "confidence": 0.85
            }]
            
            return faces
            
        except Exception as e:
            logger.error(f"Face extraction failed: {e}")
            return []


def get_vision_tool(api_key: Optional[str] = None) -> VisionTool:
    """
    Get or create vision tool singleton
    
    Args:
        api_key: Optional NVIDIA API key
        
    Returns:
        VisionTool instance
    """
    global _vision_tool
    
    if '_vision_tool' not in globals():
        _vision_tool = VisionTool(api_key)
    
    return _vision_tool
