"""
Real NeMo Agent implementation using NVIDIA NeMo Toolkit
"""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

try:
    from nemo.collections.asr.models import ASRModel
    NEMO_AVAILABLE = True
except Exception as _e:
    NEMO_AVAILABLE = False

from openai import OpenAI
from src.core.config import Config
from src.core.vector_memory import VectorMemoryManager
from src.core.logging import get_logger

logger = get_logger(__name__)

class NeMoMemoryAgent:
    """Real NeMo-based Memory Lane Agent"""
    
    def __init__(self, config: Config):
        """Initialize NeMo Agent"""
        self.config = config
        logger.info("Initializing NeMo Memory Agent")
        
        # Initialize VectorMemoryManager (only option)
        logger.info("Initializing VectorMemoryManager with FAISS + SQLite")
        self.memory_manager = VectorMemoryManager(
            config, 
            db_path=config.vector_db_path,
            embedding_model=config.embedding_model
        )
        
        # Initialize NVIDIA API client
        self.client = OpenAI(
            api_key=config.nvidia_api_key,
            base_url=config.nvidia_base_url
        )
        
        # Initialize NeMo models (ASR)
        self._init_nemo_models()
        
        # Initialize tools
        self.tools = self._init_tools()
        
    def _init_nemo_models(self):
        """Initialize NeMo models"""
        if NEMO_AVAILABLE:
            try:
                # Initialize ASR model
                logger.info("Loading NeMo ASR model...")
                # Common English CTC model; replace with your locale if needed
                self.asr_model = ASRModel.from_pretrained("stt_en_conformer_ctc_large")
                logger.info("NeMo ASR model loaded")
                self.nemo_ready = True
            except Exception as e:
                logger.error(f"Failed to load NeMo ASR model: {e}")
                self.asr_model = None
                self.nemo_ready = False
        else:
            self.asr_model = None
            self.nemo_ready = False
            
    def _init_tools(self):
        """Initialize NeMo-based tools"""
        from src.nemo_tools.memory_tool import NeMoMemoryTool
        from src.nemo_tools.asr_tool import NeMoASRTool
        from src.nemo_tools.qa_tool import NeMoQATool
        from src.nemo_tools.reminder_tool import NeMoReminderTool
        
        return {
            "memory": NeMoMemoryTool(self.memory_manager),
            "asr": NeMoASRTool(self.asr_model),
            "qa": NeMoQATool(None, self.memory_manager),
            "reminder": NeMoReminderTool(self.memory_manager)
        }
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input using NeMo agent"""
        logger.info(f"Processing input: {list(input_data.keys())}")
        
        # Determine input type and route to appropriate tool
        if "audio_file" in input_data:
            return self._process_audio(input_data)
        elif "image_path" in input_data:
            return self._process_image(input_data)  
        elif "text" in input_data:
            result = self._process_text(input_data)
            logger.info(f"QA tool returned: {result}")  # Add this line
            return result
        else:
            return {"success": False, "error": "Unknown input type"}
            
    def _process_audio(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process audio input using NeMo ASR"""
        logger.info("Processing audio with NeMo ASR")
        
        result = self.tools["asr"].execute(input_data)
        
        if result["success"]:
            # Store transcribed text as memory
            text = result["text"]
            memory_result = self.tools["memory"].execute({
                "content": text,
                "type": "voice_note",
                "metadata": {
                    "transcribed": True,
                    "confidence": result.get("confidence", 0.0),
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            return {
                "success": True,
                "text": text,
                "confidence": result.get("confidence", 0.0),
                "memory_id": memory_result.get("memory_id")
            }
        else:
            return result
            
    def _process_image(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process image input with vision AI"""
        logger.info("Processing image memory with vision AI")
        
        image_path = input_data.get("image_path")
        if not image_path:
            return {"success": False, "error": "No image path provided"}
        
        # Analyze image with vision tool
        from src.tools.vision import get_vision_tool
        vision_tool = get_vision_tool()
        analysis = vision_tool.analyze_image(image_path)
        
        if not analysis.get("success"):
            return analysis
        
        # Create rich memory content from analysis
        description = input_data.get('description', 'Family photo')
        content = f"Photo: {description}\n\n"
        content += f"Analysis: {analysis.get('description', 'No description')}\n"
        content += f"People detected: {analysis.get('people_detected', 0)}\n"
        content += f"Location: {analysis.get('location', 'Unknown')}\n"
        content += f"Activity: {analysis.get('activity', 'Unknown')}"
        
        # Store enriched image memory
        result = self.tools["memory"].execute({
            "content": content,
            "type": "photo",
            "metadata": {
                "image_path": image_path,
                "timestamp": datetime.now().isoformat(),
                "people_count": analysis.get('people_detected', 0),
                "location": analysis.get('location', 'Unknown'),
                "activity": analysis.get('activity', 'Unknown'),
                "vision_model": analysis.get('model', 'unknown')
            }
        })
        
        # Return the memory_id along with the success message
        if result.get("success"):
            return {"success": True, "memory_id": result.get("memory_id")}
        else:
            return result
        
    def _process_text(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process text input using NeMo QA"""
        logger.info("Processing text with NeMo QA")
        
        text = input_data["text"]
        
        # Check if it's a question or command
        if self._is_question(text):
            qa_result = self.tools["qa"].execute({"question": text})
            # Adapt the response to what the frontend expects
            if qa_result.get("success"):
                return {"success": True, "message": qa_result.get("answer", "I found some information but could not form a clear answer.")}
            else:
                return {"success": False, "message": qa_result.get("error", "An unknown error occurred in the QA tool.")}
        elif self._is_reminder(text):
            return self.tools["reminder"].execute({"text": text})
        else:
            # Store as memory
            return self.tools["memory"].execute({
                "content": text,
                "type": "text_note",
                "metadata": {"timestamp": datetime.now().isoformat()}
            })
            
    def _is_question(self, text: str) -> bool:
        """Check if text is a question"""
        question_words = ["who", "what", "when", "where", "why", "how", "?"]
        return any(word in text.lower() for word in question_words)
        
    def _is_reminder(self, text: str) -> bool:
        """Check if text is a reminder"""
        reminder_words = ["remind", "reminder", "schedule", "appointment"]
        return any(word in text.lower() for word in reminder_words)
        
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "nemo_available": NEMO_AVAILABLE,
            "nemo_ready": self.nemo_ready,
            "tools_loaded": len(self.tools),
            "memory_count": len(self.memory_manager.memories)
        }