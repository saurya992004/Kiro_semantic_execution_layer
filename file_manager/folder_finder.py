"""
Folder Finder - Locate folders by name on Desktop, Downloads, Documents, etc.
"""

import os
from pathlib import Path
from typing import Optional


def find_folder(folder_name: str) -> Optional[Path]:
    """
    Search for a folder by name in common locations:
    - Desktop
    - Downloads
    - Documents
    - User home directory
    - Current working directory
    - Parent of current working directory
    
    Args:
        folder_name: Name of the folder to find
    
    Returns:
        Path object if found, None otherwise
    """
    home = Path.home()
    cwd = Path.cwd()
    
    search_locations = [
        cwd,  # Current working directory first
        cwd.parent,  # Parent directory
        home / "Desktop",
        home / "Downloads",
        home / "Documents",
        home,
    ]
    
    for location in search_locations:
        if not location.exists():
            continue
        
        # Check if folder exists directly in location
        target_path = location / folder_name
        if target_path.exists() and target_path.is_dir():
            return target_path
        
        # Search in subdirectories (one level deep)
        try:
            for item in location.iterdir():
                if item.is_dir() and item.name.lower() == folder_name.lower():
                    return item
        except (PermissionError, OSError):
            continue
    
    return None


def get_folder_info(folder_path: Path) -> dict:
    """
    Get basic information about a folder (fast version - top-level only)
    
    Args:
        folder_path: Path to the folder
    
    Returns:
        Dictionary with folder info
    """
    try:
        files = []
        total_size = 0
        max_items = 10000  # Prevent excessive scanning
        item_count = 0
        
        # Count only direct children for speed
        for item in folder_path.iterdir():
            if item_count >= max_items:
                break
            
            if item.is_file():
                files.append(item)
                try:
                    total_size += item.stat().st_size
                except (OSError, PermissionError):
                    pass
            
            item_count += 1
        
        return {
            "path": str(folder_path),
            "name": folder_path.name,
            "total_files": len(files),
            "total_size": total_size,
            "size_mb": round(total_size / (1024 * 1024), 2),
        }
    except Exception as e:
        return {
            "path": str(folder_path),
            "name": folder_path.name,
            "error": str(e),
        }
