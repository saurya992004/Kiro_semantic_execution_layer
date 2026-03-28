"""
Enhanced Web Tools for Kiro OS
================================
Web search with result fetching and browser opening.
"""

import webbrowser
import urllib.parse


def search_web(query: str):
    """Open a web search in the default browser."""
    if not query:
        print("No search query.")
        return

    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    webbrowser.open(url)
    print(f"🔍 Searching for: {query}")


def open_url(url: str):
    """Open a specific URL in the default browser."""
    if not url:
        print("No URL specified.")
        return
    
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    webbrowser.open(url)
    print(f"🌐 Opening: {url}")


def search_youtube(query: str):
    """Search YouTube."""
    if not query:
        print("No search query.")
        return
    
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    webbrowser.open(url)
    print(f"📺 Searching YouTube: {query}")


def open_github(repo: str = ""):
    """Open GitHub, optionally a specific repo."""
    if repo:
        url = f"https://github.com/{repo}"
    else:
        url = "https://github.com"
    webbrowser.open(url)
    print(f"🐙 Opening GitHub: {url}")
