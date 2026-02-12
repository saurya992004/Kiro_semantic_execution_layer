def load_prompt(path: str) -> str:
    """
    Loads a prompt file.
    """

    with open(path, "r", encoding="utf-8") as file:
        return file.read()
