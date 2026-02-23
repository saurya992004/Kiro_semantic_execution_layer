# 🤖 JARVIS — Intelligent OS Automation Agent

> **Control your entire desktop intelligently, safely, and naturally.**

JARVIS is an advanced AI-powered operating system automation framework designed to understand natural language commands and execute complex system tasks with intelligent planning, safety validation, and automatic recovery mechanisms.

Built as a modular, extensible agent system, JARVIS combines the power of large language models with local system integration to provide truly autonomous desktop assistance.

---

## ✨ Key Features

### 🎯 **Intelligent Task Planning**
- Breaks down complex user requests into executable subtasks
- Learns from execution history and past patterns
- Adaptive planning based on system context

### 🛡️ **Safety-First Architecture**
- Command validation before execution
- Risk assessment and confirmation for critical actions
- Automatic rollback on failures
- Comprehensive action logging

### 💾 **Smart File Management**
- Intelligent file organization by type and category
- Duplicate file detection and removal
- Large file identification and analysis
- Folder structure optimization

### 🔍 **System Diagnostics & Maintenance**
- Real-time CPU, RAM, and disk monitoring
- System health checks and alerts
- Cleanup scanning for old and temporary files
- Performance analysis and recommendations

### 👁️ **Vision & OCR Integration**
- Screenshot analysis using Google Gemini
- Optical Character Recognition (OCR)
- Visual problem detection and troubleshooting
- Screenshot-based task automation

### 🎤 **Natural Language Interface**
- Conversational command understanding
- Multi-turn conversation support
- Context-aware request interpretation
- User preference learning

### 📚 **Memory & Learning**
- Persistent execution history
- Context storage and retrieval
- Preference management
- Task outcome tracking

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│         User Input (Natural Language) text/voice        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│    Master Agent - Central Orchestrator                  │
│    - Intent Extraction & Goal Definition                │
│    - Multi-agent coordination                           │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐      ┌────────▼──────────┐
│ Intent Router  │      │ Task Planner       │
│ - Intent       │      │ - Breakdown tasks  │
│   detection    │      │ - Prioritization   │
│ - Action       │      │ - Optimization     │
│   mapping      │      └────────┬──────────┘
└───────┬────────┘               │
        │                        │
        └────────────┬───────────┘
                     │
        ┌────────────▼────────────┐
        │  Execution Engine       │
        │  - Safe execution       │
        │  - Error handling       │
        │  - Logging              │
        └────────────┬────────────┘
                     │
      ┌──────────────┴──────────────┐
      │                             │
