import sys
import os

# Add the current directory (JARVIS root) to the module search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Now we can safely import the UI application
from ui.app import run_gui_app

if __name__ == "__main__":
    import argparse
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('jarvis_gui.log'),
            logging.StreamHandler()
        ]
    )
    
    parser = argparse.ArgumentParser(description="Kiro OS - Floating Bot")
    parser.add_argument("--voice", action="store_true", help="Enable automatic voice input mode")
    args = parser.parse_args()
    
    sys.exit(run_gui_app(enable_voice=args.voice))
