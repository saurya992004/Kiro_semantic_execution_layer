#!/usr/bin/env python3
"""
Test Commands for JARVIS Widget
Run: python run_jarvis.py
Then type these commands in the Input tab to test
"""

TEST_COMMANDS = [
    # Basic diagnostics
    ("check cpu", "Shows CPU usage"),
    ("check ram", "Shows RAM usage"),
    ("check disk", "Shows disk usage"),
    
    # Complete health check
    ("complete system health", "Comprehensive health report 🏥"),
    ("system health", "Alternative: same as above"),
    
    # System control
    ("shutdown", "Shutdown PC"),
    ("restart", "Restart PC"),
    ("sleep", "Sleep mode"),
    ("lock", "Lock computer"),
    
    # Apps
    ("open chrome", "Open Chrome browser"),
    ("open notepad", "Open Notepad"),
    ("open vscode", "Open VS Code"),
    
    # Web search
    ("search python", "Search on web"),
    ("search how to code", "Web search"),
    
    # Disk management
    ("analyze disk usage", "Show top folders by size"),
    ("find large folders", "Find folders > 1GB"),
    
    # Cleanup
    ("scan temp files", "Scan temp folder"),
    ("clean temp files", "Clean temp"),
    
    # Troubleshooting
    ("troubleshoot screen", "AI screen analysis 🧠"),
    ("health check", "Show system alerts"),
    
    # Help
    ("help", "Show all commands"),
]

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 JARVIS WIDGET - TEST COMMANDS")
    print("=" * 60)
    print("\nTo test JARVIS, run:")
    print(">>> python run_jarvis.py\n")
    print("Then type these commands in the Input tab:\n")
    print("=" * 60)
    
    for i, (cmd, desc) in enumerate(TEST_COMMANDS, 1):
        print(f"{i:2d}. {cmd:30s} → {desc}")
    
    print("\n" + "=" * 60)
    print("\nQuick test to verify everything works:")
    print("  1. Run: python run_jarvis.py")
    print("  2. Type: complete system health")
    print("  3. Click Output tab to see results")
    print("  4. Type: check cpu")
    print("  5. Type: open chrome")
    print("\n✅ If all work, JARVIS is ready!")
    print("=" * 60)
