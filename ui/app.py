"""
JARVIS GUI Application
======================
Main GUI application with floating widget and chat interface.
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

from widget.widget import FloatingBotWidget
from ui.chat_card import ChatCard
from agent.master_agent import MasterAgent
from voice.voice_listener import VoiceListener

logger = logging.getLogger(__name__)


class JarvisGUIApp:
    """Main JARVIS GUI Application"""
    
    def __init__(self, enable_voice: bool = False):
        """
        Initialize JARVIS GUI App
        
        Args:
            enable_voice: Enable voice input mode
        """
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.enable_voice = enable_voice
        
        # Initialize components
        self.agent = MasterAgent()
        # Always try to init voice listener so the mic button is available.
        # Failures are caught and surfaced in the card, not at startup.
        self.voice_listener = None
        try:
            self.voice_listener = VoiceListener()
            logger.info("Voice listener initialized")
        except Exception as e:
            logger.warning(f"Could not initialize voice listener: {e}")
        
        # Create UI
        self.widget = FloatingBotWidget()
        self.chat_card = ChatCard(self.agent, self.voice_listener)
        
        # Connect widget click to chat card open
        self.widget.clicked.connect(self.show_chat_card)
        
        # Show initial widgets
        self.widget.show()
        
        logger.info("JARVIS GUI initialized")
    
    def show_chat_card(self):
        """Show the chat card dialog"""
        print("🔔 Widget clicked - opening chat interface...")
        logger.info("Chat card requested by widget click")
        self.chat_card.show()
        self.chat_card.raise_()
        self.chat_card.activateWindow()
        print("✅ Chat interface opened")
    
    def run(self):
        """Run the GUI application"""
        return self.app.exec_()


def run_gui_app(enable_voice: bool = False):
    """
    Launch JARVIS GUI application
    
    Args:
        enable_voice: Enable voice input mode
    """
    app = JarvisGUIApp(enable_voice=enable_voice)
    return app.run()


if __name__ == "__main__":
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('jarvis_gui.log'),
            logging.StreamHandler()
        ]
    )
    
    parser = argparse.ArgumentParser(description="JARVIS GUI Application")
    parser.add_argument("--voice", action="store_true", help="Enable voice input mode")
    args = parser.parse_args()
    
    sys.exit(run_gui_app(enable_voice=args.voice))

