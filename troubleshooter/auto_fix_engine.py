import subprocess
import ctypes
import sys

def run_command(command: str) -> bool:
    print(f"\n⚙️ Executing: {command}")
    try:
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True, text=True, check=True
        )
        print("✅ Success:")
        if result.stdout.strip():
            print(result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Failed:")
        if e.stderr.strip():
            print(e.stderr.strip())
        elif e.stdout.strip():
            print(e.stdout.strip())
        return False

def run_command_as_admin(command: str) -> bool:
    print(f"\n🛡️ Prompting for Admin privileges to execute: {command}")
    # We pass the command to powershell, keeping the window open briefly to see the result, or wait
    ps_args = f'-NoProfile -ExecutionPolicy Bypass -Command "{command}; Start-Sleep -Seconds 2"'
    
    # 1 is SW_SHOWNORMAL
    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", "powershell.exe", ps_args, None, 1)
    
    if int(ret) > 32:
        print("✅ Admin command execution requested successfully. (Check the new window)")
        return True
    else:
        print(f"❌ Failed to elevate command. Error code: {ret}")
        return False

def execute_fixes(commands: list):
    if not commands:
        print("No automated commands provided by the solution.")
        return

    print(f"\n🚀 Executing {len(commands)} fix commands...")
    for cmd_info in commands:
        cmd = cmd_info.get("command")
        requires_admin = cmd_info.get("requires_admin", False)
        
        if requires_admin:
             run_command_as_admin(cmd)
        else:
             run_command(cmd)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
