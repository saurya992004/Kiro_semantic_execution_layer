"""
Memory & RAG Demo
Shows how the system learns from past executions

Key Idea:
- User says: "Speed up my PC"
- System searches history for similar tasks
- Finds: "Last time we freed 20GB cache, disabled startup apps"
- Knows to try similar approach again
- This is RAG: Retrieval Augmented Generation
"""

import asyncio
import logging
from datetime import datetime, timedelta
import uuid

from core.memory import InMemoryMemory, RAGRetriever, SimpleEmbedding
from core.protocols import ExecutionRecord


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_storage():
    """Demo: Store and retrieve executions"""
    print("\n" + "="*70)
    print("MEMORY DEMO 1 - Basic Storage & Retrieval")
    print("="*70 + "\n")
    
    memory = InMemoryMemory()
    
    # Create some past executions
    past_exec = ExecutionRecord(
        execution_id=str(uuid.uuid4()),
        user_id="user_1",
        command="Speed up my PC",
        goal="Optimize system performance",
        tasks=["Scan CPU", "Check RAM", "Find large files"],
        tools_used=["system_diagnostics", "file_scanner"],
        result="Freed 20GB, disabled 15 startup apps, optimized RAM",
        success=True,
        duration_ms=5000,
        started_at=datetime.utcnow() - timedelta(days=7),
        completed_at=datetime.utcnow() - timedelta(days=7),
    )
    
    # Store it
    print("📝 Storing past execution...")
    exec_id = await memory.store_execution(past_exec)
    print(f"   ✅ Stored: {exec_id}\n")
    
    # Retrieve it
    print("🔍 Retrieving execution...")
    retrieved = await memory.get_execution(exec_id)
    if retrieved:
        print(f"   ✅ Retrieved: {retrieved.goal}")
        print(f"   Result: {retrieved.result}\n")
    
    # List all for user
    print("📋 Listing all executions for user_1...")
    executions = await memory.list_executions("user_1", limit=10)
    print(f"   ✅ Found {len(executions)} executions")
    for i, exec_record in enumerate(executions, 1):
        print(f"   {i}. {exec_record.command} - {exec_record.result[:50]}...\n")


async def demo_rag_learning():
    """Demo: RAG - Learning from similar past tasks"""
    print("="*70)
    print("MEMORY DEMO 2 - RAG: Learn from Similar Tasks")
    print("="*70 + "\n")
    
    memory = InMemoryMemory()
    
    # Index some past executions
    print("📚 Building knowledge base from past executions...\n")
    
    past_tasks = [
        ExecutionRecord(
            execution_id=str(uuid.uuid4()),
            user_id="user_1",
            command="My computer is very slow",
            goal="Optimize system performance",
            tasks=["Check CPU", "Check RAM", "Scan disk"],
            tools_used=["system_diagnostics", "file_scanner"],
            result="Freed 20GB from cache, disabled 15 startup apps",
            success=True,
            duration_ms=8000,
            started_at=datetime.utcnow() - timedelta(days=30),
            completed_at=datetime.utcnow() - timedelta(days=30),
        ),
        ExecutionRecord(
            execution_id=str(uuid.uuid4()),
            user_id="user_1",
            command="PC is acting slow and freezing",
            goal="Speed up performance",
            tasks=["Identify bottlenecks", "Kill heavy processes"],
            tools_used=["process_monitor", "system_tools"],
            result="Killed Chrome (4GB RAM), freed memory, system responsive",
            success=True,
            duration_ms=6000,
            started_at=datetime.utcnow() - timedelta(days=14),
            completed_at=datetime.utcnow() - timedelta(days=14),
        ),
        ExecutionRecord(
            execution_id=str(uuid.uuid4()),
            user_id="user_1",
            command="Backup all my files",
            goal="Create file backup",
            tasks=["Scan files", "Compress", "Upload"],
            tools_used=["file_scanner", "compression"],
            result="Backed up 150GB to cloud",
            success=True,
            duration_ms=45000,
            started_at=datetime.utcnow() - timedelta(days=7),
            completed_at=datetime.utcnow() - timedelta(days=7),
        ),
    ]
    
    for i, task in enumerate(past_tasks, 1):
        await memory.store_execution(task)
        print(f"   {i}. Indexed: {task.command}")
    
    print("\n✅ Knowledge base ready (3 executions indexed)\n")
    
    # Now user asks something similar
    print("🔍 User asks: 'Speed up my PC, it's acting too slow'")
    print()
    
    similar = await memory.find_similar(
        "Speed up my PC, it's acting too slow",
        user_id="user_1",
        limit=3,
        similarity_threshold=0.3
    )
    
    print(f"📊 Found {len(similar)} similar past executions:\n")
    
    for i, record in enumerate(similar, 1):
        print(f"   {i}. {record.command}")
        print(f"      Goal: {record.goal}")
        print(f"      Result: {record.result}")
        print(f"      Tools used: {', '.join(record.tools_used)}")
        print()
    
    print("✅ System knows: Try same approach (free cache, disable apps)\n")


