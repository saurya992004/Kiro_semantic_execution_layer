"""
PC Speedup Tools for Kiro OS
==============================
Safe PC optimization: lower bloatware priority, clean temp, flush idle RAM.
Never kills critical system processes.
"""

import os
import psutil
import logging
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Known non-essential processes that can be safely deprioritized
BLOATWARE_PROCESSES = {
    "onedrive.exe", "onedrivesetup.exe",
    "cortana.exe", "searchapp.exe",
    "yourphone.exe", "phoneexperiencehost.exe",
    "gamebar.exe", "gamebarpresencewriter.exe",
    "widgets.exe", "widgetservice.exe",
    "msedge.exe",  # Edge background processes
    "teams.exe", "msteams.exe",
    "skype.exe", "skypeapp.exe",
    "spotify.exe",
    "discord.exe",
    "slack.exe",
    "zoom.exe",
    "adobe_updater.exe", "adobearm.exe",
    "jusched.exe",  # Java updater
    "googledrivesync.exe",
    "dropbox.exe",
    "icloud.exe", "iclouddrive.exe",
    "grammarly.exe",
}

# Critical processes to NEVER touch
PROTECTED_PROCESSES = {
    "system", "system idle process", "csrss.exe", "wininit.exe",
    "services.exe", "lsass.exe", "svchost.exe", "smss.exe",
    "winlogon.exe", "dwm.exe", "explorer.exe", "taskmgr.exe",
    "conhost.exe", "ntoskrnl.exe", "runtimebroker.exe",
    "dllhost.exe", "wudfhost.exe", "mpcmdrun.exe",
    "msmpeng.exe", "nissrv.exe",  # Windows Defender
    "python.exe", "pythonw.exe",  # Don't kill ourselves
    "cmd.exe", "powershell.exe", "windowsterminal.exe",
}


def get_before_metrics() -> Dict[str, Any]:
    """Snapshot current system metrics for before/after comparison."""
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    return {
        "cpu_percent": cpu,
        "ram_percent": ram.percent,
        "ram_used_gb": round(ram.used / (1024**3), 2),
        "ram_available_gb": round(ram.available / (1024**3), 2),
        "timestamp": datetime.now().isoformat(),
    }


