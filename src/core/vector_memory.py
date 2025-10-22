"""
Vector-based memory storage using FAISS for vector search and SQLite for metadata
Replaces SimpleMemoryManager with semantic search capabilities
"""

import os
import json
import sqlite3
import uuid
import pickle
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import logging

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from src.core.logging import get_logger

logger = get_logger(__name__)


class VectorMemoryManager:
    """Vector-based memory manager using FAISS for similarity search and SQLite for metadata"""
    
    def __init__(self, config, db_path: str = "./data/vector_db", embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize vector memory manager
        
        Args:
            config: Application configuration
            db_path: Path to store database files
            embedding_model: Name of sentence transformer model for embeddings
        """
        self.config = config
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        
        # Initialize FAISS index
        self.index_path = self.db_path / "faiss.index"
        self.init_faiss_index()
        
        # Initialize SQLite database
        self.sqlite_path = self.db_path / "memories.db"
        self.init_sqlite_db()
        
        # Track number of vectors for new additions
        self.vector_count = self._get_vector_count()
        
        logger.info(f"VectorMemoryManager initialized with {self.vector_count} existing memories")
    
    def init_faiss_index(self):
        """Initialize or load FAISS index"""
        if self.index_path.exists():
            logger.info("Loading existing FAISS index")
            self.index = faiss.read_index(str(self.index_path))
        else:
            logger.info(f"Creating new FAISS index with dimension {self.embedding_dim}")
            # Using IndexFlatIP for inner product (cosine similarity after normalization)
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self._save_index()
    
    def init_sqlite_db(self):
        """Initialize SQLite database for metadata storage"""
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()
        
        # Create memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                vector_id INTEGER UNIQUE
            )
        """)
        
        # Create reminders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                scheduled_time TEXT,
                created_at TEXT NOT NULL,
                active BOOLEAN DEFAULT 1
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_timestamp 
            ON memories(timestamp DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_vector_id 
            ON memories(vector_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reminders_active 
            ON reminders(active)
        """)
        
        conn.commit()
        conn.close()
        logger.info("SQLite database initialized")
    
    def _save_index(self):
        """Save FAISS index to disk"""
        faiss.write_index(self.index, str(self.index_path))
    
    def _get_vector_count(self) -> int:
        """Get current number of vectors in FAISS index and sync with database"""
        # Get max vector_id from database to ensure consistency
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(vector_id) FROM memories")
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] is not None:
            # Use max vector_id + 1 as the next available ID
            return result[0] + 1
        else:
            # If no memories exist, check FAISS index
            return self.index.ntotal
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text using sentence transformer"""
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        # Normalize for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)
        return embedding.astype('float32')
    
    def store_memory(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """
        Store a new memory with vector embedding
        
        Args:
            content: Memory content text
            metadata: Additional metadata
            
        Returns:
            Memory ID
        """
        memory_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Generate embedding
        embedding = self._generate_embedding(content)
        
        # Add to FAISS index
        self.index.add(np.array([embedding]))
        vector_id = self.vector_count
        self.vector_count += 1
        
        # Store in SQLite
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO memories (id, content, timestamp, metadata, vector_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            memory_id,
            content,
            timestamp,
            json.dumps(metadata or {}),
            vector_id
        ))
        
        conn.commit()
        conn.close()
        
        # Save FAISS index periodically (every 10 memories)
        if self.vector_count % 10 == 0:
            self._save_index()
        
        logger.info(f"Memory saved with ID: {memory_id} | Vector ID: {vector_id} | Total: {self.vector_count}")
        return memory_id
    
    def search_memories(self, query: str, limit: int = 5, threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Search for memories using vector similarity
        
        Args:
            query: Search query text
            limit: Maximum number of results
            threshold: Minimum similarity threshold (0-1)
            
        Returns:
            List of relevant memories with similarity scores
        """
        logger.info(f"Searching memories with query: '{query}'")
        
        if self.vector_count == 0:
            logger.info("No memories to search")
            return []
        
        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        
        # Search in FAISS
        k = min(limit, self.vector_count)
        distances, indices = self.index.search(np.array([query_embedding]), k)
        
        # Retrieve memories from SQLite
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()
        
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:  # FAISS returns -1 for padding when fewer results than k
                continue
            
            similarity = float(dist)  # Inner product similarity
            if similarity < threshold:
                continue
            
            cursor.execute("""
                SELECT id, content, timestamp, metadata
                FROM memories
                WHERE vector_id = ?
            """, (int(idx),))
            
            row = cursor.fetchone()
            if row:
                memory_id, content, timestamp, metadata_str = row
                results.append({
                    "id": memory_id,
                    "content": content,
                    "timestamp": timestamp,
                    "metadata": json.loads(metadata_str),
                    "relevance": similarity,
                    "similarity_score": similarity
                })
        
        conn.close()
        
        logger.info(f"Found {len(results)} relevant memories for query: '{query}'")
        return results
    
    def hybrid_search(self, query: str, limit: int = 5, keyword_weight: float = 0.3) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector similarity and keyword matching
        
        Args:
            query: Search query
            limit: Maximum results
            keyword_weight: Weight for keyword matching (0-1)
            
        Returns:
            List of memories with combined scores
        """
        # Get vector search results
        vector_results = self.search_memories(query, limit * 2)  # Get more for re-ranking
        
        # Add keyword scoring
        query_words = set(query.lower().split())
        
        for result in vector_results:
            content_words = set(result['content'].lower().split())
            keyword_overlap = len(query_words & content_words) / len(query_words) if query_words else 0
            
            # Combine scores
            vector_weight = 1.0 - keyword_weight
            result['combined_score'] = (
                vector_weight * result['similarity_score'] +
                keyword_weight * keyword_overlap
            )
        
        # Sort by combined score and limit
        vector_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return vector_results[:limit]
    
    def search_by_metadata(self, metadata_filter: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search memories by metadata fields
        
        Args:
            metadata_filter: Dictionary of metadata fields to filter by
            limit: Maximum results
            
        Returns:
            List of matching memories
        """
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, content, timestamp, metadata
            FROM memories
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit * 10,))  # Get more, then filter
        
        results = []
        for row in cursor.fetchall():
            memory_id, content, timestamp, metadata_str = row
            metadata = json.loads(metadata_str)
            
            # Check if all filter criteria match
            match = all(
                metadata.get(key) == value
                for key, value in metadata_filter.items()
            )
            
            if match:
                results.append({
                    "id": memory_id,
                    "content": content,
                    "timestamp": timestamp,
                    "metadata": metadata
                })
                
                if len(results) >= limit:
                    break
        
        conn.close()
        return results
    
    def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory by ID"""
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, content, timestamp, metadata
            FROM memories
            WHERE id = ?
        """, (memory_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            memory_id, content, timestamp, metadata_str = row
            return {
                "id": memory_id,
                "content": content,
                "timestamp": timestamp,
                "metadata": json.loads(metadata_str)
            }
        return None
    
    def update_memory(self, memory_id: str, content: str = None, metadata: Dict[str, Any] = None) -> bool:
        """
        Update an existing memory
        
        Args:
            memory_id: ID of memory to update
            content: New content (if provided)
            metadata: New metadata (if provided)
            
        Returns:
            Success status
        """
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()
        
        if content:
            # Get vector_id for this memory
            cursor.execute("SELECT vector_id FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            
            if row:
                vector_id = row[0]
                
                # Generate new embedding
                new_embedding = self._generate_embedding(content)
                
                # Update in FAISS (remove old, add new at same position)
                # Note: This is a simplification. In production, you might need better index management
                self.index.reconstruct(vector_id, new_embedding)
                
                # Update content in SQLite
                cursor.execute("""
                    UPDATE memories
                    SET content = ?
                    WHERE id = ?
                """, (content, memory_id))
        
        if metadata is not None:
            cursor.execute("""
                UPDATE memories
                SET metadata = ?
                WHERE id = ?
            """, (json.dumps(metadata), memory_id))
        
        conn.commit()
        changes = conn.total_changes
        conn.close()
        
        if changes > 0:
            self._save_index()
            return True
        return False
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory
        
        Args:
            memory_id: ID of memory to delete
            
        Returns:
            Success status
        """
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM memories
            WHERE id = ?
        """, (memory_id,))
        
        conn.commit()
        changes = conn.total_changes
        conn.close()
        
        # Note: Deleting from FAISS requires rebuilding index
        # For simplicity, we'll leave the vector but it won't be found in SQLite
        
        return changes > 0
    
    def store_reminder(self, title: str, description: str, scheduled_time: str) -> str:
        """Store a reminder"""
        reminder_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO reminders (id, title, description, scheduled_time, created_at, active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (
            reminder_id,
            title,
            description,
            scheduled_time,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Reminder stored: {title}")
        return reminder_id
    
    def get_active_reminders(self) -> List[Dict[str, Any]]:
        """Get all active reminders"""
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, description, scheduled_time, created_at
            FROM reminders
            WHERE active = 1
            ORDER BY scheduled_time
        """)
        
        reminders = []
        for row in cursor.fetchall():
            reminder_id, title, description, scheduled_time, created_at = row
            reminders.append({
                "id": reminder_id,
                "title": title,
                "description": description,
                "scheduled_time": scheduled_time,
                "created_at": created_at,
                "active": True
            })
        
        conn.close()
        return reminders
    
    def delete_reminder(self, reminder_id: str) -> bool:
        """Delete or deactivate a reminder"""
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE reminders
            SET active = 0
            WHERE id = ?
        """, (reminder_id,))
        
        conn.commit()
        changes = conn.total_changes
        conn.close()
        
        return changes > 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics"""
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM memories")
        memory_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reminders WHERE active = 1")
        reminder_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT metadata FROM memories
        """)
        
        type_counts = {}
        for row in cursor.fetchall():
            metadata = json.loads(row[0])
            memory_type = metadata.get('type', 'unknown')
            type_counts[memory_type] = type_counts.get(memory_type, 0) + 1
        
        conn.close()
        
        return {
            "total_memories": memory_count,
            "active_reminders": reminder_count,
            "vector_count": self.vector_count,
            "index_size": self.index_path.stat().st_size if self.index_path.exists() else 0,
            "db_size": self.sqlite_path.stat().st_size if self.sqlite_path.exists() else 0,
            "memory_types": type_counts,
            "embedding_model": getattr(self.embedding_model, 'model_name_or_path', 'all-MiniLM-L6-v2'),
            "embedding_dimension": self.embedding_dim
        }
    
    def rebuild_index(self):
        """Rebuild FAISS index from SQLite data"""
        logger.info("Rebuilding FAISS index from database")
        
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT content, vector_id
            FROM memories
            ORDER BY vector_id
        """)
        
        # Create new index
        new_index = faiss.IndexFlatIP(self.embedding_dim)
        
        for content, vector_id in cursor.fetchall():
            embedding = self._generate_embedding(content)
            new_index.add(np.array([embedding]))
        
        conn.close()
        
        # Replace old index
        self.index = new_index
        self._save_index()
        self.vector_count = self.index.ntotal
        
        logger.info(f"Index rebuilt with {self.vector_count} vectors")
    
    def export_to_json(self, filepath: str = "memories_export.json"):
        """Export all memories to JSON file"""
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, content, timestamp, metadata
            FROM memories
            ORDER BY timestamp DESC
        """)
        
        memories = []
        for row in cursor.fetchall():
            memory_id, content, timestamp, metadata_str = row
            memories.append({
                "id": memory_id,
                "content": content,
                "timestamp": timestamp,
                "metadata": json.loads(metadata_str)
            })
        
        cursor.execute("""
            SELECT id, title, description, scheduled_time, created_at, active
            FROM reminders
        """)
        
        reminders = []
        for row in cursor.fetchall():
            reminder_id, title, description, scheduled_time, created_at, active = row
            reminders.append({
                "id": reminder_id,
                "title": title,
                "description": description,
                "scheduled_time": scheduled_time,
                "created_at": created_at,
                "active": bool(active)
            })
        
        conn.close()
        
        export_data = {
            "memories": memories,
            "reminders": reminders,
            "exported_at": datetime.now().isoformat(),
            "statistics": self.get_statistics()
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported {len(memories)} memories and {len(reminders)} reminders to {filepath}")
        
    def import_from_json(self, filepath: str):
        """Import memories from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        imported_memories = 0
        imported_reminders = 0
        
        # Import memories
        for memory in data.get('memories', []):
            self.store_memory(
                content=memory['content'],
                metadata=memory.get('metadata', {})
            )
            imported_memories += 1
        
        # Import reminders
        for reminder in data.get('reminders', []):
            if reminder.get('active', True):
                self.store_reminder(
                    title=reminder['title'],
                    description=reminder.get('description', ''),
                    scheduled_time=reminder.get('scheduled_time', '')
                )
                imported_reminders += 1
        
        # Save index after bulk import
        self._save_index()
        
        logger.info(f"Imported {imported_memories} memories and {imported_reminders} reminders")
    
    # Compatibility methods for backward compatibility with SimpleMemoryManager
    @property
    def memories(self) -> List[Dict[str, Any]]:
        """Get all memories (for backward compatibility)"""
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, content, timestamp, metadata
            FROM memories
            ORDER BY timestamp DESC
        """)
        
        memories = []
        for row in cursor.fetchall():
            memory_id, content, timestamp, metadata_str = row
            memories.append({
                "id": memory_id,
                "content": content,
                "timestamp": timestamp,
                "metadata": json.loads(metadata_str)
            })
        
        conn.close()
        return memories
    
    @property
    def reminders(self) -> List[Dict[str, Any]]:
        """Get all reminders (for backward compatibility)"""
        return self.get_active_reminders()