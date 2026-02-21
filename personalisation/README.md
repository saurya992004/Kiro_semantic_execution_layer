# 🎨 Phase 12 — Personalisation Engine

## Overview

The Personalisation module enables Jarvis to modify Windows system settings and user preferences autonomously through voice/text commands. This allows users to customize their system appearance, behavior, and defaults without manual configuration.

---

## 🎯 Implemented Features

### 1. **Dark Mode / Light Mode Toggle** ✅
- Toggle Windows theme between dark and light modes
- Get current theme status
- Applies to both apps and system UI

### 2. **Wallpaper Management** ✅
- Set desktop wallpaper from image files
- Supports JPG, PNG, BMP formats
- Updates immediately using Windows API

### 3. **Display Settings** ✅
- Adjust screen brightness (0-100%)
- Set display resolution
- Real-time display adjustments

### 4. **Accent Color Customization** ✅
- Change Windows accent color
- Hex color code support
- Updates window borders, buttons, and UI accents

### 5. **App Preferences** ✅
- Set default applications (browser, mail, editor, image viewer)
- Manage startup applications
- Enable/disable apps from startup

### 6. **Theme Presets** ✅
- Pre-configured theme profiles: Dark, Light, Office, Gaming, Minimal
- One-command theme application
- Includes coordinated settings (dark mode + accent + brightness)

### 7. **Profile Management** ✅
- Save custom personalization profiles
- Load previously saved configurations
- JSON-based profile storage

---

## 📁 File Structure

```
personalisation/
├── __init__.py                    # Module initialization
├── personalisation_tools.py       # Core personalization functions
├── demo_personalisation.py        # Standalone testing suite
├── README.md                      # This file
└── profiles/                      # Saved profile storage (auto-created)
```

---

## 🚀 Example Commands

### Dark Mode Control
```
Jarvis > dark mode
Jarvis > light mode
Jarvis > toggle dark mode
Jarvis > show current theme
```

### Theme Presets
```
Jarvis > apply dark theme
Jarvis > apply office theme
Jarvis > apply gaming theme
Jarvis > apply minimal theme
Jarvis > use light preset
```

### Accent Color
```
Jarvis > set accent to blue
Jarvis > change accent color to FF0066
Jarvis > set accent to red
Jarvis > accent color purple
```

### Display Brightness
```
Jarvis > set brightness to 50
Jarvis > brighten screen to 100 percent
Jarvis > dim screen to 30 percent
Jarvis > set display brightness to 75
```

### Display Resolution
```
Jarvis > set resolution to 1920 by 1080
Jarvis > change display to 1366 by 768
Jarvis > set screen resolution 2560 1440
```

### Wallpaper
```
Jarvis > set wallpaper to C:\Pictures\nature.jpg
Jarvis > change desktop background to D:\Images\beach.png
Jarvis > set wallpaper C:\Wallpapers\landscape.jpg
```

### Startup Apps
```
Jarvis > add discord to startup
Jarvis > remove chrome from startup
Jarvis > enable spotify on startup
Jarvis > disable slack from startup
```

### Profile Management
```
Jarvis > save my settings as DarkOffice
Jarvis > load profile DarkOffice
Jarvis > save current theme as Gaming
Jarvis > apply profile MyCustomTheme
```

---

## 🧪 Testing (Demo Mode)

Run the standalone demo to test all features:

```bash
cd personalisation
python demo_personalisation.py
```

The demo will:
- Test dark/light mode toggling
- Cycle through accent colors
- Adjust brightness levels
- Apply all theme presets
- Save and load profiles
- Show all available commands

**⚠️ Warning:** The demo modifies your actual system settings. Run in a test environment or be prepared to revert changes.

---

## 🔌 Integration with Intent Router

The personalisation module is integrated into Jarvis's main intent router under the `personalization` intent:

```python
{
    "intent": "personalization",
    "action": "toggle_dark_mode|set_accent|set_brightness|apply_preset|manage_profiles",
    "parameters": {
        "enable": true/false,
        "color": "FF0066",
        "brightness": 50,
        "preset": "dark|light|office|gaming|minimal",
        "profile_name": "MyTheme"
    }
}
```

### Available Actions

