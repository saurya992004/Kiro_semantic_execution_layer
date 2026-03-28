"""
Architecture Demo - Shows new production system in action
Demonstrates:
1. Multiple LLM backends (Groq, Gemini) registered and routable
2. Tool registry auto-discovering tools
3. Simple command execution flow
4. Event-driven architecture
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from core.llm.router import LLMRouter
from core.llm.event_bus import InMemoryEventBus
from core.tools.registry import ToolRegistry
from core.protocols import LLMRequest, ToolInput, EventType
from llm_backends.groq_backend import GroqBackend
from llm_backends.gemini_backend import GeminiBackend
from tool_servers.file_tools import FileToolServer


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


async def demo_architecture():
    """
    Demonstrate the new production architecture
    """
    
    print("\n" + "="*70)
    print("JARVIS 2.0 - PRODUCTION ARCHITECTURE DEMO")
    print("="*70 + "\n")
    
    # 1. Initialize Event Bus
    print("1️⃣  Initializing Event Bus (event-driven architecture)")
    event_bus = InMemoryEventBus()
    
    # Subscribe to important events
    @event_bus.on(EventType.LLM_REQUESTED)
    async def log_llm_request(event):
        print(f"   📤 LLM Request: {event.data}")
    
    @event_bus.on(EventType.LLM_RESPONSE)
    async def log_llm_response(event):
        print(f"   📥 LLM Response: {event.data}")
    
    @event_bus.on(EventType.TOOL_CALLED)
    async def log_tool_call(event):
        print(f"   🔧 Tool Called: {event.data}")
    
    print("   ✅ Event bus initialized\n")
    
    # 2. Initialize LLM Router with multiple backends
    print("2️⃣  Setting up LLM Router with pluggable backends")
    llm_router = LLMRouter(event_bus=event_bus)
    
    # Register Groq backend
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        groq_backend = GroqBackend(api_key=groq_key)
        llm_router.register_backend("groq", groq_backend, is_primary=True)
        print("   ✅ Groq backend registered (PRIMARY)")
    else:
        print("   ⚠️  GROQ_API_KEY not found, skipping Groq")
    
    # Register Gemini backend
    gemini_key = os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        gemini_backend = GeminiBackend(api_key=gemini_key)
        llm_router.register_backend("gemini", gemini_backend)
        print("   ✅ Gemini backend registered")
    else:
        print("   ⚠️  GOOGLE_API_KEY not found, skipping Gemini")
    
    # Show registered backends
    backends = llm_router.list_backends()
    print(f"   📊 Total backends: {len(backends)}: {backends}\n")
    
    # 3. Initialize Tool Registry
    print("3️⃣  Setting up Tool Registry (auto-discovery)")
    tool_registry = ToolRegistry(event_bus=event_bus)
    
    # Register file tools server
    file_server = FileToolServer()
    await tool_registry.register_server(file_server)
    print("   ✅ File tools server registered")
    
    # Show registered tools
    all_tools = tool_registry.list_tools()
    print(f"   📊 Total tools: {len(all_tools)}")
    for tool in all_tools:
        print(f"      - {tool.name}: {tool.description}")
    print()
    
    # 4. Demo LLM Routing
    print("4️⃣  Demo: LLM Routing (asking both backends)")
    if backends:
        request = LLMRequest(
            prompt="What is the difference between Python and JavaScript?",
            temperature=0.7,
            max_tokens=256,
        )
        
        try:
            # Try Groq
            if "groq" in backends:
                print("   🔄 Routing to Groq...")
                response = await llm_router.generate(request, preferred_backend="groq")
                print(f"   ✅ Groq Response ({response.tokens_used} tokens):")
                print(f"      {response.text[:100]}...\n")
            
            # Try Gemini  
            if "gemini" in backends:
                print("   🔄 Routing to Gemini...")
                response = await llm_router.generate(request, preferred_backend="gemini")
                print(f"   ✅ Gemini Response ({response.tokens_used} tokens):")
                print(f"      {response.text[:100]}...\n")
        
        except Exception as e:
            print(f"   ⚠️  LLM generation failed: {e}\n")
    
    # 5. Demo Tool Execution
    print("5️⃣  Demo: Tool Execution")
    try:
        tool_input = ToolInput(
            tool_name="find_large_files",
            parameters={
                "path": "c:\\Users\\saury\\Desktop\\kiro\\JARVIS",
                "min_size_mb": 1,
                "max_results": 10,
            },
        )
        
        output = await tool_registry.execute(tool_input)
        
        if output.success:
            print(f"   ✅ Tool executed successfully ({output.latency_ms:.0f}ms)")
            print(f"   📊 Found {len(output.result.get('files', []))} large files")
        else:
            print(f"   ❌ Tool failed: {output.error}")
    
    except Exception as e:
        print(f"   ⚠️  Tool execution failed: {e}")
    
    print()
    
    # 6. Show statistics
    print("6️⃣  Architecture Statistics")
    llm_stats = llm_router.get_stats()
    tool_stats = tool_registry.get_stats()
    
    print(f"   LLM Router:")
    print(f"      - Backends: {llm_stats['backends']}")
    print(f"      - Healthy: {llm_stats['healthy_backends']}")
    print(f"      - Requests processed: {llm_stats['total_requests']}")
    print(f"      - Cache hits: {llm_stats['cached_hits']}")
    print(f"      - Total cost: ${llm_stats['total_cost']:.4f}")
    
    print(f"   Tool Registry:")
    print(f"      - Total tools: {tool_stats['total_tools']}")
    print(f"      - Total servers: {tool_stats['total_servers']}")
    print(f"      - Executions: {tool_stats['total_executions']}")
    print(f"      - Successful: {tool_stats['successful']}")
    print(f"      - Failed: {tool_stats['failed']}")
    
    print("\n" + "="*70)
    print("✅ ARCHITECTURE DEMO COMPLETE")
    print("="*70 + "\n")
    
    print("KEY IMPROVEMENTS FROM OLD SYSTEM:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("❌ OLD: Groq hardcoded in MasterAgent")
    print("✅ NEW: 3 LLM backends pluggable, router chooses best")
    print()
    print("❌ OLD: intent_router.py 300+ lines of if/elif")
    print("✅ NEW: Tool registry auto-discovers, 0 boilerplate")
    print()
    print("❌ OLD: Add tool = modify 5 files")
    print("✅ NEW: Add tool = create 1 file, auto-registered")
    print()
    print("❌ OLD: Synchronous, blocks on each step")
    print("✅ NEW: Async throughout, parallel execution ready")
    print()
    print("❌ OLD: No observability")
    print("✅ NEW: Event bus tracks everything in real-time")
    print()


async def demo_simple_flow():
    """
    Simple example: command execution flow
    """
    print("\n" + "="*70)
    print("SIMPLE FLOW: 'Speed up my PC'")
    print("="*70 + "\n")
    
    event_bus = InMemoryEventBus()
    llm_router = LLMRouter(event_bus=event_bus)
    
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("⚠️  GROQ_API_KEY needed for this demo\n")
        return
    
    groq = GroqBackend(api_key=groq_key)
    llm_router.register_backend("groq", groq)
    
    # Step 1: Extract user intent
    print("Step 1: User sends command: 'Speed up my PC'")
    print()
    
    # Step 2: Goal extraction using LLM
    print("Step 2: Extract goal using LLM")
    request = LLMRequest(
        prompt="""User said: "Speed up my PC"
        What is the user's goal? Answer in one sentence.""",
        temperature=0.5,
        max_tokens=100,
    )
    
    try:
        response = await llm_router.generate(request)
        print(f"   Goal extracted: {response.text}")
        print()
    except Exception as e:
        print(f"   Failed: {e}\n")
        return
    
    # Step 3: Plan generation
    print("Step 3: Generate task plan")
    plan_request = LLMRequest(
        prompt="""To speed up a PC, what are the top 3 things to check?
        Return as: 1. X, 2. Y, 3. Z""",
        temperature=0.7,
        max_tokens=150,
    )
    
    try:
        plan = await llm_router.generate(plan_request)
        print(f"   Plan:\n{plan.text}")
        print()
    except Exception as e:
        print(f"   Failed: {e}\n")
    
    print("✅ Flow complete\n")


async def main():
    """Main entry point"""
    
    # Show architecture demo
    await demo_architecture()
    
    # Show simple flow
    await demo_simple_flow()
    
    print("\n📚 NEXT STEPS:")
    print("1. Build async execution engine (core/execution/)")
    print("2. Implement agent orchestrator (core/agent/)")
    print("3. Add memory layer (core/memory/)")
    print("4. Build FastAPI REST/WebSocket interface")
    print("5. Write comprehensive tests")


if __name__ == "__main__":
    asyncio.run(main())
