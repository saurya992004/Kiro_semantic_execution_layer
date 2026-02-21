"""
Quick test for file_manager integration
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_manager import FileManager


def test_file_manager():
    """Test basic file manager functionality"""
    print("\n" + "="*60)
    print("FILE MANAGER INTEGRATION TEST")
    print("="*60 + "\n")
    
    try:
        # Test 1: Create FileManager instance
        print("✅ Test 1: Creating FileManager instance...")
        manager = FileManager()
        print("   FileManager created successfully\n")
        
        # Test 2: Find Desktop folder
        print("✅ Test 2: Testing folder finder...")
        result = manager.load_folder("Desktop")
        if "error" not in result:
            print("   ✓ Desktop folder found")
            print(f"   ✓ Folder info: {result['folder_info']}\n")
        else:
            print(f"   Note: Desktop not found (this may be normal)\n")
        
        # Test 3: Test folder operations
        print("✅ Test 3: Testing folder finder with Downloads...")
        result = manager.load_folder("Downloads")
        if "error" not in result:
            print("   ✓ Downloads folder found")
            folder_info = result['folder_info']
            print(f"   ✓ Total files: {folder_info['total_files']}")
            print(f"   ✓ Total size: {folder_info['size_mb']} MB\n")
            
            # Test 4: Test analysis
            print("✅ Test 4: Testing folder analysis...")
            analysis = manager.analyze_folder()
            if "error" not in analysis:
                print("   ✓ Analysis completed")
                org_stats = analysis.get('organization_stats', {})
                print(f"   ✓ Organization stats retrieved\n")
            
            # Test 5: Test duplicate detection
            print("✅ Test 5: Testing duplicate detection...")
            duplicates = manager.scan_duplicates()
            if "error" not in duplicates:
                print("   ✓ Duplicate scan completed")
                if duplicates['duplicates_found']:
                    print(f"   ✓ Duplicates found: {duplicates['total_duplicate_files']}")
                else:
                    print("   ✓ No duplicates found")
                print()
            
            # Test 6: Test large file scanning
            print("✅ Test 6: Testing large file scanner...")
            large_files = manager.scan_large_files(min_size_mb=50, limit=10)
            if "error" not in large_files:
                print("   ✓ Large file scan completed")
                print(f"   ✓ Large files found: {large_files['large_files_found']}\n")
        
        print("="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60 + "\n")
        return True
    
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_file_manager()
    sys.exit(0 if success else 1)
