# Phase 11: The Troubleshooter (Vision Pipeline)

## Overview

Phase 11 introduces an autonomous vision-based troubleshooting pipeline for Jarvis. Instead of relying purely on system logs, Jarvis can now look at the user's screen, identify errors, and automatically deploy fixes using advanced Vision Language Models (VLMs).

## Core Modules

Located in `troubleshooter/`:

- **screenshot_tool.py**: Captures the current visible screen using the `Pillow` library and encodes it into a Base64 string for API transmission.
- **vision_analyzer.py**: Integrates with the Groq API (using the `llama-4.1-scout-vision-preview` model) to analyze the screenshot, identify the root cause of the issue, and provide a structured JSON response containing explanations and executable fix commands.

- **solution_parser.py**: Safely parses the JSON output from the LLM, handling any stray markdown blocks (e.g., ```json) to extract the command array.
- **auto_fix_engine.py**: The execution engine that runs the parsed commands autonomously via `subprocess`.
  - **Admin Escalation**: If the AI determines a command requires administrative privileges (or if it fails and needs elevation), the engine securely prompts the user using native Windows UAC (`ctypes.windll.shell32.ShellExecuteW`).

## Router Integration

The pipeline is invoked through "Phase 2" intent router (`router/intent_router.py`) via the `troubleshoot_screen` intent.

## Environment Setup

Ensure your `.env` file contains the Groq API key:

```env
GROQ_API_KEY=your_key_here
```

## How to Test

1. Have an error message visible on your screen.
2. In the Jarvis main loop, submit a natural language prompt that maps to the `troubleshoot_screen` intent (assuming your `prompts/` and Gemini logic maps commands like "Jarvis, what is this error on my screen?" to `{"intent": "troubleshoot_screen"}`).
3. Jarvis will capture the screen, analyze it, print the explanation, and execute the automated fix commands.
