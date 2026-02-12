# Phase 1 — LLM Command Core

## Objective
Enable Jarvis to interpret natural language commands using Gemini.

## Implemented

- Gemini API wrapper
- Prompt template system
- Command → JSON parsing
- Modular LLM layer

## Example

Input:
"Open Chrome"

Output:
{
  "intent": "open_app",
  "action": "open_chrome",
  "parameters": {}
}

## Outcome
Jarvis now understands structured commands and is ready for routing.