| Action | Parameters | Description |
|--------|-----------|-------------|
| `toggle_dark_mode` | `enable: bool` | Toggle between dark/light theme |
| `set_accent_color` | `color: str` (hex) | Set accent color |
| `set_brightness` | `brightness: int` (0-100) | Adjust display brightness |
| `set_wallpaper` | `path: str` | Set wallpaper image |
| `set_resolution` | `width: int, height: int` | Set display resolution |
| `apply_preset` | `preset: str` | Apply preset theme |
| `save_profile` | `name: str, settings: dict` | Save personalization profile |
| `load_profile` | `name: str` | Load saved profile |
| `manage_startup` | `app: str, action: str` | Enable/disable startup apps |

---

## 🎨 Available Theme Presets

### 1. **Dark Mode** 🌙
- Dark theme enabled
- Cool blue accent (#0066CC)
- 50% brightness
- Professional dark workspace

### 2. **Light Mode** ☀️
- Light theme enabled
- Bright blue accent (#00A0FF)
- 100% brightness
- Well-lit environment theme

### 3. **Office** 💼
- Light theme
- Professional navy accent (#2E5090)
- 80% brightness
- Business/productivity focused

### 4. **Gaming** 🎮
- Dark theme
- High contrast pink accent (#FF0066)
- 100% brightness
- Maximum visibility for gaming

### 5. **Minimal** 🎯
- Dark theme
- Neutral gray accent (#808080)
- 60% brightness
- Clean, distraction-free theme

---

## 💾 Profile Storage

Profiles are saved as JSON files in `personalisation/profiles/` directory:

```json
{
  "name": "MyCustomTheme",
  "dark_mode": true,
  "accent_color": "0066CC",
  "brightness": 75,
  "theme_description": "Custom professional theme"
}
```

### Creating Custom Profiles

```python
from personalisation import save_personalization_profile

custom_settings = {
    "dark_mode": True,
    "accent_color": "9933FF",
    "brightness": 60,
    "custom_field": "any value"
}

result = save_personalization_profile("MyPurpleTheme", custom_settings)
```

---

## 🛠️ Technical Details

### Windows Registry Integration
- Uses `winreg` module for Windows Registry access
- Modifies `HKEY_CURRENT_USER` for user-specific settings
- Safe error handling with fallback options

### API Usage
- Windows API calls via `ctypes` for wallpaper changes
- WMI integration for brightness (with registry fallback)
- PowerShell script generation for display resolution

### Supported Windows Versions
- Windows 10 and later
- Tested on Windows 11

---

## 📝 Function Reference

### Dark Mode Control
```python
toggle_dark_mode(enable: bool) -> dict
get_current_theme() -> dict
```

### Display Settings
```python
set_display_brightness(brightness: int) -> dict
set_display_resolution(width: int, height: int) -> dict
```

### Visual Customization
```python
set_accent_color(color_hex: str) -> dict
set_wallpaper(image_path: str) -> dict
```

### Application Management
```python
set_default_app(app_type: str, app_path: str) -> dict
manage_startup_apps(app_name: str, action: str) -> dict
```

### Preset & Profile Management
```python
apply_theme_preset(preset_name: str) -> dict
save_personalization_profile(profile_name: str, settings: dict) -> dict
load_personalization_profile(profile_name: str) -> dict
```

---

## ⚡ Quick Start

1. **Using Jarvis CLI:**
   ```
   python main.py
   Jarvis > dark mode
   Jarvis > set accent to blue
   Jarvis > set brightness to 80
   Jarvis > apply office theme
   ```

2. **Standalone Testing:**
   ```
   cd personalisation
   python demo_personalisation.py
   ```

3. **In Python Scripts:**
   ```python
   from personalisation import toggle_dark_mode, apply_theme_preset
   
   toggle_dark_mode(enable=True)
   apply_theme_preset("office")
   ```

---

## ✅ Completion Status

**Phase 12 Implementation: 100% Complete**

- ✅ Dark/Light mode toggling
- ✅ Wallpaper management
- ✅ Display brightness control
- ✅ Display resolution support
- ✅ Accent color customization
- ✅ App preference management
- ✅ Startup app control
- ✅ Theme presets (5 presets)
- ✅ Profile save/load system
- ✅ Intent router integration
- ✅ Comprehensive demo suite
- ✅ Full documentation

---

## 🔮 Future Enhancements

- Lock screen customization
- Font size adjustments
- Accessibility mode control
- Quick settings automation
- Voice command optimization
- GUI theme designer
- Multi-monitor support
