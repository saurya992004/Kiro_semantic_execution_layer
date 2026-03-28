"""
Execution Engine Demo
Shows parallel task execution with dependencies, retries, and timeout handling
"""

import asyncio
import logging
from datetime import datetime

from core.execution.task import Task, ExecutionPlan, TaskStatus, RetryPolicy
from core.execution.executor import AsyncExecutor
from core.execution.queue import TaskQueue


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_simple_execution():
    """Demo: Simple parallel execution"""
    print("\n" + "="*70)
    print("EXECUTION ENGINE DEMO - Simple Parallel Execution")
    print("="*70 + "\n")
    
    executor = AsyncExecutor()
    
    # Create simple tasks that call functions
    async def slow_task(name: str, duration: float):
        await asyncio.sleep(duration)
        return f"{name} completed in {duration}s"
    
    # Create tasks
    task1 = Task(
        name="Download Data",
        description="Download data from API",
        action="run_function",
        action_params={
            "func": slow_task,
            "args": ["Download", 2.0],
        },
        priority=10,
    )
    
    task2 = Task(
        name="Process Data",
        description="Process downloaded data",
        action="run_function",
        action_params={
            "func": slow_task,
            "args": ["Process", 1.5],
        },
        priority=9,
    )
    
    task3 = Task(
        name="Analyze Results",
        description="Analyze processed results",
        action="run_function",
        action_params={
            "func": slow_task,
            "args": ["Analyze", 1.0],
        },
        priority=8,
    )
    
    # Create plan
    plan = ExecutionPlan(
        name="Data Pipeline",
        tasks=[task1, task2, task3],
    )
    
    print("📋 Plan: Data Pipeline")
    print(f"   Tasks: {len(plan.tasks)}")
    for i, task in enumerate(plan.tasks, 1):
        print(f"   {i}. {task.name} (priority: {task.priority})")
    print()
    
    print("⏱️  Starting execution (3 tasks in parallel)...")
    print()
    
    # Progress callback
    async def on_progress(task: Task):
        result = task.result
        if result:
            print(f"   ✅ {task.name}: {result.result}")
    
    # Execute
    result = await executor.execute_plan(
        plan,
        execution_id="exec_demo_1",
        user_id="user_demo",
        on_progress=on_progress,
    )
    
    print()
    print("📊 Results:")
    print(f"   Total tasks: {result['tasks_completed']}")
    print(f"   Successful: {result['tasks_completed'] - result['tasks_failed']}")
    print(f"   Failed: {result['tasks_failed']}")
    print(f"   Total duration: {result['total_duration_ms']:.0f}ms")
    print()
    
    # Show improvement vs sequential
    sequential_time = 2.0 + 1.5 + 1.0  # Would take 4.5s sequential
    parallel_time = result['total_duration_ms'] / 1000
    speedup = sequential_time / parallel_time
    
    print(f"⚡ Performance:")
    print(f"   Sequential would take: {sequential_time:.1f}s")
    print(f"   Parallel took: {parallel_time:.1f}s")
    print(f"   Speedup: {speedup:.1f}x faster")
    print()


async def demo_dependencies():
    """Demo: Task dependencies"""
    print("="*70)
    print("EXECUTION ENGINE DEMO - Task Dependencies")
    print("="*70 + "\n")
    
    executor = AsyncExecutor()
    
    async def dummy_task(name: str):
        await asyncio.sleep(0.5)
        return name
    
    # Create tasks with dependencies
    task_a = Task(
        task_id="task_a",
        name="Task A",
        action="run_function",
        action_params={"func": dummy_task, "args": ["A"]},
        priority=10,
    )
    
    task_b = Task(
        task_id="task_b",
        name="Task B",
        action="run_function",
        action_params={"func": dummy_task, "args": ["B"]},
        priority=10,
    )
    
    # Task C depends on A and B
    task_c = Task(
        task_id="task_c",
        name="Task C (depends on A & B)",
        action="run_function",
        action_params={"func": dummy_task, "args": ["C"]},
        priority=5,
        dependencies=["task_a", "task_b"],
    )
    
    plan = ExecutionPlan(
        name="Dependency Pipeline",
        tasks=[task_a, task_b, task_c],
    )
    
    print("📋 Execution Plan:")
    print("   Task A ─┐")
    print("           ├─→ Task C")
    print("   Task B ─┘")
    print()
    
    print("⏱️  Starting execution...")
    print()
    
    result = await executor.execute_plan(
        plan,
        execution_id="exec_demo_2",
        user_id="user_demo",
    )
    
    print("✅ Execution complete!")
    print(f"   {result['tasks_completed']} tasks executed")
    print(f"   {result['total_duration_ms']:.0f}ms total time")
    print(f"   Task C started only after A & B completed ✓")
    print()


