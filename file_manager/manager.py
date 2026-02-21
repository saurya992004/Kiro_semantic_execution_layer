"""
File Manager - Main orchestrator for file organization tasks
"""

from pathlib import Path
from typing import Dict, Optional
from .folder_finder import find_folder, get_folder_info
from .file_organizer import organize_files_by_type, get_organization_stats
from .duplicate_detector import find_duplicates, remove_duplicates
from .large_file_scanner import find_large_files, get_folder_size_breakdown
from .llm_organizer import prepare_files_for_llm, generate_llm_prompt


class FileManager:
    """Main file manager for organizing and analyzing folders"""
    
    def __init__(self):
        self.current_folder: Optional[Path] = None
        self.current_folder_info: Dict = {}
    
    def load_folder(self, folder_name: str) -> Dict:
        """
        Load and analyze a folder by name
        
        Args:
            folder_name: Name of folder to load
        
        Returns:
            Dictionary with folder info
        """
        folder_path = find_folder(folder_name)
        
        if not folder_path:
            return {"error": f"Folder '{folder_name}' not found in Desktop, Downloads, or Documents"}
        
        self.current_folder = folder_path
        self.current_folder_info = get_folder_info(folder_path)
        
        return {
            "success": True,
            "message": f"Loaded folder: {folder_path.name}",
            "folder_info": self.current_folder_info,
        }
    
    def analyze_folder(self) -> Dict:
        """
        Analyze the current folder comprehensively
        
        Returns:
            Dictionary with analysis results
        """
        if not self.current_folder:
            return {"error": "No folder loaded. Use load_folder() first."}
        
        analysis = {
            "folder_info": self.current_folder_info,
            "organization_stats": get_organization_stats(self.current_folder),
            "size_breakdown": get_folder_size_breakdown(self.current_folder),
        }
        
        return analysis
    
    def scan_large_files(self, min_size_mb: float = 100, limit: int = 20) -> Dict:
        """
        Scan for large files in the current folder
        
        Args:
            min_size_mb: Minimum size to consider as "large"
            limit: Maximum number of files to return
        
        Returns:
            Dictionary with large files
        """
        if not self.current_folder:
            return {"error": "No folder loaded. Use load_folder() first."}
        
        return find_large_files(self.current_folder, min_size_mb=min_size_mb, limit=limit)
    
    def scan_duplicates(self, by_name: bool = False) -> Dict:
        """
        Scan for duplicate files in the current folder
        
        Args:
            by_name: If True, find duplicates by filename only; if False, use file hash
        
        Returns:
            Dictionary with duplicate information
        """
        if not self.current_folder:
            return {"error": "No folder loaded. Use load_folder() first."}
        
        return find_duplicates(self.current_folder, by_name=by_name)
    
    def remove_duplicates(self, dry_run: bool = True) -> Dict:
        """
        Remove duplicate files from the current folder
        
        Args:
            dry_run: If True, don't actually delete files
        
        Returns:
            Dictionary with removal results
        """
        if not self.current_folder:
            return {"error": "No folder loaded. Use load_folder() first."}
        
        return remove_duplicates(self.current_folder, keep_first=True, dry_run=dry_run)
    
    def organize_by_type(self, dry_run: bool = False) -> Dict:
        """
        Organize files by type in the current folder
        
        Args:
            dry_run: If True, don't actually move files
        
        Returns:
            Dictionary with organization results
        """
        if not self.current_folder:
            return {"error": "No folder loaded. Use load_folder() first."}
        
        return organize_files_by_type(self.current_folder, dry_run=dry_run)
    
    def prepare_for_llm_organization(self) -> Dict:
        """
        Prepare file list for LLM-based organization
        
        Returns:
            Dictionary with file information
        """
        if not self.current_folder:
            return {"error": "No folder loaded. Use load_folder() first."}
        
        file_info = prepare_files_for_llm(self.current_folder)
        
        if "error" in file_info:
            return file_info
        
        return {
            "file_info": file_info,
            "llm_prompt": generate_llm_prompt(file_info),
        }
    
    def get_full_report(self) -> Dict:
        """
        Get a comprehensive report of the current folder
        
        Returns:
            Dictionary with complete analysis
        """
        if not self.current_folder:
            return {"error": "No folder loaded. Use load_folder() first."}
        
        report = {
            "folder_name": self.current_folder.name,
            "folder_path": str(self.current_folder),
            "analysis": self.analyze_folder(),
            "large_files": self.scan_large_files(limit=10),
            "duplicates": self.scan_duplicates(),
        }
        
        return report


# Convenience functions for use in other modules

def quick_organize(folder_name: str, use_llm: bool = False) -> Dict:
    """
    Quickly organize a folder
    
    Args:
        folder_name: Name of folder to organize
        use_llm: If True, try to use LLM for organization suggestions
    
    Returns:
        Organization results
    """
    manager = FileManager()
    
    # Load folder
    load_result = manager.load_folder(folder_name)
    if "error" in load_result:
        return load_result
    
    # Organize by type
    return manager.organize_by_type(dry_run=False)


def quick_report(folder_name: str) -> Dict:
    """
    Quickly get a report on a folder
    
    Args:
        folder_name: Name of folder to analyze
    
    Returns:
        Full report
    """
    manager = FileManager()
    
    # Load folder
    load_result = manager.load_folder(folder_name)
    if "error" in load_result:
        return load_result
    
    # Return full report
    return manager.get_full_report()
