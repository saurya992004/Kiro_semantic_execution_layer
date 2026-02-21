"""
File Manager Demo - Shows how to use the file management features
"""

from file_manager import FileManager, quick_organize, quick_report


def demo_basic_usage():
    """Demo: Basic file manager usage"""
    print("\n" + "="*60)
    print("DEMO: Basic File Manager Usage")
    print("="*60 + "\n")
    
    manager = FileManager()
    
    # Load a folder
    print("Loading 'Downloads' folder...")
    result = manager.load_folder("Downloads")
    if "error" in result:
        print(f"❌ {result['error']}")
        return
    
    print(f"✅ {result['message']}")
    print(f"   Files: {result['folder_info']['total_files']}")
    print(f"   Size: {result['folder_info']['size_mb']} MB\n")


def demo_organize_by_type():
    """Demo: Organize files by type"""
    print("\n" + "="*60)
    print("DEMO: Organize Files by Type")
    print("="*60 + "\n")
    
    manager = FileManager()
    
    # Load folder
    result = manager.load_folder("Downloads")
    if "error" in result:
        print(f"❌ {result['error']}")
        return
    
    # Dry run first
    print("Running DRY-RUN (no files will be moved)...\n")
    dry_run_result = manager.organize_by_type(dry_run=True)
    
    if "error" in dry_run_result:
        print(f"❌ {dry_run_result['error']}")
        return
    
    print(f"📊 Organization Plan:")
    print(f"   Total files to process: {dry_run_result['total_files_processed']}")
    print(f"   Files to move: {dry_run_result['files_moved']}")
    print(f"\n📁 Folder structure that would be created:")
    for category, files in dry_run_result['organization_map'].items():
        print(f"   📂 {category}/")
        for filename in files[:3]:  # Show first 3 files
            print(f"      - {filename}")
        if len(files) > 3:
            print(f"      ... and {len(files) - 3} more files")


def demo_scan_large_files():
    """Demo: Find large files"""
    print("\n" + "="*60)
    print("DEMO: Scan for Large Files")
    print("="*60 + "\n")
    
    manager = FileManager()
    
    # Load folder
    result = manager.load_folder("Downloads")
    if "error" in result:
        print(f"❌ {result['error']}")
        return
    
    # Scan for files > 50MB
    print("Scanning for files larger than 50MB...\n")
    large_files = manager.scan_large_files(min_size_mb=50, limit=10)
    
    if "error" in large_files:
        print(f"❌ {large_files['error']}")
        return
    
    print(f"📈 Found {large_files['large_files_found']} large files:\n")
    
    for i, file_info in enumerate(large_files['large_files'], 1):
        size_display = f"{file_info['size_gb']}GB" if file_info['size_gb'] >= 1 else f"{file_info['size_mb']}MB"
        print(f"   {i}. {file_info['name']}")
        print(f"      Size: {size_display}")
        print(f"      Path: {file_info['path']}\n")


def demo_scan_duplicates():
    """Demo: Find duplicate files"""
    print("\n" + "="*60)
    print("DEMO: Scan for Duplicate Files")
    print("="*60 + "\n")
    
    manager = FileManager()
    
    # Load folder
    result = manager.load_folder("Downloads")
    if "error" in result:
        print(f"❌ {result['error']}")
        return
    
    # Scan for duplicates
    print("Scanning for duplicate files...\n")
    duplicates = manager.scan_duplicates()
    
    if "error" in duplicates:
        print(f"❌ {duplicates['error']}")
        return
    
    if not duplicates['duplicates_found']:
        print("✅ No duplicates found!")
        return
    
    print(f"🔍 Found {duplicates['total_duplicate_files']} duplicate files:\n")
    
    for group in duplicates['duplicate_groups'][:5]:  # Show first 5 groups
        print(f"   📋 Duplicate group ({group['count']} copies):")
        for file_path in group['files']:
            print(f"      - {file_path}")
        print(f"   💾 Space savings if cleaned: {round(sum(group['file_sizes'][1:]) / (1024*1024), 2)} MB\n")
    
    if len(duplicates['duplicate_groups']) > 5:
        print(f"   ... and {len(duplicates['duplicate_groups']) - 5} more duplicate groups")
    
    print(f"   Total space that could be saved: {round(duplicates['space_savings'] / (1024*1024), 2)} MB")


def demo_full_report():
    """Demo: Get comprehensive folder report"""
    print("\n" + "="*60)
    print("DEMO: Full Folder Report")
    print("="*60 + "\n")
    
    manager = FileManager()
    
    # Load folder
    result = manager.load_folder("Downloads")
    if "error" in result:
        print(f"❌ {result['error']}")
        return
    
    # Get full report
    print("Generating comprehensive folder report...\n")
    report = manager.get_full_report()
    
    if "error" in report:
        print(f"❌ {report['error']}")
        return
    
    print(f"📂 Folder: {report['folder_name']}")
    print(f"📍 Path: {report['folder_path']}\n")
    
    # Folder info
    folder_info = report['analysis']['folder_info']
    print(f"📊 Folder Statistics:")
    print(f"   Total files: {folder_info['total_files']}")
    print(f"   Total size: {folder_info['size_mb']} MB\n")
    
    # Size breakdown
    size_breakdown = report['analysis']['size_breakdown']
    print(f"📈 Size by File Type (Top 5):")
    extensions = list(size_breakdown['by_extension'].items())[:5]
    for ext, info in extensions:
        print(f"   {ext}: {info['size_mb']}MB ({info['count']} files)")
    
    # Large files
    large_files = report['large_files']
    print(f"\n🔴 Top 5 Largest Files:")
    for file_info in large_files['large_files'][:5]:
        size_display = f"{file_info['size_gb']}GB" if file_info['size_gb'] >= 1 else f"{file_info['size_mb']}MB"
        print(f"   {file_info['name']}: {size_display}")
    
    # Duplicates
    duplicates = report['duplicates']
    if duplicates['duplicates_found']:
        print(f"\n⚠️  Duplicates Found: {duplicates['total_duplicate_files']} duplicate files")
        print(f"   Space savings possible: {round(duplicates['space_savings'] / (1024*1024), 2)} MB")
    else:
        print(f"\n✅ No duplicates found")


if __name__ == "__main__":
    print("\n🚀 FILE MANAGER DEMO\n")
    
    # Run demos
    demo_basic_usage()
    demo_organize_by_type()
    demo_scan_large_files()
    demo_scan_duplicates()
    demo_full_report()
    
    print("\n" + "="*60)
    print("DEMO Complete!")
    print("="*60 + "\n")
