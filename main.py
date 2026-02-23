"""
🤖 JARVIS - Main Entry Point
=============================
Supports two input modes:
  • Text mode (default): classic terminal input()
  • Voice mode (--voice): speak commands via Groq Whisper large-v3
"""

import argparse
import logging

from agent.master_agent import MasterAgent
from tools.help_commands import print_help

logger = logging.getLogger(__name__)


def display_welcome(voice_mode: bool = False):
    """Display welcome message."""
    mode_tag = "🎙️  VOICE MODE" if voice_mode else "⌨️  TEXT MODE"
    print("\n" + "="*60)
    print("🤖 JARVIS - Intelligent OS Automation Agent")
    print(f"   {mode_tag}")
    print("="*60)
    print("Commands: Type your request naturally, or try:")
    print("  - 'help' - Show help and commands")
    print("  - 'history' - Show execution history")
    print("  - 'stats' - Show execution statistics")
    print("  - 'status' - Show agent status")
    print("  - 'clear history' - Clear all memory")
    print("  - 'exit' - Exit JARVIS")
    if voice_mode:
        print()
        print("Voice commands:")
        print("  - Say 'exit' or 'quit' to stop")
        print("  - Say 'calibrate' to recalibrate silence threshold")
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


# ---------------------------------------------------------------------------
# Text loop (original behaviour)
# ---------------------------------------------------------------------------

def run_text_loop(agent: MasterAgent):
    """Classic keyboard-driven interaction loop."""
    while True:
        try:
            user_input = input("\n🎤 Jarvis > ").strip()

            if not user_input:
                continue

            if user_input.lower() == "exit":
                print("\n👋 Goodbye!")
                break

            if handle_special_command(user_input, agent):
                continue

            agent.process_command(user_input, auto_confirm=False)

        except KeyboardInterrupt:
            print("\n\n⛔ Interrupted by user")
            continue
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())


# ---------------------------------------------------------------------------
# Voice loop (new)
# ---------------------------------------------------------------------------

def run_voice_loop(agent: MasterAgent):
    """Voice-driven interaction loop using Groq Whisper large-v3."""
    try:
        from voice.voice_listener import VoiceListener
    except ImportError as exc:
        print(f"\n❌ Could not import VoiceListener: {exc}")
        print("   Run:  pip install sounddevice numpy scipy")
        return

    listener = VoiceListener()

    # Optional: calibrate ambient noise on startup
    try:
        listener.calibrate_silence_threshold(duration=1.5)
    except Exception as exc:
        logger.warning(f"Calibration skipped: {exc}")

    print("\n🟢 Voice mode ready. Speak your command when you see 'Listening…'")

    while True:
        try:
            user_input = listener.listen()

            # No speech captured — just loop
            if not user_input:
                continue

            cmd = user_input.lower().strip()

            # Exit words
            if cmd in ["exit", "quit", "bye", "goodbye", "stop"]:
                print("\n👋 Goodbye!")
                break

            # Allow recalibration via voice
            if cmd == "calibrate":
                listener.calibrate_silence_threshold()
                continue

            if handle_special_command(user_input, agent):
                continue

            agent.process_command(user_input, auto_confirm=False)

        except KeyboardInterrupt:
            print("\n\n⛔ Interrupted by user")
            continue
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Main JARVIS entry point with Master Agent."""

    parser = argparse.ArgumentParser(
        description="JARVIS - Intelligent OS Automation Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--voice",
        action="store_true",
        help="Enable voice mode: speak commands via Groq Whisper large-v3",
    )
    args, _ = parser.parse_known_args()

    # Initialise master agent
    agent = MasterAgent()

    display_welcome(voice_mode=args.voice)

    if args.voice:
        run_voice_loop(agent)
    else:
        run_text_loop(agent)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('jarvis.log'),
            logging.StreamHandler()
        ]
    )

    main()
