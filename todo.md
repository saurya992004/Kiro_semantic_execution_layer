# Jarvis AI — Team Build Structure & Phase TODOs

---

# 📁 Project Folder Structure

```
jarvis/
│
├── main.py                     # Entry point (command loop)
│
├── llm/
│   └── gemini_client.py       # Gemini API wrapper
│
├── prompts/
│   ├── system_prompt.txt      # Master system behavior
│   ├── command_prompt.txt     # Command → JSON prompt
│   └── planning_prompt.txt    # (Future — Phase 7)
│
├── router/
│   ├── intent_router.py       # Master intent dispatcher
│   ├── settings_router.py    # (Future split if needed)
│   └── agent_router.py       # (Future — multi-agent)
│
├── tools/
│   ├── app_tools.py           # Open / close apps
│   ├── web_tools.py           # Browser + search
│   ├── power_tools.py         # Shutdown / restart
│   ├── system_tools.py        # Deep system control
│   └── file_tools.py          # File intelligence engine
│
├── utils/
│   ├── prompt_loader.py       # Prompt file loader
│   ├── json_parser.py         # JSON extractor
│   └── logger.py              # (Future logging layer)
│
├── config/
│   └── settings.py            # Paths, defaults, keys
│
├── README_PHASES/
│   ├── PHASE_1.md
│   ├── PHASE_2.md
│   ├── PHASE_3.md
│   └── PHASE_4.md
│
└── requirements.txt
```

---

# 🧭 Phase Ownership & TODOs

Each teammate can pick a phase or module.

---

# 🥇 Phase 1 — LLM Command Core ✅

## Owner

LLM / Backend Engineer

## Implemented

* Gemini client wrapper
* Prompt template system
* Command → JSON parsing
* JSON extractor

## Files

```
llm/gemini_client.py
prompts/system_prompt.txt
prompts/command_prompt.txt
utils/prompt_loader.py
utils/json_parser.py
```

## Future TODOs

* Add JSON schema validation
* Add retry on malformed output
* Add streaming responses

---

# 🥈 Phase 2 — Intent Router + Execution ✅

## Owner

Backend / Systems Engineer

## Implemented

* Intent router
* Tool dispatcher
* App launcher
* Web search
* Shutdown control

## Files

```
router/intent_router.py
tools/app_tools.py
tools/web_tools.py
tools/power_tools.py
```

## TODOs

* Add app path auto-detection
* Add multi-command routing
* Add error handling logs

---

# 🥉 Phase 3 — System Control Layer (In Progress)

## Owner

OS / Automation Engineer

## Features

* Shutdown / Restart / Sleep / Lock
* Process killer
* Temp cleanup
* Recycle bin control

## Files

```
tools/system_tools.py
```

## TODOs

* Add confirmation layer
* Add startup app manager
* Add service control
* Add battery / power profiles

---

# 🏅 Phase 4 — File Intelligence Engine (Active)

## Owner

Productivity Automation Engineer

## Features

* Organize downloads
* Duplicate remover
* Large file detector
* Project structure generator

## Files

```
tools/file_tools.py
```

## TODOs

* Add recursive folder scan
* Add file tagging system
* Add AI file categorization
* Add restore duplicates option

---

# 🌐 Phase 5 — Internet + Installer Agent

## Owner

DevOps / Automation Engineer

## Planned Features

* Download software
* Silent installations
* Dev environment setup
* Dependency installers

## Planned Files

```
tools/installer_tools.py
utils/downloader.py
```

## TODOs

* Package manager integration
* Git repo cloning
* Auto PATH setup

---

# 🧠 Phase 6 — Diagnostics & Self-Healing

## Owner

System Monitoring Engineer

## Planned Features

* CPU / RAM monitoring
* Disk usage alerts
* Startup optimization
* Temp auto-clean

## Planned Files

```
tools/diagnostics_tools.py
utils/system_monitor.py
```

---

# 🤖 Phase 7 — Planner / Agent Layer

## Owner

AI / Agent Systems Engineer

## Planned Features

* Multi-step planning
* Goal decomposition
* Tool chaining

## Planned Files

```
agent/planner.py
prompts/planning_prompt.txt
```

---

# 🖥️ Phase 8 — Voice + Overlay Assistant

## Owner

Frontend / Interaction Engineer

## Planned Features

* Wake word
* Speech-to-text
* Text-to-speech
* Floating UI

## Planned Stack

* Whisper / Vosk
* Coqui / ElevenLabs
* Electron / PyQt

---

# 👁️ Phase 9 — Vision Intelligence

## Owner

Computer Vision Engineer

## Planned Features

* Screenshot analysis
* UI automation
* Error detection

---

# 🧩 Phase 10 — Multi-Agent Ecosystem

## Owner

Architecture Lead

## Agents

* File agent
* Installer agent
* Diagnostics agent
* Vision agent

---

# 🛠️ Team Dev Rules

1. Never hardcode prompts inside Python.
2. Every tool must live in `/tools`.
3. Every phase must have a README.
4. Router handles execution — not prompts.
5. Tools must be modular & reusable.

---

# 🚀 Current Active Phases

```
Phase 3 → System Control (partial)
Phase 4 → File Intelligence (building)
```

---

# 📌 Next Milestone

Complete Phase 4 core features → move to Installer Agent.

---

**Project Codename:** Jarvis OS Agent Framework
**LLM Layer:** Gemini (Flash)
