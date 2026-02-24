"""
Chat Card Interface for JARVIS
==============================
Displays conversation with command output, history, and logging.
"""

import sys
import json
import logging
import builtins
import threading
from datetime import datetime
from typing import Optional, Callable
from io import StringIO
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, 
    QPushButton, QTabWidget, QWidget, QLabel, QSplitter, QScrollArea,
    QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QTextCursor, QIcon
from PyQt5.QtCore import QSize

logger = logging.getLogger(__name__)


class StdoutRedirector:
    """Redirects stdout to GUI output display"""
    def __init__(self, output_callback, chat_card=None):
        """
        Args:
            output_callback: Function to call with output text
            chat_card: Reference to ChatCard for output_text
        """
        self.output_callback = output_callback
        self.chat_card = chat_card
        self.original_stdout = sys.stdout
    
    def write(self, text: str):
        """Write text to both GUI and original stdout"""
        if text and text.strip():  # Only display non-empty lines
            try:
                self.output_callback(text)
            except:
                pass  # Ignore errors during early startup
        self.original_stdout.write(text)
    
    def flush(self):
        """Flush the stream"""
        self.original_stdout.flush()
    
    def isatty(self):
        """Check if it's a tty"""
        return False




class VoiceListenerThread(QThread):
    """Background thread for voice listening"""
    text_received = pyqtSignal(str)
    listening_started = pyqtSignal()
    listening_stopped = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, voice_listener):
        super().__init__()
        self.voice_listener = voice_listener
    
    def run(self):
        try:
            self.listening_started.emit()
            text = self.voice_listener.listen()
            if text:
                self.text_received.emit(text)
            self.listening_stopped.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))
            self.listening_stopped.emit()


class RealTimeWriter:
    """
    Replaces sys.stdout during command execution.
    Every write() immediately emits the text as a signal so the GUI
    can display it before the command finishes (real-time streaming).
    Also maintains a rolling list of recent lines for confirmation context.
    """
    def __init__(self, signal, original_stdout, line_tracker=None):
        self.signal = signal
        self.original_stdout = original_stdout
        self._buffer = ""
        self._line_tracker = line_tracker  # shared list owned by the thread

    def write(self, text: str):
        if text:
            self.original_stdout.write(text)   # keep terminal output too
            self._buffer += text
            while '\n' in self._buffer:
                line, self._buffer = self._buffer.split('\n', 1)
                if line:
                    # Track for confirmation context
                    if self._line_tracker is not None:
                        self._line_tracker.append(line)
                        if len(self._line_tracker) > 50:
                            self._line_tracker.pop(0)
                    self.signal.emit(line)

    def flush(self):
        # Flush any remaining partial line
        if self._buffer.strip():
            self.signal.emit(self._buffer)
            self._buffer = ""
        self.original_stdout.flush()

    def isatty(self):
        return False


