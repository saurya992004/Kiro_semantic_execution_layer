"""
Enhanced App Tools for Kiro OS
================================
Dynamic app discovery with PATH lookup, registry check, and common paths.
"""

import subprocess
import os
import shutil


# Common Windows application paths (fallback)
COMMON_APP_PATHS = {
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
    "firefox": [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
    ],
    "brave": [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ],
    "notepad": [r"C:\Windows\System32\notepad.exe"],
    "notepad++": [
        r"C:\Program Files\Notepad++\notepad++.exe",
        r"C:\Program Files (x86)\Notepad++\notepad++.exe",
    ],
    "calculator": [r"C:\Windows\System32\calc.exe"],
    "calc": [r"C:\Windows\System32\calc.exe"],
    "cmd": [r"C:\Windows\System32\cmd.exe"],
    "powershell": [r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"],
    "terminal": [
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\wt.exe"),
    ],
    "vscode": [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
        r"C:\Program Files\Microsoft VS Code\Code.exe",
    ],
    "vs code": [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    ],
    "code": [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    ],
    "explorer": [r"C:\Windows\explorer.exe"],
    "file explorer": [r"C:\Windows\explorer.exe"],
    "paint": [r"C:\Windows\System32\mspaint.exe"],
    "snipping tool": [r"C:\Windows\System32\SnippingTool.exe"],
    "task manager": [r"C:\Windows\System32\Taskmgr.exe"],
    "taskmgr": [r"C:\Windows\System32\Taskmgr.exe"],
    "spotify": [
        os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
    ],
    "discord": [
        os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe --processStart Discord.exe"),
    ],
    "slack": [
        os.path.expandvars(r"%LOCALAPPDATA%\slack\slack.exe"),
    ],
    "steam": [
        r"C:\Program Files (x86)\Steam\steam.exe",
        r"C:\Program Files\Steam\steam.exe",
    ],
    "word": [
        r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
    ],
    "excel": [
        r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE",
    ],
    "powerpoint": [
        r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    ],
    "vlc": [
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
    ],
    "git bash": [
        r"C:\Program Files\Git\git-bash.exe",
    ],
    "python": [shutil.which("python") or "python"],
}

# Name aliases
ALIASES = {
    "google chrome": "chrome",
    "google": "chrome",
    "browser": "chrome",
    "text editor": "notepad",
    "code editor": "vscode",
    "visual studio code": "vscode",
    "files": "explorer",
    "my computer": "explorer",
    "music": "spotify",
    "video player": "vlc",
}


def find_app_path(app_name: str) -> str:
    """
    Find application path using multiple strategies:
    1. Known paths dictionary
    2. shutil.which() for PATH-discoverable apps
    3. 'where' command as fallback
    """
    name = app_name.lower().strip()
    
    # Check aliases
    name = ALIASES.get(name, name)
    
    # Strategy 1: Known paths
    if name in COMMON_APP_PATHS:
        for path in COMMON_APP_PATHS[name]:
            expanded = os.path.expandvars(path)
            if os.path.exists(expanded):
                return expanded
    
    # Strategy 2: shutil.which
    which_result = shutil.which(name)
    if which_result:
        return which_result
    
    # Also try with .exe
    which_result = shutil.which(name + ".exe")
    if which_result:
        return which_result
    
    # Strategy 3: Windows 'where' command
    try:
        result = subprocess.run(
            ["where", name], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')[0]
    except Exception:
        pass
    
    return ""


def open_app(app_name: str):
    """Open an application by name with smart path discovery."""
    if not app_name:
        print("No app specified.")
        return

    path = find_app_path(app_name)
    
    if path:
        try:
            # Handle special cases like Discord's Update.exe
            if " --" in path:
                parts = path.split(" ", 1)
                subprocess.Popen([parts[0]] + parts[1].split())
            else:
                subprocess.Popen(path)
            print(f"✅ {app_name} opened.")
        except Exception as e:
            print(f"❌ Failed to open {app_name}: {e}")
    else:
        # Try as a UWP/Store app
        try:
            subprocess.Popen(["start", app_name], shell=True)
            print(f"✅ Trying to open {app_name} via system...")
        except Exception:
            print(f"❌ {app_name} not found. Try installing it first.")


def list_available_apps() -> list:
    """List apps that Kiro can currently detect."""
    available = []
    for name in sorted(COMMON_APP_PATHS.keys()):
        path = find_app_path(name)
        if path:
            available.append({"name": name, "path": path})
    return available
