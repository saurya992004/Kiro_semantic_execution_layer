"""
Task Planner for Master Agent
==============================
Decomposes user goals into executable tasks using LLM reasoning.
"""

import json
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from agent.task import Task, TaskPlan, TaskStatus, TaskPriority
from utils.prompt_loader import load_prompt
from utils.json_parser import extract_json
from llm.groq_client import GroqClient

logger = logging.getLogger(__name__)


class TaskPlanner:
    """
    Decomposes complex user goals into concrete, executable tasks.
    
    Features:
    - Multi-step goal decomposition
    - Dependency tracking
    - Priority assignment
    - Parameter extraction
    """
    
    def __init__(self):
        """Initialize task planner."""
        self.llm = GroqClient()
        self.system_prompt = load_prompt("prompts/system_prompt.txt") if Path("prompts/system_prompt.txt").exists() else ""
        self.task_decomposition_prompt_template = """
You are a task decomposition expert for an AI OS agent. Your job is to break down the user's goal into concrete, executable tasks.

{system_prompt}

CRITICAL RULES FOR PARAMETER EXTRACTION:
1. Each task must have ALL required parameters for its action
2. For set_default_app, ALWAYS include BOTH: app_type AND app_name
3. For file operations, ALWAYS include folder_name as parameter
4. For brightness, ALWAYS include brightness value (0-100)
5. For installer tasks, ALWAYS include app_name as parameter
6. If a parameter is missing, the task WILL FAIL - include intelligent defaults based on user context
7. CRITICAL: For installing software, use ONE task with intent:installer, action:install_software.
   NEVER use separate "download" + "execute_installer" tasks — install_software handles EVERYTHING internally via winget.
   execute_installer is ONLY for when you already know an exact local file path.

INTENT → ACTION REFERENCE (use EXACTLY these names):

intent: open_app          → no sub-action needed; params: app_name
intent: web_search        → no sub-action needed; params: query
intent: system_control    → actions: sleep, lock, kill_process, clean_temp, empty_recycle_bin
intent: diagnostics       → actions: check_cpu, check_ram, check_disk, full_health_check
intent: disk_analysis     → actions: analyze_usage, find_large_folders, check_alerts
intent: maintenance       → actions: scan_temp, scan_old_files, scan_cleanup, clean_temp_files, clean_old_files
intent: health_check      → no sub-action needed
intent: troubleshoot_screen → no sub-action needed
intent: vision_analysis   → actions: analyze_screen, detect_ui, read_text
intent: personalization   → actions: toggle_dark_mode, set_accent_color, set_brightness, set_wallpaper, apply_preset, save_profile, load_profile, manage_startup, set_default_app
intent: file_management   → actions: organize_by_type, find_duplicates, remove_duplicates, find_large_files, analyze_folder, get_report
intent: system_config     → no sub-action needed
intent: installer         → actions: install_software, download_wallpaper, download_software, execute_installer, cache_info, clear_cache
  examples:
    "install discord"  → intent:installer, action:install_software, params:{{"app_name":"Discord"}}
    "download vlc"     → intent:installer, action:install_software, params:{{"app_name":"VLC"}}
    "install python"   → intent:installer, action:install_software, params:{{"app_name":"Python"}}
    "get me a wallpaper" → intent:installer, action:download_wallpaper, params:{{"query":"landscape"}}

IMPORTANT RULES:
1. Each task must have a single, clear action from the list above
2. Tasks should be in logical order with dependencies marked
3. Mark which tasks need user confirmation (especially for install/delete/destructive operations)
4. Return ONLY valid JSON, no explanations

User Goal: {goal}

Return a JSON array of tasks:
[
  {{
    "order": 1,
    "intent": "intent_name",
    "action": "action_name",
    "parameters": {{"param1": "value1"}},
    "description": "What this task does",
    "priority": "high|medium|low",
    "depends_on": [],
    "requires_confirmation": false,
    "dry_run": false
  }}
]
"""
    
    def plan_goal(self, user_input: str, goal: str) -> TaskPlan:
        """
        Create a task plan from user goal.
        
        Args:
            user_input: Original user input
            goal: Extracted goal/intent
            
        Returns:
            TaskPlan with decomposed tasks
        """
        plan_id = str(uuid.uuid4())[:8]
        plan = TaskPlan(plan_id, user_input, goal)
        
        try:
            # Generate task decomposition
            tasks_data = self._decompose_goal(goal)
            
            if not tasks_data:
                # Fallback: Create single task
                logger.warning(f"Task decomposition failed for goal: {goal}")
                task = self._create_fallback_task(goal)
                plan.add_task(task)
                return plan
            
            # Create Task objects
            task_id_map = {}  # Map order to actual ID
            
            for task_data in tasks_data:
                try:
                    task = self._create_task_from_data(task_data)
                    task_id_map[task_data.get("order", 0)] = task.id
                    plan.add_task(task)
                except ValueError as e:
                    logger.warning(f"Skipping invalid task: {e}")
                    continue
            
            # Update dependencies with actual task IDs
            self._update_task_dependencies(plan, task_id_map, tasks_data)
            
            # Sort tasks by priority and dependencies
            self._sort_tasks_by_priority(plan)
            
            return plan
        
        except Exception as e:
            logger.error(f"Error planning goal: {e}")
            # Return single-task plan as fallback
            task = self._create_fallback_task(goal)
            plan.add_task(task)
            return plan
    
    def _decompose_goal(self, goal: str) -> List[dict]:
        """Use LLM to decompose goal into tasks."""
        prompt = self.task_decomposition_prompt_template.format(goal=goal, system_prompt=self.system_prompt)
        
        try:
            response = self.llm.generate(prompt)
            logger.debug(f"LLM response (first 200 chars): {response[:200]}")
            
            tasks_data = extract_json(response)
            
            if isinstance(tasks_data, list) and len(tasks_data) > 0:
                logger.info(f"Successfully decomposed goal into {len(tasks_data)} tasks")
                return tasks_data
            elif isinstance(tasks_data, dict) and "tasks" in tasks_data:
                tasks_list = tasks_data["tasks"]
                if isinstance(tasks_list, list) and len(tasks_list) > 0:
                    logger.info(f"Successfully decomposed goal into {len(tasks_list)} tasks")
                    return tasks_list
            
            logger.warning(f"Decomposition returned empty result. Response type: {type(tasks_data)}, Content: {str(tasks_data)[:100]}")
            return []
        
        except Exception as e:
            logger.error(f"LLM decomposition failed: {e}", exc_info=True)
            return []
    
    def _create_task_from_data(self, task_data: dict) -> Task:
        """Create Task object from decomposition data."""
        intent = (task_data.get("intent") or "").strip().lower()
        action = (task_data.get("action") or "").strip().lower()
        description = task_data.get("description", "")
        
        if not intent:
            raise ValueError("Task must have intent")
        
        # Determine if confirmation is needed
        # Always require confirmation for destructive operations
        requires_confirmation = task_data.get("requires_confirmation", False)
        destructive_keywords = ['delete', 'remove', 'uninstall', 'kill', 'shutdown', 'restart', 'empty', 'clean']
        if any(keyword in description.lower() or keyword in action.lower() for keyword in destructive_keywords):
            requires_confirmation = True
        
        # Map priority string to enum
        priority_str = task_data.get("priority", "medium").lower()
        priority_map = {
            "critical": TaskPriority.CRITICAL,
            "high": TaskPriority.HIGH,
            "medium": TaskPriority.MEDIUM,
            "low": TaskPriority.LOW,
        }
        priority = priority_map.get(priority_str, TaskPriority.MEDIUM)
        
        task = Task(
            id=str(uuid.uuid4())[:12],
            intent=intent,
            action=action,
            parameters=task_data.get("parameters", {}),
            description=description,
            priority=priority,
            dependencies=task_data.get("depends_on", []),
            requires_confirmation=requires_confirmation,
            dry_run=task_data.get("dry_run", False),
        )
        
        return task
    
    def _update_task_dependencies(self, plan: TaskPlan, task_id_map: dict, tasks_data: List[dict]):
        """Update task dependencies with actual task IDs."""
        for i, task_data in enumerate(tasks_data):
            task = plan.tasks[i]
            order = task_data.get("order", 0)
            depends_on_orders = task_data.get("depends_on", [])
            
            # Convert order numbers to task IDs
            task.dependencies = [
                task_id_map[order] for order in depends_on_orders
                if order in task_id_map
            ]
    
    def _sort_tasks_by_priority(self, plan: TaskPlan):
        """Sort tasks respecting both priority and dependencies."""
        # Simple sort: maintain topological order based on dependencies
        # For now, just sort by priority within dependency constraints
        sorted_tasks = []
        processed = set()
        
        while len(sorted_tasks) < len(plan.tasks):
            added_any = False
            
            # Find tasks with all dependencies satisfied
            for task in plan.tasks:
                if task.id in processed:
                    continue
                
                if all(dep_id in processed for dep_id in task.dependencies):
                    sorted_tasks.append(task)
                    processed.add(task.id)
                    added_any = True
                    break
            
            if not added_any:
                # No valid tasks found (shouldn't happen), add highest priority
                for task in plan.tasks:
                    if task.id not in processed:
                        sorted_tasks.append(task)
                        processed.add(task.id)
                        break
        
        plan.tasks = sorted_tasks
    
    def _create_fallback_task(self, goal: str) -> Task:
        """Create a single fallback task for complex goals."""
        return Task(
            id=str(uuid.uuid4())[:12],
            intent="diagnostics",
            action="check_cpu",
            description=f"⚠️ FALLBACK: Basic health check (failed to decompose: {goal})",
            parameters={},
        )
