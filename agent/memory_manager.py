"""
Memory Manager for Master Agent
=================================
Manages execution history, context, and state persistence.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from agent.task import TaskPlan, Task, TaskStatus

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Manages agent memory including execution history, context, and preferences.
    
    Features:
    - Execution history logging
    - Context tracking (what user asked before)
    - User preferences and learning
    - State persistence
    """
    
    def __init__(self, memory_dir: str = "agent_memory"):
        """Initialize memory manager."""
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        
        self.history_file = self.memory_dir / "execution_history.json"
        self.context_file = self.memory_dir / "context.json"
        self.preferences_file = self.memory_dir / "preferences.json"
        self.plans_file = self.memory_dir / "plans.json"
        
        # In-memory cache
        self.execution_history: List[dict] = []
        self.context: Dict[str, Any] = {}
        self.preferences: Dict[str, Any] = {}
        self.plans_cache: Dict[str, TaskPlan] = {}
        
        self._load_all()
    
    def _load_all(self):
        """Load all memory from disk."""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    self.execution_history = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load execution history: {e}")
        
        try:
            if self.context_file.exists():
                with open(self.context_file, 'r') as f:
                    self.context = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load context: {e}")
        
        try:
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r') as f:
                    self.preferences = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load preferences: {e}")
    
    def save_execution(self, plan: TaskPlan) -> None:
        """Log execution of a task plan."""
        execution_record = {
            "timestamp": datetime.now().isoformat(),
            "plan_id": plan.id,
            "user_input": plan.user_input,
            "goal": plan.goal,
            "summary": plan.get_execution_summary(),
        }
        
        self.execution_history.append(execution_record)
        self._save_history()
    
    def save_plan(self, plan: TaskPlan) -> None:
        """Save a task plan to memory."""
        self.plans_cache[plan.id] = plan
        self._save_plans()
    
    def get_plan(self, plan_id: str) -> Optional[TaskPlan]:
        """Retrieve a saved plan."""
        return self.plans_cache.get(plan_id)
    
    def update_context(self, key: str, value: Any) -> None:
        """Update context information."""
        self.context[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
        }
        self._save_context()
    
    def get_context(self, key: str = None) -> Any:
        """Get context information."""
        if key is None:
            return {k: v["value"] for k, v in self.context.items()}
        
        if key in self.context:
            return self.context[key]["value"]
        return None
    
    def save_preference(self, key: str, value: Any) -> None:
        """Save user preference."""
        self.preferences[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
        }
        self._save_preferences()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference."""
        if key in self.preferences:
            return self.preferences[key]["value"]
        return default
    
    def get_all_preferences(self) -> dict:
        """Get all preferences."""
        return {k: v["value"] for k, v in self.preferences.items()}
    
    def get_recent_executions(self, limit: int = 10) -> List[dict]:
        """Get recent execution history."""
        return self.execution_history[-limit:]
    
    def get_execution_stats(self) -> dict:
        """Get execution statistics."""
        if not self.execution_history:
            return {
                "total_executions": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0,
            }
        
        successful = sum(
            1 for ex in self.execution_history
            if not ex["summary"].get("has_failures", False)
        )
        total = len(self.execution_history)
        
        return {
            "total_executions": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": (successful / total) * 100 if total > 0 else 0.0,
        }
    
    def get_execution_by_intent(self, intent: str, limit: int = 5) -> List[dict]:
        """Get execution history filtered by intent."""
        filtered = [
            ex for ex in self.execution_history
            if ex["goal"].lower().find(intent.lower()) != -1
        ]
        return filtered[-limit:]
    
    def add_to_context_chain(self, message: str, role: str = "user") -> None:
        """Add to conversation context chain for multi-turn interactions."""
        if "conversation_chain" not in self.context:
            self.update_context("conversation_chain", [])
        
        chain = self.get_context("conversation_chain") or []
        chain.append({"role": role, "message": message, "timestamp": datetime.now().isoformat()})
        self.update_context("conversation_chain", chain)
    
    def get_conversation_chain(self, limit: int = 10) -> List[dict]:
        """Get recent conversation chain."""
        chain = self.get_context("conversation_chain") or []
        return chain[-limit:]
    
    def clear_conversation_chain(self) -> None:
        """Clear conversation chain."""
        self.update_context("conversation_chain", [])
    
    def _save_history(self):
        """Persist history to disk."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.execution_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save execution history: {e}")
    
    def _save_context(self):
        """Persist context to disk."""
        try:
            with open(self.context_file, 'w') as f:
                json.dump(self.context, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save context: {e}")
    
    def _save_preferences(self):
        """Persist preferences to disk."""
        try:
            with open(self.preferences_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
    
    def _save_plans(self):
        """Persist plans to disk."""
        try:
            plans_data = {plan_id: plan.to_dict() for plan_id, plan in self.plans_cache.items()}
            with open(self.plans_file, 'w') as f:
                json.dump(plans_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save plans: {e}")
    
    def clear_all(self):
        """Clear all memory (be careful!)."""
        self.execution_history.clear()
        self.context.clear()
        self.preferences.clear()
        self.plans_cache.clear()
        self._save_history()
        self._save_context()
        self._save_preferences()
        self._save_plans()
    
    def get_memory_stats(self) -> dict:
        """Get memory usage statistics."""
        return {
            "execution_history_entries": len(self.execution_history),
            "context_keys": len(self.context),
            "preferences_keys": len(self.preferences),
            "cached_plans": len(self.plans_cache),
        }