async def demo_embeddings():
    """Demo: Text embeddings and similarity"""
    print("="*70)
    print("MEMORY DEMO 3 - Text Embeddings & Similarity")
    print("="*70 + "\n")
    
    embedder = SimpleEmbedding()
    
    # Create embeddings for similar queries
    queries = [
        "Speed up my PC",
        "Computer is slow",
        "Make my system faster",
        "Backup my files",
        "Create file backup",
    ]
    
    print("📝 Creating embeddings...\n")
    
    embeddings_list = []
    for query in queries:
        emb = embedder.embed(query)
        embeddings_list.append(emb)
        print(f"   {query}")
        print(f"      Embedding: {emb[:3]}... (truncated)")
    
    print("\n📊 Calculating similarities:\n")
    
    # Compare first query with others
    ref_query = queries[0]
    ref_embedding = embeddings_list[0]
    
    print(f"Reference: '{ref_query}'")
    print("   vs")
    print()
    
    for i, (query, embedding) in enumerate(zip(queries[1:], embeddings_list[1:]), 1):
        sim = embedder.similarity(ref_embedding, embedding)
        bar = "█" * int(sim * 20)
        print(f"   '{query}'")
        print(f"      Similarity: {sim:.2f} {bar}")
    
    print()
    print("✅ Similar queries get similar embeddings")
    print("   (Same topic = higher similarity)\n")


async def demo_context_caching():
    """Demo: Session context caching"""
    print("="*70)
    print("MEMORY DEMO 4 - Context Caching (Session State)")
    print("="*70 + "\n")
    
    memory = InMemoryMemory()
    
    user_id = "user_1"
    
    print("🔒 Storing session context...\n")
    
    # Store context
    plan = {
        "goals": ["Scan system", "Find issues", "Optimize"],
        "estimated_duration_ms": 5000,
    }
    
    await memory.set_context(user_id, "current_plan", plan, ttl_seconds=3600)
    print(f"   Stored plan for {user_id}")
    
    state = {"progress": 0.25, "current_step": "Scanning CPU"}
    await memory.set_context(user_id, "execution_state", state, ttl_seconds=600)
    print(f"   Stored execution state\n")
    
    # Retrieve context
    print("🔑 Retrieving session context...\n")
    
    retrieved_plan = await memory.get_context(user_id, "current_plan")
    print(f"   Plan: {retrieved_plan}\n")
    
    retrieved_state = await memory.get_context(user_id, "execution_state")
    print(f"   State: {retrieved_state}\n")
    
    # Clear context
    print("🧹 Clearing session context...\n")
    await memory.clear_context(user_id)
    print(f"   Context cleared for {user_id}")
    
    # Try to retrieve (should be None)
    result = await memory.get_context(user_id, "current_plan")
    print(f"   Plan after clear: {result}\n")


async def demo_production_swap():
    """Demo: Swapping backend (no code changes)"""
    print("="*70)
    print("MEMORY DEMO 5 - Production Swap (InMemory → PostgreSQL)")
    print("="*70 + "\n")
    
    print("🔧 Current setup:")
    memory = InMemoryMemory()
    print(f"   Backend: {memory.backend_name}")
    print(f"   Type: In-memory (fast, no persistence)")
    print()
    
    print("📋 When moving to production, swap to:")
    print("""
    class PostgreSQLMemory(MemoryBackend):
        async def store_execution(self, record):
            # INSERT INTO executions ...
        
        async def find_similar(self, query, user_id):
            # SELECT * FROM executions WHERE similarity > threshold
            # (using PostgreSQL vector extension)
    
    # In initialization code:
    - memory = PostgreSQLMemory(conn_string="...")
    
    # EVERYTHING ELSE WORKS UNCHANGED! ✅
    """)
    
    print("\n✅ Protocol-based design = swappable backends\n")


async def demo_stats():
    """Demo: Memory statistics"""
    print("="*70)
    print("MEMORY DEMO 6 - Statistics & Monitoring")
    print("="*70 + "\n")
    
    memory = InMemoryMemory()
    
    # Add some data
    for i in range(5):
        record = ExecutionRecord(
            execution_id=str(uuid.uuid4()),
            user_id="user_1",
            command=f"Test command {i}",
            goal=f"Goal {i}",
            tasks=[],
            tools_used=[],
            result=f"Result {i}",
            success=True,
            duration_ms=1000,
        )
        await memory.store_execution(record)
    
    # Get stats
    stats = memory.get_stats()
    
    print("📊 Memory Backend Statistics:")
    print()
    print(f"   Backend: {stats['backend']}")
    print(f"   Total records: {stats['total_records']}")
    print(f"   Max capacity: {stats['max_records']}")
    print(f"   Active contexts: {stats['active_contexts']}")
    print(f"   RAG stats:")
    print(f"      - Indexed: {stats['rag_stats']['indexed_records']}")
    print(f"      - Cached queries: {stats['rag_stats']['cached_queries']}")
    print(f"      - Threshold: {stats['rag_stats']['similarity_threshold']}")
    print()


async def main():
    """Run all demos"""
    
    await demo_basic_storage()
    await demo_rag_learning()
    await demo_embeddings()
    await demo_context_caching()
    await demo_production_swap()
    await demo_stats()
    
    print("="*70)
    print("✅ ALL MEMORY DEMOS COMPLETE")
    print("="*70 + "\n")
    
    print("📚 KEY CAPABILITIES DEMONSTRATED:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("✅ Store & retrieve execution records")
    print("✅ RAG: Find similar past tasks")
    print("✅ Text embeddings & similarity search")
    print("✅ Session context caching")
    print("✅ Production backend swapping")
    print("✅ Statistics & monitoring")
    print()
    print("🚀 This enables:")
    print("   - Learning from past: 'Worked last time, try again'")
    print("   - Pattern recognition: Similar problems get similar solutions")
    print("   - Faster problem solving: Reuse past successful approaches")
    print("   - Persistent knowledge: Remember what worked")
    print("   - Future AI improvements: More data for training")
    print()


if __name__ == "__main__":
    asyncio.run(main())
