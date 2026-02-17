"""
Test script for Phase 6 diagnostic functions.
Run with: python tests/test_diagnostics.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.diagnostics_tools import (
    get_cpu_usage,
    get_ram_usage,
    get_disk_usage,
    get_system_health,
    analyze_disk_usage,
    find_large_folders,
    get_disk_alerts,
    check_health_alerts,
    scan_cleanup_files,
    clean_temp_files,
    clean_old_files,
)


def test_cpu_usage():
    """Test CPU usage function."""
    print("\n" + "="*60)
    print("TEST: get_cpu_usage()")
    print("="*60)
    
    result = get_cpu_usage()
    
    assert "cpu_percent" in result, "Missing cpu_percent"
    assert "cpu_count" in result, "Missing cpu_count"
    assert "per_cpu" in result, "Missing per_cpu"
    assert isinstance(result["cpu_percent"], float), "cpu_percent should be float"
    assert isinstance(result["cpu_count"], int), "cpu_count should be int"
    assert isinstance(result["per_cpu"], list), "per_cpu should be list"
    
    print(f"✅ CPU Usage: {result['cpu_percent']}%")
    print(f"✅ CPU Cores: {result['cpu_count']}")
    print(f"✅ Per-core usage: {len(result['per_cpu'])} cores")
    print("✅ PASSED")


def test_ram_usage():
    """Test RAM usage function."""
    print("\n" + "="*60)
    print("TEST: get_ram_usage()")
    print("="*60)
    
    result = get_ram_usage()
    
    assert "total_gb" in result, "Missing total_gb"
    assert "used_gb" in result, "Missing used_gb"
    assert "available_gb" in result, "Missing available_gb"
    assert "percent" in result, "Missing percent"
    
    print(f"✅ Total RAM: {result['total_gb']}GB")
    print(f"✅ Used RAM: {result['used_gb']}GB")
    print(f"✅ Available RAM: {result['available_gb']}GB")
    print(f"✅ Usage: {result['percent']}%")
    print("✅ PASSED")


def test_disk_usage():
    """Test disk usage function."""
    print("\n" + "="*60)
    print("TEST: get_disk_usage()")
    print("="*60)
    
    result = get_disk_usage("C:")
    
    assert "drive" in result, "Missing drive"
    assert "total_gb" in result, "Missing total_gb"
    assert "used_gb" in result, "Missing used_gb"
    assert "free_gb" in result, "Missing free_gb"
    assert "percent" in result, "Missing percent"
    
    print(f"✅ Drive: {result['drive']}")
    print(f"✅ Total: {result['total_gb']}GB")
    print(f"✅ Used: {result['used_gb']}GB")
    print(f"✅ Free: {result['free_gb']}GB")
    print(f"✅ Usage: {result['percent']}%")
    print("✅ PASSED")


def test_system_health():
    """Test system health function."""
    print("\n" + "="*60)
    print("TEST: get_system_health()")
    print("="*60)
    
    result = get_system_health()
    
    assert "cpu" in result, "Missing cpu"
    assert "ram" in result, "Missing ram"
    assert "disk" in result, "Missing disk"
    assert "timestamp" in result, "Missing timestamp"
    
    print(f"✅ Timestamp: {result['timestamp']}")
    print(f"✅ CPU: {result['cpu']['cpu_percent']}%")
    print(f"✅ RAM: {result['ram']['percent']}%")
    print(f"✅ Disk: {result['disk']['percent']}%")
    print("✅ PASSED")


def test_disk_alerts():
    """Test disk alerts function."""
    print("\n" + "="*60)
    print("TEST: get_disk_alerts()")
    print("="*60)
    
    result = get_disk_alerts()
    
    assert "status" in result, "Missing status"
    assert "alerts" in result, "Missing alerts"
    assert result["status"] in ["ok", "warning", "critical"], "Invalid status"
    
    print(f"✅ Status: {result['status']}")
    print(f"✅ Alerts: {len(result['alerts'])}")
    if result['alerts']:
        for alert in result['alerts']:
            print(f"  - {alert['message']}")
    print("✅ PASSED")


def test_health_alerts():
    """Test health alerts function."""
    print("\n" + "="*60)
    print("TEST: check_health_alerts()")
    print("="*60)
    
    result = check_health_alerts()
    
    assert "alerts" in result, "Missing alerts"
    assert "overall_status" in result, "Missing overall_status"
    assert result["overall_status"] in ["healthy", "warning", "critical"], "Invalid status"
    
    print(f"✅ Overall Status: {result['overall_status']}")
    print(f"✅ Alerts: {len(result['alerts'])}")
    if result['alerts']:
        for alert in result['alerts']:
            print(f"  - [{alert['severity']}] {alert['message']}")
    print("✅ PASSED")


def test_cleanup_scan():
    """Test cleanup scan function."""
    print("\n" + "="*60)
    print("TEST: scan_cleanup_files()")
    print("="*60)
    
    result = scan_cleanup_files("test_cleanup")
    
    assert "target_folder" in result, "Missing target_folder"
    assert "files_to_delete" in result, "Missing files_to_delete"
    assert "total_size_mb" in result, "Missing total_size_mb"
    assert "file_count" in result, "Missing file_count"
    
    print(f"✅ Target Folder: {result['target_folder']}")
    print(f"✅ Files Found: {result['file_count']}")
    print(f"✅ Total Size: {result['total_size_mb']}MB")
    print("✅ PASSED")


def test_cleanup_safety():
    """Test cleanup safety restrictions."""
    print("\n" + "="*60)
    print("TEST: Cleanup Safety Restrictions")
    print("="*60)
    
    # Try to scan outside test folder
    result = scan_cleanup_files("C:\\")
    
    assert "error" in result, "Should have error for unsafe path"
    assert "Safety restriction" in result["error"], "Should mention safety restriction"
    
    print(f"✅ Safety check works: {result['error']}")
    print("✅ PASSED")


def test_clean_temp_files():
    """Test temp files cleanup."""
    print("\n" + "="*60)
    print("TEST: clean_temp_files()")
    print("="*60)
    
    result = clean_temp_files()
    
    assert "target_folder" in result, "Missing target_folder"
    assert "file_count" in result, "Missing file_count"
    
    print(f"✅ Target Folder: {result['target_folder']}")
    print(f"✅ Files Found: {result['file_count']}")
    print("✅ PASSED")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("PHASE 6 DIAGNOSTICS TEST SUITE")
    print("="*60)
    
    tests = [
        test_cpu_usage,
        test_ram_usage,
        test_disk_usage,
        test_system_health,
        test_disk_alerts,
        test_health_alerts,
        test_cleanup_scan,
        test_cleanup_safety,
        test_clean_temp_files,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️ {failed} test(s) failed")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
