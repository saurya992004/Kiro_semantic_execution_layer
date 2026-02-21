"""
Integration test for file_manager with Jarvis
"""

import json
from router.intent_router import route_intent


def test_file_management_intent():
    """Test file management intent routing"""
    print("\n" + "="*70)
    print("JARVIS FILE MANAGEMENT INTEGRATION TEST")
    print("="*70 + "\n")
    
    try:
        # Test 1: Organize by type (dry-run)
        print("Test 1️: File Organization (Dry-run)")
        print("-" * 70)
        command = {
            "intent": "file_management",
            "action": "organize_by_type",
            "parameters": {
                "folder_name": "test_cleanup",  # Use test folder
                "confirm": False
            }
        }
        print(f"Command: {json.dumps(command, indent=2)}\n")
        route_intent(command)
        print()
        
        # Test 2: Analyze folder
        print("\nTest 2️: Folder Analysis")
        print("-" * 70)
        command = {
            "intent": "file_management",
            "action": "analyze_folder",
            "parameters": {
                "folder_name": "test_cleanup"
            }
        }
        print(f"Command: {json.dumps(command, indent=2)}\n")
        route_intent(command)
        print()
        
        # Test 3: Find duplicates
        print("\n Test 3️: Duplicate Detection")
        print("-" * 70)
        command = {
            "intent": "file_management",
            "action": "find_duplicates",
            "parameters": {
                "folder_name": "test_cleanup"
            }
        }
        print(f"Command: {json.dumps(command, indent=2)}\n")
        route_intent(command)
        print()
        
        # Test 4: Find large files
        print("\nTest 4️: Large File Scanner")
        print("-" * 70)
        command = {
            "intent": "file_management",
            "action": "find_large_files",
            "parameters": {
                "folder_name": "test_cleanup",
                "min_size_mb": 0.01  # Low threshold for test
            }
        }
        print(f"Command: {json.dumps(command, indent=2)}\n")
        route_intent(command)
        print()
        
        # Test 5: Get comprehensive report
        print("\nTest 5️: Comprehensive Report")
        print("-" * 70)
        command = {
            "intent": "file_management",
            "action": "get_report",
            "parameters": {
                "folder_name": "test_cleanup"
            }
        }
        print(f"Command: {json.dumps(command, indent=2)}\n")
        route_intent(command)
        print()
        
        print("="*70)
        print("✅ ALL INTEGRATION TESTS COMPLETED SUCCESSFULLY")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = test_file_management_intent()
    sys.exit(0 if success else 1)
