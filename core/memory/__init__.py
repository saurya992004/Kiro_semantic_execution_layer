"""
Memory and Storage Layer

Stores execution history and learns from past tasks (RAG).

Exports:
- InMemoryMemory: In-memory implementation (dev/testing)
- RAGRetriever: Retrieval-augmented generation for learning
- SimpleEmbedding: Text embeddings for similarity search

Production swap: PostgreSQLMemory (no code changes to consumers)

Example:
    memory = InMemoryMemory()
    
    # Store execution
    await memory.store_execution(record)
    
    # Learn from similar past tasks
    similar = await memory.find_similar(
        "speed up PC",
        user_id="user_1",
        limit=3
    )
    
    for record in similar:
        print(f"Similar: {record.goal}")
"""

from .in_memory import InMemoryMemory
from .rag_retriever import RAGRetriever, SimilarExecution
from .embeddings import SimpleEmbedding

__all__ = [
    "InMemoryMemory",
    "RAGRetriever",
    "SimilarExecution",
    "SimpleEmbedding",
]
