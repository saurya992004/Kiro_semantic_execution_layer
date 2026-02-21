"""
Duplicate Detector - Find duplicate files in a folder
"""

import hashlib
from pathlib import Path
from typing import Dict, List
from collections import defaultdict


def calculate_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Calculate SHA256 hash of a file to detect duplicates
    
    Args:
        file_path: Path to the file
        chunk_size: Size of chunks to read
    
    Returns:
        SHA256 hash of the file
    """
    sha256_hash = hashlib.sha256()
    
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
    except (OSError, PermissionError, IOError):
        return None
    
    return sha256_hash.hexdigest()


def find_duplicates(folder_path: Path, by_name: bool = False) -> Dict:
    """
    Find duplicate files in a folder
    
    Args:
        folder_path: Path to the folder to scan
        by_name: If True, find duplicates by filename only; if False, use file hash
    
    Returns:
        Dictionary with duplicate information
    """
    if not folder_path.exists():
        return {"error": f"Folder does not exist: {folder_path}"}
    
    results = {
        "total_files": 0,
        "duplicates_found": False,
        "duplicate_groups": [],
        "total_duplicate_files": 0,
        "space_savings": 0,  # bytes
    }
    
    try:
        file_map = defaultdict(list)
        
        # Collect all files
        for file_path in folder_path.rglob("*"):
            if file_path.is_file():
                results["total_files"] += 1
                
                if by_name:
                    key = file_path.name
                else:
                    # Use file hash for comparison
                    file_hash = calculate_file_hash(file_path)
                    if file_hash:
                        key = file_hash
                    else:
                        continue
                
                file_map[key].append(file_path)
        
        # Find groups with duplicates
        for key, files in file_map.items():
            if len(files) > 1:
                results["duplicates_found"] = True
                results["total_duplicate_files"] += len(files) - 1
                
                # Calculate space savings (keep one, delete others)
                try:
                    file_sizes = [f.stat().st_size for f in files if f.exists()]
                    if file_sizes:
                        space_saved = sum(file_sizes[1:])  # All but the first copy
                        results["space_savings"] += space_saved
                except (OSError, PermissionError):
                    pass
                
                duplicate_group = {
                    "count": len(files),
                    "files": [str(f) for f in files],
                    "file_sizes": [],
                }
                
                # Get file sizes
                for f in files:
                    try:
                        size = f.stat().st_size
                        duplicate_group["file_sizes"].append(size)
                    except (OSError, PermissionError):
                        duplicate_group["file_sizes"].append(0)
                
                results["duplicate_groups"].append(duplicate_group)
    
    except Exception as e:
        results["error"] = str(e)
    
    return results


def remove_duplicates(folder_path: Path, keep_first: bool = True, dry_run: bool = False) -> Dict:
    """
    Remove duplicate files from a folder
    
    Args:
        folder_path: Path to the folder
        keep_first: If True, keep the first occurrence and delete others
        dry_run: If True, don't actually delete files
    
    Returns:
        Dictionary with removal results
    """
    duplicates = find_duplicates(folder_path, by_name=False)
    
    if "error" in duplicates:
        return duplicates
    
    results = {
        "files_deleted": 0,
        "space_freed": 0,
        "deleted_files": [],
        "errors": [],
    }
    
    try:
        for group in duplicates.get("duplicate_groups", []):
            files = [Path(f) for f in group["files"]]
            
            # Keep the first, delete others
            if keep_first:
                files_to_delete = files[1:]
            else:
                files_to_delete = files[:-1]
            
            for file_path in files_to_delete:
                try:
                    file_size = file_path.stat().st_size if file_path.exists() else 0
                    
                    if not dry_run:
                        file_path.unlink()  # Delete the file
                    
                    results["files_deleted"] += 1
                    results["space_freed"] += file_size
                    results["deleted_files"].append(str(file_path))
                    
                except Exception as e:
                    results["errors"].append(f"Could not delete {file_path}: {str(e)}")
    
    except Exception as e:
        results["error"] = str(e)
    
    return results
