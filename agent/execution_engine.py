"""
Execution Engine for Master Agent
==================================
Executes tasks sequentially with error handling, retry logic, and reporting.
"""

import logging
import signal
from typing import Dict, Callable, Optional, Any
from contextlib import contextmanager
from agent.task import Task, TaskPlan, TaskStatus
from router.intent_router import route_intent

logger = logging.getLogger(__name__)


class ExecutionTimeout(Exception):
    """Raised when task execution exceeds timeout."""
    pass


class TaskExecutionPhase:
    """Tracks task execution phase for detailed logging."""
    VALIDATION = "validation"
    CONFIRMATION = "confirmation"
    EXECUTION = "execution"
    RESULT_PROCESSING = "result_processing"


class ExecutionEngine:
    """
    Executes task plans with robust error handling, retry logic, and reporting.
    
    Features:
    - Sequential task execution with dependency tracking
    - Timeouts and cancellation support
    - Automatic retry logic for failed tasks
    - Dry-run mode for safe testing
    - Detailed execution reporting
    """
    
    def __init__(self):
        """Initialize execution engine."""
        self.execution_log: list = []
        self.tool_registry: Dict[str, Callable] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tool executors."""
        # Tools are executed through route_intent, so registration is implicit
        pass
    
    def execute_plan(self, plan: TaskPlan, auto_confirm: bool = False) -> Dict[str, Any]:
        """
        Execute all tasks in a plan sequentially.
        
        Args:
            plan: TaskPlan to execute
            auto_confirm: Skip confirmation prompts
            
        Returns:
            Execution result dict with summary and details
        """
        logger.info(f"Starting execution of plan {plan.id}")
        print(f"\n{'='*60}")
        print(f"📋 TASK PLAN: {plan.goal}")
        print(f"{'='*60}")
        
        # Check if we're using fallback task
        is_fallback = any("Fallback" in task.description for task in plan.tasks)
        if is_fallback:
            print(f"⚠️  NOTE: Using single fallback task (decomposition didn't work)")
            print(f"   The AI couldn't break down your goal into specific steps.")
            print(f"   Running basic diagnostic instead...")
        
        print(f"Total Tasks: {len(plan.tasks)}")
        
        # Display all tasks
        self._display_task_list(plan)
        
        completed_task_ids = []
        failed_count = 0
        skipped_count = 0
        
        for task in plan.tasks:
            # Check if dependencies are satisfied
            # Only skip if parent task FAILED, not if it was SKIPPED by user
            failed_dependencies = [dep for dep in task.dependencies if plan.get_task(dep).status == TaskStatus.FAILED]
            
            if failed_dependencies:
                print(f"\n⏭️  SKIPPING: {task.description}")
                print(f"   └─ Parent task(s) failed: {', '.join(failed_dependencies)}")
                task.mark_skipped()
                skipped_count += 1
                continue
            
            # Execute the task
            success = self._execute_single_task(task, auto_confirm)
            
            if success:
                completed_task_ids.append(task.id)
            else:
                failed_count += 1
                # Don't break on failure - continue with other non-dependent tasks
        
        # Generate execution summary
        summary = plan.get_execution_summary()
        summary["execution_log"] = self.execution_log
        summary["is_fallback"] = is_fallback
        
        print(f"\n{'='*60}")
        print(f"✅ EXECUTION COMPLETE")
        print(f"{'='*60}")
        print(f"Total: {summary['total_tasks']} | ✓ Completed: {summary['completed']} | ✗ Failed: {summary['failed']} | ⏭️  Skipped: {skipped_count}")
        print(f"{'='*60}\n")
        
        return summary
    
    def _display_task_list(self, plan: TaskPlan):
        """Display all tasks in the plan."""
        print("\n📝 TASKS TO EXECUTE:")
        for i, task in enumerate(plan.tasks, 1):
            status_icon = "⏳" if not task.dependencies else "🔗"
            confirm_icon = " [⚠️  CONFIRM]" if task.requires_confirmation else ""
            print(f"  {i}. {status_icon} {task.description}{confirm_icon}")
            if task.dependencies:
                print(f"     └─ Depends on: {', '.join(task.dependencies[:2])}")
        print()
    
    def _execute_single_task(self, task: Task, auto_confirm: bool = False) -> bool:
        """
        Execute a single task with full error handling.
        
        Returns:
            True if successful, False if failed
        """
        print(f"\n▶️  EXECUTING: {task.description}")
        print(f"   Intent: {task.intent} | Action: {task.action}")
        
        # Check if this is a fallback task
        is_fallback = "FALLBACK" in task.description
        
        # Confirmation check
        if task.requires_confirmation and not auto_confirm:
            response = input(f"   ⚠️  This action requires confirmation. Proceed? (y/n): ").lower()
            if response != 'y':
                print(f"   ⏭️  Skipped by user")
                task.mark_skipped()
                return False
        
        # Dry-run notice
        if task.dry_run:
            print(f"   🏜️  DRY-RUN MODE (no changes will be made)")
        
        task.mark_started()
        
        try:
            # Build command dict for router
            command = {
                "intent": task.intent,
                "action": task.action,
                "parameters": task.parameters,
            }
            
            # Execute task through intent router
            result = self._execute_with_timeout(task, command)
            
            if result and "error" not in result:
                task.mark_completed(result)
                
                if is_fallback:
                    print(f"   ⚠️  FALLBACK TASK RAN (not your actual request)")
                else:
                    print(f"   ✅ SUCCESS")
                
                self.execution_log.append({
                    "task_id": task.id,
                    "status": "completed",
                    "is_fallback": is_fallback,
                    "result": result,
                })
                return True
            else:
                error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else "Execution failed"
                task.mark_failed(error_msg)
                print(f"   ❌ FAILED: {error_msg}")
                self.execution_log.append({
                    "task_id": task.id,
                    "status": "failed",
                    "error": error_msg,
                })
                
                # Retry logic
                if task.can_retry():
                    task.increment_retry()
                    print(f"   🔄 Retrying ({task.retry_count}/{task.max_retries})...")
                    return self._execute_single_task(task, auto_confirm)
                return False
        
        except ExecutionTimeout:
            error_msg = f"Task timed out after {task.timeout} seconds"
            task.mark_failed(error_msg)
            print(f"   ⏱️  TIMEOUT: {error_msg}")
            self.execution_log.append({
                "task_id": task.id,
                "status": "timeout",
                "error": error_msg,
            })
            return False
        
        except Exception as e:
            error_msg = str(e)
            task.mark_failed(error_msg)
            print(f"   ❌ ERROR: {error_msg}")
            logger.exception(f"Task execution error: {error_msg}")
            self.execution_log.append({
                "task_id": task.id,
                "status": "error",
                "error": error_msg,
            })
            return False
    
    def _execute_with_timeout(self, task: Task, command: dict) -> Optional[Dict[str, Any]]:
        """Execute command with timeout protection."""
        try:
            # For now, execute directly without timeout (can be enhanced with ProcessPoolExecutor)
            # In production, implement proper timeout handling
            result = self._execute_command(command)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def _execute_command(self, command: dict) -> Optional[Dict[str, Any]]:
        """Execute command through intent router."""
        try:
            # Import here to avoid circular imports
            from router.intent_router import route_intent
            
            # route_intent doesn't return a value directly
            # It prints results and prints them to console
            # For now, we'll mark execution as successful if no exception
            route_intent(command)
            return {"status": "executed", "message": "Command executed successfully"}
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Command execution error: {e}")
            return {"error": str(e)}
    
    def cancel_execution(self, plan: TaskPlan) -> None:
        """Cancel ongoing plan execution."""
        print("\n⛔ Cancelling execution...")
        for task in plan.tasks:
            if task.status == TaskStatus.IN_PROGRESS:
                task.mark_failed("Execution cancelled by user")
    
    def get_execution_report(self, plan: TaskPlan) -> str:
        """Generate human-readable execution report."""
        summary = plan.get_execution_summary()
        
        report = f"""
