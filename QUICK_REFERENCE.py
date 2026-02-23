"""
JARVIS GUI - Quick Reference Card
==================================
Commands and keyboard shortcuts for JARVIS GUI
"""

# ============================================================
# LAUNCH COMMANDS
# ============================================================

__doc__ = """
🚀 LAUNCHING JARVIS

GUI Mode (Default):
    python run_jarvis.py

GUI with Voice:
    python run_jarvis.py --gui-voice

Terminal Mode:
    python run_jarvis.py --cli

Terminal with Voice:
    python run_jarvis.py --voice

Validate Setup:
    .venv\Scripts\python.exe test_gui_startup.py

# ============================================================
# GUI INTERFACE ELEMENTS
# ============================================================

📍 FLOATING WIDGET
  - Location: Bottom-right of screen
  - Always on top of other windows
  - Animations: Idle, Happy, Thinking, Listening, Speaking
  - Interactions:
    * Single-click + drag: Move widget
    * Double-click: Open command interface

📊 COMMAND INTERFACE (Card)
  Tabs:
  - 💬 Chat: Main command input/output
  - 📜 History: Past 20 commands
  - 📋 Logger: Activity log with timestamps

# ============================================================
# CHAT TAB CONTROLS
# ============================================================

  Input Box:
    - Type your command
    - Or paste commands
    - Press Enter to send
    - Arrow keys: Navigate history

  🎤 Voice Button:
    - Click to start voice input
    - Shows "🔴 LISTENING..." when active
    - Say your command clearly
    - Transcription appears in input box

  📤 Send Button:
    - Execute the command
    - Same as pressing Enter
    - Shows confirmation

  📤 Output Area:
    - Shows command results
    - Task execution status
    - Error messages
    - Processing indicators

# ============================================================
# KEYBOARD SHORTCUTS (Chat Tab)
# ============================================================

  Enter:              Send command
  Ctrl+A:             Select all in input
  Ctrl+C:             Copy from output
  Ctrl+V:             Paste into input
  Up/Down Arrow:      Navigate input history
  Tab:                Switch to next tab
  Shift+Tab:          Switch to previous tab
  Ctrl+L:             Clear input box
  Ctrl+E:             Clear output box

# ============================================================
# HISTORY TAB CONTROLS
# ============================================================

  View:
    - Shows last 20 executed commands
    - Most recent first
    - Numbered for reference

  Actions:
    - Click "🗑️  Clear History" to delete all
    - Confirm before clearing
    - Clears command history only (not logs)

# ============================================================
# LOGGER TAB CONTROLS
# ============================================================

  Display:
    - Real-time activity log
    - Format: [TIMESTAMP] MESSAGE
    - Includes all events:
      * Commands sent
      * Voice input started/stopped
      * Execution completed
      * Errors encountered
      * Logs cleared

  Actions:
    - Click "🗑️  Clear Logs" to delete
    - Confirm before clearing
    - Clears display only (logs still in memory)

# ============================================================
# VOICE INPUT WORKFLOW
# ============================================================

  1. Click 🎤 button
  2. Wait for "🔴 LISTENING..." indicator
  3. Speak your command (e.g., "open chrome")
  4. Listen indicator turns OFF when done
  5. Transcribed text appears in input box
  6. Review transcription
  7. Edit if needed (optional)
  8. Press Enter or click Send to execute

  Voice Tips:
    - Speak clearly and at normal pace
    - Use natural language
    - Wait for "listening stopped" before speaking
    - Max 30 seconds per command

# ============================================================
# EXAMPLE COMMANDS
# ============================================================

  System Control:
    - "lock screen"
    - "sleep"
    - "open chrome"
    - "kill process notepad"

  Analysis:
    - "check disk usage"
    - "check system health"
    - "analyze disk"
    - "find large files"

  File Management:
    - "organize files by type"
    - "find duplicate files"
    - "clean temp files"
    - "empty recycle bin"

  Diagnostics:
    - "check cpu usage"
    - "check ram"
    - "full health check"
    - "scan cleanup files"

# ============================================================
# COLOR SCHEME
# ============================================================

  UI Colors:
    - Dark Background: #0f0f1e (very dark blue)
    - Primary: #00d4ff (bright cyan)
    - Success: #00ff88 (neon green)
    - Warning: #ffff00 (yellow)
    - Error: #ff6b6b (red)
    - Text: #ffffff (white)

  Status Indicators:
    - ✅ Success / Complete
    - ❌ Error / Failed
    - ⏳ Processing
    - 🔴 Listening (voice)
    - ⚠️  Warning
    - 📝 Logged

# ============================================================
# TROUBLESHOOTING
# ============================================================

  Widget Not Showing:
    - Check display system
    - Try --cli mode
    - Review jarvis_gui.log

  Voice Not Working:
    - Check microphone is connected
    - Verify GROQ_API_KEY in .env
    - Run: test_gui_startup.py
    - Check Logger tab for errors

  Commands Not Executing:
    - Check output area for errors
    - Review Logger tab
    - Try simpler command first
    - Check agent connection

  Slow Performance:
    - Close other applications
    - Check system resources
    - Review logs for bottlenecks
    - Restart JARVIS if needed

# ============================================================
# SAFETY NOTES
# ============================================================

  ✅ Protected:
    - Shutdown/restart disabled
    - All operations logged
    - Confirmation for destructive ops
    - Voice input reviewable before execution

  ⚠️  Always:
    - Review commands before executing
    - Check logs for errors
    - Use history to learn patterns
    - Monitor Logger tab during operations

# ============================================================
# FILE LOCATIONS
# ============================================================

  Logs:
    - jarvis_gui.log (GUI logs)
    - jarvis.log (Agent logs)
    - agent_memory/execution_history.json

  Configuration:
    - .env (API keys)
    - agent_memory/ (Agent state)
    - prompts/ (System prompts)

# ============================================================
# SUPPORT
# ============================================================

  For help:
    - Type "help" in chat
    - Check UI README: ui/README.md
    - Review logs for errors
    - Check agent logs

"""

if __name__ == "__main__":
    print(__doc__)
