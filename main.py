from llm.gemini_client import GeminiClient
from utils.prompt_loader import load_prompt


def build_prompt(user_command: str) -> str:

    system_prompt = load_prompt("prompts/system_prompt.txt")
    command_prompt = load_prompt("prompts/command_prompt.txt")

    command_prompt = command_prompt.replace(
        "{command}", user_command
    )

    full_prompt = system_prompt + "\n\n" + command_prompt

    return full_prompt


def main():

    gemini = GeminiClient()

    while True:

        user_command = input("Jarvis > ")

        if user_command.lower() == "exit":
            break

        prompt = build_prompt(user_command)

        response = gemini.generate(prompt)

        print("\nParsed Command:")
        print(response)
        print()


if __name__ == "__main__":
    main()
