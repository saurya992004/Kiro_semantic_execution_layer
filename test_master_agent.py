"""
Master Agent Integration Test
==============================
Test script to verify Master Agent functionality.
Run this to validate the agent system is working properly.
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all modules can be imported."""
    print("\n" + "="*60)
    print("🧪 TEST 1: Module Imports")
    print("="*60)
    
    try:
        from agent.master_agent import MasterAgent
        print("✅ MasterAgent imported")
        
        from agent.task_planner import TaskPlanner
        print("✅ TaskPlanner imported")
        
        from agent.execution_engine import ExecutionEngine
        print("✅ ExecutionEngine imported")
        
        from agent.memory_manager import MemoryManager
        print("✅ MemoryManager imported")
        
        from agent.task import Task, TaskPlan, TaskStatus, TaskPriority
        print("✅ Task models imported")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_task_creation():
    """Test task creation and validation."""
    print("\n" + "="*60)
    print("🧪 TEST 2: Task Creation")
    print("="*60)
    
    try:
        from agent.task import Task, TaskStatus, TaskPriority
        
        # Create a simple task
        task = Task(
            id="test_task_1",
            intent="diagnostics",
            action="check_cpu",
            description="Test CPU check",
            priority=TaskPriority.HIGH,
        )
        
        print(f"✅ Task created: {task.id}")
        print(f"   - Intent: {task.intent}")
        print(f"   - Status: {task.status.value}")
        print(f"   - Priority: {task.priority.value}")
        
        # Test task status transitions
        task.mark_started()
        assert task.status == TaskStatus.IN_PROGRESS
        print(f"✅ Task status updated to: {task.status.value}")
        
        task.mark_completed({"result": "CPU: 45%"})
        assert task.status == TaskStatus.COMPLETED
        print(f"✅ Task completed with result: {task.result}")
        
        return True
    except Exception as e:
        print(f"❌ Task creation failed: {e}")
        return False


def test_task_plan():
    """Test task plan creation."""
    print("\n" + "="*60)
    print("🧪 TEST 3: Task Plan")
    print("="*60)
    
    try:
        from agent.task import Task, TaskPlan, TaskStatus
        
        plan = TaskPlan(
            id="plan_test_1",
            user_input="check my system",
            goal="Check system health"
        )
        print(f"✅ Plan created: {plan.id}")
        
        task1 = Task(
            id="t1",
            intent="diagnostics",
            action="check_cpu",
            description="Check CPU"
        )
        
        task2 = Task(
            id="t2",
            intent="diagnostics", 
            action="check_ram",
            description="Check RAM",
            dependencies=["t1"]
        )
        
        plan.add_task(task1)
        plan.add_task(task2)
        print(f"✅ Added 2 tasks to plan")
        
        summary = plan.get_execution_summary()
        print(f"✅ Plan summary: {summary['total_tasks']} tasks, {len(plan.tasks)} in plan")
        
        # Test dependency checking
        assert task1.is_ready_to_execute([])
        print(f"✅ Task 1 is ready (no dependencies)")
        
        assert not task2.is_ready_to_execute([])
        assert task2.is_ready_to_execute(["t1"])
        print(f"✅ Task 2 dependency logic works")
        
        return True
    except Exception as e:
        print(f"❌ Task plan test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_manager():
    """Test memory manager functionality."""
    print("\n" + "="*60)
    print("🧪 TEST 4: Memory Manager")
    print("="*60)
    
    try:
        from agent.memory_manager import MemoryManager
        from agent.task import TaskPlan
        
        memory = MemoryManager("test_agent_memory")
        print(f"✅ Memory manager initialized")
        
        # Test saving preferences
        memory.save_preference("test_key", "test_value")
        value = memory.get_preference("test_key")
        assert value == "test_value"
        print(f"✅ Preferences save/load works")
        
        # Test context
        memory.update_context("test_context", {"data": "value"})
        ctx = memory.get_context("test_context")
        assert ctx == {"data": "value"}
        print(f"✅ Context management works")
        
        # Test conversation chain
        memory.add_to_context_chain("Hello", role="user")
        chain = memory.get_conversation_chain()
        assert len(chain) > 0
        print(f"✅ Conversation chain works")
        
        stats = memory.get_memory_stats()
        print(f"✅ Memory stats: {stats}")
        
        # Cleanup test memory
        import shutil
        if Path("test_agent_memory").exists():
            shutil.rmtree("test_agent_memory")
        
        return True
    except Exception as e:
        print(f"❌ Memory manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_execution_engine():
    """Test execution engine."""
    print("\n" + "="*60)
    print("🧪 TEST 5: Execution Engine")
    print("="*60)
    
    try:
        from agent.execution_engine import ExecutionEngine
        from agent.task import Task, TaskPlan
        
        engine = ExecutionEngine()
        print(f"✅ Execution engine initialized")
        
        # Create a simple plan
        plan = TaskPlan(
            id="engine_test",
            user_input="test",
            goal="Test execution"
        )
        
        task = Task(
            id="test_task",
            intent="diagnostics",
            action="check_cpu",
            description="Test task"
        )
        
        plan.add_task(task)
        
        # Test report generation
        report = engine.get_execution_report(plan)
        assert "EXECUTION REPORT" in report
        print(f"✅ Execution report generation works")
        
        return True
    except Exception as e:
        print(f"❌ Execution engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_master_agent():
    """Test master agent initialization."""
    print("\n" + "="*60)
    print("🧪 TEST 6: Master Agent")
    print("="*60)
    
    try:
        from agent.master_agent import MasterAgent
        
        agent = MasterAgent(memory_dir="test_agent_memory")
        print(f"✅ Master agent initialized")
        
        status = agent.get_agent_status()
        print(f"✅ Agent status: {status['status']}")
        print(f"   - Executions: {status['execution_history_count']}")
        print(f"   - Success rate: {status['success_rate']:.1f}%")
        
        # Cleanup test memory
        import shutil
        if Path("test_agent_memory").exists():
            shutil.rmtree("test_agent_memory")
        
        return True
    except Exception as e:
        print(f"❌ Master agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all integration tests."""
    
    print("\n" + "="*60)
    print("🚀 MASTER AGENT INTEGRATION TEST SUITE")
    print("="*60)
    
    results = {
        "Imports": test_imports(),
        "Task Creation": test_task_creation(),
        "Task Plan": test_task_plan(),
        "Memory Manager": test_memory_manager(),
        "Execution Engine": test_execution_engine(),
        "Master Agent": test_master_agent(),
    }
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Master Agent is ready to use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please fix issues before running main.py")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
