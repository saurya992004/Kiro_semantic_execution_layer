# JARVIS GUI System

## Overview

JARVIS now includes a fully-featured GUI frontend with a floating widget, command interface, and voice integration.

## Features

### 🎯 Floating Widget
- Always-on-top animated bot widget
- Drag to reposition
- Double-click to open command interface
- Different animation states (idle, happy, thinking, listening, speaking)

### 💬 Chat Interface
- **Output Display**: Shows command execution results
- **Input Box**: Type or voice commands
- **Voice Button**: Click to input commands via voice
- **Send Button**: Execute commands

### 📜 History Tab
- View past command history
- Quick access to recently executed commands
- Clear history option

### 📋 Logger Tab
- Real-time activity logging
- Timestamps for all events
- Clear logs option
- Track voice input, command execution, and errors

### 🎤 Voice Integration
- Click the 🎤 button to start voice input
- Real-time transcription via Groq Whisper
- Visual "LISTENING..." indicator
- Automatic transcription into input box

### 🎨 Modern Dark Theme
- Sleek cyberpunk aesthetic
- Cyan and neon colors
- Responsive UI with smooth interactions

## Usage

### Launch GUI Mode (Default)
```bash
python run_jarvis.py
```
Starts JARVIS with GUI and floating widget.

### Launch GUI Mode with Voice
```bash
python run_jarvis.py --gui-voice
```
Starts JARVIS GUI with voice input enabled.

### Launch Terminal Mode
```bash
python run_jarvis.py --cli
```
Runs in traditional terminal interface.

### Launch Terminal + Voice Mode
```bash
python run_jarvis.py --voice
```
Runs in terminal with voice commands enabled.

## Interface Guide

### Main Widget
- **Double-click**: Open command interface
- **Single-click + drag**: Reposition widget

### Chat Card
1. **Type command** in input box or use voice input
2. **View output** in the output display area
3. **Check history** in the History tab
4. **Review logs** in the Logger tab
5. **Use voice** by clicking the 🎤 button

### Voice Input
1. Click the 🎤 button (top-right of input box)
2. Wait for "🔴 LISTENING..." indicator
3. Speak your command
4. Speech will be transcribed and placed in input box
5. Edit if needed and press Enter or click Send

## Architecture

### Components

```
ui/
├── __init__.py              # Package initialization
├── app.py                   # Main GUI application
├── chat_card.py            # Chat interface with tabs
└── components/             # UI components (expandable)

widget/
└── widget.py               # Floating bot widget
```

### Thread Safety
- Command execution runs in background thread
- Voice input runs in separate thread
- UI remains responsive during long operations

### Integration with MasterAgent
- GUI communicates with MasterAgent
- Full support for all agent features
- Command history from agent memory
- Task execution with confirmation handling

## Configuration

### Customization
Edit `chat_card.py` to customize:
- Colors and themes (stylesheets)
- Font families and sizes
- Window dimensions
- UI layout

### Voice Settings
Adjust in `voice/voice_listener.py`:
- Sample rate (default: 16000)
- Silence threshold
- Max recording duration
- Speech sensitivity

## Troubleshooting

### Voice Input Not Working
1. Check microphone is connected and working
2. Verify GROQ_API_KEY is set in .env
3. Check logs in Logger tab for errors
4. Try with `--gui-voice` flag

### Widget Not Showing
1. Ensure PyQt5 is installed: `pip install PyQt5`
2. Check if display/windowing system is available
3. Review jarvis_gui.log for errors

### Commands Not Executing
1. Check logger tab for error messages
2. Verify command syntax
3. Review execution details in output area
4. Check agent logs in Logger tab

## Future Enhancements

Planned features:
- Command suggestions/autocomplete
- Drag-and-drop file operations
- Custom themes
- Keyboard shortcuts
- Command bundling/workflows
- Real-time system monitoring dashboard
- File browser integration
- Settings/preferences UI

## Dependencies

- PyQt5: GUI framework
- groq: Voice transcription (optional)
- sounddevice: Microphone input (for voice)
- scipy: Audio processing (for voice)

Install all with:
```bash
pip install PyQt5 groq sounddevice scipy
```

