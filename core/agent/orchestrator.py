"""
Agent Orchestrator - Main Execution Loop
Ties together all components: LLM, Tools, Execution, Memory

Workflow:
1. User input: "Speed up my PC"
2. Goal extraction (LLM): "Optimize system performance"
3. Check memory: Find similar past tasks
4. Task planning (LLM): Decompose into executable tasks
5. Execution: Run tasks in parallel with retries
6. Learning: Store result in memory for future
7. Response: Stream results to user

This is the brain of JARVIS - orchestrates all components.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, AsyncIterator, List
from datetime import datetime
import uuid

from core.llm.router import LLMRouter
from core.tools.registry import ToolRegistry
from core.execution.executor import AsyncExecutor
from core.execution.task import Task, ExecutionPlan, TaskStatus
from core.memory import InMemoryMemory
from core.protocols import ExecutionRecord, EventType, Event


logger = logging.getLogger(__name__)


class ExecutionContext:
    """Context for a single execution"""
    
    def __init__(
        self,
        execution_id: str,
        user_id: str,
        command: str,
        user_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.execution_id = execution_id
        self.user_id = user_id
        self.command = command
        self.user_message = user_message or ""
        self.metadata = metadata or {}
        
        # Execution state
        self.goal: Optional[str] = None
        self.plan: Optional[ExecutionPlan] = None
        self.result: Optional[str] = None
        self.error: Optional[str] = None
        self.similar_past: List[ExecutionRecord] = []
        
        self.started_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None


class AgentOrchestrator:
    """
    Main orchestrator that ties all systems together.
    
    Processes user commands end-to-end:
    - Extract goals from natural language
    - Check memory for similar past solutions
    - Plan tasks using LLM
    - Execute in parallel
    - Learn from results
    
    Usage:
        orchestrator = AgentOrchestrator(router, tool_registry, executor, memory)
        
        async for event in orchestrator.process_command("Speed up my PC", user_id):
            print(f"Event: {event.event_type} - {event.data}")
    """
    
    def __init__(
        self,
        llm_router: LLMRouter,
        tool_registry: ToolRegistry,
        executor: AsyncExecutor,
        memory: InMemoryMemory,
        event_bus: Optional[Any] = None,
    ):
        """
        Initialize orchestrator with all components
        
        Args:
            llm_router: LLM router for goal extraction and planning
            tool_registry: Tool registry for available tools
            executor: Async executor for task execution
            memory: Memory backend for learning
            event_bus: Optional event bus for publishing events
        """
        self.llm_router = llm_router
        self.tool_registry = tool_registry
        self.executor = executor
        self.memory = memory
        self.event_bus = event_bus
        
        logger.info("Agent Orchestrator initialized")
    
    async def process_command(
        self,
        command: str,
        user_id: str,
        stream_events: bool = True,
    ) -> AsyncIterator[Event]:
        """
        Process a user command end-to-end.
        
        Yields events as they happen (STREAMING):
        - GOAL_EXTRACTED: Goal was extracted from command
        - MEMORY_CHECKED: Similar past tasks found
        - PLAN_GENERATED: Execution plan created
        - EXECUTION_STARTED: Plan execution began
        - TASK_STARTED: Individual task started
        - TASK_COMPLETED: Task finished
        - EXECUTION_COMPLETED: Full plan finished
        
        Args:
            command: User command (e.g., "Speed up my PC")
            user_id: User ID for personalization
            stream_events: Whether to yield events as they happen
            
        Yields:
            Event objects describing progress
        """
        
        # Create context
        execution_id = str(uuid.uuid4())
        ctx = ExecutionContext(
            execution_id=execution_id,
            user_id=user_id,
            command=command,
        )
        
        logger.info(f"Processing command: {command} (exec_id: {execution_id[:8]}...)")
        
        try:
            # Step 1: Extract goal from command
            logger.info("Step 1: Extracting goal...")
            goal = await self._extract_goal(command)
            ctx.goal = goal
            
            if stream_events:
                yield Event(
                    event_type=EventType.GOAL_EXTRACTED,
                    data={
                        "execution_id": execution_id,
                        "goal": goal,
                    },
                    source="orchestrator",
                    user_id=user_id,
                    execution_id=execution_id,
                )
            
            # Step 2: Check memory for similar past tasks
            logger.info("Step 2: Checking memory for similar tasks...")
            similar = await self._check_memory(command, user_id)
            ctx.similar_past = similar
            
            if similar and stream_events:
                yield Event(
                    event_type=EventType.EXECUTION_STARTED,
                    data={
                        "execution_id": execution_id,
                        "message": f"Found {len(similar)} similar past task(s)",
                        "similar_count": len(similar),
                    },
                    source="orchestrator",
                    user_id=user_id,
                    execution_id=execution_id,
                )
            
            # Step 3: Generate execution plan
            logger.info("Step 3: Generating execution plan...")
            plan = await self._generate_plan(goal, command, similar)
            ctx.plan = plan
            
            if stream_events:
                yield Event(
                    event_type=EventType.PLAN_GENERATED,
                    data={
                        "execution_id": execution_id,
                        "task_count": len(plan.tasks),
                        "estimated_duration_ms": sum(t.timeout_seconds * 1000 for t in plan.tasks),
                    },
                    source="orchestrator",
                    user_id=user_id,
                    execution_id=execution_id,
                )
            
            # Step 4: Execute plan
            logger.info("Step 4: Executing plan...")
            
            async def on_execution_event(event):
                """Forward execution events to caller"""
                if stream_events:
                    yield event
            
            task_events = []
            
            async for event in self._execute_plan(plan, execution_id, user_id):
                task_events.append(event)
                if stream_events:
                    yield event
            
            # Step 5: Learn from results
            logger.info("Step 5: Storing results and learning...")
            await self._learn_from_execution(
                execution_id,
                user_id,
                command,
                goal,
                plan,
                success=True,
            )
            
            # Final response
            ctx.result = "Execution completed successfully"
            ctx.completed_at = datetime.utcnow()
            
            if stream_events:
                yield Event(
                    event_type=EventType.COMMAND_COMPLETED,
                    data={
                        "execution_id": execution_id,
                        "duration_ms": int(
                            (ctx.completed_at - ctx.started_at).total_seconds() * 1000
                        ),
                        "task_count": len(plan.tasks),
                    },
                    source="orchestrator",
                    user_id=user_id,
                    execution_id=execution_id,
                )
        
        except Exception as e:
            logger.error(f"Execution failed: {e}", exc_info=True)
            ctx.error = str(e)
            ctx.completed_at = datetime.utcnow()
            
            if stream_events:
                yield Event(
                    event_type=EventType.COMMAND_FAILED,
                    data={
                        "execution_id": execution_id,
                        "error": str(e),
                        "duration_ms": int(
                            (ctx.completed_at - ctx.started_at).total_seconds() * 1000
                        ),
                    },
                    source="orchestrator",
                    user_id=user_id,
                    execution_id=execution_id,
                )
    
    async def _extract_goal(self, command: str) -> str:
        """Extract goal from user command using LLM"""
        prompt = f"""Given this user command, extract the main goal in 1-2 sentences.

