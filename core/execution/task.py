"""
Task Definition and Execution Context
Core data structures for the execution engine
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Dict, Callable
from datetime import datetime
from enum import Enum
import uuid


class TaskStatus(str, Enum):
    """Status of a task during execution"""
    PENDING = "pending"  # Queued, waiting to run
    RUNNING = "running"  # Currently executing
    PAUSED = "paused"  # Paused by user
    COMPLETED = "completed"  # Finished successfully
    FAILED = "failed"  # Failed with error
    CANCELLED = "cancelled"  # Cancelled by user
    TIMEOUT = "timeout"  # Exceeded timeout


@dataclass
class RetryPolicy:
    """Policy for retrying failed tasks"""
    max_attempts: int = 3
    initial_delay_ms: int = 1000  # Start with 1 second
    max_delay_ms: int = 30000  # Cap at 30 seconds
    backoff_multiplier: float = 2.0  # Exponential backoff
    
    def get_delay_ms(self, attempt: int) -> int:
        """Calculate delay for given attempt number (0-indexed)"""
        delay = self.initial_delay_ms * (self.backoff_multiplier ** attempt)
        return min(int(delay), self.max_delay_ms)


@dataclass
class ExecutionResult:
    """Result of a single task execution"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    duration_ms: float = 0.0
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    attempt: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "error_type": self.error_type,
            "duration_ms": self.duration_ms,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "attempt": self.attempt,
        }


@dataclass
class Task:
    """A single task to be executed"""
    
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "task"
    description: str = ""
    
    # What to execute
    action: str = ""  # "call_tool", "call_llm", "run_function"
    action_params: Dict[str, Any] = field(default_factory=dict)
    
    # Execution control
    timeout_seconds: float = 30.0
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    priority: int = 0  # Higher = execute first
    dependencies: list[str] = field(default_factory=list)  # Task IDs this depends on
    
    # State tracking
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[ExecutionResult] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    user_id: Optional[str] = None
    execution_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "action": self.action,
            "status": self.status.value,
            "result": self.result.to_dict() if self.result else None,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
    
    def is_complete(self) -> bool:
        """Check if task is in a terminal state"""
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        )
    
    def is_failed(self) -> bool:
        """Check if task failed"""
        return self.status in (TaskStatus.FAILED, TaskStatus.TIMEOUT)
    
    def can_retry(self) -> bool:
        """Check if task can be retried"""
        if not self.result:
            return False
        return self.result.attempt < self.retry_policy.max_attempts


@dataclass
class ExecutionPlan:
    """A plan of tasks to execute"""
    
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "plan"
    description: str = ""
    
    tasks: list[Task] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    execution_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_tasks_by_priority(self) -> list[Task]:
        """Get tasks sorted by priority (higher first) and topological order"""
        # Simple topo sort: if task has dependencies, it comes after them
        sorted_tasks = []
        remaining = set(task.task_id for task in self.tasks)
        task_map = {task.task_id: task for task in self.tasks}
        
        while remaining:
            # Find tasks with no unmet dependencies
            ready = [
                task_id for task_id in remaining
                if not (set(task_map[task_id].dependencies) & remaining)
            ]
            
            if not ready:
                # Circular dependency - just take next by priority
                ready = [min(remaining, key=lambda t: task_map[t].priority)]
            
            # Sort by priority descending
            ready.sort(key=lambda t: task_map[t].priority, reverse=True)
            
            sorted_tasks.extend(task_map[tid] for tid in ready)
            remaining -= set(ready)
        
        return sorted_tasks
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict"""
        return {
            "plan_id": self.plan_id,
            "name": self.name,
            "tasks": [task.to_dict() for task in self.tasks],
        }
