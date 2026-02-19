import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class GeminiClient:
    """Groq-based LLM client with GeminiClient interface for compatibility."""

    def __init__(self):
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    def generate(self, prompt: str) -> str:
        """
        Sends prompt to Groq and returns text response.
        """
        chat_completion = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )

        return chat_completion.choices[0].message.content
