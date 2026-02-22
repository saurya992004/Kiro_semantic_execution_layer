"""
JARVIS Help System - Consolidated Command Reference
Maps all available commands to intents and actions

QUICK START:
  1. Type "help" at any prompt to see all available commands
  2. Type "exit" to quit Jarvis
  3. Use natural language variations of commands
  4. Parameters are shown in [brackets]

INTENT MAPPING:
  Every user command is converted to one of these intents:
  - help: Show command help
  - open_app: Open applications
  - web_search: Search the web
  - system_control: Control system (shutdown, restart, etc.)
  - diagnostics: Check CPU, RAM, disk status
  - disk_analysis: Analyze disk usage
  - maintenance: Clean and scan system
  - health_check: Check system health
  - troubleshoot_screen: Analyze screen errors visually
  - vision_analysis: Analyze screen content
  - personalization: Customize appearance and settings
  - file_management: Organize files and find duplicates
"""

HELP_COMMANDS = {
    "APPLICATION & WEB": {
        "intent": "open_app",
        "commands": [
            {
                "command": "open chrome",
                "description": "Open Google Chrome browser",
                "example": "open chrome, launch chrome, open google"
            },
            {
                "command": "open notepad",
                "description": "Open Notepad text editor",
                "example": "open notepad, open text editor"
            },
            {
                "command": "open vscode",
                "description": "Open Visual Studio Code",
                "example": "open vscode, launch vscode, open code"
            },
            {
                "command": "open [app_name]",
                "description": "Open any installed application",
                "example": "open word, launch excel, open photoshop"
            }
        ],
        "web_commands": [
            {
                "intent": "web_search",
                "command": "search [query]",
                "description": "Search the web for information",
                "example": "search python programming, search how to code, search machine learning"
            }
        ]
    },
    "SYSTEM CONTROL": {
        "intent": "system_control",
        "commands": [
            {
                "action": "shutdown",
                "command": "shutdown",
                "description": "Shut down the system",
                "example": "shutdown system, shutdown pc, power off"
            },
            {
                "action": "restart",
                "command": "restart",
                "description": "Restart the system",
                "example": "restart system, restart pc, reboot"
            },
            {
                "action": "sleep",
                "command": "sleep",
                "description": "Put system to sleep mode",
                "example": "sleep, sleep system, put pc to sleep"
            },
            {
                "action": "lock",
                "command": "lock",
                "description": "Lock the system",
                "example": "lock system, lock pc, lock screen"
            },
            {
                "action": "kill_process",
                "command": "kill [process_name]",
                "description": "Kill/close a running process",
                "example": "kill chrome, kill notepad, close process"
            },
            {
                "action": "clean_temp",
                "command": "clean temp files",
                "description": "Clean temporary files from system",
                "example": "clean temp, cleanup temp files, remove temp files"
            },
            {
                "action": "empty_recycle_bin",
                "command": "empty recycle bin",
                "description": "Empty the recycle bin permanently",
                "example": "empty recycle, clear trash, delete recycle bin"
            }
        ]
    },
    "DIAGNOSTICS & HEALTH": {
        "intent": "diagnostics",
        "commands": [
            {
                "action": "check_cpu",
                "command": "check cpu",
                "description": "Check CPU usage and performance",
                "example": "check cpu, cpu usage, cpu status"
            },
            {
                "action": "check_ram",
                "command": "check ram",
                "description": "Check RAM memory usage",
                "example": "check ram, ram usage, memory check"
            },
            {
                "action": "check_disk",
                "command": "check disk",
                "description": "Check disk usage (default C:)",
                "example": "check disk, disk usage, check storage"
            },
            {
                "action": "complete_system_health",
                "command": "complete system health",
                "description": "Run comprehensive system health check",
                "example": "complete system health, full health check, system health report"
            }
        ],
        "health_intent": "health_check",
        "health_commands": [
            {
                "command": "health check",
                "description": "Check system health and show alerts",
                "example": "health check, check health, system status"
            }
        ]
    },
    "DISK ANALYSIS": {
        "intent": "disk_analysis",
        "commands": [
            {
                "action": "analyze_usage",
                "command": "analyze disk usage",
                "description": "Analyze disk usage patterns",
                "example": "analyze disk usage, disk analysis, check disk space"
            },
            {
                "action": "find_large_folders",
                "command": "find large folders",
                "description": "Find large folders taking up space",
                "example": "find large folders, find big folders, locate large directories"
            },
            {
                "action": "check_alerts",
                "command": "check disk alerts",
                "description": "Check for disk space warnings",
                "example": "check disk alerts, disk alerts, storage warnings"
            }
        ]
    },
    "MAINTENANCE & CLEANUP": {
        "intent": "maintenance",
        "commands": [
            {
                "action": "scan_temp",
                "command": "scan temp files",
                "description": "Scan temporary files for cleanup",
                "example": "scan temp files, scan temp, check temp files"
            },
            {
                "action": "scan_old_files",
                "command": "scan old files",
                "description": "Scan for old unused files",
                "example": "scan old files, find old files, locate unused files"
            },
            {
                "action": "scan_cleanup",
                "command": "scan cleanup folder",
                "description": "Scan cleanup folder for removable items",
                "example": "scan cleanup, cleanup scan, check cleanup folder"
            },
            {
                "action": "clean_temp_files",
                "command": "clean temp files",
                "description": "Remove temporary files",
                "example": "clean temp files, remove temp, cleanup temp"
            },
            {
                "action": "clean_old_files",
                "command": "clean old files",
                "description": "Remove old unused files",
                "example": "clean old files, remove old files, delete old files"
            }
        ]
    },
    "TROUBLESHOOTING": {
        "intent": "troubleshoot_screen",
        "commands": [
            {
                "command": "troubleshoot screen",
                "description": "Capture screen and analyze errors visually",
                "example": "troubleshoot screen, fix errors, analyze error"
            },
            {
                "command": "troubleshoot",
                "description": "Troubleshoot current screen issues",
                "example": "troubleshoot, help me, what's wrong"
            }
        ]
    },
    "SCREEN ANALYSIS": {
        "intent": "vision_analysis",
        "commands": [
            {
                "action": "analyze_screen",
                "command": "analyze screen",
                "description": "Analyze what's currently on the screen",
                "example": "analyze screen, what's on screen, describe screen"
            },
            {
                "action": "detect_ui",
                "command": "detect ui elements",
                "description": "Detect UI elements on the screen",
                "example": "detect ui elements, find buttons, identify controls"
            },
            {
                "action": "read_text",
                "command": "read text from screen",
                "description": "Read and extract text from screen",
                "example": "read text from screen, extract text, read screen"
            }
        ]
    },
    "FILE MANAGEMENT": {
        "intent": "file_management",
        "commands": [
            {
                "action": "organize_by_type",
                "command": "organize [folder_name]",
                "description": "Organize files in a folder by type",
                "example": "organize downloads, organize documents, organize desktop"
            },
            {
                "action": "find_duplicates",
                "command": "find duplicates in [folder_name]",
                "description": "Find duplicate files in a folder",
                "example": "find duplicates in downloads, find duplicates in documents"
            },
            {
                "action": "remove_duplicates",
                "command": "clean up duplicates in [folder_name]",
                "description": "Remove duplicate files from a folder",
                "example": "clean up duplicates in downloads, remove duplicates in documents"
            },
            {
                "action": "find_large_files",
                "command": "find large files",
                "description": "Find large files on the system",
                "example": "find large files, locate big files, search for large files"
            },
            {
                "action": "analyze_folder",
                "command": "analyze [folder_name]",
                "description": "Analyze a specific folder",
                "example": "analyze downloads, analyze documents, analyze desktop"
            },
            {
                "action": "get_report",
                "command": "generate report for [folder_name]",
                "description": "Generate detailed report for a folder",
                "example": "generate report for documents, create report for downloads"
            }
        ]
    },
    "PERSONALIZATION": {
        "intent": "personalization",
        "commands": [
            {
                "action": "toggle_dark_mode",
                "command": "dark mode / light mode",
                "description": "Toggle between dark and light theme",
                "example": "dark mode, light mode, enable dark mode, disable dark mode"
            },
            {
                "action": "set_accent_color",
                "command": "set accent color [color]",
                "description": "Set system accent color",
                "example": "set accent to blue, set accent color red, change accent"
            },
            {
                "action": "set_brightness",
                "command": "set brightness [0-100]",
                "description": "Set display brightness",
                "example": "set brightness to 50, brightness 75, dim screen"
            },
            {
                "action": "set_wallpaper",
                "command": "set wallpaper [path]",
                "description": "Set desktop wallpaper",
                "example": "set wallpaper, change wallpaper, set background"
            },
            {
                "action": "apply_preset",
                "command": "apply [preset] theme",
                "description": "Apply preset theme (dark/light/office/gaming/minimal)",
                "example": "apply dark theme, apply gaming preset, apply office theme"
            },
            {
                "action": "save_profile",
                "command": "save profile [name]",
                "description": "Save current personalization profile",
                "example": "save profile myTheme, save my settings, save profile"
            },
            {
                "action": "load_profile",
                "command": "load profile [name]",
                "description": "Load a saved personalization profile",
                "example": "load profile myTheme, load my settings, restore profile"
            },
            {
                "action": "manage_startup",
                "command": "add [app_name] to startup",
                "description": "Manage startup applications",
                "example": "add chrome to startup, remove discord from startup"
            },
            {
                "action": "set_default_app",
                "command": "set [app_name] as default [app_type]",
                "description": "Set default application for a type",
                "example": "set chrome as default browser, make outlook default mail"
            }
        ]
    },
    "SYSTEM INFORMATION": {
        "intent": "system_config",
        "commands": [
            {
                "command": "system config",
                "description": "Display complete system configuration details",
                "example": "system config, show config, tell me the config"
            },
            {
                "command": "about this computer",
                "description": "Display system information and specifications",
                "example": "about this computer, about my system, computer info"
            },
            {
                "command": "system information",
                "description": "Show detailed system and hardware information",
                "example": "system information, system specs, hardware specs"
            },
            {
                "command": "laptop specs",
                "description": "Display laptop specifications",
                "example": "what are my laptop specs, show laptop specs, laptop specifications"
            },
            {
                "command": "system details",
                "description": "Show comprehensive system details",
                "example": "system details, give me system details, show details"
            }
        ]
    }
}