class CommandExecutionThread(QThread):
    """Background thread for command execution with real-time output and GUI confirmation"""
    output_received = pyqtSignal(str)      # emitted per-line in real time
    execution_completed = pyqtSignal(dict)
    execution_failed = pyqtSignal(str)
    # Emitted when execution_engine needs a y/n confirmation.
    # Carries the FULL context prompt so the dialog is informative.
    confirmation_requested = pyqtSignal(str)

    def __init__(self, agent, command: str):
        super().__init__()
        self.agent = agent
        self.command = command
        # Threading primitives for main-thread confirmation round-trip
        self._confirm_event = threading.Event()
        self._confirm_result = False
        self._last_output_lines = []   # collect recent lines for context

    def _gui_input(self, prompt: str = "") -> str:
        """
        Replacement for builtins.input() that runs inside the worker thread.
        Emits a signal (with recent output context) so the main thread can
        show a dialog, then blocks until the main thread sets _confirm_event.
        """
        self._confirm_event.clear()
        self._confirm_result = False
        # Build a rich context message: last few output lines + the prompt
        context_lines = self._last_output_lines[-8:]  # last 8 lines of output
        context = '\n'.join(context_lines)
        full_prompt = f"{context}\n\n{prompt}".strip() if context else str(prompt)
        self.confirmation_requested.emit(full_prompt)
        # Block the worker thread until the main thread answers
        self._confirm_event.wait(timeout=120)  # 2-minute safety timeout
        return 'y' if self._confirm_result else 'n'

    def run(self):
        old_stdout = sys.stdout
        old_input = builtins.input

        # Walk the stdout chain to find the real console stdout.
        # sys.stdout may be a StdoutRedirector (GUI wrapper) — calling its
        # write() from a background thread would crash Qt. We must only use
        # the underlying real file object for terminal echo.
        console_stdout = old_stdout
        while hasattr(console_stdout, 'original_stdout'):
            console_stdout = console_stdout.original_stdout

        # RealTimeWriter emits signals (thread-safe) for GUI and echoes to
        # the real console stdout only (no GUI calls from this thread).
        writer = RealTimeWriter(self.output_received, console_stdout,
                                line_tracker=self._last_output_lines)
        sys.stdout = writer
        builtins.input = self._gui_input
        try:
            result = self.agent.process_command(self.command, auto_confirm=False)
            writer.flush()  # flush any trailing partial line
            self.execution_completed.emit(result)
        except Exception as e:
            self.execution_failed.emit(str(e))
        finally:
            sys.stdout = old_stdout
            builtins.input = old_input


