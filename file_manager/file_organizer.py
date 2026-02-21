"""
File Organizer - Organize files by type/category
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List
from datetime import datetime


# File type categories
FILE_CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".xlsx", ".xls", ".ppt", ".pptx"],
    "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg", ".wma"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Code": [".py", ".js", ".java", ".cpp", ".c", ".html", ".css", ".php", ".go", ".rs"],
    "Data": [".json", ".xml", ".csv", ".sql", ".db"],
    "Executables": [".exe", ".bat", ".sh", ".msi", ".app"],
}


def get_file_category(file_path: Path) -> str:
    """
    Determine the category of a file based on its extension
    
    Args:
        file_path: Path to the file
    
    Returns:
        Category name or "Others"
    """
    extension = file_path.suffix.lower()
    
    for category, extensions in FILE_CATEGORIES.items():
        if extension in extensions:
            return category
    
    return "Others"


def organize_files_by_type(folder_path: Path, dry_run: bool = False) -> Dict:
    """
    Organize files in a folder by their type/category
    
    Args:
        folder_path: Path to the folder to organize
        dry_run: If True, don't actually move files, just show what would happen
    
    Returns:
        Dictionary with organization results
    """
    if not folder_path.exists():
        return {"error": f"Folder does not exist: {folder_path}"}
    
    results = {
        "total_files_processed": 0,
        "files_moved": 0,
        "organization_map": {},
        "errors": [],
    }
    
    try:
        # Get all files in folder (not subdirectories)
        files = [f for f in folder_path.iterdir() if f.is_file()]
        
        for file_path in files:
            try:
                category = get_file_category(file_path)
                
                # Create category folder
                category_folder = folder_path / category
                
                if not dry_run:
                    category_folder.mkdir(exist_ok=True)
                
                # Track organization
                if category not in results["organization_map"]:
                    results["organization_map"][category] = []
                
                results["organization_map"][category].append(file_path.name)
                
                # Move file
                if not dry_run:
                    destination = category_folder / file_path.name
                    
                    # Handle duplicates
                    if destination.exists():
                        name, ext = os.path.splitext(file_path.name)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        destination = category_folder / f"{name}_{timestamp}{ext}"
                    
                    shutil.move(str(file_path), str(destination))
                    results["files_moved"] += 1
                
                results["total_files_processed"] += 1
                
            except Exception as e:
                results["errors"].append(f"Error processing {file_path.name}: {str(e)}")
    
    except Exception as e:
        results["error"] = str(e)
    
    return results


def get_organization_stats(folder_path: Path) -> Dict:
    """
    Get statistics about current folder organization
    
    Args:
        folder_path: Path to the folder
    
    Returns:
        Statistics about file organization
    """
    stats = {
        "total_files": 0,
        "organized_files": 0,
        "unorganized_files": 0,
        "categories_found": {},
    }
    
    try:
        for item in folder_path.rglob("*"):
            if item.is_file():
                stats["total_files"] += 1
                
                # Check if file is in a category folder
                parent_name = item.parent.name
                if parent_name in FILE_CATEGORIES or parent_name == "Others":
                    stats["organized_files"] += 1
                    stats["categories_found"][parent_name] = stats["categories_found"].get(parent_name, 0) + 1
                else:
                    stats["unorganized_files"] += 1
    
    except Exception as e:
        stats["error"] = str(e)
    
    return stats
