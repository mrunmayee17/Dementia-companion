"""
Configuration management for Memory Lane
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class Config:
    """Application configuration"""
    
    # NVIDIA API Configuration
    nvidia_api_key: str = field(default_factory=lambda: os.getenv("NVIDIA_API_KEY", ""))
    nvidia_base_url: str = field(default_factory=lambda: os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"))
    model_name: str = "nvidia/llama-3.1-nemotron-51b-instruct"
    
    # Vector Database Configuration
    vector_db_path: str = field(default_factory=lambda: os.getenv("VECTOR_DB_PATH", "./data/vector_db"))
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
    
    # Agent Configuration
    agent_name: str = "Memory Lane Assistant"
    temperature: float = 0.7
    max_tokens: int = 300
    
    # Memory Settings
    max_search_results: int = 5
    memory_retention_days: int = 365
    similarity_threshold: float = 0.3  # Minimum similarity for vector search
    hybrid_search_keyword_weight: float = 0.3  # Weight for keyword matching in hybrid search
    
    @classmethod
    def from_file(cls, path: str) -> "Config":
        """Load configuration from YAML file"""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "nvidia_api_key": self.nvidia_api_key,
            "nvidia_base_url": self.nvidia_base_url,
            "model_name": self.model_name,
            "db_path": self.db_path,
            "embedding_model": self.embedding_model,
            "agent_name": self.agent_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "max_search_results": self.max_search_results,
            "memory_retention_days": self.memory_retention_days
        }
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.nvidia_api_key or not self.nvidia_api_key.startswith("nvapi-"):
            raise ValueError("NVIDIA_API_KEY is missing or invalid. Please check your .env file.")
        
        # Create database directory if it doesn't exist
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        return True