┌─────▼────────┐          ┌────────▼──────┐
│ Tool Modules │          │ LLM Services  │
│ - File Mgmt  │          │ - Gemini      │
│ - System     │          │ - Groq        │
│ - Diagnosis  │          └───────────────┘
│ - Web        │
└──────────────┘
```

---

## 🤖 Core Agents

### **Master Agent**
Central orchestrator that coordinates all system operations:
- Receives and interprets user requests
- Manages task planning and execution flow
- Maintains memory and context
- Provides feedback and reporting
- **Location:** `agent/master_agent.py`

### **Task Planner**
Intelligent task decomposition and planning:
- Converts goals into executable task sequences
- Handles dependencies between tasks
- Estimates execution time and resource requirements
- Adapts plans based on execution feedback
- **Location:** `agent/task_planner.py`

### **Execution Engine**
Manages safe task execution:
- Pre-execution validation and safety checks
- Handles task execution with error recovery
- Logs all operations for audit trails
- Implements automatic rollback on failures
- **Location:** `agent/execution_engine.py`

### **Memory Manager**
Maintains system state and learning:
- Execution history tracking
- Context and preference storage
- Performance metrics recording
- Learning from past executions
- **Location:** `agent/memory_manager.py`

---

## 📦 Module Overview

### **LLM Services** (`llm/`)
Multi-LLM support for flexible AI backend:
- **Gemini Client:** Google's advanced language model for vision and text
- **Groq Client:** High-speed inference for real-time responses

### **File Manager** (`file_manager/`)
Comprehensive file and folder management:
- `manager.py` - Main orchestrator
- `file_organizer.py` - Auto-organize files by type
- `duplicate_detector.py` - Find and remove duplicates
- `large_file_scanner.py` - Identify large files
- `folder_finder.py` - Smart folder discovery
- `llm_organizer.py` - AI-powered categorization

### **Tools** (`tools/`)
System integration and action execution:
- `file_tools.py` - File operations
- `system_tools.py` - System control (shutdown, restart, etc.)
- `system_config.py` - System configuration management
- `diagnostics_tools.py` - Health checks and monitoring
- `app_tools.py` - Application launching
- `web_tools.py` - Web searching and browsing
- `help_commands.py` - User guidance

### **Troubleshooting** (`troubleshooter/`)
Advanced problem diagnosis and resolution:
- `vision_analyzer.py` - Visual problem analysis
- `screenshot_tool.py` - Screenshot capture and analysis
- `solution_parser.py` - Parse and format solutions
- `auto_fix_engine.py` - Automated fixing mechanisms

### **Vision** (`vision/`)
Computer vision capabilities:
- `vision_engine.py` - Image analysis and OCR
- Screenshot-based automation support

### **Personalization** (`personalisation/`)
User preference and behavior learning:
- `personalisation_tools.py` - Customization features
- User profile management

### **Router** (`router/`)
Intent-based command routing:
- `intent_router.py` - Maps intents to actions
- Multi-intent support for complex requests

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.8+**
- **Windows 10/11** (or Linux/macOS with adaptation)
- **API Keys:** Google Gemini, Groq (optional but recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/jarvis.git
   cd jarvis
   ```

2. **Create a Python virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/macOS
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file in root directory
   GOOGLE_API_KEY=your_gemini_api_key
   GROQ_API_KEY=your_groq_api_key
   ```

5. **Run JARVIS**
   ```bash
   python main.py
   ```

---

## 💻 Usage Examples

### Basic Commands

```
> organize my downloads
✅ Analyzed 245 files
✅ Created 8 category folders
✅ Moved 187 files successfully

> find large files on my desktop
📊 Scanning: C:\Users\YourName\Desktop
✅ Found 12 files over 100MB
  • video_backup.mp4 (2.3GB)
  • old_project.zip (890MB)

> what's my system health
🏥 System Health Check
  CPU Usage: 34%
  RAM Usage: 62% (8.9GB/16GB)
  Disk Usage: 71% (425GB/600GB)
  Status: ✅ HEALTHY

> scan for old files
🗑️  OLD FILES SCAN
Files older than 7 days: 23
Total recoverable space: 2.4GB
Use 'confirm cleanup' to delete

> take a screenshot and analyze it
📸 Captured screenshot
🤖 Analysis:
  - Browser window detected
  - Showing error message
  - Recommended: Check browser console logs
