import subprocess
import os


# Known application paths
APP_PATHS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "notepad": r"C:\Windows\System32\notepad.exe",
    "calculator": r"C:\Windows\System32\calc.exe",
    "cmd": r"C:\Windows\System32\cmd.exe",
}


def open_app(app_name: str):

    if not app_name:
        print("No app specified.")
        return

    app_key = app_name.lower()

    if app_key in APP_PATHS:

        path = APP_PATHS[app_key]

        if os.path.exists(path):
            subprocess.Popen(path)
            print(f"{app_name} opened.")
        else:
            print(f"Path not found for {app_name}.")

    else:
        print(f"{app_name} not configured yet.")

