"""
NeMo ASR Tool for real speech-to-text processing
"""
from typing import Dict, Any, Optional

# Optional imports for audio processing
try:
    import torch
    import librosa
    import numpy as np
    AUDIO_LIBS_AVAILABLE = True
except ImportError:
    AUDIO_LIBS_AVAILABLE = False

from src.core.logging import get_logger

logger = get_logger(__name__)

if not AUDIO_LIBS_AVAILABLE:
    logger.warning("Audio libraries (torch/librosa) not installed, using API fallback")

class NeMoASRTool:
    """Real NeMo ASR tool"""
    
    def __init__(self, asr_model):
        """Initialize with NeMo ASR model"""
        self.asr_model = asr_model
        self.model_ready = asr_model is not None
        logger.info(f"NeMo ASR Tool initialized, model ready: {self.model_ready}")
        
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ASR transcription"""
        audio_file = input_data.get("audio_file")
        
        if not audio_file:
            return {"success": False, "error": "No audio file provided"}
            
        try:
            if self.model_ready and AUDIO_LIBS_AVAILABLE:
                # Use real NeMo ASR model
                logger.info(f"Transcribing audio with NeMo: {audio_file}")
                
                # Load and preprocess audio
                audio, sr = librosa.load(audio_file, sr=16000)
                
                # Transcribe using NeMo model
                transcription = self.asr_model.transcribe([audio_file])
                text = transcription[0] if transcription else ""
                
                # Calculate confidence (simplified)
                confidence = 0.95 if text else 0.0
                
                logger.info(f"Transcription result: {text}")
                
                return {
                    "success": True,
                    "text": text,
                    "confidence": confidence,
                    "model": "nemo-asr"
                }
                
            else:
                # Fallback to NVIDIA API
                logger.info("Using NVIDIA ASR API fallback")
                from src.tools.nvidia_asr import get_asr_client
                asr_client = get_asr_client()
                result = asr_client.transcribe_audio_file(audio_file)
                
                if result["success"]:
                    return {
                        "success": True,
                        "text": result["text"],
                        "confidence": result.get("confidence", 0.9),
                        "model": "nvidia-api"
                    }
                else:
                    return result
                    
        except Exception as e:
            logger.error(f"ASR transcription failed: {e}")
            return {
                "success": False,
                "error": f"Transcription failed: {str(e)}"
            }