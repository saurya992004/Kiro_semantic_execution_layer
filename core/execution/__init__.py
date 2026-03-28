"""
Async Execution Engine

Parallel task execution with:
- Dependency management
- Retry logic (exponential backoff)
- Timeout handling
- Priority-based queuing
- Progress tracking
- Event publishing

Replaces old synchronous execute_plan() with async parallel execution.

Exports:
- AsyncExecutor: Main executor for parallel task execution
- TaskQueue: Priority task queue
- Task: Task definition
- ExecutionPlan: Plan of tasks to execute
- TaskStatus: Task status enumeration
"""

from .executor import AsyncExecutor
from .queue import TaskQueue
from .task import Task, ExecutionPlan, TaskStatus, RetryPolicy, ExecutionResult

__all__ = [
    "AsyncExecutor",
    "TaskQueue",
    "Task",
    "ExecutionPlan",
    "TaskStatus",
    "RetryPolicy",
    "ExecutionResult",
]