Command: "{command}"

Goal:"""
        
        try:
            # Use LLM to extract goal
            from core.protocols import LLMRequest
            request = LLMRequest(
                prompt=prompt,
                temperature=0.3,
                max_tokens=100,
            )
            
            response = await self.llm_router.generate(request)
            goal = response.text.strip()
            
            return goal if goal else "Process user request"
        
        except Exception as e:
            logger.warning(f"Failed to extract goal with LLM, using fallback: {e}")
            return f"Process: {command}"
    
    async def _check_memory(
        self,
        command: str,
        user_id: str,
        limit: int = 3,
    ) -> List[ExecutionRecord]:
        """Check memory for similar past tasks"""
        try:
            similar = await self.memory.find_similar(
                command,
                user_id=user_id,
                limit=limit,
                similarity_threshold=0.3,
            )
            
            logger.info(f"Found {len(similar)} similar past tasks")
            return similar
        
        except Exception as e:
            logger.warning(f"Failed to check memory: {e}")
            return []
    
    async def _generate_plan(
        self,
        goal: str,
        command: str,
        similar_past: List[ExecutionRecord],
    ) -> ExecutionPlan:
        """Generate execution plan using LLM"""
        
        # Build context from similar tasks
        past_context = ""
        if similar_past:
            past_context = "Similar past approach:\n"
            for rec in similar_past[:1]:
                past_context += f"- Tools used: {', '.join(rec.tools_used)}\n"
                past_context += f"- Result: {rec.result}\n"
        
        prompt = f"""Given this goal, create a step-by-step plan.
