"""
Memory Backend Protocol
Defines the interface for storing/retrieving execution history and learned context.
Implementations: PostgreSQL, Redis, Vector DB for RAG.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
from datetime import datetime


@dataclass
class ExecutionRecord:
    """Single execution in agent history"""
    
    execution_id: str
    user_id: str
    command: str
    goal: str  # Extracted goal
    tasks: List[Dict[str, Any]]  # Decomposed tasks
    tools_used: List[str]  # Which tools were called
    result: Any  # Final result
    success: bool
    error: Optional[str] = None
    duration_ms: float = 0.0
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[List[float]] = None  # For RAG similarity search
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable format"""
        return {
            "execution_id": self.execution_id,
            "user_id": self.user_id,
            "command": self.command,
            "goal": self.goal,
            "tasks": self.tasks,
            "tools_used": self.tools_used,
            "result": self.result,
            "success": self.success,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }


class MemoryBackend(ABC):
    """
    Abstract base class for memory/storage backends.
    Stores execution history and learns from past executions (RAG).
    
    Implementations:
    - PostgreSQL: Durable storage with indexing
    - Redis: Fast cache for recent context
    - Vector DB (Pinecone/Weaviate): Semantic similarity search for RAG
    
    Usage:
        memory = PostgreSQLMemory(connection_string="...")
        await memory.store_execution(record)
        previous = await memory.find_similar("speed up PC", limit=5)
    """
    
    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Identifier for this backend"""
        pass
    
    @abstractmethod
    async def store_execution(self, record: ExecutionRecord) -> str:
        """
        Store an execution record
        
        Args:
            record: ExecutionRecord to store
            
        Returns:
            execution_id of stored record
        """
        pass
    
    @abstractmethod
    async def get_execution(self, execution_id: str) -> Optional[ExecutionRecord]:
        """Retrieve a single execution by ID"""
        pass
    
    @abstractmethod
    async def list_executions(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0, 
        success_only: bool = False
    ) -> List[ExecutionRecord]:
        """
        List recent executions for a user
        
        Args:
            user_id: User to filter by
            limit: Max results
            offset: Pagination
            success_only: Only successful executions?
            
        Returns:
            List of ExecutionRecord sorted by recency
        """
        pass
    
    @abstractmethod
    async def find_similar(
        self, 
        query: str, 
        user_id: str,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[ExecutionRecord]:
        """
        Find executions similar to query (for RAG - learning from past)
        
        Args:
            query: Natural language query
            user_id: User context
            limit: Max results
            similarity_threshold: Min similarity score (0-1)
            
        Returns:
            List of similar past executions, most similar first
        """
        pass
    
    @abstractmethod
    async def update_execution(self, execution_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing execution record"""
        pass
    
    @abstractmethod
    async def delete_execution(self, execution_id: str) -> bool:
        """Delete an execution (for privacy/compliance)"""
        pass
    
    @abstractmethod
    async def clear_user_data(self, user_id: str) -> int:
        """Delete all data for a user. Returns number of records deleted."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if backend is available"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close connections gracefully"""
        pass
    
    # Context caching for current session
    
    @abstractmethod
    async def set_context(self, user_id: str, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """Store temporary context (e.g., current task plan)"""
        pass
    
    @abstractmethod
    async def get_context(self, user_id: str, key: str) -> Optional[Any]:
        """Retrieve temporary context"""
        pass
    
    @abstractmethod
    async def clear_context(self, user_id: str) -> None:
        """Clear all context for user (end of session)"""
        pass