```

### Special Commands

```
help              - Show available commands
history           - View recent executions
stats             - Display execution statistics
status            - Agent system status
clear history     - Reset execution memory
exit              - Shutdown JARVIS
```

---

## ⚙️ Configuration

### System Configuration (`tools/system_config.py`)
Manage system-wide settings:
- LLM model selection
- Execution timeouts
- Safety levels
- Logging verbosity

### Memory Configuration (`agent_memory/`)
- `execution_history.json` - Past execution logs
- `context.json` - Current system context
- `preferences.json` - User preferences
- `plans.json` - Saved task plans

---

## 🛡️ Safety & Security

JARVIS implements multiple layers of protection:

### **Pre-Execution Validation**
- Intent risk assessment
- Command whitelisting/blacklisting
- User confirmation for critical actions

### **Protected Zones**
- System32 directory
- Registry operations  
- Forced process termination
- Mass file deletion

### **Execution Monitoring**
- Real-time operation logging
- Resource usage tracking
- Error detection and handling

### **Rollback Capabilities**
- Pre-execution snapshots
- File restoration on failures
- Process restart mechanisms
- State rollback on user request

---

## 📊 Project Structure

```
jarvis/
├── main.py                      # Entry point
├── requirements.txt             # Dependencies
├── README.md                    # This file
│
├── agent/                       # Core agent system
│   ├── master_agent.py         # Central orchestrator
│   ├── task_planner.py         # Task decomposition
│   ├── execution_engine.py     # Safe execution
│   ├── memory_manager.py       # State management
│   └── task.py                 # Task definition
│
├── llm/                         # LLM integrations
│   ├── gemini_client.py        # Google Gemini
│   └── groq_client.py          # Groq API
│
├── file_manager/               # File management suite
│   ├── manager.py              # Main orchestrator
│   ├── file_organizer.py       # Auto-organization
│   ├── duplicate_detector.py   # Deduplication
│   ├── large_file_scanner.py   # Size analysis
│   └── folder_finder.py        # Folder discovery
│
├── tools/                       # System tools
│   ├── file_tools.py           # File operations
│   ├── system_tools.py         # System control
│   ├── diagnostics_tools.py    # Health & monitoring
│   ├── app_tools.py            # App launching
│   ├── web_tools.py            # Web integration
│   └── help_commands.py        # User guidance
│
├── troubleshooter/             # Problem diagnosis
│   ├── vision_analyzer.py      # Image analysis
│   ├── screenshot_tool.py      # Screenshot capture
│   ├── solution_parser.py      # Solution parsing
│   └── auto_fix_engine.py      # Auto-fixing
│
├── vision/                      # Computer vision
│   └── vision_engine.py        # Vision processing
│
├── router/                      # Intent routing
│   └── intent_router.py        # Command routing
│
├── personalisation/             # User customization
│   └── personalisation_tools.py
│
├── agent_memory/               # Persistent storage
│   ├── execution_history.json
│   ├── context.json
│   ├── preferences.json
│   └── plans.json
│
└── utils/                       # Utility functions
    ├── prompt_loader.py        # Prompt management
    ├── json_parser.py          # JSON utilities
    ├── system_monitor.py       # Monitoring
    └── prompt_loader.py        # Prompt loading
```

---

## 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM** | Google Gemini, Groq | Natural language understanding & generation |
| **Vision** | EasyOCR, Pillow | Image analysis and OCR |
| **System Monitoring** | psutil | CPU, RAM, Disk metrics |
| **Screenshots** | mss | Screen capture |
| **GUI** | CustomTkinter | Desktop interface (optional) |
| **HTTP** | requests | Web operations |
| **Config** | python-dotenv | Environment management |

---

## 📈 Performance Metrics

Monitor JARVIS performance:

```python
# Execution statistics
stats = agent.get_execution_stats()
print(f"Success Rate: {stats['success_rate']:.1f}%")
print(f"Avg Task Time: {stats['avg_execution_time']}s")
print(f"Total Executions: {stats['total_executions']}")

# Agent status
status = agent.get_agent_status()
print(f"Memory Entries: {status['memory_entries']}")
print(f"History Count: {status['execution_history_count']}")
```

---

## 🎨 Enhancement Areas

Potential improvements and future phases:

- [ ] Multi-language support
- [ ] Real-time collaboration features
- [ ] Custom automation workflow builder
- [ ] Advanced scheduling capabilities
- [ ] Database integration for complex queries
- [ ] Mobile app companion
- [ ] Cloud sync for cross-device support
- [ ] Advanced ML-based pattern recognition
- [ ] Plugin system for third-party integrations

---

## 📝 License

This project is provided as-is for educational and personal use. Ensure compliance with your operating system's terms of service when using automation features.

---

## 🤝 Contributing

We welcome contributions! Please feel free to submit issues, feature requests, and pull requests.

---

## 📞 Support

For issues, questions, or feature requests, please open an issue on the project repository.

---

**Built with ❤️ as an advanced AI desktop automation framework.**

Last Updated: February 2026
