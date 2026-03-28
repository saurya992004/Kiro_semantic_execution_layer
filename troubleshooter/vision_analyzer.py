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

    def plan_fix_from_text(self, error_text: str) -> str:
        prompt = f"""You are an autonomous code-fixing agent on Windows. Analyze this error and generate PowerShell commands to fix it.

ERROR CONTEXT:
{error_text}

RULES:
- For CODE ERRORS (NameError, SyntaxError, TypeError, typos like 'rint' instead of 'print'):
  * If the exact file path is missing, use PowerShell to search for the broken code dynamically.
  * Generate a robust PowerShell command to find the specific file containing the broken code, and then edit it. Search from the Desktop to ensure you find it. ALWAYS use the actual filename if you know it:
    $file = (Get-ChildItem -Path $env:USERPROFILE/Desktop -Recurse -Filter 'THE_ACTUAL_FILENAME.py' -File -ErrorAction SilentlyContinue | Select-String -Pattern 'WRONG_CODE' | Select-Object -First 1).Path; if ($file) {{ (Get-Content $file) -replace 'WRONG_CODE','CORRECT_CODE' | Set-Content $file }}
  * Example: fix 'rint' to 'print' in 'python_test.py':
    $f = (Get-ChildItem -Path $env:USERPROFILE/Desktop -Recurse -Filter 'python_test.py' -File -ErrorAction SilentlyContinue | Select-String -Pattern 'rint\\(' | Select-Object -First 1).Path; if ($f) {{ (Get-Content $f) -replace 'rint\\(','print(' | Set-Content $f }}

- For IMPORT ERRORS: pip install the_missing_package
- For SYSTEM ERRORS: appropriate system command

IMPORTANT: You are writing a JSON string. You MUST escape all backslashes! Use `\\(` instead of `\(`.

Output ONLY valid JSON, no markdown:
{{
  "explanation": "brief description of error and fix",
  "commands": [
    {{"command": "powershell command here (make sure to escape backslashes!)", "requires_admin": false}}
  ]
}}"""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a JSON-only API. You output ONLY valid JSON objects, never markdown, never explanations, never code fences. Just raw JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.05,
                max_tokens=512
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error formulating fix with Groq API: {e}")
            return None