def print_help():
    """Display comprehensive help information."""
    print("\n")
    print("╔" + "═" * 70 + "╗")
    print("║" + " " * 15 + "🤖 JARVIS - COMPREHENSIVE COMMAND HELP" + " " * 17 + "║")
    print("╚" + "═" * 70 + "╝")
    print()
    
    for category, details in HELP_COMMANDS.items():
        print(f"\n📍 {category}")
        print("─" * 72)
        
        if "commands" in details:
            for cmd in details["commands"]:
                print(f"  • {cmd['command']:<40} | {cmd['description']}")
                print(f"    └─ Example: {cmd['example']}")
                if "action" in cmd:
                    print(f"    └─ Action: {cmd['action']}")
                print()
        
        if "web_commands" in details:
            for cmd in details["web_commands"]:
                print(f"  • {cmd['command']:<40} | {cmd['description']}")
                print(f"    └─ Example: {cmd['example']}")
                print()
        
        if "health_commands" in details:
            for cmd in details["health_commands"]:
                print(f"  • {cmd['command']:<40} | {cmd['description']}")
                print(f"    └─ Example: {cmd['example']}")
                print()
    
    print("\n" + "═" * 72)
    print("💡 Tips:")
    print("  • Type 'help' anytime to see this message")
    print("  • You can use natural language variations of the commands")
    print("  • Parameters are shown in [brackets]")
    print("  • For file operations, use folder names: Downloads, Documents, Desktop")
    print("  • Type 'exit' to quit Jarvis")
    print("═" * 72)
    print()

def get_commands_by_intent(intent: str) -> list:
    """Get all commands for a specific intent."""
    for category, details in HELP_COMMANDS.items():
        if details.get("intent") == intent:
            return details.get("commands", [])
        if details.get("health_intent") == intent:
            return details.get("health_commands", [])
    return []

def get_all_command_examples() -> list:
    """Get all command examples for quick reference."""
    examples = []
    for category, details in HELP_COMMANDS.items():
        if "commands" in details:
            for cmd in details["commands"]:
                examples.append({
                    "command": cmd["command"],
                    "examples": cmd["example"].split(", "),
                    "intent": details.get("intent")
                })
        if "web_commands" in details:
            for cmd in details["web_commands"]:
                examples.append({
                    "command": cmd["command"],
                    "examples": cmd["example"].split(", "),
                    "intent": cmd.get("intent")
                })
        if "health_commands" in details:
            for cmd in details["health_commands"]:
                examples.append({
                    "command": cmd["command"],
                    "examples": cmd["example"].split(", "),
                    "intent": details.get("health_intent")
                })
    return examples
