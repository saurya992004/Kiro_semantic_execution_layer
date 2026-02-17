# Phase 6 — Diagnostics & Self-Healing

**Owner**: System Monitoring Engineer

**Status**: ✅ Implemented

---

## Overview

Phase 6 adds comprehensive system monitoring and automated maintenance capabilities to JARVIS. All functions are designed to be **agent-callable**, returning data structures that can be processed by the central agent.

---

## Features Implemented

### 1. System Monitoring

Monitor real-time system metrics:

- **CPU Usage**: Overall and per-core CPU utilization
- **RAM Usage**: Memory consumption and availability
- **Disk Usage**: Storage space for all drives
- **System Health**: Combined health check of all metrics

**Example Commands:**

- "Check my CPU usage"
- "How much RAM am I using?"
- "Show disk space"
- "Give me a full health check"

### 2. Disk Analysis

Analyze disk usage and identify large folders:

- **Disk Usage Analysis**: Breakdown by top-level folders
- **Large Folder Detection**: Find folders exceeding size threshold
- **Disk Alerts**: Automatic warnings at 80% and critical alerts at 90%

**Example Commands:**

- "Analyze my disk usage"
- "Find large folders"
- "Check disk alerts"

### 3. Automated Maintenance

Safe file cleanup with explicit confirmation:

- **Temp File Scanning**: Identify temporary files for cleanup
- **Old File Detection**: Find files older than N days
- **Interactive Cleanup**: Two-step process (scan → confirm → delete)
- **Test Folder Safety**: All cleanup restricted to `test_cleanup/` folder

**Example Commands:**

- "Scan temp files"
- "Find old files"
- "Clean test folder"

### 4. Health Alerts

Intelligent system health monitoring:

- **CPU Alerts**: Warning at 75%, critical at 90%
- **RAM Alerts**: Warning at 80%, critical at 90%
- **Disk Alerts**: Warning at 80%, critical at 90%
- **Overall Status**: Healthy, warning, or critical

**Example Commands:**

- "Check system health"
- "Show health alerts"

### 5. Background Monitoring (Advanced)

Continuous system monitoring with historical data:

- **SystemMonitor Class**: Thread-safe background monitoring
- **Historical Data**: Track metrics over time (up to 7 days)
- **Statistical Analysis**: Average, min, max over time periods
- **JSON Logging**: Persistent storage of metrics

---

## Architecture

### Agent-Callable Design

All functions return data structures instead of printing directly:

```python
# Example: get_cpu_usage()
{
    "cpu_percent": 45.2,
    "cpu_count": 8,
    "per_cpu": [42.1, 48.3, 44.5, ...]
}

# Example: get_ram_usage()
{
    "total_gb": 16.0,
    "used_gb": 8.5,
    "available_gb": 7.5,
    "percent": 53.1
}
```

This allows the central agent to:

- Process data programmatically
- Format output as needed
- Make decisions based on metrics
- Chain multiple operations

### LLM Client Separation

Diagnostic tools are completely independent:

- No direct dependency on Gemini or any LLM
- Can be called by any agent system
- Pure Python functions with clear interfaces
- Easy to test and maintain

### Safety Architecture

**Cleanup Safety:**

- Two-step process: scan first, delete after confirmation
- Test folder restriction: `_is_safe_cleanup_path()` validates all paths
- Detailed file lists: User sees exactly what will be deleted
- Error handling: Failed deletions logged, don't crash system

**Data Validation:**

- Drive letters validated before disk operations
- Paths validated before folder scanning
- Thresholds validated (positive numbers)
- Graceful error messages for invalid inputs

---

## File Structure

```
tools/
└── diagnostics_tools.py      # All diagnostic functions

utils/
└── system_monitor.py          # Background monitoring utility

test_cleanup/                  # Safe testing folder
├── temp_files/
│   ├── test1.tmp
│   ├── test2.tmp
│   └── test3.log
├── old_files/
│   ├── old_doc1.txt
│   └── old_doc2.txt
└── large_files/
    └── large_test.bin
```

---

## Function Reference

### System Monitoring

#### `get_cpu_usage() -> dict`

Returns current CPU usage metrics.

**Returns:**

```python
{
    "cpu_percent": float,  # Overall CPU usage
    "cpu_count": int,      # Number of cores
    "per_cpu": list        # Usage per core
}
```

#### `get_ram_usage() -> dict`

Returns RAM usage metrics.

**Returns:**

```python
{
    "total_gb": float,
    "used_gb": float,
    "available_gb": float,
    "percent": float
}
```

#### `get_disk_usage(drive: str = "C:") -> dict`

Returns disk space info for specified drive.

**Args:**

- `drive`: Drive letter (default "C:")

**Returns:**

```python
{
    "drive": str,
    "total_gb": float,
    "used_gb": float,
    "free_gb": float,
    "percent": float
}
```

#### `get_system_health() -> dict`

Comprehensive health check combining all metrics.

**Returns:**

```python
{
    "cpu": dict,        # from get_cpu_usage()
    "ram": dict,        # from get_ram_usage()
    "disk": dict,       # from get_disk_usage()
    "timestamp": str
}
```

### Disk Analysis

#### `analyze_disk_usage(path: str = "C:\\") -> dict`

Detailed breakdown of disk usage by top-level folders.

**Args:**

- `path`: Path to analyze

**Returns:**

