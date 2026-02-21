import logging
from tools.app_tools import open_app
from tools.web_tools import search_web
from tools.system_tools import (
    shutdown_pc,
    restart_pc,
    sleep_pc,
    lock_pc,
    kill_process,
    clean_temp,
    empty_recycle_bin,
)
from tools.diagnostics_tools import (
    get_cpu_usage,
    get_ram_usage,
    get_disk_usage,
    get_system_health,
    get_complete_system_health,
    analyze_disk_usage,
    find_large_folders,
    get_disk_alerts,
    check_health_alerts,
    scan_cleanup_files,
    execute_cleanup,
    clean_temp_files,
    clean_old_files,
)
from troubleshooter.screenshot_tool import capture_screen_base64
from troubleshooter.vision_analyzer import VisionAnalyzer
from troubleshooter.solution_parser import parse_solution
from troubleshooter.auto_fix_engine import execute_fixes
from vision.vision_engine import run_vision_pipeline

# Setup logging
logger = logging.getLogger(__name__)

# ============================================================================
# INTENT ROUTER CONFIGURATION - VALID INTENTS & ACTIONS
# ============================================================================

VALID_INTENTS = {
    "help": {
        "actions": [],
        "description": "Show help information"
    },
    "open_app": {
        "actions": [],  # No sub-actions, just action=None
        "description": "Open applications or websites"
    },
    "web_search": {
        "actions": [],
        "description": "Search the web for information"
    },
    "system_control": {
        "actions": [
            "shutdown", "restart", "sleep", "lock",
            "kill_process", "clean_temp", "empty_recycle_bin"
        ],
        "description": "Control system operations"
    },
    "diagnostics": {
        "actions": [
            "check_cpu", "check_ram", "check_disk",
            "full_health_check", "complete_system_health"
        ],
        "description": "Run system diagnostics"
    },
    "disk_analysis": {
        "actions": [
            "analyze_usage", "find_large_folders", "check_alerts"
        ],
        "description": "Analyze disk usage and find large files"
    },
    "maintenance": {
        "actions": [
            "scan_temp", "scan_old_files", "scan_cleanup",
            "clean_temp_files", "clean_old_files"
        ],
        "description": "Perform system maintenance and cleanup"
    },
    "health_check": {
        "actions": [],
        "description": "Check overall system health and alerts"
    },
    "troubleshoot_screen": {
        "actions": [],
        "description": "Troubleshoot errors on screen using vision"
    },
    "vision_analysis": {
        "actions": ["analyze_screen", "detect_ui", "read_text"],
        "description": "Analyze screen content with vision"
    }
}


def _validate_intent(intent: str, action: str) -> tuple[bool, str]:
    """
    Validate if intent and action are legitimate.
    
    Returns:
        (is_valid, message)
    """
    if intent not in VALID_INTENTS:
        return False, f"Intent '{intent}' not recognized. Valid intents: {list(VALID_INTENTS.keys())}"
    
    valid_actions = VALID_INTENTS[intent]["actions"]
    if valid_actions and action and action not in valid_actions:
        return False, f"Action '{action}' not valid for intent '{intent}'. Valid actions: {valid_actions}"
    
    return True, "OK"


