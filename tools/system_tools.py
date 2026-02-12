import os
import subprocess
import psutil
import shutil


# ---------------- POWER ---------------- #

def shutdown_pc():
    os.system("shutdown /s /t 1")


def restart_pc():
    os.system("shutdown /r /t 1")


def sleep_pc():
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")


def lock_pc():
    os.system("rundll32.exe user32.dll,LockWorkStation")


# ---------------- PROCESS ---------------- #

def kill_process(process_name: str):

    if not process_name:
        print("No process specified.")
        return

    for proc in psutil.process_iter(["name"]):
        if process_name.lower() in proc.info["name"].lower():
            proc.kill()
            print(f"Killed {proc.info['name']}")


# ---------------- TEMP CLEANUP ---------------- #

def clean_temp():

    temp_path = os.getenv("TEMP")

    try:
        shutil.rmtree(temp_path)
        os.makedirs(temp_path)
        print("Temp files cleaned.")
    except Exception as e:
        print("Cleanup error:", e)


# ---------------- RECYCLE BIN ---------------- #

def empty_recycle_bin():
    os.system("PowerShell.exe Clear-RecycleBin -Force")
