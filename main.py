from llm.groq_client import GroqClient
from utils.prompt_loader import load_prompt
from utils.json_parser import extract_json
from router.intent_router import route_intent


def build_prompt(user_command: str) -> str:

    system_prompt = load_prompt("prompts/system_prompt.txt")
    command_prompt = load_prompt("prompts/command_prompt.txt")

    command_prompt = command_prompt.replace(
        "{command}", user_command
    )

    full_prompt = system_prompt + "\n\n" + command_prompt

    return full_prompt


def main():

    groq = GroqClient()

    while True:

        user_command = input("Jarvis > ")

        if user_command.lower() == "exit":
            break

        prompt = build_prompt(user_command)

        response = groq.generate(prompt)

        parsed = extract_json(response)

        if not parsed:
            print("Failed to parse command.\n")
            continue

        print("\nParsed Command:")
        print(parsed)
        print()

        # 🔥 Phase 2 Execution Hook
        route_intent(parsed)


if __name__ == "__main__":
    main()
