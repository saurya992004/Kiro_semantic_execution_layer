"""
Master Agent for JARVIS
=======================
Central orchestrator that coordinates task planning, execution, and memory management.
"""

import logging
from typing import Dict, Any, Optional
from agent.task import TaskPlan
from agent.task_planner import TaskPlanner
from agent.execution_engine import ExecutionEngine
from agent.memory_manager import MemoryManager
from utils.prompt_loader import load_prompt
from utils.json_parser import extract_json
from llm.groq_client import GroqClient

logger = logging.getLogger(__name__)


class MasterAgent:
    """
    Central agent that orchestrates the entire JARVIS system.
    
    Responsibilities:
    1. Receive user input
    2. Extract intent and goal
    3. Plan tasks using TaskPlanner
    4. Execute tasks using ExecutionEngine
    5. Store results in MemoryManager
    6. Provide feedback to user
    
    Features:
    - Multi-turn conversation support
    - Learning from past executions
    - Adaptive task planning
    - Comprehensive execution reporting
    """
    
    def __init__(self, memory_dir: str = "agent_memory"):
        """Initialize master agent."""
        self.memory = MemoryManager(memory_dir)
        self.planner = TaskPlanner()
        self.executor = ExecutionEngine()
        self.llm = GroqClient()
        
        # Load prompts
        self.system_prompt = self._load_system_prompt()
        self.goal_extraction_prompt = self._load_goal_extraction_prompt()
        
        logger.info("Master Agent initialized")
    
    def _load_system_prompt(self) -> str:
        """Load or create system prompt."""
        try:
            return load_prompt("prompts/system_prompt.txt")
        except:
            return "You are JARVIS, an intelligent OS automation assistant."
    
    def _load_goal_extraction_prompt(self) -> str:
        """Load or create goal extraction prompt."""
        return """
You are an AI assistant specialized in understanding user intents. Your job is to extract the core goal from user input.

Return a JSON object with:
{{
  "intent": "main intent (open_app, system_control, file_management, etc)",
  "goal": "concise description of what user wants",
  "confidence": 0.0-1.0,
  "is_complex": true if goal needs multiple steps, false if single step,
  "requires_safety_check": true if goal involves system changes, false otherwise
}}

User input: {user_input}

Respond with ONLY the JSON, no explanations.
"""
    
    def process_command(self, user_input: str, auto_confirm: bool = False) -> Dict[str, Any]:
        """
        Process user command end-to-end.
        
        Args:
            user_input: Natural language command from user
            auto_confirm: Skip confirmation prompts
            
        Returns:
            Execution result dictionary
        """
        logger.info(f"Processing command: {user_input}")
        
        # Add to conversation chain
        self.memory.add_to_context_chain(user_input, role="user")
        
        # Step 1: Extract goal
        goal_info = self._extract_goal(user_input)
        if not goal_info:
            return {
                "status": "error",
                "message": "Failed to understand command",
                "user_input": user_input,
            }
        
        goal = goal_info.get("goal", "")
        is_complex = goal_info.get("is_complex", False)
        requires_safety_check = goal_info.get("requires_safety_check", False)
        confidence = goal_info.get("confidence", 0.0)
        
        print(f"\n🎯 Goal: {goal}")
        print(f"🔍 Confidence: {confidence*100:.0f}%")
        if requires_safety_check:
            print(f"⚠️  This operation involves system changes")
        
        # Step 2: Create task plan
        plan = self.planner.plan_goal(user_input, goal)
        
        # Check if using fallback
        is_fallback = any("Fallback" in task.description for task in plan.tasks)
        
        if is_fallback:
            print(f"\n⚠️  NOTICE:")
            print(f"   The system couldn't break down your goal into specific steps.")
            print(f"   This might be because:")
            print(f"   - The goal is too complex for the current AI")
            print(f"   - The LLM returned invalid JSON")
            print(f"   - The intent wasn't recognized")
            print(f"   Running a basic diagnostic task instead...")
        else:
            print(f"\n📄 Created plan with {len(plan.tasks)} tasks")
        
        # Save plan to memory
        self.memory.save_plan(plan)
        
        # Step 3: Execute plan
        execution_result = self.executor.execute_plan(plan, auto_confirm=auto_confirm)
        
        # Step 4: Save execution to memory
        self.memory.save_execution(plan)
        
        # Step 5: Add result to context
        self.memory.add_to_context_chain(
            f"Executed plan with {execution_result['completed']} completed, {execution_result['failed']} failed",
            role="assistant"
        )
        
        # Generate report
        report = self.executor.get_execution_report(plan)
        
        if is_fallback:
            print("\n" + "="*60)
            print("💡 HOW TO GET BETTER RESULTS:")
            print("="*60)
            print("Try more specific commands:")
            print("  ✓ 'check my cpu usage'")
            print("  ✓ 'find duplicate files in Downloads'")
            print("  ✓ 'clean temp files'")
            print("  ✓ 'organize my downloads'")
            print("Instead of:")
            print("  ✗ 'speed up my pc' (too vague)")
            print("  ✗ 'clean my computer' (ambiguous)")
            print("="*60 + "\n")
        
        print(report)
        
        return {
            "status": "completed" if not execution_result.get("has_failures") else "partial",
            "plan_id": plan.id,
            "user_input": user_input,
            "goal": goal,
            "is_fallback": is_fallback,
            "execution_result": execution_result,
            "report": report,
        }
    
    def _extract_goal(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Extract goal from user input using LLM."""
        prompt = self.goal_extraction_prompt.format(user_input=user_input)
        
        try:
            response = self.llm.generate(prompt)
            goal_info = extract_json(response)
            
            if isinstance(goal_info, dict):
                return goal_info
            return None
        except Exception as e:
            logger.error(f"Goal extraction error: {e}")
            return None
    
    def get_execution_history(self, limit: int = 10) -> list:
        """Get recent execution history."""
        return self.memory.get_recent_executions(limit)
    
    def get_execution_stats(self) -> dict:
        """Get execution statistics."""
        return self.memory.get_execution_stats()
    
    def get_context_summary(self) -> dict:
        """Get current context summary."""
        return {
            "context": self.memory.get_context(),
            "preferences": self.memory.get_all_preferences(),
            "memory_stats": self.memory.get_memory_stats(),
            "execution_stats": self.get_execution_stats(),
        }
    
    def set_preference(self, key: str, value: Any) -> None:
        """Save user preference."""
        self.memory.save_preference(key, value)
        logger.info(f"Preference set: {key} = {value}")
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference."""
        return self.memory.get_preference(key, default)
    
    def clear_history(self) -> None:
        """Clear all history and context."""
        self.memory.clear_all()
        logger.info("All history cleared")
    
    def get_agent_status(self) -> dict:
        """Get overall agent status."""
        stats = self.get_execution_stats()
        memory_stats = self.memory.get_memory_stats()
        
        return {
            "status": "ready",
            "execution_history_count": stats.get("total_executions", 0),
            "success_rate": stats.get("success_rate", 0.0),
            "memory_entries": memory_stats.get("execution_history_entries", 0),
            "cached_plans": memory_stats.get("cached_plans", 0),
        }
    
    def adaptive_execute(self, user_input: str) -> Dict[str, Any]:
        """
        Execute with adaptive behavior based on preferences and history.
        
        - Auto-confirm if user has done similar task before
        - Suggest skipping if user always skips similar tasks
        - Learn optimal parameters from past executions
        """
        # Check similar past executions
        similar_executions = self.memory.get_execution_by_intent(user_input, limit=3)
        
        if similar_executions:
            # User has done this before
            success_rate = sum(
                1 for ex in similar_executions
                if not ex["summary"].get("has_failures", False)
            ) / len(similar_executions)
            
            if success_rate > 0.8:
                # High success rate - auto-confirm
                print("🎓 Learning: Auto-confirming based on past successful executions")
                return self.process_command(user_input, auto_confirm=True)
        
        # Normal execution
        return self.process_command(user_input, auto_confirm=False)
