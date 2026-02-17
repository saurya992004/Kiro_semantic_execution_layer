# Phase 6 Implementation Walkthrough — Diagnostics & Self-Healing

## Overview

Successfully implemented Phase 6 of the JARVIS AI automation agent, adding comprehensive system monitoring and automated maintenance capabilities with agent-callable architecture.

---

## What Was Implemented

### 1. Core Diagnostics Module ([diagnostics_tools.py](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tools/diagnostics_tools.py))

Created comprehensive diagnostic tools with **all functions returning data structures** for agent consumption:

**System Monitoring:**
- [get_cpu_usage()](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tools/diagnostics_tools.py#11-39) - CPU metrics with per-core breakdown
- [get_ram_usage()](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tools/diagnostics_tools.py#41-70) - Memory usage statistics
- [get_disk_usage()](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tools/diagnostics_tools.py#72-114) - Disk space information
- [get_system_health()](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tools/diagnostics_tools.py#116-134) - Combined health check

**Disk Analysis:**
- [analyze_disk_usage()](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tools/diagnostics_tools.py#140-227) - Folder size breakdown
- [find_large_folders()](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tools/diagnostics_tools.py#255-304) - Detect folders over threshold
- [get_disk_alerts()](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tools/diagnostics_tools.py#306-368) - Automatic warnings (80%) and critical alerts (90%)

**Automated Maintenance:**
- [scan_cleanup_files()](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tools/diagnostics_tools.py#374-455) - Scan files for cleanup (does NOT delete)
- [execute_cleanup()](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tools/diagnostics_tools.py#457-500) - Delete files after confirmation
- [clean_temp_files()](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tools/diagnostics_tools.py#502-513) - Scan temp files
- [clean_old_files()](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tools/diagnostics_tools.py#515-590) - Find files older than N days

**Health Alerts:**
- [check_health_alerts()](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tools/diagnostics_tools.py#617-694) - Comprehensive system health status

### 2. System Monitor Utility ([system_monitor.py](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/utils/system_monitor.py))

Background monitoring system with:
- Thread-safe continuous monitoring
- Historical data tracking (up to 7 days)
- Statistical analysis (avg, min, max)
- JSON-based persistent storage
- Singleton pattern for easy access

### 3. Router Integration

Updated [intent_router.py](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/router/intent_router.py) with four new intents:
- `diagnostics` - System monitoring commands
- `disk_analysis` - Disk usage analysis
- `maintenance` - File cleanup operations
- `health_check` - Health alert checking

All intents format returned data for user-friendly display.

### 4. Test Infrastructure

**Test Folder Structure:**
```
test_cleanup/
├── temp_files/
│   ├── test1.tmp
│   ├── test2.tmp
│   └── test3.log
├── old_files/
│   ├── old_doc1.txt
│   └── old_doc2.txt
└── large_files/
    └── large_test.bin (1MB)
```

**Test Script ([tests/test_diagnostics.py](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tests/test_diagnostics.py)):**
- 9 comprehensive tests
- Validates all function return types
- Tests safety restrictions
- Verifies data accuracy

### 5. Documentation

Created [README_PHASES/PHASE_6.md](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/README_PHASES/PHASE_6.md) with:
- Feature overview
- Complete function reference with return types
- Architecture decisions
- Testing guide
- Integration instructions for central agent

---

## Key Architecture Decisions

### Agent-Callable Design

**All functions return data structures instead of printing:**

```python
# Example: get_cpu_usage()
{
    "cpu_percent": 45.2,
    "cpu_count": 8,
    "per_cpu": [42.1, 48.3, ...]
}
```

**Benefits:**
- Central agent can process data programmatically
- Easy to test and validate
- Flexible presentation layer
- LLM-independent

### LLM Client Separation

- Zero dependency on Gemini or any specific LLM
- Pure Python functions with clear interfaces
- Can be called by any agent system
- Easy to swap LLM clients

### Safety-First Cleanup

**Two-step process:**
1. **Scan**: [scan_cleanup_files()](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tools/diagnostics_tools.py#374-455) returns list of files
2. **Confirm**: User reviews list
3. **Execute**: [execute_cleanup()](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tools/diagnostics_tools.py#457-500) deletes files

**Test folder restriction:**
- All cleanup paths validated with [_is_safe_cleanup_path()](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tools/diagnostics_tools.py#592-611)
- Only paths containing "test_cleanup" allowed
- Prevents accidental data loss during development

---

## Testing Results

### Test Suite Results

Ran `python tests\test_diagnostics.py`:

```
✅ test_cpu_usage() - PASSED
✅ test_ram_usage() - PASSED
✅ test_disk_usage() - PASSED
✅ test_system_health() - PASSED
✅ test_disk_alerts() - PASSED
✅ test_health_alerts() - PASSED
✅ test_cleanup_scan() - PASSED
✅ test_cleanup_safety() - PASSED
✅ test_clean_temp_files() - PASSED

🎉 ALL TESTS PASSED! (9/9)
```

### Manual Verification

**System Monitoring:**
- ✅ CPU usage returns accurate percentage
- ✅ RAM usage shows correct GB values
- ✅ Disk usage reports accurate space info
- ✅ System health combines all metrics

**Disk Analysis:**
- ✅ Folder analysis calculates sizes correctly
- ✅ Large folder detection works with thresholds
- ✅ Disk alerts trigger at 80% and 90%

**Cleanup Safety:**
- ✅ Scan returns file list without deleting
- ✅ Safety check rejects paths outside test_cleanup
- ✅ Error messages are clear and helpful

**Health Alerts:**
- ✅ Correctly identifies CPU/RAM/disk issues
- ✅ Severity levels (info/warning/critical) work
- ✅ Overall status reflects worst issue

---

## Integration with Existing System

### Router Integration

The router now handles diagnostic commands:

```python
# Example: "Check my CPU usage"
{
    "intent": "diagnostics",
    "action": "check_cpu",
    "parameters": {}
}
→ Calls get_cpu_usage()
→ Formats and displays result
```

### Backward Compatibility

- ✅ No changes to existing intents
- ✅ All Phase 1-5 features still work
- ✅ No breaking changes to router interface

---

## Files Created/Modified

### New Files

| File | Purpose |
|------|---------|
| [tools/diagnostics_tools.py](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tools/diagnostics_tools.py) | All diagnostic functions (600+ lines) |
| [utils/system_monitor.py](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/utils/system_monitor.py) | Background monitoring utility |
| [tests/test_diagnostics.py](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tests/test_diagnostics.py) | Comprehensive test suite |
| [README_PHASES/PHASE_6.md](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/README_PHASES/PHASE_6.md) | Complete documentation |
| [test_cleanup/](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tests/test_diagnostics.py#150-167) | Test folder structure with test files |

### Modified Files

| File | Changes |
|------|---------|
| [router/intent_router.py](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/router/intent_router.py) | Added 4 new intents with handlers |

---

## Usage Examples

### Example 1: Check System Health

**User Command:** "Give me a full health check"

**LLM Parses to:**
```json
{
    "intent": "diagnostics",
    "action": "full_health_check",
    "parameters": {}
}
```

**Function Called:** [get_system_health()](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tools/diagnostics_tools.py#116-134)

**Returns:**
```python
{
    "cpu": {"cpu_percent": 45.2, "cpu_count": 8, ...},
    "ram": {"percent": 62.3, "used_gb": 9.9, ...},
    "disk": {"percent": 75.1, "used_gb": 375.5, ...},
    "timestamp": "2026-02-17 16:15:30"
}
```

**Router Displays:**
```
🏥 System Health Check - 2026-02-17 16:15:30

CPU: 45.2%
RAM: 62.3% (9.9GB / 16.0GB)
Disk: 75.1% (375.5GB / 500.0GB)
```

### Example 2: Scan for Cleanup

**User Command:** "Scan temp files"

**Function Called:** [clean_temp_files()](file:///d:/Programming/Web%20Development/hackoclock%20project/JARVIS/tools/diagnostics_tools.py#502-513)

**Returns:**
```python
{
    "target_folder": "test_cleanup/temp_files",
    "files_to_delete": [
        {"path": "test1.tmp", "size_mb": 0.01, ...},
        {"path": "test2.tmp", "size_mb": 0.01, ...},
        {"path": "test3.log", "size_mb": 0.01, ...}
    ],
    "total_size_mb": 0.03,
    "file_count": 3
}
```

**Router Displays:**
```
🧹 Temp Files Scan: test_cleanup/temp_files
Files found: 3
Total size: 0.03MB

Files to delete:
  test_cleanup\temp_files\test1.tmp (0.01MB)
  test_cleanup\temp_files\test2.tmp (0.01MB)
  test_cleanup\temp_files\test3.log (0.01MB)

⚠️ Use 'confirm cleanup' to delete these files
```

### Example 3: Safety Check

**User Command:** "Clean files in C:\\"

**Function Called:** `scan_cleanup_files("C:\\")`

**Returns:**
```python
{
    "error": "Safety restriction: Can only clean files in 'test_cleanup' folder",
    "target_folder": "C:\\",
    "files_to_delete": [],
    "total_size_mb": 0.0,
    "file_count": 0
}
```

**Router Displays:**
```
Error: Safety restriction: Can only clean files in 'test_cleanup' folder
```

---

## Success Criteria Met

All Phase 6 success criteria achieved:

- ✅ All monitoring functions return accurate data structures
- ✅ Disk analysis correctly identifies and measures folders
- ✅ Cleanup functions scan and list files (test folder only)
- ✅ Cleanup requires explicit confirmation before deletion
- ✅ All functions are agent-callable (return data, not print)
- ✅ Safety validations prevent operations outside test folder
- ✅ Router successfully dispatches to diagnostic tools
- ✅ LLM correctly parses diagnostic commands (via existing system)
- ✅ All tests pass without errors (9/9)
- ✅ Documentation complete with return type specifications
- ✅ No crashes or unhandled exceptions

---

## Future Integration with Central Agent

When the central agent is implemented, it can:

**1. Call functions directly:**
```python
from tools.diagnostics_tools import get_system_health
health = get_system_health()
```

**2. Make decisions based on data:**
```python
if health["cpu"]["cpu_percent"] > 80:
    # Suggest closing applications
    # or alert user
```

**3. Chain operations:**
```python
# Scan → analyze → decide → execute
scan_result = scan_cleanup_files("test_cleanup")
if scan_result["total_size_mb"] > 100:
    # Ask for confirmation
    execute_cleanup(scan_result["files_to_delete"])
```

**4. Custom formatting:**
```python
# Format for different interfaces
# CLI, GUI, voice, etc.
```

---

## Lessons Learned

### What Went Well

1. **Agent-callable design** makes functions highly reusable
2. **Safety-first approach** prevents accidental data loss
3. **Comprehensive testing** caught issues early
4. **Clear documentation** makes integration easy

### Design Patterns Used

1. **Separation of concerns**: Tools vs. Router vs. Agent
2. **Data-driven architecture**: Functions return data, not strings
3. **Defensive programming**: Validate all inputs, handle all errors
4. **Test-driven development**: Tests written alongside code

---

## Next Steps

Phase 6 is complete and ready for integration with the central agent. The diagnostic tools are:

- ✅ Fully functional
- ✅ Well-tested
- ✅ Well-documented
- ✅ Agent-callable
- ✅ LLM-independent
- ✅ Safe and reliable

**Ready for Phase 7 or central agent integration!**
