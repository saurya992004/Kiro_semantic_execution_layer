"""
Quick demo of Phase 6 diagnostic functions.
Run with: python demo_phase6.py
"""

from tools.diagnostics_tools import (
    get_cpu_usage,
    get_ram_usage,
    get_disk_usage,
    get_system_health,
    check_health_alerts,
    scan_cleanup_files,
)

print("="*60)
print("PHASE 6 DIAGNOSTICS DEMO")
print("="*60)

# 1. CPU Usage
print("\n1. CPU Usage:")
cpu = get_cpu_usage()
print(f"   CPU: {cpu['cpu_percent']}%")
print(f"   Cores: {cpu['cpu_count']}")

# 2. RAM Usage
print("\n2. RAM Usage:")
ram = get_ram_usage()
print(f"   Used: {ram['used_gb']}GB / {ram['total_gb']}GB")
print(f"   Usage: {ram['percent']}%")

# 3. Disk Usage
print("\n3. Disk Usage:")
disk = get_disk_usage("C:")
print(f"   Used: {disk['used_gb']}GB / {disk['total_gb']}GB")
print(f"   Usage: {disk['percent']}%")

# 4. System Health
print("\n4. System Health Check:")
health = get_system_health()
print(f"   Timestamp: {health['timestamp']}")
print(f"   CPU: {health['cpu']['cpu_percent']}%")
print(f"   RAM: {health['ram']['percent']}%")
print(f"   Disk: {health['disk']['percent']}%")

# 5. Health Alerts
print("\n5. Health Alerts:")
alerts = check_health_alerts()
print(f"   Status: {alerts['overall_status'].upper()}")
if alerts['alerts']:
    for alert in alerts['alerts']:
        print(f"   - [{alert['severity']}] {alert['message']}")
else:
    print("   ✅ System is healthy!")

# 6. Cleanup Scan (Safe)
print("\n6. Cleanup Scan (Test Folder):")
cleanup = scan_cleanup_files("test_cleanup")
if "error" not in cleanup:
    print(f"   Files found: {cleanup['file_count']}")
    print(f"   Total size: {cleanup['total_size_mb']}MB")
else:
    print(f"   {cleanup['error']}")

print("\n" + "="*60)
print("✅ All diagnostic functions working!")
print("="*60)