```python
{
    "path": str,
    "total_size_gb": float,
    "folders": [
        {
            "name": str,
            "size_gb": float,
            "percent_of_total": float
        },
        ...
    ]
}
```

#### `find_large_folders(path: str = "C:\\", threshold_gb: float = 1.0) -> list`

Find folders exceeding size threshold.

**Args:**

- `path`: Path to search
- `threshold_gb`: Minimum folder size in GB

**Returns:**

```python
[
    {
        "path": str,
        "size_gb": float
    },
    ...
]
```

#### `get_disk_alerts() -> dict`

Check if disk usage exceeds warning thresholds.

**Returns:**

```python
{
    "status": str,  # "ok", "warning", "critical"
    "alerts": [
        {
            "drive": str,
            "percent": float,
            "level": str,
            "message": str
        },
        ...
    ]
}
```

### Automated Maintenance

#### `scan_cleanup_files(target_folder: str) -> dict`

Scan for files to clean up. **DOES NOT DELETE**.

**Args:**

- `target_folder`: Folder to scan (must contain "test_cleanup")

**Returns:**

```python
{
    "target_folder": str,
    "files_to_delete": [
        {
            "path": str,
            "size_mb": float,
            "modified_date": str
        },
        ...
    ],
    "total_size_mb": float,
    "file_count": int
}
```

#### `execute_cleanup(file_list: list) -> dict`

Execute cleanup after user confirmation.

**Args:**

- `file_list`: List of file paths to delete

**Returns:**

```python
{
    "deleted_count": int,
    "failed_count": int,
    "total_size_freed_mb": float,
    "errors": [str, ...]
}
```

#### `clean_temp_files() -> dict`

Scan temp files in `test_cleanup/temp_files/`. Returns scan results.

#### `clean_old_files(folder: str, days_old: int = 30) -> dict`

Scan for files older than N days. Returns scan results.

### Health Alerts

#### `check_health_alerts() -> dict`

Returns list of current system issues.

**Returns:**

```python
{
    "alerts": [
        {
            "type": str,       # "cpu", "ram", "disk"
            "severity": str,   # "info", "warning", "critical"
            "message": str
        },
        ...
    ],
    "overall_status": str  # "healthy", "warning", "critical"
}
```

---

## Router Integration

### Intents Added

**1. `diagnostics`**

- Actions: `check_cpu`, `check_ram`, `check_disk`, `full_health_check`

**2. `disk_analysis`**

- Actions: `analyze_usage`, `find_large_folders`, `check_alerts`

**3. `maintenance`**

- Actions: `scan_temp`, `scan_old_files`, `scan_cleanup`

**4. `health_check`**

- Returns comprehensive health alerts

---

## Testing Guide

### Manual Testing

1. **Test System Monitoring:**

   ```bash
   python main.py
   ```

   Commands:
   - "Check my CPU usage"
   - "How much RAM am I using?"
   - "Show disk space"

2. **Test Disk Analysis:**
   - "Analyze my disk usage"
   - "Find large folders"

3. **Test Cleanup (Safe):**
   - "Scan temp files"
   - Files are listed but NOT deleted

4. **Test Safety:**
   - Try to clean outside test folder
   - Should be rejected with safety error

### Unit Testing

Run the test script:

```bash
python tests/test_diagnostics.py
```

---

## Safety Considerations

### Cleanup Safety

- ✅ Two-step process (scan → confirm → delete)
- ✅ Test folder restriction enforced
- ✅ Detailed file lists before deletion
- ✅ Error handling for failed deletions

### Data Protection

- ✅ Never delete without explicit user command
- ✅ All paths validated before operations
- ✅ Graceful error messages
- ✅ No system-critical operations

---

## Future Enhancements

1. **Predictive Maintenance**: Use historical data to predict failures
2. **Network Diagnostics**: Monitor network usage and connectivity
3. **Temperature Monitoring**: Track CPU/GPU temperatures
4. **Smart Alerts**: Push notifications for critical issues
5. **Scheduled Reports**: Daily/weekly system health reports

---

## Dependencies

- `psutil`: System metrics and monitoring

No additional dependencies required for Phase 6 core features.

---

## Integration with Central Agent

When the central agent is implemented, it can:

1. **Call functions directly:**

   ```python
   from tools.diagnostics_tools import get_system_health
   health = get_system_health()
   ```

2. **Process returned data:**

   ```python
   if health["cpu"]["cpu_percent"] > 80:
       # Take action
   ```

3. **Format output as needed:**

   ```python
   # Custom formatting for different interfaces
   # (CLI, GUI, voice, etc.)
   ```

4. **Chain operations:**
   ```python
   # Scan → analyze → decide → execute
   scan_result = scan_cleanup_files("test_cleanup")
   if scan_result["total_size_mb"] > 100:
       # Ask for confirmation
       execute_cleanup(scan_result["files_to_delete"])
   ```

---

## Success Criteria

Phase 6 is complete when:

- ✅ All monitoring functions return accurate data
- ✅ Disk analysis correctly identifies and measures folders
- ✅ Cleanup functions scan and list files (test folder only)
- ✅ Cleanup requires explicit confirmation before deletion
- ✅ All functions are agent-callable (return data, not print)
- ✅ Safety validations prevent operations outside test folder
- ✅ Router successfully dispatches to diagnostic tools
- ✅ All tests pass without errors
- ✅ Documentation complete with return type specifications
