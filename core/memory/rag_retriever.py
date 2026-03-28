"""
RAG (Retrieval Augmented Generation) Retriever
Finds similar past execution records to learn from

Core Idea:
1. User asks: "Speed up my PC"
2. System searches for similar past tasks: "PC is slow, optimize performance"
3. Finds: "Last time we freed 20GB, disabled 15 startup apps"
4. Suggests: Try same solution again or learn patterns

This is Retrieval Augmented Generation (RAG) - using past knowledge to improve current decisions
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import math

from ..protocols import ExecutionRecord
from .embeddings import SimpleEmbedding


logger = logging.getLogger(__name__)


@dataclass
class SimilarExecution:
    """A similar past execution found by RAG"""
    execution_record: ExecutionRecord
    similarity_score: float  # 0-1, higher = more similar
    reason: str  # Why it's similar


class RAGRetriever:
    """
    Retrieval Augmented Generation system
    Finds similar past executions for learning
    
    Usage:
        retriever = RAGRetriever()
        
        # Index past executions
        for record in past_executions:
            retriever.index(record)
        
        # Find similar when processing new command
        similar = await retriever.find_similar(
            "Speed up PC",
            user_id="user_1",
            limit=3
        )
        
        for exec in similar:
            print(f"Similar: {exec.execution_record.goal}")
            print(f"Solution: {exec.execution_record.result}")
    """
    
    def __init__(self, similarity_threshold: float = 0.5):
        """
        Initialize RAG retriever
        
        Args:
            similarity_threshold: Min similarity to consider (0-1)
        """
        self._embeddings: Dict[str, List[float]] = {}  # execution_id -> embedding
        self._records: Dict[str, ExecutionRecord] = {}  # execution_id -> record
        self._embedder = SimpleEmbedding()
        self._similarity_threshold = similarity_threshold
        self._query_cache: Dict[str, List[SimilarExecution]] = {}
    
    def index(self, record: ExecutionRecord) -> None:
        """
        Index an execution record for retrieval
        
        Args:
            record: ExecutionRecord to index
        """
        # Create searchable text from record
        search_text = f"{record.goal} {record.command}"
        if record.tools_used:
            search_text += " " + " ".join(record.tools_used)
        
        # Generate embedding
        embedding = self._embedder.embed(search_text)
        
        # Store
        self._records[record.execution_id] = record
        self._embeddings[record.execution_id] = embedding
        
        logger.debug(f"Indexed execution: {record.execution_id}")
    
    async def find_similar(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 5,
        similarity_threshold: Optional[float] = None,
    ) -> List[SimilarExecution]:
        """
        Find similar past executions
        
        Args:
            query: Natural language query (e.g., "speed up PC")
            user_id: Filter by user (if provided)
            limit: Max results
            similarity_threshold: Override default threshold
            
        Returns:
            List of similar executions sorted by similarity (highest first)
        """
        threshold = similarity_threshold or self._similarity_threshold
        
        # Check cache first
        cache_key = f"{query}:{user_id}:{limit}"
        if cache_key in self._query_cache:
            logger.debug(f"Cache hit for query: {query}")
            return self._query_cache[cache_key]
        
        # Generate query embedding
        query_embedding = self._embedder.embed(query)
        
        results = []
        
        # Compare with all indexed records
        for exec_id, record in self._records.items():
            # Filter by user if specified
            if user_id and record.user_id != user_id:
                continue
            
            # Calculate similarity
            record_embedding = self._embeddings.get(exec_id, [])
            similarity = self._embedder.similarity(query_embedding, record_embedding)
            
            if similarity >= threshold:
                # Determine why it's similar
                reason = self._get_similarity_reason(query, record)
                
                results.append(SimilarExecution(
                    execution_record=record,
                    similarity_score=similarity,
                    reason=reason,
                ))
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        results = results[:limit]
        
        # Cache results
        self._query_cache[cache_key] = results
        
        logger.info(f"Found {len(results)} similar executions for: {query}")
        
        return results
    
    def _get_similarity_reason(self, query: str, record: ExecutionRecord) -> str:
        """Generate human-readable reason for similarity"""
        query_lower = query.lower()
        goal_lower = record.goal.lower()
        
        # Check for keyword overlap
        query_words = set(query_lower.split())
        goal_words = set(goal_lower.split())
        overlap = query_words & goal_words
        
        if overlap:
            return f"Shared keywords: {', '.join(list(overlap)[:3])}"
        
        # Check for tool overlap
        if record.tools_used:
            return f"Used tools: {', '.join(record.tools_used[:2])}"
        
        return "Similar pattern"
    
    def clear_cache(self) -> None:
        """Clear query cache"""
        self._query_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics"""
        return {
            "indexed_records": len(self._records),
            "cached_queries": len(self._query_cache),
            "similarity_threshold": self._similarity_threshold,
        }
    
    async def remove(self, execution_id: str) -> bool:
        """Remove execution from index (for deletion/privacy)"""
        if execution_id in self._records:
            del self._records[execution_id]
            del self._embeddings[execution_id]
            self.clear_cache()
            return True
        return False
    
    async def clear_all(self) -> None:
        """Clear all indexed records"""
        self._records.clear()
        self._embeddings.clear()
        self.clear_cache()
        logger.info("RAG retriever cleared all records")