def _safe_execute(func, *args, **kwargs):
    """Safely execute a function with error handling."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_msg = f"❌ Error executing operation: {str(e)}"
        print(error_msg)
        logger.error(f"Execution error: {str(e)}", exc_info=True)
        return {"error": str(e), "message": error_msg}


def route_intent(command: dict):
    """
    Route command to appropriate handler.
    Validates intent and action before execution.
    """
    
    intent = command.get("intent", "").strip().lower()
    action = command.get("action", "").strip().lower() if command.get("action") else None
    params = command.get("parameters", {})
    
    # Validate intent and action
    is_valid, msg = _validate_intent(intent, action)
    if not is_valid:
        print(f"❌ Validation Error: {msg}")
        logger.warning(f"Invalid command: {msg}")
        return
    
    # Route to appropriate handler
    try:
        if intent == "help":
            _show_help()
        
        elif intent == "open_app":
            app_name = params.get("app_name", "").strip()
            if not app_name:
                print("❌ App name is required")
                return
            print(f"🚀 Opening app: {app_name}")
            open_app(app_name)
        
        elif intent == "web_search":
            query = params.get("query", "").strip()
            if not query:
                print("❌ Search query is required")
                return
            print(f"🔍 Searching web: {query}")
            search_web(query)
        
        elif intent == "system_control":
            _handle_system_control(action, params)
        
        elif intent == "diagnostics":
            _handle_diagnostics(action, params)
        
        elif intent == "disk_analysis":
            _handle_disk_analysis(action, params)
        
        elif intent == "maintenance":
            _handle_maintenance(action, params)
        
        elif intent == "health_check":
            _handle_health_check()
        
        elif intent == "troubleshoot_screen":
            _handle_troubleshoot_screen()
        
        elif intent == "vision_analysis":
            _handle_vision_analysis(action, params)
        
        else:
            print(f"❌ Intent '{intent}' handler not implemented")
    
    except Exception as e:
        print(f"❌ Unhandled error: {str(e)}")
        logger.error(f"Route intent error: {str(e)}", exc_info=True)


def _handle_system_control(action: str, params: dict):
    """Handle system control operations."""
    if action == "shutdown":
        print("⏹️  Shutting down system...")
        _safe_execute(shutdown_pc)
    
    elif action == "restart":
        print("🔄 Restarting system...")
        _safe_execute(restart_pc)
    
    elif action == "sleep":
        print("😴 Putting system to sleep...")
        _safe_execute(sleep_pc)
    
    elif action == "lock":
        print("🔒 Locking system...")
        _safe_execute(lock_pc)
    
    elif action == "kill_process":
        process_name = params.get("process_name", "").strip()
        if not process_name:
            print("❌ Process name is required")
            return
        print(f"🔪 Killing process: {process_name}")
        _safe_execute(kill_process, process_name)
    
    elif action == "clean_temp":
        print("🧹 Cleaning temp files...")
        _safe_execute(clean_temp)
    
    elif action == "empty_recycle_bin":
        print("🗑️  Emptying recycle bin...")
        _safe_execute(empty_recycle_bin)
    
    else:
        print(f"❌ Unknown system control action: {action}")


def _handle_diagnostics(action: str, params: dict):
    """Handle diagnostic operations."""
    if action == "check_cpu":
        result = _safe_execute(get_cpu_usage)
        if "error" not in result:
            print(f"\n🖥️  CPU USAGE")
            print(f"  ├─ Usage: {result.get('cpu_percent', 0)}%")
            print(f"  ├─ Cores: {result.get('cpu_count', 0)}")
            print(f"  └─ Per-Core: {result.get('per_cpu', [])}")
    
    elif action == "check_ram":
        result = _safe_execute(get_ram_usage)
        if "error" not in result:
            print(f"\n💾 RAM USAGE")
            print(f"  ├─ Usage: {result.get('percent', 0)}%")
            print(f"  ├─ Used: {result.get('used_gb', 0):.1f}GB")
            print(f"  └─ Total: {result.get('total_gb', 0):.1f}GB")
    
    elif action == "check_disk":
        drive = params.get("drive", "C:").upper()
        result = _safe_execute(get_disk_usage, drive)
        if "error" not in result:
            print(f"\n💿 DISK USAGE ({drive})")
            print(f"  ├─ Usage: {result.get('percent', 0)}%")
            print(f"  ├─ Used: {result.get('used_gb', 0):.1f}GB")
            print(f"  ├─ Total: {result.get('total_gb', 0):.1f}GB")
            print(f"  └─ Free: {result.get('free_gb', 0):.1f}GB")
    
    elif action == "complete_system_health" or action == "full_health_check":
        print("\n🏥 Running complete system health check...")
        result = _safe_execute(get_complete_system_health)
        if "error" not in result:
            print(result.get("health_summary", "No summary available"))
    
    else:
        print(f"❌ Unknown diagnostics action: {action}")


def _handle_disk_analysis(action: str, params: dict):
    """Handle disk analysis operations."""
    if action == "analyze_usage":
        path = params.get("path", "C:\\")
        result = _safe_execute(analyze_disk_usage, path)
        if "error" not in result:
            print(f"\n📊 DISK ANALYSIS: {result.get('path')}")
            print(f"Total Size: {result.get('total_size_gb', 0):.2f}GB\n")
            print("Top Folders:")
            for folder in result.get('folders', [])[:10]:
                print(f"  {folder.get('name')}: {folder.get('size_gb', 0):.2f}GB ({folder.get('percent_of_total', 0):.1f}%)")
    
    elif action == "find_large_folders":
        path = params.get("path", "C:\\")
        threshold = params.get("threshold_gb", 1.0)
        result = _safe_execute(find_large_folders, path, threshold)
        print(f"\n📁 LARGE FOLDERS (>{threshold}GB):")
        if result:
            for folder in result:
                print(f"  {folder.get('path')}: {folder.get('size_gb', 0):.2f}GB")
        else:
            print("  No large folders found")
    
    elif action == "check_alerts":
        result = _safe_execute(get_disk_alerts)
        if "error" not in result:
            print(f"\n⚠️  DISK ALERTS - {result.get('status', 'unknown').upper()}")
            if result.get('alerts'):
                for alert in result['alerts']:
                    icon = "🔴" if alert.get('level') == "critical" else "🟡"
                    print(f"  {icon} {alert.get('message')}")
            else:
                print("  ✅ All disks are healthy")
    
    else:
        print(f"❌ Unknown disk analysis action: {action}")


def _handle_maintenance(action: str, params: dict):
    """Handle maintenance operations."""
    if action == "scan_temp":
        result = _safe_execute(clean_temp_files)
        if "error" not in result:
            print(f"\n🧹 TEMP FILES SCAN")
            print(f"Target: {result.get('target_folder')}")
            print(f"Files found: {result.get('file_count', 0)}")
            print(f"Total size: {result.get('total_size_mb', 0):.2f}MB")
            if result.get('files_to_delete'):
                print("\nFiles to delete:")
                for file in result.get('files_to_delete', [])[:10]:
                    print(f"  {file.get('path')} ({file.get('size_mb', 0):.2f}MB)")
                print("\n⚠️  Use 'confirm cleanup' to delete these files")
    
    elif action == "scan_old_files":
        folder = params.get("folder", "test_cleanup/old_files")
        days = params.get("days", 30)
        result = _safe_execute(clean_old_files, folder, days)
        if "error" not in result:
            print(f"\n🗑️  OLD FILES SCAN")
            print(f"Target: {result.get('target_folder')}")
            print(f"Files older than {result.get('days_threshold', 0)} days: {result.get('file_count', 0)}")
            print(f"Total size: {result.get('total_size_mb', 0):.2f}MB")
            if result.get('files_to_delete'):
                print("\nFiles to delete:")
                for file in result.get('files_to_delete', [])[:10]:
                    days_old = file.get('days_old', 0)
                    size = file.get('size_mb', 0)
                    print(f"  {file.get('path')} ({days_old} days old, {size:.2f}MB)")
                print("\n⚠️  Use 'confirm cleanup' to delete these files")
    
    elif action == "scan_cleanup":
        folder = params.get("folder", "test_cleanup")
        result = _safe_execute(scan_cleanup_files, folder)
        if "error" not in result:
            print(f"\n🔍 CLEANUP SCAN: {result.get('target_folder')}")
            print(f"Files found: {result.get('file_count', 0)}")
            print(f"Total size: {result.get('total_size_mb', 0):.2f}MB")
    
    else:
        print(f"❌ Unknown maintenance action: {action}")


def _handle_health_check():
    """Handle health check operations."""
    result = _safe_execute(check_health_alerts)
    if "error" not in result:
        status = result.get('overall_status', 'unknown').upper()
        print(f"\n🏥 HEALTH CHECK - Overall Status: {status}")
        if result.get('alerts'):
            for alert in result['alerts']:
                severity = alert.get('severity', 'info')
                icon = "🔴" if severity == "critical" else "🟡" if severity == "warning" else "ℹ️"
                print(f"  {icon} [{alert.get('type', 'unknown').upper()}] {alert.get('message')}")
        else:
            print("  ✅ System is healthy")


def _handle_troubleshoot_screen():
    """Handle screen troubleshooting with vision."""
    print("\n📸 Capturing screenshot...")
    base64_image = _safe_execute(capture_screen_base64)
    if not base64_image or isinstance(base64_image, dict):
        print("❌ Failed to capture screen.")
        return
    
    print("🧠 Analyzing error with Groq Vision (this may take a few seconds)...")
    analyzer = VisionAnalyzer()
    raw_response = _safe_execute(analyzer.analyze_error, base64_image)
    
    if not raw_response or isinstance(raw_response, dict):
        print("❌ Failed to get response from Groq API.")
        return
    
    solution = _safe_execute(parse_solution, raw_response)
    if solution is None or (isinstance(solution, dict) and "error" in solution):
        print("❌ Failed to parse solution.")
        return
    
    print("\n💡 EXPLANATION:")
    print(solution.get("explanation", "No explanation provided."))
    
    commands = solution.get("commands", [])
    if commands:
        print("\n✅ Executing fixes...")
        _safe_execute(execute_fixes, commands)
    else:
        print("\n✅ No automated commands needed to fix this issue.")


def _handle_vision_analysis(action: str, params: dict):
    """Handle vision analysis operations using Gemini Vision."""
    if action == "analyze_screen":
        query = params.get("query", "Describe what you see on screen. List all visible buttons, text, options, and UI elements.")
        print(f"🧠 Analyzing screen with Gemini Vision (this may take a few seconds)...")
        
        result = _safe_execute(run_vision_pipeline, user_query=query)
        
        if isinstance(result, dict) and result.get("error"):
            print(f"❌ Vision analysis failed: {result.get('error')}")
            return
        
        if not result.get("success"):
            print(f"❌ Vision analysis failed: {result.get('error', 'Unknown error')}")
            return
        
        analysis = result.get("analysis", {})
        
        # Display results
        print("\n📋 SCREEN ANALYSIS:")
        print(f"  Summary: {analysis.get('screen_summary', 'N/A')}")
        print(f"  App/Window: {analysis.get('window_title_or_app', 'N/A')}")
        
        buttons = analysis.get("detected_buttons", [])
        if buttons:
            print("\n  🔘 Buttons detected:")
            for btn in buttons:
                print(f"     • {btn.get('label')} ({btn.get('context', 'N/A')})")
                if btn.get('action_hint'):
                    print(f"       → {btn.get('action_hint')}")
        
        options = analysis.get("detected_options", [])
        if options:
            print("\n  ⚙️  Options/UI Elements detected:")
            for opt in options:
                print(f"     • {opt.get('label')} [{opt.get('type', 'unknown')}]")
        
        text_regions = analysis.get("visible_text_regions", [])
        if text_regions:
            print("\n  📝 Text detected:")
            for text in text_regions:
                print(f"     • {text.get('text', 'N/A')} ({text.get('role', 'body')})")
        
        errors = analysis.get("possible_errors_or_alerts", [])
        if errors:
            print("\n  ⚠️  Alerts/Errors detected:")
            for err in errors:
                severity = err.get('severity', 'unknown')
                icon = "🔴" if severity == "error" else "🟡" if severity == "warning" else "ℹ️"
                print(f"     {icon} {err.get('text', 'N/A')} [{severity}]")
        
        access_hints = analysis.get("accessibility_hints", "")
        if access_hints:
            print(f"\n  ♿ Accessibility hints: {access_hints}")
        
        json_path = result.get("json_path")
        screenshot_path = result.get("screenshot_path")
        print(f"\n  ✅ Analysis saved to: {json_path}")
        print(f"  📸 Screenshot saved to: {screenshot_path}")
    
    elif action == "detect_ui":
        print("🎯 Detecting UI elements...")
        query = "List all clickable UI elements, buttons, text fields, checkboxes, radio buttons, menus, and interactive controls."
        
        result = _safe_execute(run_vision_pipeline, user_query=query)
        
        if isinstance(result, dict) and result.get("error"):
            print(f"❌ UI detection failed: {result.get('error')}")
            return
        
        if not result.get("success"):
            print(f"❌ UI detection failed")
            return
        
        analysis = result.get("analysis", {})
        
        print("\n🎯 DETECTED UI ELEMENTS:")
        
        buttons = analysis.get("detected_buttons", [])
        if buttons:
            print(f"\n  Buttons ({len(buttons)}):")
            for btn in buttons:
                print(f"    • {btn.get('label')}")
        
        options = analysis.get("detected_options", [])
        if options:
            print(f"\n  Interactive Elements ({len(options)}):")
            for opt in options:
                print(f"    • {opt.get('label')} ({opt.get('type')})")
        
        access = analysis.get("accessibility_hints", "")
        if access:
            print(f"\n  Accessibility: {access}")
    
    elif action == "read_text":
        print("📝 Reading text from screen...")
        query = "Extract and list all readable text visible on the screen, organized by context (headings, body text, labels, buttons, etc.)"
        
        result = _safe_execute(run_vision_pipeline, user_query=query)
        
        if isinstance(result, dict) and result.get("error"):
            print(f"❌ Text reading failed: {result.get('error')}")
            return
        
        if not result.get("success"):
            print(f"❌ Text reading failed")
            return
        
        analysis = result.get("analysis", {})
        
        print("\n📝 TEXT DETECTED:")
        
        text_regions = analysis.get("visible_text_regions", [])
        if text_regions:
            for text in text_regions:
                role = text.get('role', 'body')
                print(f"  [{role.upper()}] {text.get('text')}")
        else:
            print("  No text detected")
    
    else:
        print(f"❌ Unknown vision analysis action: {action}")


def _show_help():
    """Display help information."""
    help_text = """
