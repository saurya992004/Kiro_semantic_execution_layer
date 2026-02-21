"""
LLM Client Selector
Change the LLM_PROVIDER below to switch between providers:
  - "gemini" for Google Gemini
  - "groq" for Groq only generates text
"""

LLM_PROVIDER = "groq"  # <-- CHANGE THIS LINE TO SWITCH BETWEEN "gemini" or "groq"

if LLM_PROVIDER == "groq":
    from llm.groq_client import GroqClient
    LLMClient = GroqClient
elif LLM_PROVIDER == "gemini":
    from llm.gemini_client import GeminiClient
    LLMClient = GeminiClient
else:
    raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}. Use 'gemini' or 'groq'")

__all__ = ["LLMClient", "GroqClient", "GeminiClient"]
