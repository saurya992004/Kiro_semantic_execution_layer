"""
JARVIS GUI Application
======================
Main GUI application with floating widget and chat interface.
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow
import time
import requests
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QIcon

from widget.widget import FloatingBotWidget
from ui.chat_card import ChatCard
from agent.master_agent import MasterAgent
from voice.voice_listener import VoiceListener

logger = logging.getLogger(__name__)
class GhostPollerThread(QThread):
    error_detected = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.last_run = None
        
    def run(self):
        while self.running:
            try:
                resp = requests.get("http://localhost:8000/api/ghost-mode/status", timeout=45)
                if resp.status_code == 200:
                    data = resp.json()
                    current_run = data.get("last_run")
                    
                    if data.get("active") and current_run and current_run != self.last_run:
                        self.last_run = current_run
                        analysis = data.get("latest_analysis")
                        if analysis and isinstance(analysis, dict):
                            errors = analysis.get("possible_errors_or_alerts", [])
                            # Catch ALL errors & warnings — Gemini sometimes labels NameErrors as "warning"
                            actionable = [e for e in errors if e.get("severity") in ("error", "critical", "warning")]
                            
                            # Filter out our own debug output that Gemini might read from our terminal
                            noise_keywords = ["GhostPoller", "Ghost Mode", "AUTONOMOUS_FIX", "Diagnostic Engine"]
                            clean_errors = [e for e in actionable if not any(n in e.get("text", "") for n in noise_keywords)]
                            
                            if clean_errors:
                                # Build a clean, structured error description
                                all_error_texts = [e.get("text", "") for e in clean_errors]
                                
                                # Also grab error-tagged visible text (often has the full traceback)
                                visible_regions = analysis.get("visible_text_regions", [])
                                error_regions = [r.get("text", "") for r in visible_regions 
                                                 if r.get("role") == "error" and not any(n in r.get("text", "") for n in noise_keywords)]
                                
                                # Build structured report for the troubleshooter
                                parts = []
                                if analysis.get("window_title_or_app"):
                                    parts.append(f"App: {analysis['window_title_or_app']}")
                                for et in all_error_texts:
                                    if et not in parts:
                                        parts.append(et)
                                for er in error_regions:
                                    if er not in parts:
                                        parts.append(er)
                                
                                full_error = " | ".join(parts)
                                short_error = all_error_texts[0][:60] if all_error_texts else "Unknown error"
                                
                                print(f"[GhostPoller] ERROR DETECTED: {short_error}")
                                self.error_detected.emit({
                                    "error": short_error,
                                    "error_detail": full_error,
                                    "full_analysis": analysis
                                })
                            else:
                                print(f"[GhostPoller] Scan done, no actionable errors. ({len(errors)} total, {len(actionable)} actionable, all filtered as noise)")
            except requests.exceptions.Timeout:
                print("[GhostPoller] Server busy (Gemini scan in progress), will retry...")
            except Exception as e:
                print(f"[GhostPoller] Error: {e}")
            time.sleep(8)
            
    def stop(self):
        self.running = False
        self.wait()

class JarvisGUIApp:
    """Main JARVIS GUI Application"""
    
    def __init__(self, enable_voice: bool = False):
        """
        Initialize JARVIS GUI App
        """
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.enable_voice = enable_voice
        
        # Initialize components
        self.agent = MasterAgent()
        self.voice_listener = None
        try:
            self.voice_listener = VoiceListener()
            logger.info("Voice listener initialized")
        except Exception as e:
            logger.warning(f"Could not initialize voice listener: {e}")
        
        # Create UI
        self.widget = FloatingBotWidget()
        self.chat_card = ChatCard(self.agent, self.voice_listener)
        
        # Connect widget click to chat card toggle
        self.widget.clicked.connect(self.toggle_chat_card)
        self.widget.fix_error_requested.connect(self.trigger_troubleshooter)
        
        # Start Ghost Mode Poller
        self.ghost_poller = GhostPollerThread()
        self.ghost_poller.error_detected.connect(self.handle_ghost_error)
        self.ghost_poller.start()
        
        # Show initial widgets
        self.widget.show()
        
        logger.info("JARVIS GUI initialized")
        
    def handle_ghost_error(self, error_data):
        logger.info(f"Ghost Mode detected error: {error_data['error']}")
        self.widget.alert_error(error_data["error"], error_data)
        
    def trigger_troubleshooter(self, error_data):
        """Fired when user clicks widget during error alert"""
        logger.info("User requested autonomous fix for error.")
        self.chat_card.show()
        self.chat_card.raise_()
        self.chat_card.activateWindow()
        
        error_text = error_data.get("error", "Unknown error")
        self.chat_card.append_ai_message(f"Starting autonomous resolution for: **{error_text}**")
        self.chat_card.show_yes_no_options(error_data)
    
    def toggle_chat_card(self):
        """Toggle the chat card dialog visibility"""
        if self.chat_card.isVisible():
            print("🔔 Widget clicked - hiding chat interface...")
            logger.info("Chat card hidden by widget click")
            self.chat_card.hide()
        else:
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

