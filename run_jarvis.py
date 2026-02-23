#!/usr/bin/env python3
"""
🤖 JARVIS - Main Launcher
Launch Jarvis AI System Controller

Usage:
    python run_jarvis.py           # text mode (default)
    python run_jarvis.py --voice   # voice mode via Groq Whisper large-v3
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == "__main__":
    print("🤖 Launching JARVIS...")
    print()

    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 JARVIS shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