def find_bloatware_processes() -> List[Dict[str, Any]]:
    """Find non-essential processes currently running."""
    found = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
        try:
            name = proc.info["name"].lower()
            if name in BLOATWARE_PROCESSES and name not in PROTECTED_PROCESSES:
                mem_mb = proc.info["memory_info"].rss / (1024**2) if proc.info["memory_info"] else 0
                found.append({
                    "pid": proc.info["pid"],
                    "name": proc.info["name"],
                    "memory_mb": round(mem_mb, 1),
                    "cpu_percent": proc.info["cpu_percent"] or 0,
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return found


def lower_bloatware_priority() -> Dict[str, Any]:
    """Lower priority of non-essential processes (safe, non-destructive)."""
    adjusted = []
    errors = []
    
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = proc.info["name"].lower()
            if name in BLOATWARE_PROCESSES and name not in PROTECTED_PROCESSES:
                p = psutil.Process(proc.info["pid"])
                current_nice = p.nice()
                # Set to below-normal priority (higher nice value = lower priority)
                if current_nice <= psutil.BELOW_NORMAL_PRIORITY_CLASS:
                    p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                    adjusted.append({
                        "pid": proc.info["pid"],
                        "name": proc.info["name"],
                        "action": "priority_lowered",
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            errors.append(f"{proc.info.get('name', 'unknown')}: {str(e)}")
        except Exception as e:
            errors.append(f"{proc.info.get('name', 'unknown')}: {str(e)}")
    
    return {
        "adjusted_count": len(adjusted),
        "processes": adjusted,
        "errors": errors[:5],  # Limit error output
    }


def flush_idle_memory() -> Dict[str, Any]:
    """
    Reduce memory footprint of idle processes.
    Uses EmptyWorkingSet via ctypes on Windows.
    """
    freed_count = 0
    errors = []
    
    try:
        import ctypes
        from ctypes import wintypes
        
        # Get handle to reduce working set
        kernel32 = ctypes.windll.kernel32
        psapi = ctypes.windll.psapi
        
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_SET_QUOTA = 0x0100
        
        for proc in psutil.process_iter(["pid", "name", "memory_info"]):
            try:
                name = proc.info["name"].lower()
                if name in PROTECTED_PROCESSES:
                    continue
                
                mem = proc.info["memory_info"]
                if not mem:
                    continue
                
                # Only flush processes using >50MB and not actively using CPU
                if mem.rss > 50 * 1024 * 1024:
                    p = psutil.Process(proc.info["pid"])
                    if p.cpu_percent(interval=0) < 1.0:
                        # Try to reduce working set
                        handle = kernel32.OpenProcess(
                            PROCESS_QUERY_INFORMATION | PROCESS_SET_QUOTA,
                            False,
                            proc.info["pid"]
                        )
                        if handle:
                            # EmptyWorkingSet
                            psapi.EmptyWorkingSet(handle)
                            kernel32.CloseHandle(handle)
                            freed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            except Exception:
                continue
    except Exception as e:
        errors.append(f"Memory flush error: {str(e)}")
    
    return {
        "processes_flushed": freed_count,
        "errors": errors,
    }


def get_startup_programs() -> List[Dict[str, str]]:
    """List programs that run at Windows startup."""
    startup_programs = []
    
    try:
        import winreg
        
        # Check HKCU Run key
        for key_path in [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
        ]:
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        startup_programs.append({
                            "name": name,
                            "command": value,
                            "location": f"HKCU\\{key_path}",
                        })
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except OSError:
                continue
    except ImportError:
        pass
    
    # Also check startup folder
    startup_folder = os.path.join(
        os.environ.get("APPDATA", ""),
        r"Microsoft\Windows\Start Menu\Programs\Startup"
    )
    if os.path.exists(startup_folder):
        for item in os.listdir(startup_folder):
            startup_programs.append({
                "name": item,
                "command": os.path.join(startup_folder, item),
                "location": "Startup Folder",
            })
    
    return startup_programs


def clean_temp_files_safe() -> Dict[str, Any]:
    """Clean Windows temp files safely (only files, not folders in use)."""
    temp_path = os.environ.get("TEMP", os.environ.get("TMP", ""))
    if not temp_path or not os.path.exists(temp_path):
        return {"error": "Temp path not found", "freed_mb": 0}
    
    freed_bytes = 0
    deleted_count = 0
    errors = 0
    
    for root, dirs, files in os.walk(temp_path):
        for f in files:
            filepath = os.path.join(root, f)
            try:
                size = os.path.getsize(filepath)
                os.remove(filepath)
                freed_bytes += size
                deleted_count += 1
            except (PermissionError, OSError):
                errors += 1
                continue
    
    return {
        "deleted_files": deleted_count,
        "freed_mb": round(freed_bytes / (1024**2), 2),
        "errors_skipped": errors,
    }


def speedup_pc() -> Dict[str, Any]:
    """
    Full PC speedup pipeline.
    Returns before/after metrics and detailed actions taken.
    """
    print("\n🚀 KIRO PC SPEEDUP")
    print("=" * 50)
    
    # Step 1: Before metrics
    print("📊 Capturing baseline metrics...")
    before = get_before_metrics()
    print(f"   CPU: {before['cpu_percent']}% | RAM: {before['ram_percent']}%")
    
    # Step 2: Find bloatware
    print("\n🔍 Scanning for non-essential processes...")
    bloatware = find_bloatware_processes()
    if bloatware:
        print(f"   Found {len(bloatware)} non-essential processes:")
        for p in bloatware[:5]:
            print(f"   • {p['name']} (PID: {p['pid']}, RAM: {p['memory_mb']}MB)")
    else:
        print("   ✅ No bloatware detected")
    
    # Step 3: Lower priority
    print("\n⬇️  Lowering bloatware priority...")
    priority_result = lower_bloatware_priority()
    print(f"   Adjusted {priority_result['adjusted_count']} processes")
    
    # Step 4: Clean temp files
    print("\n🧹 Cleaning temp files...")
    temp_result = clean_temp_files_safe()
    print(f"   Deleted {temp_result['deleted_files']} files, freed {temp_result['freed_mb']}MB")
    
    # Step 5: Flush idle memory
    print("\n💾 Optimizing memory...")
    memory_result = flush_idle_memory()
    print(f"   Flushed {memory_result['processes_flushed']} idle processes")
    
    # Step 6: After metrics
    print("\n📊 Capturing post-optimization metrics...")
    after = get_before_metrics()
    print(f"   CPU: {after['cpu_percent']}% | RAM: {after['ram_percent']}%")
    
    # Calculate improvements
    cpu_improvement = before["cpu_percent"] - after["cpu_percent"]
    ram_improvement = before["ram_percent"] - after["ram_percent"]
    
    print(f"\n{'=' * 50}")
    print(f"📈 RESULTS:")
    print(f"   CPU: {before['cpu_percent']}% → {after['cpu_percent']}% ({'+' if cpu_improvement < 0 else '-'}{abs(cpu_improvement):.1f}%)")
    print(f"   RAM: {before['ram_percent']}% → {after['ram_percent']}% ({'+' if ram_improvement < 0 else '-'}{abs(ram_improvement):.1f}%)")
    print(f"   Temp files cleaned: {temp_result['freed_mb']}MB freed")
    print(f"   Processes optimized: {priority_result['adjusted_count'] + memory_result['processes_flushed']}")
    print(f"{'=' * 50}\n")
    
    return {
        "success": True,
        "before": before,
        "after": after,
        "improvements": {
            "cpu_reduction": round(cpu_improvement, 1),
            "ram_reduction": round(ram_improvement, 1),
            "temp_freed_mb": temp_result["freed_mb"],
            "processes_optimized": priority_result["adjusted_count"],
            "memory_flushed": memory_result["processes_flushed"],
        },
        "details": {
            "bloatware_found": bloatware,
            "priority_adjusted": priority_result,
            "temp_cleaned": temp_result,
            "memory_flushed": memory_result,
        },
        "startup_programs": get_startup_programs(),
    }