Format as: TASK: <name> | ACTION: <action> | TOOLS: <tools>

Goal: {goal}
Command: {command}

{past_context}

Plan:
1. TASK: Analyze system | ACTION: run_function | TOOLS: diagnostics
2. TASK: Find issues | ACTION: run_function | TOOLS: scanner
3. TASK: Report results | ACTION: run_function | TOOLS: reporter"""
        
        try:
            from core.protocols import LLMRequest
            request = LLMRequest(
                prompt=prompt,
                temperature=0.3,
                max_tokens=300,
            )
            
            response = await self.llm_router.generate(request)
            
            # Parse response into tasks (simplified)
            tasks = self._parse_plan_response(response.text)
            
            if not tasks:
                # Fallback: create basic plan
                tasks = self._create_fallback_plan(goal)
            
            plan = ExecutionPlan(tasks=tasks)
            logger.info(f"Generated plan with {len(tasks)} tasks")
            
            return plan
        
        except Exception as e:
            logger.warning(f"Failed to generate plan with LLM: {e}")
            return ExecutionPlan(tasks=self._create_fallback_plan(goal))
    
    def _parse_plan_response(self, response_text: str) -> List[Task]:
        """Parse LLM response into tasks"""
        tasks = []
        
        lines = response_text.split('\n')
        for line in lines:
            if 'TASK:' in line and 'ACTION:' in line:
                try:
                    # Extract task name
                    task_part = line.split('TASK:')[1].split('|')[0].strip()
                    action_part = line.split('ACTION:')[1].split('|')[0].strip()
                    
                    task = Task(
                        name=task_part[:50],
                        action="run_function",
                        action_params={"function": task_part.lower().replace(' ', '_')},
                        description=task_part,
                    )
                    tasks.append(task)
                
                except (IndexError, AttributeError):
                    continue
        
        return tasks
    
    def _create_fallback_plan(self, goal: str) -> List[Task]:
        """Create a basic fallback plan"""
        tasks = [
            Task(
                name="analyze",
                action="run_function",
                action_params={"function": "analyze_situation"},
                description=f"Analyze: {goal}",
            ),
            Task(
                name="plan",
                action="run_function",
                action_params={"function": "create_solution"},
                description="Create solution",
            ),
        ]
        return tasks
    
    async def _execute_plan(
        self,
        plan: ExecutionPlan,
        execution_id: str,
        user_id: str,
    ) -> AsyncIterator[Event]:
        """Execute plan and yield progress events"""
        
        # Set execution context on tasks
        for task in plan.tasks:
            task.execution_id = execution_id
            task.user_id = user_id
        
        # Execute with progress callback
        async def on_progress(completed_task, total_tasks):
            logger.info(f"Progress: {completed_task}/{total_tasks}")
        
        result = await self.executor.execute_plan(
            plan,
            execution_id=execution_id,
            user_id=user_id,
        )
        
        # Yield execution event
        yield Event(
            event_type=EventType.TASK_COMPLETED,
            data={
                "execution_id": execution_id,
                "completed_tasks": result["tasks_completed"],
                "failed_tasks": result["tasks_failed"],
                "duration_ms": result["total_duration_ms"],
            },
            source="orchestrator",
            user_id=user_id,
            execution_id=execution_id,
        )
    
    async def _learn_from_execution(
        self,
        execution_id: str,
        user_id: str,
        command: str,
        goal: str,
        plan: ExecutionPlan,
        success: bool,
    ) -> None:
        """Store execution result in memory for learning"""
        try:
            result_text = "Successfully completed"
            
            record = ExecutionRecord(
                execution_id=execution_id,
                user_id=user_id,
                command=command,
                goal=goal,
                tasks=[t.name for t in plan.tasks],
                tools_used=[],  # Would extract from plan
                result=result_text,
                success=success,
                duration_ms=0,  # Would calculate
            )
            
            await self.memory.store_execution(record)
            logger.info(f"Stored execution {execution_id[:8]}... for learning")
        
        except Exception as e:
            logger.warning(f"Failed to store execution: {e}")
    
    async def cancel_execution(self, execution_id: str) -> None:
        """Cancel a running execution"""
        logger.info(f"Cancelling execution {execution_id}")
        # Would implement cancellation logic
