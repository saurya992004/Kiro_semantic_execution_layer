import psutil
import os
from datetime import datetime, timedelta
from pathlib import Path


# ============================================================================
# SYSTEM MONITORING FUNCTIONS
# ============================================================================

def get_cpu_usage() -> dict:
    """
    Returns current CPU usage metrics.
    
    Returns:
        dict: {
            "cpu_percent": float,  # Overall CPU usage percentage
            "cpu_count": int,      # Number of CPU cores
            "per_cpu": list        # Usage per core
        }
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        per_cpu = psutil.cpu_percent(interval=1, percpu=True)
        
        return {
            "cpu_percent": cpu_percent,
            "cpu_count": cpu_count,
            "per_cpu": per_cpu
        }
    except Exception as e:
        return {
            "error": str(e),
            "cpu_percent": 0.0,
            "cpu_count": 0,
            "per_cpu": []
        }


def get_ram_usage() -> dict:
    """
    Returns RAM usage metrics.
    
    Returns:
        dict: {
            "total_gb": float,
            "used_gb": float,
            "available_gb": float,
            "percent": float
        }
    """
    try:
        ram = psutil.virtual_memory()
        
        return {
            "total_gb": round(ram.total / (1024**3), 2),
            "used_gb": round(ram.used / (1024**3), 2),
            "available_gb": round(ram.available / (1024**3), 2),
            "percent": ram.percent
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_gb": 0.0,
            "used_gb": 0.0,
            "available_gb": 0.0,
            "percent": 0.0
        }


def get_disk_usage(drive: str = "C:") -> dict:
    """
    Returns disk space info for specified drive.
    
    Args:
        drive: Drive letter (default "C:")
    
    Returns:
        dict: {
            "drive": str,
            "total_gb": float,
            "used_gb": float,
            "free_gb": float,
            "percent": float
        }
    """
    try:
        # Ensure drive format is correct (e.g., "C:" or "C:\\")
        if not drive.endswith(":") and not drive.endswith(":\\"):
            drive = drive + ":"
        
        if not drive.endswith("\\"):
            drive = drive + "\\"
        
        disk = psutil.disk_usage(drive)
        
        return {
            "drive": drive,
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent": disk.percent
        }
    except Exception as e:
        return {
            "error": str(e),
            "drive": drive,
            "total_gb": 0.0,
            "used_gb": 0.0,
            "free_gb": 0.0,
            "percent": 0.0
        }


def get_system_health() -> dict:
    """
    Comprehensive health check returning all metrics.
    
    Returns:
        dict: {
            "cpu": dict,    # from get_cpu_usage()
            "ram": dict,    # from get_ram_usage()
            "disk": dict,   # from get_disk_usage()
            "timestamp": str
        }
    """
    return {
        "cpu": get_cpu_usage(),
        "ram": get_ram_usage(),
        "disk": get_disk_usage(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# ============================================================================
# DISK ANALYSIS FUNCTIONS
# ============================================================================

def analyze_disk_usage(path: str = "C:\\") -> dict:
    """
    Detailed breakdown of disk usage by top-level folders.
    
    Args:
        path: Path to analyze (default "C:\\")
    
    Returns:
        dict: {
            "path": str,
            "total_size_gb": float,
            "folders": [
                {
                    "name": str,
                    "size_gb": float,
                    "percent_of_total": float
                },
                ...
            ]
        }
    """
    try:
        if not os.path.exists(path):
            return {
                "error": f"Path does not exist: {path}",
                "path": path,
                "total_size_gb": 0.0,
                "folders": []
            }
        
        folders = []
        total_size = 0
        
        # Get top-level folders
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                
                if os.path.isdir(item_path):
                    try:
                        # Calculate folder size
                        folder_size = get_folder_size(item_path)
                        total_size += folder_size
                        
                        folders.append({
                            "name": item,
                            "size_gb": round(folder_size / (1024**3), 2),
                            "size_bytes": folder_size
                        })
                    except (PermissionError, OSError):
                        # Skip folders we can't access
                        continue
        except PermissionError:
            return {
                "error": "Permission denied",
                "path": path,
                "total_size_gb": 0.0,
                "folders": []
            }
        
        # Calculate percentages
        for folder in folders:
            if total_size > 0:
                folder["percent_of_total"] = round(
                    (folder["size_bytes"] / total_size) * 100, 2
                )
            else:
                folder["percent_of_total"] = 0.0
            # Remove size_bytes from output
            del folder["size_bytes"]
        
        # Sort by size descending
        folders.sort(key=lambda x: x["size_gb"], reverse=True)
        
        return {
            "path": path,
            "total_size_gb": round(total_size / (1024**3), 2),
            "folders": folders
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "path": path,
            "total_size_gb": 0.0,
            "folders": []
        }


def get_folder_size(path: str) -> int:
    """
    Calculate total size of a folder in bytes.
    
    Args:
        path: Folder path
    
    Returns:
        int: Total size in bytes
    """
    total = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += get_folder_size(entry.path)
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError):
        pass
    
    return total


def find_large_folders(path: str = "C:\\", threshold_gb: float = 1.0) -> list:
    """
    Find folders exceeding size threshold.
    
    Args:
        path: Path to search
        threshold_gb: Minimum folder size in GB
    
    Returns:
        list: [
            {
                "path": str,
                "size_gb": float
            },
            ...
        ]
    """
    try:
        if not os.path.exists(path):
            return []
        
        threshold_bytes = threshold_gb * (1024**3)
        large_folders = []
        
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                
                if os.path.isdir(item_path):
                    try:
                        folder_size = get_folder_size(item_path)
                        
                        if folder_size >= threshold_bytes:
                            large_folders.append({
                                "path": item_path,
                                "size_gb": round(folder_size / (1024**3), 2)
                            })
                    except (PermissionError, OSError):
                        continue
        except PermissionError:
            return []
        
        # Sort by size descending
        large_folders.sort(key=lambda x: x["size_gb"], reverse=True)
        
        return large_folders
    
    except Exception as e:
        return []


def get_disk_alerts() -> dict:
    """
    Check if disk usage exceeds warning thresholds.
    
    Returns:
        dict: {
            "status": str,  # "ok", "warning", "critical"
            "alerts": [
                {
                    "drive": str,
                    "percent": float,
                    "level": str,  # "warning" (>80%) or "critical" (>90%)
                    "message": str
                },
                ...
            ]
        }
    """
    try:
        alerts = []
        overall_status = "ok"
        
        # Check all disk partitions
        partitions = psutil.disk_partitions()
        
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                
                if usage.percent >= 90:
                    alerts.append({
                        "drive": partition.mountpoint,
                        "percent": usage.percent,
                        "level": "critical",
                        "message": f"Drive {partition.mountpoint} is {usage.percent}% full (CRITICAL)"
                    })
                    overall_status = "critical"
                
                elif usage.percent >= 80:
                    alerts.append({
                        "drive": partition.mountpoint,
                        "percent": usage.percent,
                        "level": "warning",
                        "message": f"Drive {partition.mountpoint} is {usage.percent}% full (WARNING)"
                    })
                    if overall_status != "critical":
                        overall_status = "warning"
            
            except (PermissionError, OSError):
                continue
        
        return {
            "status": overall_status,
            "alerts": alerts
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "alerts": []
        }


# ============================================================================
# AUTOMATED MAINTENANCE FUNCTIONS
# ============================================================================

def scan_cleanup_files(target_folder: str) -> dict:
    """
    Scan for files to clean up. DOES NOT DELETE.
    
    Args:
        target_folder: Folder to scan (restricted to test_cleanup for safety)
    
    Returns:
        dict: {
            "target_folder": str,
            "files_to_delete": [
                {
                    "path": str,
                    "size_mb": float,
                    "modified_date": str
                },
                ...
            ],
            "total_size_mb": float,
            "file_count": int
        }
    """
    # SAFETY CHECK: Only allow test_cleanup folder
    if not _is_safe_cleanup_path(target_folder):
        return {
            "error": "Safety restriction: Can only clean files in 'test_cleanup' folder",
            "target_folder": target_folder,
            "files_to_delete": [],
            "total_size_mb": 0.0,
            "file_count": 0
        }
    
    try:
        if not os.path.exists(target_folder):
            return {
                "error": f"Folder does not exist: {target_folder}",
                "target_folder": target_folder,
                "files_to_delete": [],
                "total_size_mb": 0.0,
                "file_count": 0
            }
        
        files_to_delete = []
        total_size = 0
        
        # Scan all files in folder and subfolders
        for root, dirs, files in os.walk(target_folder):
            for file in files:
                file_path = os.path.join(root, file)
                
                try:
                    stat = os.stat(file_path)
                    size_bytes = stat.st_size
                    modified_time = datetime.fromtimestamp(stat.st_mtime)
                    
                    files_to_delete.append({
                        "path": file_path,
                        "size_mb": round(size_bytes / (1024**2), 2),
                        "modified_date": modified_time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    total_size += size_bytes
                
                except (PermissionError, OSError):
                    continue
        
        return {
            "target_folder": target_folder,
            "files_to_delete": files_to_delete,
            "total_size_mb": round(total_size / (1024**2), 2),
            "file_count": len(files_to_delete)
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "target_folder": target_folder,
            "files_to_delete": [],
            "total_size_mb": 0.0,
            "file_count": 0
        }


def execute_cleanup(file_list: list) -> dict:
    """
    Execute cleanup after user confirmation.
    
    Args:
        file_list: List of file paths to delete (from scan_cleanup_files)
    
    Returns:
        dict: {
            "deleted_count": int,
            "failed_count": int,
            "total_size_freed_mb": float,
            "errors": [str, ...]
        }
    """
    deleted_count = 0
    failed_count = 0
    total_size_freed = 0
    errors = []
    
    for file_path in file_list:
        # SAFETY CHECK: Only delete files in test_cleanup
        if not _is_safe_cleanup_path(file_path):
            errors.append(f"Safety restriction prevented deletion: {file_path}")
            failed_count += 1
            continue
        
        try:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                os.remove(file_path)
                deleted_count += 1
                total_size_freed += size
        except Exception as e:
            errors.append(f"Failed to delete {file_path}: {str(e)}")
            failed_count += 1
    
    return {
        "deleted_count": deleted_count,
        "failed_count": failed_count,
        "total_size_freed_mb": round(total_size_freed / (1024**2), 2),
        "errors": errors
    }


def clean_temp_files() -> dict:
    """
    Scan temp files for cleanup (test folder only).
    Returns scan results, does NOT delete.
    
    Returns:
        dict: Scan results from scan_cleanup_files()
    """
    # Use test_cleanup/temp_files folder for safety
    temp_folder = os.path.join("test_cleanup", "temp_files")
    return scan_cleanup_files(temp_folder)


def clean_old_files(folder: str, days_old: int = 1) -> dict:
    """
    Scan for files older than N days (test folder only).
    Returns scan results, does NOT delete.
    
    Args:
        folder: Folder to scan (must be in test_cleanup)
        days_old: Files older than this many days (default: 1 day for demo)
    
    Returns:
        dict: Scan results with old files
    """
    # SAFETY CHECK
    if not _is_safe_cleanup_path(folder):
        return {
            "error": "Safety restriction: Can only scan files in 'test_cleanup' folder",
            "target_folder": folder,
            "files_to_delete": [],
            "total_size_mb": 0.0,
            "file_count": 0
        }
    
    try:
        if not os.path.exists(folder):
            return {
                "error": f"Folder does not exist: {folder}",
                "target_folder": folder,
                "files_to_delete": [],
                "total_size_mb": 0.0,
                "file_count": 0
            }
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        old_files = []
        total_size = 0
        
        for root, dirs, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                
                try:
                    stat = os.stat(file_path)
                    modified_time = datetime.fromtimestamp(stat.st_mtime)
                    
                    if modified_time < cutoff_date:
                        size_bytes = stat.st_size
                        
                        old_files.append({
                            "path": file_path,
                            "size_mb": round(size_bytes / (1024**2), 2),
                            "modified_date": modified_time.strftime("%Y-%m-%d %H:%M:%S"),
                            "days_old": (datetime.now() - modified_time).days
                        })
                        
                        total_size += size_bytes
                
                except (PermissionError, OSError):
                    continue
        
        return {
            "target_folder": folder,
            "days_threshold": days_old,
            "files_to_delete": old_files,
            "total_size_mb": round(total_size / (1024**2), 2),
            "file_count": len(old_files)
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "target_folder": folder,
            "files_to_delete": [],
            "total_size_mb": 0.0,
            "file_count": 0
        }


def _is_safe_cleanup_path(path: str) -> bool:
    """
    Check if path is safe for cleanup operations.
    Only allows paths within test_cleanup folder.
    
    Args:
        path: Path to check
    
    Returns:
        bool: True if safe, False otherwise
    """
    try:
        # Normalize path
        normalized_path = os.path.normpath(path).lower()
        
        # Check if path contains test_cleanup
        return "test_cleanup" in normalized_path
    except:
        return False


# ============================================================================
# HEALTH ALERT FUNCTIONS
# ============================================================================

def check_health_alerts() -> dict:
    """
    Returns list of current system issues.
    
    Returns:
        dict: {
            "alerts": [
                {
                    "type": str,  # "cpu", "ram", "disk"
                    "severity": str,  # "info", "warning", "critical"
                    "message": str
                },
                ...
            ],
            "overall_status": str  # "healthy", "warning", "critical"
        }
    """
    alerts = []
    overall_status = "healthy"
    
    # Check CPU
    cpu = get_cpu_usage()
    if "error" not in cpu:
        if cpu["cpu_percent"] > 90:
            alerts.append({
                "type": "cpu",
                "severity": "critical",
                "message": f"CPU usage is very high: {cpu['cpu_percent']}%"
            })
            overall_status = "critical"
        elif cpu["cpu_percent"] > 75:
            alerts.append({
                "type": "cpu",
                "severity": "warning",
                "message": f"CPU usage is high: {cpu['cpu_percent']}%"
            })
            if overall_status == "healthy":
                overall_status = "warning"
    
    # Check RAM
    ram = get_ram_usage()
    if "error" not in ram:
        if ram["percent"] > 90:
            alerts.append({
                "type": "ram",
                "severity": "critical",
                "message": f"RAM usage is very high: {ram['percent']}% ({ram['used_gb']}GB / {ram['total_gb']}GB)"
            })
            overall_status = "critical"
        elif ram["percent"] > 80:
            alerts.append({
                "type": "ram",
                "severity": "warning",
                "message": f"RAM usage is high: {ram['percent']}% ({ram['used_gb']}GB / {ram['total_gb']}GB)"
            })
            if overall_status == "healthy":
                overall_status = "warning"
    
    # Check Disk
    disk_alerts = get_disk_alerts()
    if disk_alerts["status"] != "ok":
        for alert in disk_alerts["alerts"]:
            alerts.append({
                "type": "disk",
                "severity": alert["level"],
                "message": alert["message"]
            })
        
        if disk_alerts["status"] == "critical":
            overall_status = "critical"
        elif disk_alerts["status"] == "warning" and overall_status == "healthy":
            overall_status = "warning"
    
    return {
        "alerts": alerts,
        "overall_status": overall_status
    }


# ============================================================================
# COMPLETE SYSTEM HEALTH - COMPREHENSIVE DIAGNOSTIC
# ============================================================================

def get_complete_system_health() -> dict:
    """
    Get comprehensive system health information.
    Runs complete diagnostic and returns detailed report.
    
    Returns:
        dict: {
            "timestamp": str,
            "overall_status": str,  # healthy, warning, critical
            "cpu": {...},
            "ram": {...},
            "disk": {...},
            "alerts": [...],
            "health_summary": str
        }
    """
    try:
        timestamp = datetime.now().isoformat()
        
        # Collect all metrics
        cpu = get_cpu_usage()
        ram = get_ram_usage()
        disk = get_disk_usage("C:")
        health_alerts = check_health_alerts()
        
        # Format summary
        status = health_alerts.get("overall_status", "healthy")
        icons = {
            "healthy": "✅",
            "warning": "⚠️",
            "critical": "🔴"
        }
        
        summary_lines = [
            f"{'='*60}",
            f"🏥 COMPLETE SYSTEM HEALTH REPORT",
            f"{'='*60}",
            f"Timestamp: {timestamp}",
            f"Overall Status: {icons.get(status)} {status.upper()}",
            f"{'='*60}",
            "",
            f"📊 CPU STATUS",
            f"  └─ Usage: {cpu.get('cpu_percent', 0)}%",
            f"  └─ Cores: {cpu.get('cpu_count', 0)}",
            f"  └─ Per-Core: {[f'{p}%' for p in cpu.get('per_cpu', [])[:4]]}",
            "",
            f"💾 RAM STATUS",
            f"  └─ Usage: {ram.get('percent', 0)}%",
            f"  └─ Used: {ram.get('used_gb', 0):.1f}GB / {ram.get('total_gb', 0):.1f}GB",
            f"  └─ Available: {ram.get('available_gb', 0):.1f}GB",
            "",
            f"💿 DISK STATUS (C:)",
            f"  └─ Usage: {disk.get('percent', 0)}%",
            f"  └─ Used: {disk.get('used_gb', 0):.1f}GB / {disk.get('total_gb', 0):.1f}GB",
            f"  └─ Free: {disk.get('free_gb', 0):.1f}GB",
            "",
        ]
        
        # Add alerts if any
        if health_alerts.get("alerts"):
            summary_lines.append("⚠️ ALERTS & ISSUES:")
            for alert in health_alerts["alerts"]:
                severity = alert.get("severity", "info")
                msg = alert.get("message", "Unknown alert")
                alert_icon = "🔴" if severity == "critical" else "🟡" if severity == "warning" else "ℹ️"
                summary_lines.append(f"  {alert_icon} [{severity.upper()}] {msg}")
        else:
            summary_lines.append("✅ No alerts - System is running smoothly!")
        
        summary_lines.extend([
            "",
            f"{'='*60}",
            "🎯 RECOMMENDATIONS",
            f"{'='*60}",
        ])
        
        # Add recommendations based on status
        if cpu.get("cpu_percent", 0) > 80:
            summary_lines.append("• Close unnecessary applications to reduce CPU usage")
        if ram.get("percent", 0) > 80:
            summary_lines.append("• Free up RAM by closing memory-intensive programs")
        if disk.get("percent", 0) > 80:
            summary_lines.append("• Consider cleaning up or deleting unnecessary files")
        if not summary_lines[-1].startswith("•"):
            summary_lines.append("• System is performing well! No immediate action needed.")
        
        summary_lines.append(f"{'='*60}")
        
        health_summary = "\n".join(summary_lines)
        
        # Print to console for visibility
        print(health_summary)
        
        return {
            "timestamp": timestamp,
            "overall_status": status,
            "cpu": cpu,
            "ram": ram,
            "disk": disk,
            "alerts": health_alerts.get("alerts", []),
            "health_summary": health_summary
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "overall_status": "error",
            "health_summary": f"Error getting system health: {str(e)}"
        }
