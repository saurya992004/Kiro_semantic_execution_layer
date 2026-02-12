import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

class GeminiClient:

    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY1"))

    def generate(self, prompt: str) -> str:
        """
        Sends prompt to Gemini and returns text response.
        """

        response = self.client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
        )

        return response.text
