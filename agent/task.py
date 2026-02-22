"""
Task Model for Master Agent
================================
Defines task structures for agent decomposition and execution.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional, List
from datetime import datetime


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRY = "retry"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class Task:
    """
    Represents an atomic task that can be executed.
    
    Attributes:
        id: Unique task identifier
        intent: The intent this task fulfills (e.g., "file_management")
        action: The action to perform (e.g., "organize_by_type")
        parameters: Parameters for the action
        description: Human-readable description
        status: Current task status
        priority: Task priority
        dependencies: List of task IDs this depends on
        dry_run: Whether to run in dry-run mode
        requires_confirmation: Whether user confirmation is needed
        result: Result of task execution
        error: Error message if task failed
        retry_count: Number of retries
        max_retries: Maximum number of retries allowed
        timeout: Timeout in seconds
        created_at: When task was created
        started_at: When task execution started
        completed_at: When task execution completed
    """
    
    id: str
    intent: str
    action: str
    parameters: dict = field(default_factory=dict)
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[str] = field(default_factory=list)
    dry_run: bool = False
    requires_confirmation: bool = False
    result: Optional[dict] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 300  # 5 minutes default
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate task on creation."""
        if not self.id:
            raise ValueError("Task ID is required")
        if not self.intent:
            raise ValueError("Intent is required")
    
    def to_dict(self) -> dict:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "intent": self.intent,
            "action": self.action,
            "parameters": self.parameters,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
            "dry_run": self.dry_run,
            "requires_confirmation": self.requires_confirmation,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
    
    def mark_started(self):
        """Mark task as started."""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now()
    
    def mark_completed(self, result: dict = None):
        """Mark task as completed with result."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result or {}
    
    def mark_failed(self, error: str):
        """Mark task as failed with error."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error
    
    def mark_skipped(self):
        """Mark task as skipped."""
        self.status = TaskStatus.SKIPPED
        self.completed_at = datetime.now()
    
    def is_ready_to_execute(self, completed_tasks: List[str]) -> bool:
        """Check if task's dependencies are satisfied."""
        if not self.dependencies:
            return True
        return all(dep_id in completed_tasks for dep_id in self.dependencies)
    
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries
    
    def increment_retry(self):
        """Increment retry count."""
        self.retry_count += 1
        self.status = TaskStatus.RETRY


class TaskPlan:
    """
    A collection of tasks that form a plan for goal execution.
    
    Attributes:
        id: Plan identifier
        user_input: Original user input
        goal: Extracted goal/intent
        tasks: List of tasks
        metadata: Additional plan metadata
    """
    
    def __init__(self, id: str, user_input: str, goal: str):
        """Initialize task plan."""
        self.id = id
        self.user_input = user_input
        self.goal = goal
        self.tasks: List[Task] = []
        self.metadata: dict = {}
        self.created_at = datetime.now()
    
    def add_task(self, task: Task) -> None:
        """Add a task to the plan."""
        if any(t.id == task.id for t in self.tasks):
            raise ValueError(f"Task with ID {task.id} already exists")
        self.tasks.append(task)
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return next((t for t in self.tasks if t.id == task_id), None)
    
    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks."""
        return [t for t in self.tasks if t.status == TaskStatus.PENDING]
    
    def get_completed_tasks(self) -> List[Task]:
        """Get all completed tasks."""
        return [t for t in self.tasks if t.status == TaskStatus.COMPLETED]
    
    def get_failed_tasks(self) -> List[Task]:
        """Get all failed tasks."""
        return [t for t in self.tasks if t.status == TaskStatus.FAILED]
    
    def get_task_ids_by_status(self, status: TaskStatus) -> List[str]:
        """Get task IDs filtered by status."""
        return [t.id for t in self.tasks if t.status == status]
    
    def is_complete(self) -> bool:
        """Check if all tasks are completed or skipped."""
        completed_statuses = {TaskStatus.COMPLETED, TaskStatus.SKIPPED}
        return all(t.status in completed_statuses for t in self.tasks)
    
    def has_failures(self) -> bool:
        """Check if plan has any failed tasks."""
        return any(t.status == TaskStatus.FAILED for t in self.tasks)
    
    def get_execution_summary(self) -> dict:
        """Get summary of plan execution."""
        return {
            "plan_id": self.id,
            "user_input": self.user_input,
            "goal": self.goal,
            "total_tasks": len(self.tasks),
            "completed": len(self.get_completed_tasks()),
            "failed": len(self.get_failed_tasks()),
            "pending": len(self.get_pending_tasks()),
            "is_complete": self.is_complete(),
            "has_failures": self.has_failures(),
            "tasks": [t.to_dict() for t in self.tasks],
        }
    
    def to_dict(self) -> dict:
        """Convert plan to dictionary."""
        return {
            "id": self.id,
            "user_input": self.user_input,
            "goal": self.goal,
            "tasks": [t.to_dict() for t in self.tasks],
            "created_at": self.created_at.isoformat(),
        }
