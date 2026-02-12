import webbrowser


def search_web(query: str):

    if not query:
        print("No search query.")
        return

    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)

    print(f"Searching for {query}...")
