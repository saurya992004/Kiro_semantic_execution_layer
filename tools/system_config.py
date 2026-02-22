"""
System Configuration Tool
Retrieves detailed system information about the computer
"""

import platform
import psutil
import socket
import subprocess
import os
from datetime import datetime


def get_system_config():
    """
    Get comprehensive system configuration information.
    
    Returns:
        dict: System configuration details
    """
    try:
        config = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "system_information": _get_system_info(),
            "processor": _get_processor_info(),
            "memory": _get_memory_info(),
            "storage": _get_storage_info(),
            "network": _get_network_info(),
            "graphics": _get_graphics_info(),
            "display": _get_display_info()
        }
        return config
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve system configuration"}


def _get_system_info():
    """Get basic system information."""
    return {
        "os": platform.system(),
        "os_version": platform.release(),
        "os_build": _get_windows_build(),
        "architecture": platform.architecture()[0],
        "hostname": socket.gethostname(),
        "username": os.getenv('USERNAME', 'Unknown'),
        "system": platform.platform(),
        "processor_name": platform.processor()
    }


def _get_processor_info():
    """Get CPU information."""
    try:
        return {
            "cpu_count": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "cpu_frequency": f"{psutil.cpu_freq().current:.2f} MHz",
            "cpu_usage": f"{psutil.cpu_percent(interval=1)}%",
            "processor_name": platform.processor()
        }
    except Exception as e:
        return {"error": str(e)}


def _get_memory_info():
    """Get RAM information."""
    try:
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            "total_ram": f"{memory.total / (1024**3):.2f} GB",
            "available_ram": f"{memory.available / (1024**3):.2f} GB",
            "used_ram": f"{memory.used / (1024**3):.2f} GB",
            "ram_percent": f"{memory.percent}%",
            "total_swap": f"{swap.total / (1024**3):.2f} GB",
            "available_swap": f"{swap.free / (1024**3):.2f} GB",
            "swap_percent": f"{swap.percent}%"
        }
    except Exception as e:
        return {"error": str(e)}


def _get_storage_info():
    """Get storage/disk information."""
    try:
        storage_info = {}
        partitions = psutil.disk_partitions()
        
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                storage_info[partition.device] = {
                    "mountpoint": partition.mountpoint,
                    "filesystem": partition.fstype,
                    "total": f"{usage.total / (1024**3):.2f} GB",
                    "used": f"{usage.used / (1024**3):.2f} GB",
                    "free": f"{usage.free / (1024**3):.2f} GB",
                    "percent_used": f"{usage.percent}%"
                }
            except PermissionError:
                continue
        
        return storage_info if storage_info else {"error": "Could not retrieve disk information"}
    except Exception as e:
        return {"error": str(e)}


def _get_network_info():
    """Get network information."""
    try:
        network_info = {
            "hostname": socket.gethostname(),
            "local_ip": socket.gethostbyname(socket.gethostname()),
            "mac_address": _get_mac_address()
        }
        
        # Get network interfaces
        interfaces = psutil.net_if_addrs()
        network_info["interfaces"] = {}
        
        for interface, addrs in interfaces.items():
            for addr in addrs:
                if interface not in network_info["interfaces"]:
                    network_info["interfaces"][interface] = []
                network_info["interfaces"][interface].append({
                    "family": addr.family.name,
                    "address": addr.address
                })
        
        return network_info
    except Exception as e:
        return {"error": str(e)}


