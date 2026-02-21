"""
File Manager Module - Organize and analyze files in folders
"""

from .manager import FileManager, quick_organize, quick_report
from .folder_finder import find_folder, get_folder_info
from .file_organizer import organize_files_by_type, get_organization_stats, FILE_CATEGORIES
from .duplicate_detector import find_duplicates, remove_duplicates
from .large_file_scanner import find_large_files, get_folder_size_breakdown
from .llm_organizer import (
    prepare_files_for_llm,
    generate_llm_prompt,
    parse_llm_response,
    apply_llm_organization,
)

__all__ = [
    # Main classes
    "FileManager",
    # Convenience functions
    "quick_organize",
    "quick_report",
    # Folder operations
    "find_folder",
    "get_folder_info",
    # File organization
    "organize_files_by_type",
    "get_organization_stats",
    "FILE_CATEGORIES",
    # Duplicate detection
    "find_duplicates",
    "remove_duplicates",
    # Large file scanning
    "find_large_files",
    "get_folder_size_breakdown",
    # LLM organization
    "prepare_files_for_llm",
    "generate_llm_prompt",
    "parse_llm_response",
    "apply_llm_organization",
]
