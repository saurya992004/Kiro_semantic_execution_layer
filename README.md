# 🤖 AURA — AI OS Agent Framework

**Hackathon Project — Team Build**

AURA is a modular AI system assistant that can understand natural language commands and execute real operating system actions.

Unlike traditional voice assistants, AURA is designed as an **extensible OS agent framework** capable of automation, diagnostics, planning, and multi-agent task execution — now enhanced with **built-in safety, validation, and rollback mechanisms**.

---

# 🚀 Vision

> “Control your entire computer like you control ChatGPT — safely.”

AURA converts human commands into structured system actions with verification and recovery layers:

```
User → AI → Intent → Validator → Tool → OS Execution → Fallback Monitor
```

Our goal is to evolve AURA from a command executor into a **fully autonomous yet safety-aware desktop agent**.

---

#  System Architecture

```
User Command
      ↓
Gemini LLM Layer
      ↓
Structured JSON Intent
      ↓
Command Validator 🛡️
      ↓
Intent Router
      ↓
Tool Modules
      ↓
Operating System Actions
      ↓
Fallback & Recovery Engine ↩️
```

---

## 🛡️ Command Validator Layer (NEW)

Before executing any action, AURA verifies intent safety.

### Responsibilities

* Detect destructive commands
* Classify risk level
* Require confirmation for critical actions
* Block unsafe or ambiguous instructions

### Example

```json
{
  "intent": "delete_files",
  "risk_level": "high",
  "requires_confirmation": true
}
```

### Protection Scenarios

* Mass file deletion
* Registry edits
* System32 access
* Forced process kills
* Disk formatting commands

**Impact:** Prevents unintended or malicious system damage.

---

## ↩️ Fallback & Revert System (NEW)

AURA includes a rollback engine to restore system state if something goes wrong — or if the user requests reversal.

### Core Capabilities

* Action logging
* Pre-execution snapshots
* File restore
* Process restart
* Undo automation workflows

---

# 📁 Project Structure

```
AURA/
│
├── main.py
├── llm/
├── prompts/
├── router/
├── tools/
├── utils/
├── config/
├── README_PHASES/
└── requirements.txt
```

Each module is independently extensible for future agents.

---

# 🧭 Hackathon Build Roadmap

---

## 🥇 Phase 1 — LLM Command Core ✅

**Objective**

Enable AURA to understand natural language commands.

**Built**

* Gemini API integration
* Prompt template system
* Command → JSON parsing
* Response validation

**Outcome**

AURA can interpret structured intents like:

```json
{
  "intent": "open_app",
  "action": "open",
  "parameters": {
    "app_name": "Chrome"
  }
}
```

---

## 🥈 Phase 2 — Intent Routing & Execution ✅

**Objective**

Connect AI understanding to real system actions.

**Built**

* Intent router
* Tool dispatcher
* App launcher
* Web search
* Power commands

**Outcome**

AURA executes commands like:

* Open apps
* Search web
* Shutdown system

---

## 🥉 Phase 3 — System Control Layer ⚙️

**Objective**

Give AURA deeper OS authority.

**Implemented**

* Shutdown / Restart / Sleep / Lock
* Process termination
* Temp cleanup
* Recycle bin control

**Impact**

AURA moves from assistant → system controller.

---

## 🏅 Phase 4 — File Intelligence Engine 📂

**Objective**

Automate file management workflows.

**Features**

* Organize Downloads
* Duplicate remover
* Large file detector
* Project structure generator

**Impact**

Real productivity automation.

---

## 🌐 Phase 5 — Internet & Installer Agent (Planned)

**Goal**

Automate system setup.

**Planned**

* Software downloads
* Silent installations
* Dev environment setup

---

## 🧠 Phase 6 — Diagnostics & Self-Healing (Planned)

**Goal**

System monitoring & optimization.

**Planned**

* CPU / RAM tracking
* Disk alerts
* Startup optimization

---

## 🤖 Phase 7 — Planning Agent (Planned)

AURA will decompose goals:

> “Speed up my PC”

Into:

1. Clean temp files
2. Disable startup apps
3. Kill heavy processes

---

## 🖥️ Phase 8 — Voice + Overlay UI (Planned)

* Wake word
* Speech recognition
* Floating assistant

---

## 👁️ Phase 9 — Vision Intelligence (Planned)

* Screenshot analysis
* Error detection
* UI automation

---

## 🧩 Phase 10 — Multi-Agent Ecosystem (Vision)

Specialized agents:

* File agent
* Installer agent
* Diagnostics agent
* Vision agent

---

# 🛠️ Tech Stack

| Layer            | Tech               |
| ---------------- | ------------------ |
| LLM              | Gemini Flash       |
| Backend          | Python             |
| OS Control       | PowerShell, psutil |
| Automation       | shutil, subprocess |
| Vision (planned) | OpenCV             |
| Voice (planned)  | Whisper / Vosk     |

---

# ⚙️ Setup Instructions

```bash
git clone <repo>
cd AURA

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

Add API key in `.env`:

```
GEMINI_API_KEY=your_key_here
```

Run:

```bash
python main.py
```

---

# 🧪 Demo Commands

```
Open Chrome
Search AI news
Shutdown my PC
Organize my downloads
Kill Chrome
Clean temp files
```

---

# 🏆 Hackathon Value Proposition

### Innovation

AI controlling OS via modular agent architecture.

### Technical Depth

* Prompt engineering
* Tool routing
* System automation
* Agent planning roadmap

### Real-World Use

* Productivity automation
* System optimization
* Developer environment setup

---

# 🔮 Future Scope

AURA can evolve into:

* Personal desktop co-pilot
* Developer automation agent
* IT support AI
* Accessibility assistant

---

# 📌 Project Status

```
Phase 1 → Complete
Phase 2 → Complete
Phase 3 → Implemented
Phase 4 → In Progress
```

---

# 🧠 Inspiration

Inspired by the concept of a modular AI operating layer — bridging LLM intelligence with real system control.

---

# 🏁 Closing Statement

AURA is not just an assistant.

It’s the foundation of an **AI-driven operating experience** where computers execute intent, not clicks.
