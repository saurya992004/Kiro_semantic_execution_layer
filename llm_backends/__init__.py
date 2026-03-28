"""
LLM Backend Implementations

Production-ready implementations of the LLMBackend protocol.

Exports:
- GroqBackend: Groq API integration
- GeminiBackend: Google Gemini API integration
- ClaudeBackend: Anthropic Claude API integration

Each backend can be plugged into LLMRouter - no core changes needed!
"""

from .groq_backend import GroqBackend
from .gemini_backend import GeminiBackend
from .claude_backend import ClaudeBackend

__all__ = ["GroqBackend", "GeminiBackend", "ClaudeBackend"]