def _get_graphics_info():
    """Get graphics/GPU information from Windows system."""
    gpu_list = []
    
    # Method 1: Try WMIC
    try:
        result = subprocess.run(
            ['wmic', 'path', 'win32_videocontroller', 'get', 'name,description,driverversion'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and line.strip() != 'Name']
            if lines:
                gpu_list.extend(lines)
    except Exception:
        pass
    
    # Method 2: Try PowerShell Get-CimInstance if WMIC failed
    if not gpu_list:
        try:
            result = subprocess.run(
                ['powershell', '-Command', 
                 'Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                if lines:
                    gpu_list.extend(lines)
        except Exception:
            pass
    
    # Method 3: Try DirectX Diagnostic Tool output
    if not gpu_list:
        try:
            result = subprocess.run(
                ['powershell', '-Command',
                 'Get-CimInstance -ClassName Win32_DisplayConfiguration | Select-Object -ExpandProperty Description'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                if lines:
                    gpu_list.extend(lines)
        except Exception:
            pass
    
    # Return results
    if gpu_list:
        # Remove duplicates while preserving order
        seen = set()
        unique_gpus = []
        for gpu in gpu_list:
            if gpu and gpu not in seen:
                unique_gpus.append(gpu)
                seen.add(gpu)
        return {"gpus": unique_gpus}
    else:
        # Fallback: Try to detect if integrated GPU is present
        try:
            result = subprocess.run(
                ['powershell', '-Command', 
                 'Get-CimInstance Win32_VideoController | Measure-Object | Select-Object -ExpandProperty Count'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and int(result.stdout.strip() or 0) > 0:
                return {"gpus": ["Graphics adapter detected (unable to retrieve name)"]}
        except Exception:
            pass
        
        return {"gpus": ["No GPU information available"]}



def _get_display_info():
    """Get display/monitor information from Windows system."""
    monitors = []
    
    # Method 1: Try WMIC for physical monitors
    try:
        result = subprocess.run(
            ['wmic', 'path', 'Win32_DesktopMonitor', 'get', 'Name'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            lines = [line.strip() for line in result.stdout.split('\n') 
                    if line.strip() and line.strip() != 'Name']
            if lines:
                monitors.extend(lines)
    except Exception:
        pass
    
    # Method 2: Try WMIC for PnP displays
    if not monitors:
        try:
            result = subprocess.run(
                ['wmic', 'path', 'Win32_PnPDevice', 'where', 'Description like "Monitor"', 'get', 'Name'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.split('\n')
                        if line.strip() and line.strip() != 'Name']
                if lines:
                    monitors.extend(lines)
        except Exception:
            pass
    
    # Method 3: Try PowerShell Get-CimInstance for monitors
    if not monitors:
        try:
            result = subprocess.run(
                ['powershell', '-Command',
                 'Get-CimInstance -ClassName Win32_DesktopMonitor | Select-Object -ExpandProperty Name'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                if lines:
                    monitors.extend(lines)
        except Exception:
            pass
    
    # Method 4: Try registry for display information
    if not monitors:
        try:
            result = subprocess.run(
                ['powershell', '-Command',
                 'Get-CimInstance -ClassName Win32_PnPEntity | Where-Object Description -like "*Monitor*" | Select-Object -ExpandProperty Description'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                if lines:
                    monitors.extend(lines)
        except Exception:
            pass
    
    # Method 5: Try to get screen resolution info
    if not monitors:
        try:
            result = subprocess.run(
                ['powershell', '-Command',
                 'Get-CimInstance -ClassName Win32_DisplayConfiguration | Select-Object -ExpandProperty Description'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                if lines:
                    monitors.extend(lines)
        except Exception:
            pass
    
    # Method 6: Fallback to screen resolution detection
    if not monitors:
        try:
            result = subprocess.run(
                ['powershell', '-Command',
                 '[System.Windows.Forms.Screen]::AllScreens | Select-Object -ExpandProperty DeviceName'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                if lines:
                    monitors.extend(lines)
        except Exception:
            pass
    
    # Return results
    if monitors:
        # Remove duplicates while preserving order
        seen = set()
        unique_monitors = []
        for monitor in monitors:
            if monitor and monitor not in seen:
                unique_monitors.append(monitor)
                seen.add(monitor)
        return {"monitors": unique_monitors}
    else:
        return {"monitors": ["No monitor information available"]}


def _get_windows_build():
    """Get Windows build number."""
    try:
        result = subprocess.run(
            ['powershell', '-Command', 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion" -Name CurrentBuild'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if 'CurrentBuild' in result.stdout:
            for line in result.stdout.split('\n'):
                if 'CurrentBuild' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        return parts[1].strip()
        return "Unknown"
    except Exception:
        return "Unknown"


def _get_mac_address():
    """Get MAC address."""
    try:
        import uuid
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        return ':'.join([mac[e:e+2] for e in range(0, 12, 2)]).upper()
    except Exception:
        return "Unknown"


def print_system_config():
    """Print formatted system configuration."""
    config = get_system_config()
    
    if "error" in config:
        print(f"Error: {config['error']}")
        return
    
    print("\n")
    print("=" * 82)
    print(" " * 15 + "SYSTEM CONFIGURATION INFORMATION")
    print("=" * 82)
    
    # System Information
    print("\n[SYSTEM INFORMATION]")
    print("-" * 82)
    sys_info = config["system_information"]
    print(f"  Operating System:     {sys_info.get('os')} {sys_info.get('os_version')}")
    print(f"  Build Number:         {sys_info.get('os_build')}")
    print(f"  Architecture:         {sys_info.get('architecture')}")
    print(f"  Computer Name:        {sys_info.get('hostname')}")
    print(f"  Username:             {sys_info.get('username')}")
    
    # Processor
    print("\n[PROCESSOR]")
    print("-" * 82)
    proc = config["processor"]
    if "error" not in proc:
        print(f"  Processor:            {proc.get('processor_name')}")
        print(f"  Physical Cores:       {proc.get('cpu_count')}")
        print(f"  Logical Cores:        {proc.get('logical_cores')}")
        print(f"  CPU Speed:            {proc.get('cpu_frequency')}")
        print(f"  Current Usage:        {proc.get('cpu_usage')}")
    
    # Memory
    print("\n[MEMORY - RAM]")
    print("-" * 82)
    mem = config["memory"]
    if "error" not in mem:
        print(f"  Total RAM:            {mem.get('total_ram')}")
        print(f"  Used RAM:             {mem.get('used_ram')}")
        print(f"  Available RAM:        {mem.get('available_ram')}")
        print(f"  RAM Usage:            {mem.get('ram_percent')}")
        print(f"  Total Swap:           {mem.get('total_swap')}")
        print(f"  Swap Usage:           {mem.get('swap_percent')}")
    
    # Storage
    print("\n[STORAGE]")
    print("-" * 82)
    storage = config["storage"]
    if isinstance(storage, dict) and "error" not in storage:
        for drive, info in storage.items():
            print(f"\n  {drive} ({info.get('filesystem')})")
            print(f"    Total:              {info.get('total')}")
            print(f"    Used:               {info.get('used')}")
            print(f"    Free:               {info.get('free')}")
            print(f"    Usage:              {info.get('percent_used')}")
    
    # Network
    print("\n[NETWORK]")
    print("-" * 82)
    network = config["network"]
    if "error" not in network:
        print(f"  Hostname:             {network.get('hostname')}")
        print(f"  Local IP:             {network.get('local_ip')}")
        print(f"  MAC Address:          {network.get('mac_address')}")
        
        if "interfaces" in network and network["interfaces"]:
            print(f"\n  Network Interfaces:")
            for iface, addrs in network["interfaces"].items():
                print(f"    {iface}:")
                for addr in addrs:
                    print(f"      {addr.get('family')}: {addr.get('address')}")
    
    # Graphics
    print("\n[GRAPHICS]")
    print("-" * 82)
    graphics = config["graphics"]
    if "gpus" in graphics:
        for gpu in graphics["gpus"]:
            print(f"  GPU:                  {gpu}")
    
    # Display
    print("\n[DISPLAY]")
    print("-" * 82)
    display = config["display"]
    if "monitors" in display:
        for monitor in display["monitors"]:
            print(f"  Monitor:              {monitor}")
    
    print("\n" + "=" * 82)
    print(f"Generated at: {config['timestamp']}")
    print("=" * 82)
    print()