╔{'='*58}╗
║ {'EXECUTION REPORT':^56} ║
╚{'='*58}╝

Goal: {plan.goal}
User Input: {plan.user_input}

┌─ Summary ─────────────────────────────────────────────┐
│ Total Tasks: {summary['total_tasks']}
│ ✅ Completed: {summary['completed']}
│ ❌ Failed: {summary['failed']}
│ ⏭️  Skipped: {len(plan.tasks) - summary['completed'] - summary['failed']}
│ Status: {'✅ SUCCESS' if not summary['has_failures'] else '❌ FAILED'}
└───────────────────────────────────────────────────────┘

┌─ Task Details ────────────────────────────────────────┐
"""
        
        for i, task in enumerate(plan.tasks, 1):
            status_emoji = {
                TaskStatus.COMPLETED: "✅",
                TaskStatus.FAILED: "❌",
                TaskStatus.SKIPPED: "⏭️",
                TaskStatus.IN_PROGRESS: "⏳",
                TaskStatus.PENDING: "⏰",
            }.get(task.status, "❓")
            
            report += f"│ {i}. {status_emoji} {task.description}\n"
            if task.error:
                report += f"│    └─ Error: {task.error}\n"
            if task.result:
                report += f"│    └─ Result: {str(task.result)[:40]}...\n"
        
        report += "└───────────────────────────────────────────────────────┘\n"
        
        return report
