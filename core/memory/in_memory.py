"""
In-Memory Memory Backend Implementation
Implements the MemoryBackend protocol for development/testing
Production: Replace with PostgreSQL + Redis + Vector DB (no code changes to consumers)

Features:
- Store execution records
- Retrieve by ID or list
- Find similar (RAG)
- Session context caching
- Event publishing
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio

from ..protocols import MemoryBackend, ExecutionRecord, EventType, Event, EventBus
from .rag_retriever import RAGRetriever, SimilarExecution


logger = logging.getLogger(__name__)


class InMemoryMemory(MemoryBackend):
    """
    In-memory memory backend
    Good for: Development, testing, single-machine deployments
    
    Production swap-in: PostgreSQLMemory
    
    Usage:
        memory = InMemoryMemory()
        
        # Store
        await memory.store_execution(record)
        
        # Retrieve
        past = await memory.list_executions(user_id, limit=10)
        
        # Learn from similar
        similar = await memory.find_similar("speed up PC", user_id)
        
        # Context cache for session
        await memory.set_context(user_id, "plan", plan_json)
        plan = await memory.get_context(user_id, "plan")
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None, max_records: int = 10000):
        """
        Initialize in-memory backend
        
        Args:
            event_bus: EventBus for events
            max_records: Max executions to keep in memory
        """
        self._records: Dict[str, ExecutionRecord] = {}
        self._contexts: Dict[str, Dict[str, Any]] = {}  # user_id -> {key: value}
        self._context_ttl: Dict[str, Dict[str, datetime]] = {}  # user_id -> {key: expiry}
        self._rag = RAGRetriever()
        self._event_bus = event_bus
        self._max_records = max_records
        self._lock = asyncio.Lock()
    
    @property
    def backend_name(self) -> str:
        return "memory_in_memory"
    
    async def store_execution(self, record: ExecutionRecord) -> str:
        """Store an execution record"""
        async with self._lock:
            execution_id = record.execution_id
            
            # Store
            self._records[execution_id] = record
            
            # Index for RAG
            self._rag.index(record)
            
            # Trim if too many
            if len(self._records) > self._max_records:
                # Remove oldest
                oldest_id = min(
                    self._records.keys(),
                    key=lambda k: self._records[k].started_at
                )
                del self._records[oldest_id]
                await self._rag.remove(oldest_id)
            
            # Publish event
            if self._event_bus:
                await self._event_bus.publish(Event(
                    event_type=EventType.EXECUTION_STORED,
                    data={"execution_id": execution_id},
                    source="memory",
                    user_id=record.user_id,
                    execution_id=execution_id,
                ))
            
            logger.debug(f"Stored execution: {execution_id}")
            return execution_id
    
    async def get_execution(self, execution_id: str) -> Optional[ExecutionRecord]:
        """Retrieve a single execution by ID"""
        async with self._lock:
            return self._records.get(execution_id)
    
    async def list_executions(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        success_only: bool = False
    ) -> List[ExecutionRecord]:
        """List executions for a user"""
        async with self._lock:
            # Filter by user
            executions = [
                r for r in self._records.values()
                if r.user_id == user_id
            ]
            
            # Filter by success
            if success_only:
                executions = [r for r in executions if r.success]
            
            # Sort by recency (newest first)
            executions.sort(key=lambda r: r.completed_at or r.started_at, reverse=True)
            
            # Pagination
            return executions[offset:offset + limit]
    
    async def find_similar(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[ExecutionRecord]:
        """Find similar executions (RAG)"""
        async with self._lock:
            similar = await self._rag.find_similar(
                query,
                user_id=user_id,
                limit=limit,
                similarity_threshold=similarity_threshold,
            )
            
            # Return only the records
            return [s.execution_record for s in similar]
    
    async def update_execution(self, execution_id: str, updates: Dict[str, Any]) -> bool:
        """Update an execution record"""
        async with self._lock:
            if execution_id not in self._records:
                return False
            
            record = self._records[execution_id]
            
            # Update fields
            if "result" in updates:
                record.result = updates["result"]
            if "error" in updates:
                record.error = updates["error"]
            if "metadata" in updates:
                record.metadata.update(updates["metadata"])
            
            logger.debug(f"Updated execution: {execution_id}")
            return True
    
    async def delete_execution(self, execution_id: str) -> bool:
        """Delete an execution"""
        async with self._lock:
            if execution_id in self._records:
                del self._records[execution_id]
                await self._rag.remove(execution_id)
                logger.debug(f"Deleted execution: {execution_id}")
                return True
        return False
    
    async def clear_user_data(self, user_id: str) -> int:
        """Delete all data for a user"""
        async with self._lock:
            to_delete = [
                exec_id for exec_id, record in self._records.items()
                if record.user_id == user_id
            ]
            
            for exec_id in to_delete:
                del self._records[exec_id]
                await self._rag.remove(exec_id)
            
            # Clear context
            if user_id in self._contexts:
                del self._contexts[user_id]
            if user_id in self._context_ttl:
                del self._context_ttl[user_id]
            
            logger.info(f"Cleared {len(to_delete)} records for user: {user_id}")
            return len(to_delete)
    
    async def health_check(self) -> bool:
        """Check if backend is healthy"""
        try:
            async with self._lock:
                # Simple check: can we access records?
                _ = len(self._records)
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close gracefully"""
        logger.info("Closing in-memory memory backend")
        # Nothing to close, but good for protocol compliance
    
    # Context caching
    
    async def set_context(self, user_id: str, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """Store temporary context"""
        async with self._lock:
            if user_id not in self._contexts:
                self._contexts[user_id] = {}
                self._context_ttl[user_id] = {}
            
            self._contexts[user_id][key] = value
            self._context_ttl[user_id][key] = datetime.utcnow().timestamp() + ttl_seconds
            
            logger.debug(f"Set context: {user_id}/{key}")
    
    async def get_context(self, user_id: str, key: str) -> Optional[Any]:
        """Retrieve temporary context"""
        async with self._lock:
            if user_id not in self._contexts:
                return None
            
            # Check expiry
            if user_id in self._context_ttl and key in self._context_ttl[user_id]:
                if datetime.utcnow().timestamp() > self._context_ttl[user_id][key]:
                    # Expired
                    del self._contexts[user_id][key]
                    del self._context_ttl[user_id][key]
                    return None
            
            return self._contexts[user_id].get(key)
    
    async def clear_context(self, user_id: str) -> None:
        """Clear all context for user"""
        async with self._lock:
            if user_id in self._contexts:
                del self._contexts[user_id]
            if user_id in self._context_ttl:
                del self._context_ttl[user_id]
            
            logger.debug(f"Cleared context for user: {user_id}")
    
    # Stats
    
    def get_stats(self) -> Dict[str, Any]:
        """Get backend statistics"""
        return {
            "backend": self.backend_name,
            "total_records": len(self._records),
            "max_records": self._max_records,
            "active_contexts": len(self._contexts),
            "rag_stats": self._rag.get_stats(),
        }