╔═══════════════════════════════════════════════════════════════╗
║                    🤖 JARVIS COMMAND HELP                    ║
╚═══════════════════════════════════════════════════════════════╝

📱 APPLICATION COMMANDS:
  • open chrome, open notepad, open vscode, launch ms word
  • search python, search how to code, search tutorial

🖥️  SYSTEM CONTROL:
  • shutdown, restart, sleep, lock system
  • kill chrome (close a process)
  • clean temp files, empty recycle bin

🏥 DIAGNOSTICS & HEALTH:
  • check cpu, check ram, check disk
  • complete system health (comprehensive report)
  • system health (same as above)
  • health check (show alerts and warnings)

💾 DISK MANAGEMENT:
  • analyze disk usage
  • find large folders
  • check disk alerts

🧹 MAINTENANCE & CLEANUP:
  • scan temp files
  • scan old files
  • scan cleanup folder

🔍 TROUBLESHOOTING:
  • troubleshoot screen (capture and analyze errors)
  • fix errors (automated error detection)

👁️  SCREEN ANALYSIS:
  • analyze screen
  • detect ui elements
  • read text from screen

ℹ️  OTHER:
  • help (show this message)
  • Type any of the above commands or variations

═══════════════════════════════════════════════════════════════
"""
    print(help_text)
