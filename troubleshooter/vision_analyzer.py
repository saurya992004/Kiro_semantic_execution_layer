import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

class VisionAnalyzer:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("Warning: GROQ_API_KEY not found in environment.")
        self.client = Groq(api_key=api_key)

    def analyze_error(self, base64_image: str) -> str:
        prompt = """
        You are an expert IT Troubleshooter. The user has encountered an error on their screen.
        Analyze this screenshot. Identify the error and provide a specific, well-organized solution.
        You MUST output a JSON response in the exact following format, without any markdown formatting around the JSON block:
        {
          "explanation": "A concise human-readable explanation of the error and the proposed solution.",
          "commands": [
             {
               "command": "powershell command",
               "requires_admin": true_or_false
             }
          ]
        }
        Only include commands that are safe to run autonomously to fix the issue.
        If no commands are needed, leave the commands array empty.
        Output ONLY valid JSON.
        """
        try:
            response = self.client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.2,
                max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error analyzing with Groq API: {e}")
            return None
