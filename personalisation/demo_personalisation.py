"""
Phase 12 Personalisation — Demo & Test File
Tests all personalization features independently
Run: python demo_personalisation.py
"""

from pathlib import Path
from personalisation_tools import (
    toggle_dark_mode,
    get_current_theme,
    set_wallpaper,
    set_display_brightness,
    set_accent_color,
    apply_theme_preset,
    save_personalization_profile,
    load_personalization_profile,
    manage_startup_apps
)


def print_header(title):
    """Print section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_dark_mode():
    """Test dark/light mode toggling."""
    print_header("TEST 1: DARK MODE TOGGLE")
    
    # Get current theme
    current = get_current_theme()
    print(f"📊 Current Theme: {current.get('current_theme', 'unknown').upper()}")
    
    # Toggle to dark
    print("\n▶ Toggling to DARK mode...")
    result = toggle_dark_mode(enable=True)
    print(f"   {result['message']}")
    
    # Toggle to light
    print("\n▶ Toggling to LIGHT mode...")
    result = toggle_dark_mode(enable=False)
    print(f"   {result['message']}")
    
    # Toggle back to dark
    print("\n▶ Toggling back to DARK mode...")
    result = toggle_dark_mode(enable=True)
    print(f"   {result['message']}")


def test_accent_color():
    """Test accent color settings."""
    print_header("TEST 2: ACCENT COLOR")
    
    colors = {
        "Blue": "0066CC",
        "Red": "CC0000",
        "Green": "00CC00",
        "Purple": "9933FF",
        "Orange": "FF9900"
    }
    
    for color_name, hex_code in colors.items():
        print(f"▶ Setting accent to {color_name} ({hex_code})...")
        result = set_accent_color(hex_code)
        print(f"   {result['message']}")


def test_display_brightness():
    """Test brightness adjustment."""
    print_header("TEST 3: DISPLAY BRIGHTNESS")
    
    brightness_levels = [30, 50, 70, 100]
    
    for level in brightness_levels:
        print(f"▶ Setting brightness to {level}%...")
        result = set_display_brightness(level)
        print(f"   {result['message']}")


def test_theme_presets():
    """Test theme presets."""
    print_header("TEST 4: THEME PRESETS")
    
    presets = ["dark", "light", "office", "gaming", "minimal"]
    
    for preset in presets:
        print(f"\n▶ Applying '{preset}' preset...")
        result = apply_theme_preset(preset)
        
        if result['success']:
            print(f"   {result['message']}")
            print(f"   Description: {result['description']}")
            print(f"   Settings: {result['applied_settings']}")
        else:
            print(f"   {result['message']}")


def test_profile_management():
    """Test saving and loading profiles."""
    print_header("TEST 5: PROFILE MANAGEMENT")
    
    # Create a custom profile
    custom_profile = {
        "name": "MyCustomTheme",
        "dark_mode": True,
        "accent_color": "0066CC",
        "brightness": 75,
        "theme_description": "Custom professional theme"
    }
    
    print("▶ Saving custom profile 'MyCustomTheme'...")
    result = save_personalization_profile("MyCustomTheme", custom_profile)
    print(f"   {result['message']}")
    
    print("\n▶ Loading profile 'MyCustomTheme'...")
    result = load_personalization_profile("MyCustomTheme")
    
    if result['success']:
        print(f"   {result['message']}")
        print(f"   Settings: {result['settings']}")
    else:
        print(f"   {result['message']}")


def test_wallpaper():
    """Test wallpaper setting (informational only - requires valid image)."""
    print_header("TEST 6: WALLPAPER MANAGEMENT")
    
    print("ℹ️  Wallpaper function is available but requires a valid image path.")
    print("\nExample usage:")
    print('   result = set_wallpaper("C:\\\\Users\\\\Pictures\\\\wallpaper.jpg")')
    print("\nSupported formats: JPG, PNG, BMP")


def test_startup_apps():
    """Test startup app management."""
    print_header("TEST 7: STARTUP APPS MANAGEMENT")
    
    print("ℹ️  Startup app management is available.")
    print("\nExample usage:")
    print('   result = manage_startup_apps("Discord", "enable")')
    print('   result = manage_startup_apps("Discord", "disable")')


def show_command_examples():
    """Display example commands for Jarvis."""
    print_header("EXAMPLE JARVIS COMMANDS")
    
    examples = [
        ("Theme Control", [
            "Jarvis > dark mode",
            "Jarvis > light mode",
            "Jarvis > toggle dark mode",
            "Jarvis > show current theme"
        ]),
        ("Theme Presets", [
            "Jarvis > apply dark theme",
            "Jarvis > apply office theme",
            "Jarvis > apply gaming theme",
            "Jarvis > apply minimal theme"
        ]),
        ("Accent Color", [
            "Jarvis > set accent to blue",
            "Jarvis > set accent color to FF0066",
            "Jarvis > change accent to red"
        ]),
        ("Display Settings", [
            "Jarvis > set brightness to 50",
            "Jarvis > set brightness to 100",
            "Jarvis > dim screen to 30 percent"
        ]),
        ("Wallpaper", [
            "Jarvis > set wallpaper to C:\\\\Pictures\\\\nature.jpg",
            "Jarvis > change desktop background"
        ]),
        ("Startup Apps", [
            "Jarvis > add discord to startup",
            "Jarvis > remove chrome from startup",
            "Jarvis > enable discord on startup"
        ]),
        ("Profile Management", [
            "Jarvis > save my settings as MyTheme",
            "Jarvis > load profile MyTheme",
            "Jarvis > save current theme as office"
        ])
    ]
    
    for category, commands in examples:
        print(f"\n📌 {category}:")
        for cmd in commands:
            print(f"   {cmd}")


def show_menu():
    """Display interactive menu."""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║          PHASE 12 - PERSONALISATION DEMO & TEST SUITE             ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    
    print("\n⚠️  WARNING: Tests will modify your system settings!")
    print("   Make sure you're in a test environment or backup your settings.\n")
    
    print("📋 SELECT A TEST TO RUN:")
    print("   1. Dark Mode Toggle")
    print("   2. Accent Color")
    print("   3. Display Brightness")
    print("   4. Theme Presets")
    print("   5. Profile Management")
    print("   6. Wallpaper Management")
    print("   7. Startup Apps Management")
    print("   8. Show Example Commands")
    print("   9. Exit Demo")
    print("\n")


def run_selected_test(choice):
    """Run the selected test."""
    tests = {
        "1": ("Dark Mode Toggle", test_dark_mode),
        "2": ("Accent Color", test_accent_color),
        "3": ("Display Brightness", test_display_brightness),
        "4": ("Theme Presets", test_theme_presets),
        "5": ("Profile Management", test_profile_management),
        "6": ("Wallpaper Management", test_wallpaper),
        "7": ("Startup Apps Management", test_startup_apps),
        "8": ("Example Commands", show_command_examples),
    }
    
    if choice in tests:
        test_name, test_func = tests[choice]
        try:
            test_func()
            return True
        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            return False
    else:
        print("❌ Invalid choice. Please select 1-9.")
        return False


def main():
    """Run interactive demo with menu selection."""
    while True:
        show_menu()
        choice = input("Enter your choice (1-9): ").strip()
        
        if choice == "9":
            print("\n✅ Thanks for testing! Goodbye!")
            print("\nTo use with Jarvis:")
            print("  1. Use 'python main.py'")
            print("  2. Try commands like: 'dark mode', 'set bright to 50', etc.")
            print("\n")
            break
        elif choice in ["1", "2", "3", "4", "5", "6", "7", "8"]:
            run_selected_test(choice)
            input("\n▶ Press Enter to continue...")
        else:
            print("❌ Invalid choice. Please select 1-9.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()
