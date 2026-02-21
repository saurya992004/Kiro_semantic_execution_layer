# File Manager Module

A comprehensive file management system for organizing, analyzing, and optimizing file structures on Windows systems.

## Features

### 1. **Organization by File Type**
Automatically organize files into folders based on their type (Images, Documents, Videos, Audio, Archives, Code, Data, Executables, etc.)

**Usage:**
```json
{
    "intent": "file_management",
    "action": "organize_by_type",
    "parameters": {
        "folder_name": "Downloads",
        "confirm": false  // true to apply, false for dry-run
    }
}
```

### 2. **Duplicate File Detection**
Find and identify duplicate files using file hash comparison or filename matching.

**Usage:**
```json
{
    "intent": "file_management",
    "action": "find_duplicates",
    "parameters": {
        "folder_name": "Downloads"
    }
}
```

### 3. **Remove Duplicates**
Safely remove duplicate files while keeping the original.

**Usage:**
```json
{
    "intent": "file_management",
    "action": "remove_duplicates",
    "parameters": {
        "folder_name": "Downloads",
        "confirm": false  // true to delete, false for dry-run
    }
}
```

### 4. **Large File Scanning**
Find the largest files in a folder to identify space hogs.

**Usage:**
```json
{
    "intent": "file_management",
    "action": "find_large_files",
    "parameters": {
        "folder_name": "Downloads",
        "min_size_mb": 100,  // Minimum file size to report
        "limit": 20          // Maximum number of files to show
    }
}
```

### 5. **Folder Analysis**
Get statistics about file organization and distribution.

**Usage:**
```json
{
    "intent": "file_management",
    "action": "analyze_folder",
    "parameters": {
        "folder_name": "Downloads"
    }
}
```

### 6. **Comprehensive Report**
Get a complete analysis including all metrics.

**Usage:**
```json
{
    "intent": "file_management",
    "action": "get_report",
    "parameters": {
        "folder_name": "Downloads"
    }
}
```

## Module Structure

```
file_manager/
├── __init__.py                 # Module exports
├── folder_finder.py            # Find folders by name on Desktop/Downloads
├── file_organizer.py           # Organize files by type
├── duplicate_detector.py        # Find and remove duplicate files
├── large_file_scanner.py        # Find large files and analyze disk usage
├── llm_organizer.py            # LLM-based organization suggestions
├── manager.py                  # Main orchestrator (FileManager class)
└── demo_file_manager.py        # Demo and usage examples
```

## API Reference

### FileManager Class

```python
from file_manager import FileManager

manager = FileManager()

# Load a folder by name (searches Desktop, Downloads, Documents, Home)
result = manager.load_folder("Downloads")

# Organize files by type (dry_run=True shows what would happen)
result = manager.organize_by_type(dry_run=True)

# Scan for duplicates
duplicates = manager.scan_duplicates()

# Remove duplicates
result = manager.remove_duplicates(dry_run=False)

# Scan for large files
large_files = manager.scan_large_files(min_size_mb=100, limit=20)

# Analyze folder structure
analysis = manager.analyze_folder()

# Get comprehensive report
report = manager.get_full_report()
```

### Convenience Functions

```python
from file_manager import quick_organize, quick_report

# Quickly organize a folder
result = quick_organize("MyFolder", use_llm=False)

# Quickly get a report
report = quick_report("MyFolder")
```

## File Categories

Files are organized into these default categories:

- **Images**: .jpg, .jpeg, .png, .gif, .bmp, .svg, .webp, .ico
- **Documents**: .pdf, .doc, .docx, .txt, .xlsx, .xls, .ppt, .pptx
- **Videos**: .mp4, .avi, .mkv, .mov, .wmv, .flv, .webm
- **Audio**: .mp3, .wav, .flac, .aac, .m4a, .ogg, .wma
- **Archives**: .zip, .rar, .7z, .tar, .gz, .bz2
- **Code**: .py, .js, .java, .cpp, .c, .html, .css, .php, .go, .rs
- **Data**: .json, .xml, .csv, .sql, .db
- **Executables**: .exe, .bat, .sh, .msi, .app
- **Others**: Any file not matching above categories

## Examples

### Example 1: Organize Downloads Folder

```python
from file_manager import FileManager

manager = FileManager()
manager.load_folder("Downloads")

# Preview what will happen
dry_run = manager.organize_by_type(dry_run=True)
print(f"Would move {dry_run['files_moved']} files")

# Apply organization
result = manager.organize_by_type(dry_run=False)
print(f"Moved {result['files_moved']} files")
```

### Example 2: Find and Report Duplicates

```python
manager = FileManager()
manager.load_folder("Downloads")

duplicates = manager.scan_duplicates()
if duplicates['duplicates_found']:
    print(f"Found {duplicates['total_duplicate_files']} duplicate files")
    print(f"Could save {duplicates['space_savings'] / (1024*1024):.2f} MB")
```

### Example 3: Find Large Files

```python
manager = FileManager()
manager.load_folder("Downloads")

large_files = manager.scan_large_files(min_size_mb=500, limit=10)
for file_info in large_files['large_files']:
    print(f"{file_info['name']}: {file_info['size_gb']}GB")
```

### Example 4: Comprehensive Folder Report

```python
manager = FileManager()
manager.load_folder("MyFolder")

report = manager.get_full_report()

print(f"Folder: {report['folder_name']}")
print(f"Total files: {report['analysis']['folder_info']['total_files']}")
print(f"Large files found: {len(report['large_files']['large_files'])}")
print(f"Duplicates: {report['duplicates']['total_duplicate_files']}")
```

## Optional: LLM-Based Organization

The file_manager includes support for using an LLM to suggest intelligent folder structures:

```python
from file_manager import FileManager, generate_llm_prompt

manager = FileManager()
manager.load_folder("Downloads")

# Prepare files for LLM analysis
prep = manager.prepare_for_llm_organization()

# The generated prompt can be sent to your LLM for suggestions
print(prep['llm_prompt'])

# LLM would respond with suggested structure
# Then you can apply it using apply_llm_organization()
```

## Folder Search

The module searches for folders in this order:
1. Desktop
2. Downloads
3. Documents
4. User home directory

You only need to specify the folder name, not the full path:
```python
# This will find the folder in any of the above locations
manager.load_folder("MyFolder")
```

## Safety Features

- **Dry-run mode**: Preview all actions before executing
- **Conflict handling**: Automatically renames files if duplicates exist during organization
- **Error handling**: Comprehensive error messages for permission/access issues
- **Hash-based comparison**: Uses SHA256 hashes to detect true duplicates (not just same filenames)

## Performance Notes

- Large file scanning may take time on folders with many files
- Duplicate detection using hash comparison is thorough but slower than filename-only comparison
- Organization operations preserve file metadata (timestamps, attributes)

## Limitations

- Folder name search is case-insensitive but searches only one level deep in each location
- Cannot move files across different drives (must be on same Windows volume)
- Requires read/write permissions on the target folders

## Future Enhancements

- Smart grouping by date, project name, or content similarity
- Archive old files to external storage
- Scheduled organization tasks
- Custom category definitions
- Compression recommendations
