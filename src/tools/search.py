"""
Search Tool for Memory Lane
Provides semantic memory search functionality
"""
from typing import Dict, Any, List, Optional
from src.core.logging import get_logger

logger = get_logger(__name__)


class SearchTool:
    """Tool for searching memories"""
    
    def __init__(self, memory_manager):
        """
        Initialize search tool
        
        Args:
            memory_manager: Memory manager instance (VectorMemoryManager)
        """
        self.memory_manager = memory_manager
        logger.info("Search Tool initialized")
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute memory search
        
        Args:
            input_data: Dictionary containing:
                - query: Search query string
                - limit: Maximum number of results (default: 5)
                - search_type: 'vector', 'keyword', or 'hybrid' (default: 'hybrid')
                
        Returns:
            Dictionary with search results
        """
        query = input_data.get("query", "")
        limit = input_data.get("limit", 5)
        search_type = input_data.get("search_type", "hybrid")
        
        if not query:
            return {
                "success": False,
                "error": "No search query provided",
                "memories": []
            }
        
        try:
            logger.info(f"Searching memories with query: '{query}', limit: {limit}, type: {search_type}")
            
            # Use appropriate search method based on memory manager capabilities
            if hasattr(self.memory_manager, 'hybrid_search') and search_type == "hybrid":
                memories = self.memory_manager.hybrid_search(query, limit=limit)
            elif hasattr(self.memory_manager, 'search_memories'):
                memories = self.memory_manager.search_memories(query, limit=limit)
            else:
                # Fallback for compatibility
                memories = self.memory_manager.search_memories(query, limit=limit)
            
            logger.info(f"Found {len(memories)} matching memories")
            
            return {
                "success": True,
                "query": query,
                "count": len(memories),
                "memories": memories
            }
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "memories": []
            }
    
    def search_by_type(self, memory_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search memories by type
        
        Args:
            memory_type: Type of memory (e.g., 'photo', 'voice_note', 'text_note')
            limit: Maximum number of results
            
        Returns:
            List of matching memories
        """
        try:
            logger.info(f"Searching memories by type: {memory_type}")
            
            # Filter memories by type
            all_memories = self.memory_manager.memories if hasattr(self.memory_manager, 'memories') else []
            
            filtered_memories = [
                m for m in all_memories
                if m.get("metadata", {}).get("type") == memory_type
            ]
            
            # Sort by timestamp (most recent first)
            filtered_memories.sort(
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )
            
            return filtered_memories[:limit]
            
        except Exception as e:
            logger.error(f"Search by type failed: {e}")
            return []
    
    def search_by_date(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Search memories within a date range
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            
        Returns:
            List of matching memories
        """
        try:
            logger.info(f"Searching memories between {start_date} and {end_date}")
            
            all_memories = self.memory_manager.memories if hasattr(self.memory_manager, 'memories') else []
            
            filtered_memories = [
                m for m in all_memories
                if start_date <= m.get("timestamp", "") <= end_date
            ]
            
            # Sort by timestamp
            filtered_memories.sort(
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )
            
            return filtered_memories
            
        except Exception as e:
            logger.error(f"Search by date failed: {e}")
            return []
