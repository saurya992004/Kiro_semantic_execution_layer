"""
Async Task Executor
Executes tasks in parallel with retry logic, timeouts, and progress tracking

Replaces old synchronous execute_plan() with async parallel execution
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable, Coroutine, List
from datetime import datetime
import time

from .task import Task, ExecutionPlan, TaskStatus, ExecutionResult, RetryPolicy
from ..protocols import EventType, Event, EventBus, ToolInput, ToolOutput, LLMRequest, LLMResponse


logger = logging.getLogger(__name__)


class AsyncExecutor:
    """
    Executes tasks asynchronously with:
    - Parallel execution (multiple tasks at once)
    - Retry logic (exponential backoff)
    - Timeout handling
    - Dependency management
    - Progress tracking
    - Event publishing
    
    Usage:
        executor = AsyncExecutor(tool_registry=registry, llm_router=router, event_bus=bus)
        
        task1 = Task(action="call_tool", action_params={...})
        task2 = Task(action="call_tool", dependencies=[task1.task_id], ...)
        plan = ExecutionPlan(tasks=[task1, task2])
        
        results = await executor.execute_plan(plan, execution_id="exec_123", user_id="user_1")
    """
    
    def __init__(
        self,
        tool_registry: Optional[Any] = None,
        llm_router: Optional[Any] = None,
        event_bus: Optional[EventBus] = None,
        max_parallel_tasks: int = 5,
    ):
        """
        Initialize executor
        
        Args:
            tool_registry: ToolRegistry for executing tools
            llm_router: LLMRouter for LLM calls
            event_bus: EventBus for publishing events
            max_parallel_tasks: Max concurrent task executions
        """
        self._tool_registry = tool_registry
        self._llm_router = llm_router
        self._event_bus = event_bus
        self._max_parallel = max_parallel_tasks
        self._execution_stats = {
            "total_executions": 0,
            "successful": 0,
            "failed": 0,
            "total_duration_ms": 0.0,
        }
    
    async def execute_plan(
        self,
        plan: ExecutionPlan,
        execution_id: str,
        user_id: str,
        on_progress: Optional[Callable[[Task], Coroutine]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a plan of tasks in parallel with dependency management
        
        Args:
            plan: ExecutionPlan with tasks
            execution_id: ID for this execution
            user_id: User making the request
            on_progress: Optional callback for progress updates
            
        Returns:
            Dict with results:
            {
                "execution_id": str,
                "success": bool,
                "tasks_completed": int,
                "tasks_failed": int,
                "total_duration_ms": float,
                "results": {task_id: ExecutionResult},
                "errors": [error strings],
            }
        """
        start_time = time.time()
        self._execution_stats["total_executions"] += 1
        
        # Publish execution started event
        if self._event_bus:
            await self._event_bus.publish(Event(
                event_type=EventType.EXECUTION_STARTED,
                data={"task_count": len(plan.tasks)},
                source="executor",
                user_id=user_id,
                execution_id=execution_id,
            ))
        
        logger.info(f"Starting execution {execution_id} with {len(plan.tasks)} tasks")
        
        # Track task results
        task_results: Dict[str, ExecutionResult] = {}
        task_map = {task.task_id: task for task in plan.tasks}
        
        # Get ordered tasks (respects dependencies)
        ordered_tasks = plan.get_tasks_by_priority()
        
        errors = []
        
        try:
            # Execute tasks with concurrency limit
            pending_tasks: Dict[str, asyncio.Task] = {}
            completed_tasks: set = set()
            
            task_index = 0
            
            while task_index < len(ordered_tasks) or pending_tasks:
                # Fill up to max parallel
                while task_index < len(ordered_tasks) and len(pending_tasks) < self._max_parallel:
                    task = ordered_tasks[task_index]
                    
                    # Check if dependencies are met
                    deps_met = all(dep in completed_tasks for dep in task.dependencies)
                    
                    if deps_met:
                        # Start task execution
                        exec_coro = self._execute_task(
                            task,
                            task_results,
                            execution_id,
                            user_id,
                            on_progress,
                        )
                        pending_tasks[task.task_id] = asyncio.create_task(exec_coro)
                        task_index += 1
                    else:
                        # Dependencies not ready yet, skip for now
                        break
                
                # Wait for at least one task to complete
                if pending_tasks:
                    done, pending = await asyncio.wait(
                        pending_tasks.values(),
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    
                    # Process completed tasks
                    for task_result in done:
                        task_id = None
                        for tid, t in pending_tasks.items():
                            if t == task_result:
                                task_id = tid
                                break
                        
                        try:
                            await task_result
                            completed_tasks.add(task_id)
                            del pending_tasks[task_id]
                        except Exception as e:
                            logger.error(f"Task {task_id} failed: {e}")
                            errors.append(str(e))
                            del pending_tasks[task_id]
            
            # Wait for remaining tasks
            if pending_tasks:
                await asyncio.gather(*pending_tasks.values(), return_exceptions=True)
                completed_tasks.update(pending_tasks.keys())
            
        except asyncio.CancelledError:
            logger.warning(f"Execution {execution_id} was cancelled")
            raise
        except Exception as e:
            logger.error(f"Execution {execution_id} failed: {e}", exc_info=True)
            errors.append(str(e))
        
        # Calculate final stats
        duration_ms = (time.time() - start_time) * 1000
        successful = sum(1 for r in task_results.values() if r.success)
        failed = len(task_results) - successful
        
        self._execution_stats["successful"] += successful
        self._execution_stats["failed"] += failed
        self._execution_stats["total_duration_ms"] += duration_ms
        
        # Publish execution completed event
        if self._event_bus:
            await self._event_bus.publish(Event(
                event_type=EventType.EXECUTION_STARTED if not errors else EventType.COMMAND_FAILED,
                data={
                    "completed": len(task_results),
                    "successful": successful,
                    "failed": failed,
                    "duration_ms": duration_ms,
                },
                source="executor",
                user_id=user_id,
                execution_id=execution_id,
            ))
        
        logger.info(
            f"Execution {execution_id} completed: "
            f"{successful} successful, {failed} failed in {duration_ms:.0f}ms"
        )
        
        return {
            "execution_id": execution_id,
            "success": len(errors) == 0 and failed == 0,
            "tasks_completed": len(task_results),
            "tasks_failed": failed,
            "total_duration_ms": duration_ms,
            "results": task_results,
            "errors": errors,
        }
    
    async def _execute_task(
        self,
        task: Task,
        task_results: Dict[str, ExecutionResult],
        execution_id: str,
        user_id: str,
        on_progress: Optional[Callable[[Task], Coroutine]],
    ) -> None:
        """Execute a single task with retry logic"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        task.execution_id = execution_id
        task.user_id = user_id
        
        attempt = 0
        last_error = None
        
        while attempt < task.retry_policy.max_attempts:
            attempt += 1
            
            # Publish task started event
            if self._event_bus:
                await self._event_bus.publish(Event(
                    event_type=EventType.TASK_STARTED,
                    data={
                        "task_id": task.task_id,
                        "task_name": task.name,
                        "attempt": attempt,
                    },
                    source="executor",
                    user_id=user_id,
                    execution_id=execution_id,
                ))
            
            try:
                start_time = time.time()
                
                # Route based on action type
                if task.action == "call_tool":
                    result = await self._execute_tool(task, user_id, execution_id)
                elif task.action == "call_llm":
                    result = await self._execute_llm(task, user_id, execution_id)
                elif task.action == "run_function":
                    result = await self._execute_function(task, user_id, execution_id)
                else:
                    raise ValueError(f"Unknown action: {task.action}")
                
                duration_ms = (time.time() - start_time) * 1000
                
                # Success!
                exec_result = ExecutionResult(
                    success=True,
                    result=result,
                    duration_ms=duration_ms,
                    attempt=attempt,
                    completed_at=datetime.utcnow(),
                )
                
                task.status = TaskStatus.COMPLETED
                task.result = exec_result
                task_results[task.task_id] = exec_result
                
                # Publish success event
                if self._event_bus:
                    await self._event_bus.publish(Event(
                        event_type=EventType.TASK_COMPLETED,
                        data={
                            "task_id": task.task_id,
                            "duration_ms": duration_ms,
                        },
                        source="executor",
                        user_id=user_id,
                        execution_id=execution_id,
                    ))
                
                # Progress callback
                if on_progress:
                    await on_progress(task)
                
                logger.info(f"Task {task.task_id} completed in {duration_ms:.0f}ms")
                return
                
            except asyncio.TimeoutError:
                last_error = f"Task timeout after {task.timeout_seconds}s"
                task.status = TaskStatus.TIMEOUT
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Task {task.task_id} attempt {attempt} failed: {e}")
            
            # Check if we should retry
            if attempt < task.retry_policy.max_attempts:
                delay_ms = task.retry_policy.get_delay_ms(attempt - 1)
                logger.info(f"Retrying task {task.task_id} in {delay_ms}ms (attempt {attempt + 1})")
                await asyncio.sleep(delay_ms / 1000)
        
        # All retries exhausted
        exec_result = ExecutionResult(
            success=False,
            error=last_error,
            error_type="execution_failed",
            attempt=attempt,
            completed_at=datetime.utcnow(),
        )
        
        task.status = TaskStatus.FAILED
        task.result = exec_result
        task_results[task.task_id] = exec_result
        
        # Publish failure event
        if self._event_bus:
            await self._event_bus.publish(Event(
                event_type=EventType.TASK_FAILED,
                data={
                    "task_id": task.task_id,
                    "error": last_error,
                },
                source="executor",
                user_id=user_id,
                execution_id=execution_id,
            ))
        
        logger.error(f"Task {task.task_id} failed after {attempt} attempts: {last_error}")
    
    async def _execute_tool(
        self,
        task: Task,
        user_id: str,
        execution_id: str,
    ) -> Any:
        """Execute a tool action"""
        if not self._tool_registry:
            raise RuntimeError("Tool registry not initialized")
        
        tool_name = task.action_params.get("tool_name")
        parameters = task.action_params.get("parameters", {})
        
        tool_input = ToolInput(
            tool_name=tool_name,
            parameters=parameters,
            user_id=user_id,
            request_id=execution_id,
            timeout=task.timeout_seconds,
        )
        
        output = await asyncio.wait_for(
            self._tool_registry.execute(tool_input),
            timeout=task.timeout_seconds,
        )
        
        if not output.success:
            raise RuntimeError(f"Tool {tool_name} failed: {output.error}")
        
        return output.result
    
    async def _execute_llm(
        self,
        task: Task,
        user_id: str,
        execution_id: str,
    ) -> str:
        """Execute an LLM action"""
        if not self._llm_router:
            raise RuntimeError("LLM router not initialized")
        
        prompt = task.action_params.get("prompt")
        system_prompt = task.action_params.get("system_prompt")
        max_tokens = task.action_params.get("max_tokens", 512)
        
        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            user_id=user_id,
            request_id=execution_id,
            timeout=task.timeout_seconds,
        )
        
        response = await asyncio.wait_for(
            self._llm_router.generate(request),
            timeout=task.timeout_seconds,
        )
        
        return response.text
    
    async def _execute_function(
        self,
        task: Task,
        user_id: str,
        execution_id: str,
    ) -> Any:
        """Execute a custom async function"""
        func = task.action_params.get("func")
        args = task.action_params.get("args", [])
        kwargs = task.action_params.get("kwargs", {})
        
        if not callable(func):
            raise ValueError("Function not callable")
        
        coro = func(*args, **kwargs)
        result = await asyncio.wait_for(coro, timeout=task.timeout_seconds)
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return {
            **self._execution_stats,
            "max_parallel": self._max_parallel,
        }