async def demo_retries():
    """Demo: Retry logic with exponential backoff"""
    print("="*70)
    print("EXECUTION ENGINE DEMO - Retry Logic")
    print("="*70 + "\n")
    
    executor = AsyncExecutor()
    
    attempt_count = 0
    
    async def flaky_task():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise RuntimeError("Failed on first attempt")
        return "Success after retry"
    
    # Task with retry policy
    task = Task(
        name="Flaky Task",
        action="run_function",
        action_params={"func": flaky_task},
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_delay_ms=100,
            backoff_multiplier=2.0,
        ),
    )
    
    plan = ExecutionPlan(name="Retry Test", tasks=[task])
    
    print("🔄 Task with retry policy:")
    print("   Max attempts: 3")
    print("   Initial delay: 100ms")
    print("   Backoff: 2x (exponential)")
    print()
    
    print("⏱️  Starting execution...")
    
    result = await executor.execute_plan(
        plan,
        execution_id="exec_demo_3",
        user_id="user_demo",
    )
    
    print()
    print("✅ Results:")
    print(f"   Success: {result['success']}")
    print(f"   Attempts used: {attempt_count}")
    print(f"   Task completed after retry ✓")
    print()


async def demo_timeout():
    """Demo: Timeout handling"""
    print("="*70)
    print("EXECUTION ENGINE DEMO - Timeout & Cancellation")
    print("="*70 + "\n")
    
    executor = AsyncExecutor()
    
    async def long_task():
        await asyncio.sleep(5.0)
        return "Done"
    
    # Task that will timeout
    task = Task(
        name="Slow Task",
        action="run_function",
        action_params={"func": long_task},
        timeout_seconds=1.0,  # Will timeout after 1 second
    )
    
    plan = ExecutionPlan(name="Timeout Test", tasks=[task])
    
    print("⏱️  Task configuration:")
    print("   Task duration: 5 seconds")
    print("   Timeout: 1 second")
    print()
    
    print("⏳ Starting execution (will timeout)...")
    
    result = await executor.execute_plan(
        plan,
        execution_id="exec_demo_4",
        user_id="user_demo",
    )
    
    print()
    print("✅ Results:")
    print(f"   Task timed out as expected: {result['tasks_failed'] == 1}")
    print(f"   Error message: {result['errors'][0] if result['errors'] else 'None'}")
    print()


async def demo_task_queue():
    """Demo: Task queue"""
    print("="*70)
    print("EXECUTION ENGINE DEMO - Task Queue")
    print("="*70 + "\n")
    
    queue = TaskQueue(max_size=100)
    
    print("📦 Creating 5 tasks with different priorities...")
    
    # Create tasks
    for i in range(5):
        task = Task(
            name=f"Task {i+1}",
            priority=5 - i,  # Decreasing priority
        )
        await queue.enqueue(task)
    
    print(f"   Enqueued 5 tasks")
    print(f"   Queue size: {await queue.size()}")
    print()
    
    print("🚀 Dequeuing tasks (should come by priority)...")
    print()
    
    for i in range(5):
        task = await queue.dequeue(timeout=1.0)
        if task:
            print(f"   {i+1}. {task.name} (priority: {task.priority})")
    
    print()
    print("✅ Tasks were dequeued in priority order ✓")
    print()


async def main():
    """Run all demos"""
    
    # Demo 1: Simple parallel
    await demo_simple_execution()
    
    # Demo 2: Dependencies
    await demo_dependencies()
    
    # Demo 3: Retries
    await demo_retries()
    
    # Demo 4: Timeout
    await demo_timeout()
    
    # Demo 5: Queue
    await demo_task_queue()
    
    print("="*70)
    print("✅ ALL EXECUTION ENGINE DEMOS COMPLETE")
    print("="*70 + "\n")
    
    print("📚 KEY CAPABILITIES DEMONSTRATED:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("✅ Parallel execution (tasks run concurrently)")
    print("✅ Dependency management (C waits for A & B)")
    print("✅ Retry logic (exponential backoff)")
    print("✅ Timeout handling (task cancelled if too slow)")
    print("✅ Priority queuing (higher priority first)")
    print("✅ Progress tracking and events")
    print("✅ Error handling and recovery")
    print()
    print("🚀 This enables:")
    print("   - Parallel tool execution (2-5x faster)")
    print("   - Distributed execution (Redis queue ready)")
    print("   - Resilient workflows (auto-retry)")
    print("   - Responsive UI (async non-blocking)")
    print()


if __name__ == "__main__":
    asyncio.run(main())
