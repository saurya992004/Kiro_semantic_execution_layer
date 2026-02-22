from agent.master_agent import MasterAgent
from tools.help_commands import print_help


def display_welcome():
    """Display welcome message."""
    print("\n" + "="*60)
    print("🤖 JARVIS - Intelligent OS Automation Agent")
    print("="*60)
    print("Commands: Type your request naturally, or try:")
    print("  - 'help' - Show help and commands")
    print("  - 'history' - Show execution history")
    print("  - 'stats' - Show execution statistics")
    print("  - 'status' - Show agent status")
    print("  - 'clear history' - Clear all memory")
    print("  - 'exit' - Exit JARVIS")
    print("="*60 + "\n")


def handle_special_command(command: str, agent: MasterAgent) -> bool:
    """
    Handle special commands.
    
    Returns:
        True if command was handled, False otherwise
    """
    cmd = command.lower().strip()
    
    if cmd in ["help", "help map", "?", "commands"]:
        print_help()
        return True
    
    elif cmd == "history":
        history = agent.get_execution_history(limit=5)
        print("\n📜 RECENT EXECUTION HISTORY:")
        for i, entry in enumerate(history, 1):
            print(f"{i}. {entry['user_input']}")
            print(f"   └─ {entry['summary']['completed']}/{entry['summary']['total_tasks']} tasks completed")
        return True
    
    elif cmd == "stats":
        stats = agent.get_execution_stats()
        print("\n📊 EXECUTION STATISTICS:")
        print(f"Total Executions: {stats['total_executions']}")
        print(f"Successful: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        print(f"Success Rate: {stats['success_rate']:.1f}%")
        return True
    
    elif cmd == "status":
        status = agent.get_agent_status()
        print("\n⚙️  AGENT STATUS:")
        print(f"Status: {status['status']}")
        print(f"Execution History: {status['execution_history_count']}")
        print(f"Success Rate: {status['success_rate']:.1f}%")
        print(f"Memory Entries: {status['memory_entries']}")
        return True
    
    elif cmd == "clear history":
        confirm = input("Are you sure? This will delete all execution history. (y/n): ").lower()
        if confirm == 'y':
            agent.clear_history()
            print("✅ History cleared")
        return True
    
    return False


def main():
    """Main JARVIS entry point with Master Agent."""
    
    # Initialize master agent
    agent = MasterAgent()
    
    display_welcome()
    
    while True:
        try:
            user_input = input("\n🎤 Jarvis > ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                print("\n👋 Goodbye!")
                break
            
            # Try to handle special commands
            if handle_special_command(user_input, agent):
                continue
            
            # Process as regular command through Master Agent
            result = agent.process_command(user_input, auto_confirm=False)
            
        except KeyboardInterrupt:
            print("\n\n⛔ Interrupted by user")
            continue
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('jarvis.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    main()
