"""
JARVIS Master Agent Module
==========================
Intelligent orchestration layer for OS automation tasks.

Components:
- TaskPlanner: Decomposes goals into executable tasks
- ExecutionEngine: Runs tasks with error handling and retries
- MemoryManager: Manages history, context, and preferences
- MasterAgent: Central orchestrator coordinating all components
"""

from agent.master_agent import MasterAgent
from agent.task_planner import TaskPlanner
from agent.execution_engine import ExecutionEngine
from agent.memory_manager import MemoryManager
from agent.task import Task, TaskPlan, TaskStatus, TaskPriority

__all__ = [
    "MasterAgent",
    "TaskPlanner",
    "ExecutionEngine",
    "MemoryManager",
    "Task",
    "TaskPlan",
    "TaskStatus",
    "TaskPriority",
]
