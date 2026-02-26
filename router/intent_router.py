import logging
import os
from tools.app_tools import open_app
from tools.web_tools import search_web
from tools.system_tools import (
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
from personalisation.personalisation_tools import (
    toggle_dark_mode,
    set_accent_color,
    set_display_brightness,
    set_wallpaper,
    apply_theme_preset,
    save_personalization_profile,
    load_personalization_profile,
    manage_startup_apps,
    set_default_app,
    get_current_theme
)
from file_manager import FileManager
from tools.system_config import get_system_config, print_system_config
from installer.installer import InstallerAgent

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
            "sleep", "lock",
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
    },
    "personalization": {
        "actions": [
            "toggle_dark_mode", "set_accent_color", "set_brightness",
            "set_wallpaper", "set_resolution", "apply_preset",
            "save_profile", "load_profile", "manage_startup", "set_default_app"
        ],
        "description": "Customize system appearance and settings"
    },
    "file_management": {
        "actions": [
            "organize_by_type", "find_duplicates", "remove_duplicates",
            "find_large_files", "analyze_folder", "get_report"
        ],
        "description": "Organize files, find duplicates, and scan for large files"
    },
    "system_config": {
        "actions": [],
        "description": "Get system configuration and hardware information"
    },
    "installer": {
        "actions": [
            "install_software", "download_wallpaper", "download_software", "download_resource",
            "execute_installer", "cache_info", "clear_cache"
        ],
        "description": "Download and install resources from the internet (uses winget for software)"
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
        
        elif intent == "personalization":
            _handle_personalization(action, params)
        
        elif intent == "file_management":
            _handle_file_management(action, params)
        
        elif intent == "system_config":
            _handle_system_config()
        
        elif intent == "installer":
            _handle_installer(action, params)
        
        else:
            print(f"❌ Intent '{intent}' handler not implemented")
    
    except Exception as e:
        print(f"❌ Unhandled error: {str(e)}")
        logger.error(f"Route intent error: {str(e)}", exc_info=True)


def _handle_system_control(action: str, params: dict):
    """Handle system control operations."""
    if action == "sleep":
        print("😴 About to put system to sleep...")
        confirm = input("⚠️  Are you sure you want to sleep the PC? (y/n): ").strip().lower()
        if confirm not in ("y", "yes"):
            print("❌ Sleep cancelled.")
            return
        _safe_execute(sleep_pc)
    
    elif action == "lock":
        print("🔒 About to lock the system...")
        confirm = input("⚠️  Are you sure you want to lock the PC? (y/n): ").strip().lower()
        if confirm not in ("y", "yes"):
            print("❌ Lock cancelled.")
            return
        _safe_execute(lock_pc)
    
    elif action == "kill_process":
        process_name = params.get("process_name", "").strip()
        if not process_name:
            print("❌ Process name is required")
            return
        confirm = input(f"⚠️  Kill process '{process_name}'? This may lose unsaved work. (y/n): ").strip().lower()
        if confirm not in ("y", "yes"):
            print("❌ Kill process cancelled.")
            return
        print(f"🔪 Killing process: {process_name}")
        _safe_execute(kill_process, process_name)
    
    elif action == "clean_temp":
        print("🧹 Cleaning temp files...")
        _safe_execute(clean_temp)
    
    elif action == "empty_recycle_bin":
        confirm = input("⚠️  Empty the Recycle Bin? This cannot be undone. (y/n): ").strip().lower()
        if confirm not in ("y", "yes"):
            print("❌ Empty recycle bin cancelled.")
            return
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
        days = params.get("days", 1)  # 1 day for demo
        result = _safe_execute(clean_old_files, folder, days)
        if "error" not in result:
            print(f"\n🗑️  OLD FILES SCAN")
            print(f"Scanning: {result.get('target_folder')}")
            threshold = result.get('days_threshold', 0)
            count = result.get('file_count', 0)
            print(f"Files older than {threshold} day(s): {count}")
            print(f"Total size: {result.get('total_size_mb', 0):.2f}MB")
            if result.get('files_to_delete'):
                print("\n📋 Files found:")
                for file in result.get('files_to_delete', [])[:10]:
                    days_old = file.get('days_old', 0)
                    size = file.get('size_mb', 0)
                    modified = file.get('modified_date', 'unknown')
                    print(f"  • {os.path.basename(file.get('path'))} ({days_old}d old | {size:.2f}MB | {modified})")
                if count > 10:
                    print(f"  ... and {count - 10} more files")
                print("\n⚠️  Use 'confirm cleanup' to delete these files")
            else:
                print("✅ No old files found")
    
    elif action == "scan_cleanup":
        folder = params.get("folder", "test_cleanup")
        result = _safe_execute(scan_cleanup_files, folder)
        if "error" not in result:
            print(f"\n🔍 CLEANUP SCAN")
            print(f"Scanning: {result.get('target_folder')}")
            count = result.get('file_count', 0)
            print(f"Files found: {count}")
            print(f"Total size: {result.get('total_size_mb', 0):.2f}MB")
            if result.get('files_to_delete'):
                print("\n📋 Cleanup candidates:")
                for file in result.get('files_to_delete', [])[:15]:
                    size = file.get('size_mb', 0)
                    modified = file.get('modified_date', 'unknown')
                    print(f"  • {os.path.basename(file.get('path'))} ({size:.2f}MB | {modified})")
                if count > 15:
                    print(f"  ... and {count - 15} more files")
                print(f"\n💾 Total recoverable: {result.get('total_size_mb', 0):.2f}MB")
                print("⚠️  Use 'confirm cleanup' to delete these files")
    
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
    """Display help information using consolidated help commands."""
    from tools.help_commands import print_help
    print_help()


def _handle_personalization(action: str, params: dict):
    """Handle system personalization operations."""
    
    if action == "toggle_dark_mode":
        enable = params.get("enable", True)
        print(f"🌙 Toggling dark mode...")
        result = _safe_execute(toggle_dark_mode, enable)
        if result.get("success"):
            print(f"   {result['message']}")
        else:
            print(f"   {result['message']}")
    
    elif action == "set_accent_color":
        color = params.get("color", "").strip()
        if not color:
            print("❌ Color code is required (e.g., 0066CC)")
            return
        print(f"🎨 Setting accent color to {color}...")
        result = _safe_execute(set_accent_color, color)
        if result.get("success"):
            print(f"   {result['message']}")
        else:
            print(f"   {result['message']}")
    
    elif action == "set_brightness":
        brightness = params.get("brightness")
        if brightness is None:
            print("❌ Brightness value is required (0-100)")
            return
        try:
            brightness = int(brightness)
            if not (0 <= brightness <= 100):
                print("❌ Brightness must be between 0 and 100")
                return
        except (ValueError, TypeError):
            print("❌ Invalid brightness value")
            return
        
        print(f"☀️  Setting brightness to {brightness}%...")
        result = _safe_execute(set_display_brightness, brightness)
        if result.get("success"):
            print(f"   {result['message']}")
        else:
            print(f"   {result['message']}")
    
    elif action == "set_wallpaper":
        path = params.get("path", "").strip()
        if not path:
            print("❌ Image path is required")
            return
        print(f"🖼️  Setting wallpaper to {path}...")
        result = _safe_execute(set_wallpaper, path)
        if result.get("success"):
            print(f"   {result['message']}")
        else:
            print(f"   {result['message']}")
    
    elif action == "set_resolution":
        width = params.get("width")
        height = params.get("height")
        if not width or not height:
            print("❌ Width and height are required")
            return
        try:
            width, height = int(width), int(height)
        except (ValueError, TypeError):
            print("❌ Invalid resolution values")
            return
        
        print(f"📺 Setting resolution to {width}x{height}...")
        result = _safe_execute(set_display_brightness, width, height)
        if result.get("success"):
            print(f"   {result['message']}")
        else:
            print(f"   {result['message']}")
    
    elif action == "apply_preset":
        preset = params.get("preset", "").strip().lower()
        if not preset:
            print("❌ Preset name is required (dark, light, office, gaming, minimal)")
            return
        
        print(f"✨ Applying '{preset}' theme preset...")
        result = _safe_execute(apply_theme_preset, preset)
        
        if result.get("success"):
            print(f"   {result['message']}")
            print(f"   Description: {result.get('description')}")
        else:
            print(f"   {result['message']}")
    
    elif action == "save_profile":
        name = params.get("name", "").strip()
        if not name:
            print("❌ Profile name is required")
            return
        
        profile_settings = {
            "name": name,
            "dark_mode": params.get("dark_mode", True),
            "accent_color": params.get("accent_color", "0066CC"),
            "brightness": params.get("brightness", 50),
            "description": params.get("description", "Custom profile")
        }
        
        print(f"💾 Saving profile '{name}'...")
        result = _safe_execute(save_personalization_profile, name, profile_settings)
        if result.get("success"):
            print(f"   {result['message']}")
        else:
            print(f"   {result['message']}")
    
    elif action == "load_profile":
        name = params.get("name", "").strip()
        if not name:
            print("❌ Profile name is required")
            return
        
        print(f"📂 Loading profile '{name}'...")
        result = _safe_execute(load_personalization_profile, name)
        
        if result.get("success"):
            print(f"   {result['message']}")
            settings = result.get("settings", {})
            print(f"   Loaded settings: {settings}")
        else:
            print(f"   {result['message']}")
    
    elif action == "manage_startup":
        app = params.get("app", "").strip()
        startup_action = params.get("action", "").strip().lower()
        
        if not app or startup_action not in ["enable", "disable"]:
            print("❌ App name and action (enable/disable) are required")
            return
        
        print(f"⚙️  {startup_action.capitalize()}ing {app} in startup...")
        result = _safe_execute(manage_startup_apps, app, startup_action)
        if result.get("success"):
            print(f"   {result['message']}")
        else:
            print(f"   {result['message']}")
    
    elif action == "set_default_app":
        app_type = params.get("app_type", "").strip().lower()
        app_name = params.get("app_name", "").strip().lower()
        
        if not app_type or not app_name:
            print("❌ App type and app name are required")
            return
        
        # Map app names to common paths
        app_paths = {
            "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "firefox": "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
            "edge": "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
            "brave": "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
            "opera": "C:\\Program Files\\Opera\\opera.exe",
            "vivaldi": "C:\\Program Files\\Vivaldi\\Application\\vivaldi.exe",
            "outlook": "C:\\Program Files\\Microsoft Office\\root\\Office16\\OUTLOOK.EXE",
            "thunderbird": "C:\\Program Files\\Mozilla Thunderbird\\thunderbird.exe",
            "vs code": "C:\\Users\\ASUS\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
            "notepad": "C:\\Windows\\System32\\notepad.exe",
            "notepad++": "C:\\Program Files\\Notepad++\\notepad++.exe",
        }
        
        app_path = app_paths.get(app_name)
        if not app_path:
            print(f"❌ Application '{app_name}' path not found. Supported apps: {list(app_paths.keys())}")
            return
        
        print(f"🔗 Setting {app_name} as default {app_type}...")
        result = _safe_execute(set_default_app, app_type, app_path)
        if result.get("success"):
            print(f"   {result['message']}")
            if result.get("elevated"):
                print(f"   ℹ️  Admin privileges were automatically requested and granted.")
        else:
            print(f"   {result['message']}")
            
            # Show helpful details for different error types
            if result.get("error") in ["NO_ADMIN", "ELEVATION_FAILED", "ELEVATION_ERROR"]:
                print(f"\n   📌 Solution:")
                if result.get("workaround"):
                    print(f"      1. {result.get('workaround')}")
                if result.get("manual_option"):
                    print(f"      2. {result.get('manual_option')}")
                if result.get("details"):
                    print(f"\n   Details: {result.get('details')}")
            elif result.get("error") == "PERMISSION_DENIED":
                print(f"\n   📌 Solution:")
                print(f"      • {result.get('workaround')}")
                print(f"      • {result.get('manual_option')}")
            elif result.get("details"):
                print(f"   Details: {result.get('details')}")
    
    else:
        print(f"❌ Unknown personalization action: {action}")


def _handle_file_management(action: str, params: dict):
    """Handle file management operations."""
    
    folder_name = params.get("folder_name", "").strip()
    if not folder_name:
        print("❌ Folder name is required")
        return
    
    # Initialize file manager
    manager = FileManager()
    
    # Load the folder
    print(f"📂 Loading folder '{folder_name}'...")
    load_result = manager.load_folder(folder_name)
    
    if "error" in load_result:
        print(f"❌ {load_result['error']}")
        return
    
    print(f"✅ {load_result['message']}")
    folder_info = load_result.get('folder_info', {})
    print(f"   📊 Total files: {folder_info.get('total_files', 0)}")
    print(f"   💾 Total size: {folder_info.get('size_mb', 0)} MB\n")
    
    if action == "organize_by_type":
        print("📋 Organizing files...\n")
        result = manager.organize_by_type(dry_run=False)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return
        
        print(f"📊 Organization Results:")
        print(f"   Total files processed: {result.get('total_files_processed', 0)}")
        print(f"   Files moved: {result.get('files_moved', 0)}")
        
        # Show what was organized
        print(f"\n📁 Files organized into folders:")
        for category, files in result.get('organization_map', {}).items():
            print(f"   📂 {category}/ ({len(files)} files)")
            for filename in files[:3]:  # Show first 3 files
                print(f"      • {filename}")
            if len(files) > 3:
                print(f"      ... and {len(files) - 3} more files")
        
        if result.get('files_moved') > 0:
            print(f"\n✅ Successfully organized {result.get('files_moved', 0)} files!")
        else:
            print(f"\n✅ Folder already organized!")
    
    elif action == "find_duplicates":
        print("🔍 Scanning for duplicate files...\n")
        duplicates = manager.scan_duplicates()
        
        if "error" in duplicates:
            print(f"❌ Error: {duplicates['error']}")
            return
        
        if not duplicates.get('duplicates_found'):
            print("✅ No duplicates found!")
            return
        
        print(f"⚠️  Found {duplicates.get('total_duplicate_files', 0)} duplicate files:\n")
        
        for i, group in enumerate(duplicates.get('duplicate_groups', [])[:5], 1):
            print(f"   📋 Duplicate group {i} ({group.get('count')} copies):")
            for file_path in group.get('files', []):
                print(f"      • {file_path}")
            
            # Calculate space savings
            file_sizes = group.get('file_sizes', [])
            if file_sizes:
                space_saved = sum(file_sizes[1:]) / (1024 * 1024)  # All but first copy
                print(f"      💾 Space savings: {space_saved:.2f} MB\n")
        
        if len(duplicates.get('duplicate_groups', [])) > 5:
            print(f"   ... and {len(duplicates.get('duplicate_groups', [])) - 5} more groups")
        
        total_space = duplicates.get('space_savings', 0) / (1024 * 1024)
        print(f"\n   💾 Total space that could be freed: {total_space:.2f} MB")
    
    elif action == "remove_duplicates":
        print("🔍 Scanning for duplicate files...\n")
        duplicates = manager.scan_duplicates()
        
        if "error" in duplicates:
            print(f"❌ Error: {duplicates['error']}")
            return
        
        if not duplicates.get('duplicates_found'):
            print("✅ No duplicates found!")
            return
        
        total_space = duplicates.get('space_savings', 0) / (1024 * 1024)
        print(f"🔴 Found {duplicates.get('total_duplicate_files', 0)} duplicate files")
        print(f"   💾 Space to be freed: {total_space:.2f} MB\n")
        
        print(f"🚀 Removing duplicates...")
        result = manager.remove_duplicates(dry_run=False)
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Successfully deleted {result.get('files_deleted', 0)} duplicate files")
            freed_space = result.get('space_freed', 0) / (1024 * 1024)
            print(f"   💾 Space freed: {freed_space:.2f} MB")
    
    elif action == "find_large_files":
        min_size = params.get("min_size_mb", 100)
        limit = params.get("limit", 20)
        
        print(f"🔴 Scanning for files larger than {min_size}MB...\n")
        large_files = manager.scan_large_files(min_size_mb=min_size, limit=limit)
        
        if "error" in large_files:
            print(f"❌ Error: {large_files['error']}")
            return
        
        if not large_files.get('large_files'):
            print(f"✅ No files larger than {min_size}MB found!")
            return
        
        print(f"📈 Found {large_files.get('large_files_found', 0)} large files:\n")
        
        for i, file_info in enumerate(large_files.get('large_files', []), 1):
            size_display = f"{file_info['size_gb']}GB" if file_info['size_gb'] >= 1 else f"{file_info['size_mb']}MB"
            print(f"   {i}. {file_info['name']}")
            print(f"      📊 Size: {size_display}")
            print(f"      📍 Path: {file_info['path']}\n")
    
    elif action == "analyze_folder":
        print("📊 Analyzing folder structure...\n")
        analysis = manager.analyze_folder()
        
        if "error" in analysis:
            print(f"❌ Error: {analysis['error']}")
            return
        
        # Organization stats
        org_stats = analysis.get('organization_stats', {})
        print(f"📁 Organization Status:")
        print(f"   Total files: {org_stats.get('total_files', 0)}")
        print(f"   Organized: {org_stats.get('organized_files', 0)}")
        print(f"   Unorganized: {org_stats.get('unorganized_files', 0)}")
        
        # Size breakdown
        size_break = analysis.get('size_breakdown', {})
        print(f"\n💾 Size by File Type (Top 5):")
        extensions = list(size_break.get('by_extension', {}).items())[:5]
        for ext, info in extensions:
            print(f"   {ext}: {info.get('size_mb', 0):.2f}MB ({info.get('count', 0)} files)")
    
    elif action == "get_report":
        print("📋 Generating comprehensive folder report...\n")
        report = manager.get_full_report()
        
        if "error" in report:
            print(f"❌ Error: {report['error']}")
            return
        
        # Basic info
        print(f"📂 Folder: {report.get('folder_name')}")
        print(f"📍 Path: {report.get('folder_path')}\n")
        
        # Analysis
        analysis = report.get('analysis', {})
        folder_info = analysis.get('folder_info', {})
        print(f"📊 Folder Statistics:")
        print(f"   Total files: {folder_info.get('total_files', 0)}")
        print(f"   Total size: {folder_info.get('size_mb', 0):.2f} MB\n")
        
        # Size by type
        size_break = analysis.get('size_breakdown', {})
        if size_break.get('by_extension'):
            print(f"💾 Size by File Type (Top 5):")
            extensions = list(size_break.get('by_extension', {}).items())[:5]
            for ext, info in extensions:
                print(f"   {ext}: {info.get('size_mb', 0):.2f}MB")
        
        # Large files
        large = report.get('large_files', {})
        if large.get('large_files'):
            print(f"\n🔴 Largest Files (Top 5):")
            for file_info in large.get('large_files', [])[:5]:
                size_display = f"{file_info['size_gb']}GB" if file_info['size_gb'] >= 1 else f"{file_info['size_mb']}MB"
                print(f"   • {file_info['name']}: {size_display}")
        
        # Duplicates
        dups = report.get('duplicates', {})
        if dups.get('duplicates_found'):
            print(f"\n⚠️  Duplicates Found: {dups.get('total_duplicate_files', 0)} files")
            freed_space = dups.get('space_savings', 0) / (1024 * 1024)
            print(f"   💾 Possible space savings: {freed_space:.2f} MB")
        else:
            print(f"\n✅ No duplicates found")
    
    else:
        print(f"❌ Unknown file management action: {action}")


def _handle_system_config():
    """Handle system configuration information request."""
    print("💻 Retrieving system configuration information...\n")
    print_system_config()


def _handle_installer(action: str, params: dict):
    """Handle installer operations (download wallpapers, software, resources)."""
    agent = InstallerAgent()
    
    if action == "download_wallpaper":
        query = params.get("query", "").strip()
        if not query:
            print("❌ Wallpaper query is required")
            return
        
        auto_set = params.get("auto_set", False)
        folder = params.get("folder")
        
        result = agent.install_wallpaper(query, folder, auto_set)
        
        if result["status"] == "success":
            print(f"✅ {result['message']}")
            if result.get("from_cache"):
                print(f"   📦 (from cache)")
            if result.get("auto_set"):
                print(f"   🖼️  Set as desktop background")
        else:
            print(f"❌ {result['message']}")
    
    elif action in ("install_software", "download_software"):
        # install_software = primary name; download_software = legacy alias
        app_name = (params.get("app_name") or params.get("query") or "").strip()
        if not app_name:
            print("❌ App name is required (e.g. 'Discord', 'VLC')")
            return

        folder = params.get("folder")
        result = agent.install_software(app_name, folder)

        if result.get("status") == "success":
            print(f"✅ {result['message']}")
            if result.get("from_cache"):
                print(f"   📦 (from cache)")
            if result.get("next_step"):
                print(f"\n   {result['next_step']}")
            # Offer to execute if a local installer was downloaded (fallback path)
            if result.get("can_execute") and result.get("installer_path"):
                print(f"\n🤖 Would you like me to run the installer now? (y/n): ", end="")
                response = input().strip().lower()
                if response in ['y', 'yes']:
                    exec_result = agent.execute_installer(result["installer_path"])
                    print(f"\n{exec_result['message']}")
                    if exec_result.get("instructions"):
                        print(f"   📋 {exec_result['instructions']}")
                    if exec_result.get("extracted_to"):
                        print(f"   📂 Extracted to: {exec_result['extracted_to']}")
                else:
                    print(f"   Installer saved to: {result['installer_path']}")
        else:
            print(f"❌ {result['message']}")
    
    elif action == "execute_installer":
        installer_path = params.get("installer_path", "").strip()
        if not installer_path:
            print("❌ Installer path is required")
            return
        
        result = agent.execute_installer(installer_path)
        
        if result["status"] == "success":
            print(f"✅ {result['message']}")
            if result.get("instructions"):
                print(f"   📋 {result['instructions']}")
        elif result["status"] == "extract":
            print(f"✅ {result['message']}")
            print(f"   📂 Extracted to: {result['extracted_to']}")
            if result.get("instructions"):
                print(f"   📋 {result['instructions']}")
        else:
            print(f"❌ {result['message']}")
            if result.get("manual_instruction"):
                print(f"   📋 {result['manual_instruction']}")
    
    elif action == "download_resource":
        query = params.get("query", "").strip()
        resource_type = params.get("resource_type", "").strip().lower()
        
        if not query:
            print("❌ Query is required")
            return
        
        if not resource_type:
            print("❌ Resource type is required (wallpaper, software, image, document)")
            return
        
        folder = params.get("folder")
        result = agent.download_resource(query, resource_type, folder)
        
        if result["status"] == "success":
            print(f"✅ {result['message']}")
            if result.get("from_cache"):
                print(f"   📦 (from cache)")
        else:
            print(f"❌ {result['message']}")
    
    elif action == "cache_info":
        info = agent.get_cache_info()
        print(f"📦 Cache Information:")
        print(f"   Total items: {info['total_items']}")
        print(f"   Total size: {info['total_size_mb']}MB")
        if info.get("oldest_item"):
            print(f"   Oldest: {info['oldest_item']}")
        if info.get("newest_item"):
            print(f"   Newest: {info['newest_item']}")
    
    elif action == "clear_cache":
        query = params.get("query")
        result = agent.clear_cache(query)
        
        if result["status"] == "success":
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
    
    else:
        print(f"❌ Unknown installer action: {action}")
