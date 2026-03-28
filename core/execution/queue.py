"""
Task Queue
In-memory task queue with support for Redis backend in future

For now: Simple priority queue
Future: Swap for Redis-backed queue for distributed execution
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import heapq

from .task import Task, TaskStatus


logger = logging.getLogger(__name__)


class TaskQueue:
    """
    In-memory priority task queue
    
    Features:
    - Priority-based ordering (higher priority = earlier execution)
    - Timeout-based expiration
    - Task state tracking
    - Durable persistence (in future: Redis backend)
    
    Usage:
        queue = TaskQueue()
        
        task = Task(name="analyze", priority=10)
        queue.enqueue(task)
        
        next_task = await queue.dequeue(timeout=30.0)
        await queue.mark_complete(task.task_id)
    """
    
    def __init__(self, max_size: int = 10000):
        """
        Initialize queue
        
        Args:
            max_size: Maximum tasks in queue
        """
        self._queue: List[tuple] = []  # Min-heap of (-priority, time_added, task)
        self._tasks: Dict[str, Task] = {}  # task_id -> task
        self._max_size = max_size
        self._lock = asyncio.Lock()
        self._not_empty = asyncio.Condition(self._lock)
        self._stats = {
            "enqueued": 0,
            "dequeued": 0,
            "completed": 0,
            "failed": 0,
            "current_size": 0,
        }
    
    async def enqueue(self, task: Task) -> None:
        """
        Add task to queue
        
        Args:
            task: Task to queue
            
        Raises:
            RuntimeError: If queue is full
        """
        async with self._lock:
            if len(self._tasks) >= self._max_size:
                raise RuntimeError(f"Queue is full (max: {self._max_size})")
            
            self._tasks[task.task_id] = task
            # Store as: (-priority to get max-heap, timestamp, task_id)
            heapq.heappush(
                self._queue,
                (-task.priority, datetime.utcnow().timestamp(), task.task_id),
            )
            
            self._stats["enqueued"] += 1
            self._stats["current_size"] = len(self._tasks)
            
            logger.debug(f"Task enqueued: {task.task_id} (priority: {task.priority})")
            
            # Notify waiters
            self._not_empty.notify()
    
    async def dequeue(self, timeout: float = 30.0) -> Optional[Task]:
        """
        Get next task from queue (blocks until available or timeout)
        
        Args:
            timeout: Wait timeout in seconds
            
        Returns:
            Next Task or None if timeout
        """
        async with self._not_empty:
            # Wait for queue to have items
            try:
                await asyncio.wait_for(
                    self._not_empty.wait(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                return None
            
            if not self._queue:
                return None
            
            # Get next task
            _, _, task_id = heapq.heappop(self._queue)
            task = self._tasks[task_id]
            
            self._stats["dequeued"] += 1
            self._stats["current_size"] = len(self._tasks)
            
            logger.debug(f"Task dequeued: {task_id}")
            
            return task
    
    async def mark_complete(self, task_id: str) -> None:
        """Mark task as completed"""
        async with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                self._stats["completed"] += 1
                logger.debug(f"Task marked complete: {task_id}")
    
    async def mark_failed(self, task_id: str, error: str) -> None:
        """Mark task as failed"""
        async with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                self._stats["failed"] += 1
                logger.debug(f"Task marked failed: {task_id}: {error}")
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID without removing from queue"""
        return self._tasks.get(task_id)
    
    async def remove(self, task_id: str) -> bool:
        """Remove task from queue (rare, for cancellation)"""
        async with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                # Note: not removing from heap (lazy deletion)
                self._stats["current_size"] = len(self._tasks)
                logger.debug(f"Task removed: {task_id}")
                return True
        return False
    
    async def size(self) -> int:
        """Get current queue size"""
        async with self._lock:
            return len(self._tasks)
    
    async def clear(self) -> None:
        """Clear all tasks"""
        async with self._lock:
            self._queue.clear()
            self._tasks.clear()
            self._stats["current_size"] = 0
            logger.info("Task queue cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            **self._stats,
            "max_size": self._max_size,
        }
    
    async def list_pending(self) -> List[Task]:
        """List all pending tasks"""
        async with self._lock:
            return [
                task for task in self._tasks.values()
                if task.status == TaskStatus.PENDING
            ]
    
    async def list_running(self) -> List[Task]:
        """List all running tasks"""
        async with self._lock:
            return [
                task for task in self._tasks.values()
                if task.status == TaskStatus.RUNNING
            ]
