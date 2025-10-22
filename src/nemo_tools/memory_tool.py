"""
NeMo Memory Tool for memory storage and retrieval
"""
from typing import Dict, Any
import uuid
from datetime import datetime
from src.core.logging import get_logger

logger = get_logger(__name__)

class NeMoMemoryTool:
    """Real NeMo memory management tool"""
    
    def __init__(self, memory_manager):
        """Initialize with memory manager"""
        self.memory_manager = memory_manager
        logger.info("NeMo Memory Tool initialized")
        
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute memory storage"""
        content = input_data.get("content")
        memory_type = input_data.get("type", "general")
        metadata = input_data.get("metadata", {})
        
        if not content:
            return {"success": False, "error": "No content provided for memory storage"}
            
        try:
            # Generate memory ID
            memory_id = str(uuid.uuid4())
            
            # Add timestamp if not provided
            if "timestamp" not in metadata:
                metadata["timestamp"] = datetime.now().isoformat()
                
            # Store memory
            logger.info(f"Storing memory: {memory_type} - {content[:50]}...")
            
            result = self.memory_manager.store_memory(
                content=content,
                metadata={
                    **metadata,
                    "type": memory_type,
                    "id": memory_id
                }
            )
            
            if result:
                logger.info(f"Memory stored successfully with ID: {memory_id}")
                return {
                    "success": True,
                    "memory_id": memory_id,
                    "type": memory_type,
                    "message": "Memory stored successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to store memory"
                }
                
        except Exception as e:
            logger.error(f"Memory storage failed: {e}")
            return {
                "success": False,
                "error": f"Memory storage failed: {str(e)}"
            }