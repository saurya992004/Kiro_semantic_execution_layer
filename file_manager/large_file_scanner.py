"""
Large File Scanner - Find large files in a folder
"""

from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class FileInfo:
    path: str
    name: str
    size: int
    size_mb: float
    size_gb: float


def find_large_files(folder_path: Path, min_size_mb: float = 100, limit: int = 20) -> Dict:
    """
    Find large files in a folder
    
    Args:
        folder_path: Path to the folder to scan
        min_size_mb: Minimum file size in MB to consider as "large"
        limit: Maximum number of files to return
    
    Returns:
        Dictionary with large files information
    """
    if not folder_path.exists():
        return {"error": f"Folder does not exist: {folder_path}"}
    
    results = {
        "total_files": 0,
        "large_files_found": 0,
        "large_files": [],
        "total_scanned_size_mb": 0,
        "scan_errors": [],
    }
    
    large_files = []
    min_size_bytes = min_size_mb * 1024 * 1024
    
    try:
        for file_path in folder_path.rglob("*"):
            if file_path.is_file():
                results["total_files"] += 1
                
                try:
                    file_size = file_path.stat().st_size
                    results["total_scanned_size_mb"] += file_size / (1024 * 1024)
                    
                    if file_size >= min_size_bytes:
                        file_info = {
                            "path": str(file_path),
                            "name": file_path.name,
                            "size_bytes": file_size,
                            "size_mb": round(file_size / (1024 * 1024), 2),
                            "size_gb": round(file_size / (1024 * 1024 * 1024), 2),
                        }
                        large_files.append(file_info)
                        results["large_files_found"] += 1
                
                except (OSError, PermissionError) as e:
                    results["scan_errors"].append(f"Could not read: {file_path}")
        
        # Sort by size (largest first) and limit results
        large_files.sort(key=lambda x: x["size_bytes"], reverse=True)
        results["large_files"] = large_files[:limit]
        results["total_scanned_size_mb"] = round(results["total_scanned_size_mb"], 2)
    
    except Exception as e:
        results["error"] = str(e)
    
    return results


def get_folder_size_breakdown(folder_path: Path) -> Dict:
    """
    Get size breakdown by file type in a folder
    
    Args:
        folder_path: Path to the folder
    
    Returns:
        Dictionary with size breakdown by extension
    """
    if not folder_path.exists():
        return {"error": f"Folder does not exist: {folder_path}"}
    
    results = {
        "total_size_bytes": 0,
        "total_size_mb": 0,
        "by_extension": {},
        "by_folder": {},
    }
    
    try:
        # By extension
        for file_path in folder_path.rglob("*"):
            if file_path.is_file():
                try:
                    size = file_path.stat().st_size
                    results["total_size_bytes"] += size
                    
                    ext = file_path.suffix.lower() or "no_extension"
                    if ext not in results["by_extension"]:
                        results["by_extension"][ext] = {
                            "count": 0,
                            "size_bytes": 0,
                            "size_mb": 0,
                        }
                    
                    results["by_extension"][ext]["count"] += 1
                    results["by_extension"][ext]["size_bytes"] += size
                    results["by_extension"][ext]["size_mb"] = round(
                        results["by_extension"][ext]["size_bytes"] / (1024 * 1024), 2
                    )
                
                except (OSError, PermissionError):
                    pass
        
        # By subfolder
        for subfolder in folder_path.iterdir():
            if subfolder.is_dir():
                folder_size = 0
                file_count = 0
                
                try:
                    for item in subfolder.rglob("*"):
                        if item.is_file():
                            try:
                                folder_size += item.stat().st_size
                                file_count += 1
                            except (OSError, PermissionError):
                                pass
                    
                    results["by_folder"][subfolder.name] = {
                        "size_bytes": folder_size,
                        "size_mb": round(folder_size / (1024 * 1024), 2),
                        "file_count": file_count,
                    }
                
                except (OSError, PermissionError):
                    pass
        
        results["total_size_mb"] = round(results["total_size_bytes"] / (1024 * 1024), 2)
        
        # Sort extensions by size
        results["by_extension"] = dict(
            sorted(
                results["by_extension"].items(),
                key=lambda x: x[1]["size_bytes"],
                reverse=True,
            )
        )
    
    except Exception as e:
        results["error"] = str(e)
    
    return results