class ChatCard(QDialog):
    """Chat interface card that opens when widget is clicked"""
    
    def __init__(self, agent, voice_listener=None, parent=None):
        super().__init__(parent)
        self.agent = agent
        self.voice_listener = voice_listener
        self.execution_thread = None
        self.voice_thread = None
        self.is_listening = False
        
        # Setup logging
        self.log_entries = []
        self.command_history = []
        self.command_history_index = -1
        
        self.setWindowTitle("🤖 JARVIS - Command Interface")
        self.setGeometry(100, 100, 900, 700)
        self.setup_ui()
        
        # Redirect stdout to output display (after setup_ui so output_text exists)
        self.stdout_redirector = StdoutRedirector(self.display_output, self)
        sys.stdout = self.stdout_redirector
        
        self.load_history()
    
    def display_output(self, text: str):
        """Display output from stdin/terminal in output area"""
        if hasattr(self, 'output_text') and self.output_text:
            self.output_text.append(text.rstrip())
            # Auto-scroll to bottom
            scrollbar = self.output_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def show_confirmation_dialog(self, title: str, message: str) -> bool:
        """
        Show a confirmation dialog with Yes/No buttons.
        
        Args:
            title: Dialog title
            message: Confirmation message
            
        Returns:
            True if user clicked Yes/✓, False if No/✗
        """
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #0f0f1e;
            }
            QMessageBox QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #44475a;
                color: white;
                border: 1px solid #667;
                border-radius: 5px;
                padding: 8px 25px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        
        # Create Yes (✓) and No (✗) buttons
        yes_button = msg_box.addButton("✓ Yes", QMessageBox.AcceptRole)
        no_button = msg_box.addButton("✗ No", QMessageBox.RejectRole)
        
        yes_button.setStyleSheet("""
            QPushButton {
                background-color: #00d4ff;
                color: black;
                border: 2px solid #00d4ff;
                border-radius: 5px;
                padding: 8px 25px;
                min-width: 100px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00e6ff;
            }
        """)
        
        no_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: 2px solid #ff6b6b;
                border-radius: 5px;
                padding: 8px 25px;
                min-width: 100px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff8888;
            }
        """)
        
        msg_box.exec_()
        # Bug 4 fix: compare the clicked button object, not the return int
        return msg_box.clickedButton() == yes_button
        
    def setup_ui(self):
        """Setup the UI components"""
        main_layout = QVBoxLayout()
        
        # Create tabs
        self.tabs = QTabWidget()
        
        # Tab 1: Chat/Command Interface
        self.chat_tab = QWidget()
        self.setup_chat_tab()
        self.tabs.addTab(self.chat_tab, "💬 Chat")
        
        # Tab 2: History
        self.history_tab = QWidget()
        self.setup_history_tab()
        self.tabs.addTab(self.history_tab, "📜 History")
        
        # Tab 3: Logger
        self.logger_tab = QWidget()
        self.setup_logger_tab()
        self.tabs.addTab(self.logger_tab, "📋 Logger")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        
        # Setup stylesheet
        self.apply_stylesheet()
    
    def setup_chat_tab(self):
        """Setup the chat/command interface tab"""
        layout = QVBoxLayout()
        
        # Output display area
        output_label = QLabel("📤 Output:")
        output_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Courier", 9))
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e2e;
                color: #00ff00;
                border: 1px solid #44475a;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        layout.addWidget(output_label)
        layout.addWidget(self.output_text, 3)
        
        # Input section
        input_label = QLabel("⌨️  Input:")
        input_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        input_layout = QHBoxLayout()
        
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type your command here...")
        self.input_box.setFont(QFont("Arial", 10))
        self.input_box.returnPressed.connect(self.send_command)
        self.input_box.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d3d;
                color: #ffffff;
                border: 2px solid #44475a;
                border-radius: 5px;
                padding: 8px;
            }
            QLineEdit:focus {
                border: 2px solid #00d4ff;
            }
        """)
        
        # Voice button
        self.voice_button = QPushButton("🎤")
        self.voice_button.setFont(QFont("Arial", 14))
        self.voice_button.setMaximumWidth(50)
        self.voice_button.setToolTip("Click to start voice input")
        self.voice_button.clicked.connect(self.toggle_voice_input)
        self.voice_button.setEnabled(True)  # always enabled; errors shown in output
        self.voice_button.setStyleSheet("""
            QPushButton {
                background-color: #44475a;
                color: white;
                border: 1px solid #667;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QPushButton:pressed {
                background-color: #00d4ff;
                color: black;
            }
        """)
        
        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.setMaximumWidth(100)
        self.send_button.clicked.connect(self.send_command)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #00d4ff;
                color: black;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00e6ff;
            }
            QPushButton:pressed {
                background-color: #00b8cc;
            }
        """)
        
        self.listening_label = QLabel("")
        self.listening_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        
        input_layout.addWidget(self.input_box, 1)
        input_layout.addWidget(self.voice_button)
        input_layout.addWidget(self.send_button)
        
        layout.addWidget(input_label)
        layout.addLayout(input_layout)
        layout.addWidget(self.listening_label)
        
        self.chat_tab.setLayout(layout)
    
    def setup_history_tab(self):
        """Setup command history tab"""
        layout = QVBoxLayout()
        
        title = QLabel("📜 Command History")
        title.setFont(QFont("Arial", 11, QFont.Bold))
        
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setFont(QFont("Arial", 9))
        self.history_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e2e;
                color: #00ff00;
                border: 1px solid #44475a;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        clear_button = QPushButton("🗑️  Clear History")
        clear_button.clicked.connect(self.clear_history)
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #ff8888;
            }
        """)
        
        layout.addWidget(title)
        layout.addWidget(self.history_text)
        layout.addWidget(clear_button)
        
        self.history_tab.setLayout(layout)
    
    def setup_logger_tab(self):
        """Setup logger/activity tab"""
        layout = QVBoxLayout()
        
        title = QLabel("📋 Activity Logger")
        title.setFont(QFont("Arial", 11, QFont.Bold))
        
        self.logger_text = QTextEdit()
        self.logger_text.setReadOnly(True)
        self.logger_text.setFont(QFont("Courier", 8))
        self.logger_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e2e;
                color: #ffff00;
                border: 1px solid #44475a;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        clear_button = QPushButton("🗑️  Clear Logs")
        clear_button.clicked.connect(self.clear_logs)
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #ff8888;
            }
        """)
        
        layout.addWidget(title)
        layout.addWidget(self.logger_text)
        layout.addWidget(clear_button)
        
        self.logger_tab.setLayout(layout)
    
    def needs_confirmation(self, command: str) -> bool:
        """
        Check if command contains destructive operations that need confirmation.
        
        Args:
            command: User's command string
            
        Returns:
            True if confirmation needed, False otherwise
        """
        destructive_keywords = [
            'delete', 'remove', 'uninstall', 'kill',
            'empty', 'format', 'wipe'
        ]
        
        command_lower = command.lower()
        return any(keyword in command_lower for keyword in destructive_keywords)
    
    def send_command(self):
        """Send command to JARVIS"""
        command = self.input_box.text().strip()
        
        if not command:
            self.log_activity("⚠️  Empty command")
            return
        
        # ── Intercept exit/quit — close the app, don't send to the agent ──
        EXIT_WORDS = {"exit", "quit", "bye", "close", "goodbye"}
        if command.strip().lower() in EXIT_WORDS:
            self.output_text.append("\n👋 Closing JARVIS...")
            self.input_box.clear()
            from PyQt5.QtWidgets import QApplication
            QApplication.instance().quit()
            return

        # ── Intercept help — show built-in command reference, skip LLM ──
        HELP_WORDS = {"help", "?", "commands", "what can you do", "show commands"}
        if command.strip().lower() in HELP_WORDS:
            self._show_help_in_gui()
            self.input_box.clear()
            self.log_activity("📖 Help shown")
            return

        # ── Intercept GUI-internal clear commands — never send to the agent ──
        cmd_lower = command.strip().lower()
        if cmd_lower in {"clear history", "clear command history", "delete history",
                         "reset history", "wipe history"}:
            self.clear_history()
            self.input_box.clear()
            return
        if cmd_lower in {"clear logs", "clear log", "clear activity", "clear logger",
                         "reset logs", "wipe logs"}:
            self.clear_logs()
            self.input_box.clear()
            return
        if cmd_lower in {"clear output", "clear chat", "clear screen", "cls", "clear"}:
            self.output_text.clear()
            self.output_text.append("🧹 Output cleared.\n")
            self.input_box.clear()
            self.log_activity("🧹 Output cleared")
            return

        # Check if command needs confirmation
        if self.needs_confirmation(command):
            if not self.show_confirmation_dialog(
                "⚠️  Destructive Operation",
                f"This command may delete or remove files:\n\n\"{command}\"\n\nProceed?"
            ):
                self.output_text.append("❌ Operation cancelled by user\n")
                self.log_activity(f"🚫 Command cancelled: {command}")
                self.input_box.clear()
                return
        
        # Add to history
        self.command_history.insert(0, command)
        self.command_history_index = -1
        self.update_history_display()
        
        # Display command in output and a separator
        self.output_text.append(f"\n{'='*60}")
        self.output_text.append(f"🎤 You: {command}")
        self.output_text.append(f"{'='*60}\n")
        
        # Log activity
        self.log_activity(f"📤 Command sent: {command}")
        
        # Clear input
        self.input_box.clear()
        self.input_box.setFocus()
        
        # Execute in background thread
        # Confirmations from execution_engine are routed to the GUI via signal/event
        self.execution_thread = CommandExecutionThread(self.agent, command)
        self.execution_thread.output_received.connect(self.on_execution_output)
        self.execution_thread.execution_completed.connect(self.on_execution_complete)
        self.execution_thread.execution_failed.connect(self.on_execution_failed)
        self.execution_thread.confirmation_requested.connect(self.on_confirmation_requested)
        self.execution_thread.start()
    
    def on_confirmation_requested(self, prompt: str):
        """
        Slot called in the main thread when execution_engine needs a y/n answer.
        Shows the confirmation dialog, then unblocks the worker thread.
        """
        # Show the ✓/✗ dialog on the main thread
        confirmed = self.show_confirmation_dialog(
            "⚠️  Task Confirmation Required",
            prompt if prompt else "This task requires your confirmation. Proceed?"
        )
        # Feed the answer back to the worker thread
        thread = self.execution_thread
        if thread:
            thread._confirm_result = confirmed
            thread._confirm_event.set()
        
        status = "✓ Confirmed" if confirmed else "✗ Declined"
        self.log_activity(f"🔔 Confirmation dialog: {status}")
        if not confirmed:
            self.output_text.append("❌ Task cancelled by user\n")

    def on_execution_output(self, line: str):
        """Display a single output line from execution in real-time"""
        self.output_text.append(line)
        # Auto-scroll to bottom
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_execution_complete(self, result: dict):
        """Handle command execution completion"""
        try:
            if result.get("status") == "error":
                self.output_text.append(f"\n❌ Error: {result.get('message', 'Unknown error')}\n")
                self.log_activity(f"❌ Execution failed: {result.get('message')}")
            else:
                summary = result.get("summary", result.get("execution_result", {}))
                completed = summary.get('completed', 0)
                total = summary.get('total_tasks', 0)
                failed = summary.get('failed', 0)
                self.output_text.append(f"\n{'─'*60}")
                self.output_text.append(f"✅ Done — {completed}/{total} tasks completed" +
                                        (f"  ⚠️ {failed} failed" if failed else ""))
                self.log_activity(f"✅ Done: {completed}/{total} tasks")
        except Exception as e:
            self.output_text.append(f"❌ Error processing result: {str(e)}")
            self.log_activity(f"❌ Error: {str(e)}")
    
    def on_execution_failed(self, error: str):
        """Handle command execution failure"""
        self.output_text.append(f"\n❌ Execution Failed: {error}\n")
        self.log_activity(f"❌ Execution error: {error}")
    
    def toggle_voice_input(self):
        """Toggle voice input on/off"""
        # Lazy-init voice listener if it wasn't initialized at startup
        if not self.voice_listener:
            try:
                from voice.voice_listener import VoiceListener
                self.voice_listener = VoiceListener()
                self.output_text.append("🎤 Voice listener initialized\n")
                self.log_activity("🎤 Voice listener initialized on demand")
            except ImportError:
                self.output_text.append(
                    "❌ Voice not available — install: pip install sounddevice numpy scipy\n"
                )
                return
            except Exception as e:
                self.output_text.append(f"❌ Could not start voice listener: {e}\n")
                return

        if self.is_listening:
            return  # Already listening

        self.is_listening = True
        self.listening_label.setText("🔴 LISTENING...")
        self.output_text.append("🎤 Listening... speak now, auto-stops on silence\n")
        self.voice_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: 2px solid #ff0000;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        self.voice_button.setEnabled(False)

        self.log_activity("🎤 Voice input started")

        # Start voice listening in background thread
        self.voice_thread = VoiceListenerThread(self.voice_listener)
        self.voice_thread.text_received.connect(self.on_voice_text_received)
        self.voice_thread.listening_stopped.connect(self.on_voice_listening_stopped)
        self.voice_thread.error_occurred.connect(self.on_voice_error)
        self.voice_thread.start()
    
    def on_voice_text_received(self, text: str):
        """Handle voice transcription result"""
        self.input_box.setText(text)
        self.output_text.append(f"🎤 Transcribed: {text}\n")
        self.log_activity(f"🎤 Voice transcribed: {text}")
    
    def on_voice_listening_stopped(self):
        """Handle voice listening stopped"""
        self.is_listening = False
        self.listening_label.setText("")
        self.voice_button.setEnabled(True)
        self.voice_button.setStyleSheet("""
            QPushButton {
                background-color: #44475a;
                color: white;
                border: 1px solid #667;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QPushButton:pressed {
                background-color: #00d4ff;
                color: black;
            }
        """)
        self.log_activity("🎤 Voice input stopped")
    
    def on_voice_error(self, error: str):
        """Handle voice input error"""
        self.output_text.append(f"❌ Voice Error: {error}\n")
        self.log_activity(f"❌ Voice error: {error}")
        self.on_voice_listening_stopped()
    
    # ─────────────────────────────────────────────────────────────────
    #  Built-in help renderer — no LLM involved
    # ─────────────────────────────────────────────────────────────────
    def _show_help_in_gui(self):
        """Render the full JARVIS command reference in the output panel."""
        try:
            from tools.help_commands import HELP_COMMANDS
        except ImportError:
            self.output_text.append("❌ help_commands module not found.\n")
            return

        out = self.output_text  # shorthand

        out.append("")
        out.append("╔" + "═" * 62 + "╗")
        out.append("║" + "  🤖  JARVIS — COMMAND REFERENCE".center(62) + "║")
        out.append("╚" + "═" * 62 + "╝")

        for category, details in HELP_COMMANDS.items():
            out.append("")
            out.append(f"📍 {category}")
            out.append("─" * 64)

            all_cmds = []
            all_cmds += details.get("commands", [])
            all_cmds += details.get("web_commands", [])
            all_cmds += details.get("health_commands", [])

            for cmd in all_cmds:
                out.append(f"  • {cmd['command']:<38}  {cmd['description']}")
                out.append(f"      └─ e.g.: {cmd['example']}")

        out.append("")
        out.append("═" * 64)
        out.append("💡 Tips:")
        out.append("  • Use natural language — JARVIS understands variations")
        out.append("  • Parameters are shown in [brackets]")
        out.append("  • Type 'exit' to close JARVIS")
        out.append("  • Type 'help' anytime to see this list again")
        out.append("═" * 64)
        out.append("")

        # Switch focus to chat tab so the user sees the output
        self.tabs.setCurrentIndex(0)

        # Auto-scroll to bottom
        sb = out.verticalScrollBar()
        sb.setValue(sb.maximum())

    def log_activity(self, message: str):
        """Log activity to logger tab"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_entries.append(log_entry)
        self.logger_text.append(log_entry)
        
        # Scroll to bottom
        cursor = self.logger_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.logger_text.setTextCursor(cursor)
    
    def update_history_display(self):
        """Update history tab with numbered commands and stats header."""
        total = len(self.command_history)
        header = (
            f"{'═'*50}\n"
            f"  📜 Session Commands — {total} total\n"
            f"{'═'*50}\n"
        )
        rows = ""
        for i, cmd in enumerate(self.command_history[:50], 1):  # Show last 50
            rows += f"  {i:>2}. {cmd}\n"
        if not rows:
            rows = "  (no commands yet)\n"
        self.history_text.setText(header + rows)
    
    def load_history(self):
        """Load command history from agent memory (graceful fallback)."""
        try:
            loader = getattr(self.agent, 'get_execution_history', None)
            if callable(loader):
                history = loader(limit=10)
                for entry in history:
                    cmd = entry.get('user_input', '') or entry.get('command', '')
                    if cmd:
                        self.command_history.append(cmd)
            self.update_history_display()
            self.log_activity("📜 History loaded")
        except Exception as e:
            self.log_activity(f"⚠️  Could not load history: {str(e)}")
    
    def clear_history(self):
        """Clear command history"""
        if self.show_confirmation_dialog("Clear History", "Are you sure you want to delete all command history?"):
            self.command_history.clear()
            self.update_history_display()
            self.log_activity("🗑️  History cleared")
            self.output_text.append("✅ History cleared\n")
    
    def clear_logs(self):
        """Clear activity logs"""
        if self.show_confirmation_dialog("Clear Logs", "Are you sure you want to delete all activity logs?"):
            self.log_entries.clear()
            self.logger_text.clear()
            self.log_activity("🗑️  Logs cleared")
    
    def closeEvent(self, event):
        """Handle chat card close - restore stdout"""
        try:
            if self.stdout_redirector:
                sys.stdout = self.stdout_redirector.original_stdout
        except:
            pass
        event.accept()
    
    def apply_stylesheet(self):
        """Apply overall stylesheet"""
        self.setStyleSheet("""
            QDialog {
                background-color: #0f0f1e;
            }
            QTabWidget {
                background-color: #0f0f1e;
            }
            QTabBar::tab {
                background-color: #2d2d3d;
                color: #ffffff;
                padding: 8px 20px;
                border: 1px solid #44475a;
            }
            QTabBar::tab:selected {
                background-color: #00d4ff;
                color: black;
            }
            QLabel {
                color: #ffffff;
            }
        """)

