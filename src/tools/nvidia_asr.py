"""
Speech-to-Text ASR Client using OpenAI Whisper
"""
import os
from typing import Dict, Any, Optional
from src.core.logging import get_logger

logger = get_logger(__name__)


class NVIDIAASRClient:
    """ASR Client using OpenAI Whisper for local transcription"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Whisper ASR client"""
        self.enabled = False
        self.model = None
        
        try:
            import whisper
            # Use base model for faster transcription (you can use 'small', 'medium', or 'large' for better accuracy)
            logger.info("🎤 Loading Whisper model...")
            self.model = whisper.load_model("base")
            self.enabled = True
            logger.info("✅ Whisper ASR initialized successfully")
        except ImportError:
            logger.warning("⚠️ openai-whisper not installed. Run: pip install openai-whisper")
        except Exception as e:
            logger.warning(f"⚠️ Whisper initialization failed: {e}")
    
    def transcribe_audio_file(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio using Whisper AI
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with transcription result
        """
        if not self.enabled:
            return {
                "success": True,
                "text": "",
                "message": "🎤 Audio recorded! Whisper not available. Please type below."
            }
        
        try:
            logger.info(f"🎤 Transcribing audio with Whisper: {audio_path}")
            
            # Transcribe with Whisper
            result = self.model.transcribe(audio_path, fp16=False)
            transcription = result["text"].strip()
            
            logger.info(f"✅ Transcription: {transcription}")
            
            return {
                "success": True,
                "text": transcription
            }
            
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            return {
                "success": True,
                "text": "",
                "message": f"🎤 Transcription failed: {str(e)[:60]}. Please type below."
            }


class WebAudioRecorder:
    """Web audio recording placeholder"""
    
    def __init__(self):
        logger.info("WebAudioRecorder initialized")
    
    def start_recording(self):
        pass
    
    def stop_recording(self) -> Optional[bytes]:
        return None
    
    def get_audio_data(self) -> Optional[bytes]:
        return None


# Singleton
_asr_client = None


def get_asr_client(api_key: Optional[str] = None) -> NVIDIAASRClient:
    """Get or create ASR client"""
    global _asr_client
    
    if _asr_client is None:
        _asr_client = NVIDIAASRClient(api_key)
    
    return _asr_client
