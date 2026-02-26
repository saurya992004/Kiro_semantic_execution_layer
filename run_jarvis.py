#!/usr/bin/env python3
"""
🤖 JARVIS - Main Launcher
Launch Jarvis AI System Controller

Usage:
    python run_jarvis.py           # GUI mode (default) - floating widget + chat card
    python run_jarvis.py --voice   # GUI mode + voice input enabled
    python run_jarvis.py --cli     # CLI/terminal text mode (no GUI)
"""

import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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

    parser = argparse.ArgumentParser(
        description="JARVIS - Intelligent OS Automation Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--voice",
        action="store_true",
        help="Enable voice mode (works in both GUI and CLI)",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in CLI/terminal mode instead of GUI",
    )
    args, _ = parser.parse_known_args()

    print("🤖 Launching JARVIS...")
    print()

    try:
        if args.cli:
            # Legacy terminal mode
            from main import main
            main()
        else:
            # GUI mode: floating widget + chat card (default)
            from ui.app import run_gui_app
            sys.exit(run_gui_app(enable_voice=args.voice))

    except KeyboardInterrupt:
        print("\n\n👋 JARVIS shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
