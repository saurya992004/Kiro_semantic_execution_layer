"""
Phase 12 — Personalisation Engine
Handles system personalization: dark mode, wallpaper, themes, display settings, app preferences.
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from winreg import ConnectRegistry, OpenKey, SetValueEx, QueryValueEx, REG_DWORD, REG_SZ, HKEY_CURRENT_USER


# ============================================================================
# DARK MODE / LIGHT MODE
# ============================================================================

def toggle_dark_mode(enable: bool = True) -> dict:
    """
    Toggle Windows dark mode.
    
    Args:
        enable: True for dark mode, False for light mode
    
    Returns:
        dict with success status
    """
    try:
        reg = ConnectRegistry(None, HKEY_CURRENT_USER)
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        
        key = OpenKey(reg, key_path, 0, 0x20002)  # Write access
        
        # AppsUseLightTheme: 1 = Light, 0 = Dark
        theme_value = 0 if enable else 1
        SetValueEx(key, "AppsUseLightTheme", 0, REG_DWORD, theme_value)
        SetValueEx(key, "SystemUsesLightTheme", 0, REG_DWORD, theme_value)
        
        key.Close()
        
        mode = "🌙 DARK MODE" if enable else "☀️  LIGHT MODE"
        return {
            "success": True,
            "message": f"✅ Switched to {mode}",
            "mode": "dark" if enable else "light"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to toggle theme: {str(e)}"
        }


def get_current_theme() -> dict:
    """Get current Windows theme (dark or light)."""
    try:
        reg = ConnectRegistry(None, HKEY_CURRENT_USER)
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        
        key = OpenKey(reg, key_path, 0)
        theme_value, _ = QueryValueEx(key, "AppsUseLightTheme")
        key.Close()
        
        return {
            "success": True,
            "current_theme": "light" if theme_value == 1 else "dark"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# WALLPAPER MANAGEMENT
# ============================================================================

def set_wallpaper(image_path: str) -> dict:
    """
    Set desktop wallpaper.
    
    Args:
        image_path: Full path to image file (jpg, png, bmp)
    
    Returns:
        dict with success status
    """
    try:
        image_path = Path(image_path)
        
        if not image_path.exists():
            return {
                "success": False,
                "error": f"File not found: {image_path}",
                "message": f"❌ Image not found: {image_path}"
            }
        
        if image_path.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.bmp']:
            return {
                "success": False,
                "error": "Invalid image format. Use JPG, PNG, or BMP",
                "message": "❌ Unsupported image format"
            }
        
        # Use Windows API to set wallpaper
        import ctypes
        ctypes.windll.user32.SystemParametersInfoW(20, 0, str(image_path), 3)
        
        return {
            "success": True,
            "message": f"✅ Wallpaper changed to: {image_path.name}",
            "wallpaper_path": str(image_path)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to set wallpaper: {str(e)}"
        }


# ============================================================================
# DISPLAY SETTINGS
# ============================================================================

def set_display_brightness(brightness: int) -> dict:
    """
    Set display brightness (0-100).
    Uses PowerShell WMI method for Windows 10/11.
    """
    try:
        if brightness < 0 or brightness > 100:
            return {
                "success": False,
                "error": "Brightness must be between 0 and 100",
                "message": "❌ Invalid brightness value"
            }
        
        # Use PowerShell to set brightness via WMI
        ps_command = f"""
$brightness = {brightness}
$monitors = Get-WmiObject -Namespace "root\\WMI" -Class WmiMonitorBrightnessMethods
if ($monitors) {{
    $monitors.WmiSetBrightness(1, $brightness) | Out-Null
    Write-Host "SUCCESS"
}} else {{
    Write-Host "FAILED"
}}
"""
        
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-Command', ps_command],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "SUCCESS" in result.stdout:
            return {
                "success": True,
                "message": f"✅ Brightness set to {brightness}%",
                "brightness": brightness
            }
        elif "FAILED" in result.stdout:
            # Brightness control not available or no external monitors
            return {
                "success": False,
                "error": "WMI_NOT_SUPPORTED",
                "message": f"⚠️  Brightness control not available (may be laptop with fixed brightness)",
                "workaround": "Use keyboard brightness controls or Windows Settings > System > Display"
            }
        else:
            return {
                "success": False,
                "error": result.stderr[:100] if result.stderr else "Unknown error",
                "message": f"❌ Failed to set brightness",
                "workaround": "Use keyboard brightness controls or Windows Settings > System > Display"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "TIMEOUT",
            "message": "❌ Operation timed out",
            "workaround": "Use keyboard brightness controls"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to set brightness: {str(e)[:50]}",
            "workaround": "Use keyboard brightness controls or Windows Settings > System > Display"
        }


def set_display_resolution(width: int, height: int) -> dict:
    """
    Set display resolution.
    
    Args:
        width: Screen width in pixels
        height: Screen height in pixels
    """
    try:
        cmd = f'powershell -Command "Add-Type -TypeDefinition \'using System.Runtime.InteropServices; public class WindowFunc {{ [DllImport(\\"user32.dll\\")] public static extern bool ChangeDisplaySettings(ref DEVMODE lpDevMode, uint dwflags); }} public struct DEVMODE {{ [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string dmDeviceName; public uint dmSpecVersion; public uint dmDriverVersion; public uint dmSize; public uint dmDriverExtra; public uint dmFields; public int dmOrientation; public int dmPaperSize; public int dmPaperLength; public int dmPaperWidth; public int dmScale; public int dmCopies; public int dmDefaultSource; public int dmPrintQuality; public int dmColor; public int dmDuplex; public int dmYResolution; public int dmTTOption; public int dmCollate; [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string dmFormName; public uint dmLogPixels; public uint dmBitsPerPel; public int dmPelsWidth; public int dmPelsHeight; public uint dmDisplayFlags; public uint dmDisplayFrequency; public uint dmICMMethod; public uint dmICMIntent; public uint dmMediaType; public uint dmDitherType; public uint dmReserved1; public uint dmReserved2; public uint dmPanningWidth; public uint dmPanningHeight; }}\' -PassThru; $mode = New-Object DEVMODE; $mode.dmSize = [System.Runtime.InteropServices.Marshal]::SizeOf([type]::GetType(\\"DEVMODE\\")); $mode.dmPelsWidth = {width}; $mode.dmPelsHeight = {height}; $mode.dmFields = 0x80000; [WindowFunc]::ChangeDisplaySettings([ref]$mode, 0)"'
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": f"✅ Resolution set to {width}x{height}",
                "resolution": {"width": width, "height": height}
            }
        else:
            return {
                "success": False,
                "error": result.stderr,
                "message": f"❌ Failed to set resolution"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to set resolution: {str(e)}"
        }


# ============================================================================
# ACCENT COLOR / THEME COLORS
# ============================================================================

def set_accent_color(color_hex: str) -> dict:
    """
    Set Windows accent color.
    
    Args:
        color_hex: Hex color code (e.g., "0066CC")
    """
    try:
        if len(color_hex) != 6:
            return {
                "success": False,
                "error": "Color must be 6-digit hex (e.g., 0066CC)",
                "message": "❌ Invalid color format"
            }
        
        # Convert hex to BGR integer
        color_int = int(color_hex[4:6] + color_hex[2:4] + color_hex[0:2], 16)
        
        reg = ConnectRegistry(None, HKEY_CURRENT_USER)
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Accent"
        
        key = OpenKey(reg, key_path, 0, 0x20002)
        SetValueEx(key, "AccentColorMenu", 0, REG_DWORD, color_int)
        SetValueEx(key, "AccentPalette", 0, REG_SZ, color_hex)
        key.Close()
        
        return {
            "success": True,
            "message": f"✅ Accent color set to #{color_hex}",
            "color": color_hex
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to set accent color: {str(e)}"
        }


# ============================================================================
# APP PREFERENCES
# ============================================================================

def _attempt_elevate_privileges() -> bool:
    """
    Attempt to elevate to admin privileges using PowerShell UAC prompt.
    
    Returns:
        True if successfully elevated or already admin, False otherwise
    """
    import ctypes
    import sys
    
    try:
        # Check if already admin
        if ctypes.windll.shell.IsUserAnAdmin():
            return True
    except:
        pass
    
    # Try to elevate privileges
    try:
        # Create a minimal PowerShell script that re-runs with elevation
        ps_cmd = """
        if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] 'Administrator')) {
            Start-Process powershell.exe -Verb runas -ArgumentList '-NoExit', '-Command', 'Set-Location \\'%cd%\\''; Exit
        }
        """ % {"cd": os.getcwd()}
        
        # Attempt to run with elevation
        subprocess.Popen(
            ["powershell.exe", "-Command", ps_cmd],
            shell=False,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        return True
    except Exception as e:
        return False


def set_default_app(app_type: str, app_path: str) -> dict:
    """
    Set default application for file type.
    Automatically requests admin privileges if needed.
    
    Args:
        app_type: Type (browser, mail, image_viewer, text_editor)
        app_path: Path to application executable
    
    Returns:
        dict with success status
    """
    import ctypes
    import tempfile
    import time
    import sys
    
    try:
        # Check if running as administrator
        try:
            is_admin = ctypes.windll.shell.IsUserAnAdmin()
        except:
            is_admin = False
        
        if not is_admin:
            # Windows 10/11 uses hash-protected registry for default apps
            # The only reliable way is to open Settings where user can set it properly
            print("\n🔄 Opening Windows Settings for Default Apps...")
            print("   ℹ️  Please select your preferred app from the list.\n")
            
            try:
                import subprocess as sp
                import os
                
                # Open Windows Settings to Default Apps page using Windows URI protocol
                # Use cmd.exe to launch the URI (more reliable than direct subprocess)
                os.system("start ms-settings:defaultapps")
                
                return {
                    "success": True,
                    "message": f"✅ Opened Windows Settings - please select your preferred {app_type}",
                    "app_type": app_type,
                    "app_path": app_path,
                    "elevated": False,
                    "method": "manual_via_settings",
                    "note": "Windows 10/11 uses protected registry. Settings dialog is the reliable way to set defaults."
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": str(type(e).__name__),
                    "message": f"❌ Could not open Settings: {str(e)[:40]}",
                    "workaround": "Manually open Settings > Apps > Default apps and select your browser"
                }
        
        # Already admin - do it directly
        if not Path(app_path).exists():
            return {
                "success": False,
                "error": f"App not found: {app_path}",
                "message": f"❌ App not found: {app_path}"
            }
        
        # Registry mappings
        registry_mappings = {
            "browser": {
                "key": r"Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.html\UserChoice",
                "prog_id": "htmlfile"
            },
            "mail": {
                "key": r"Software\Microsoft\Windows\CurrentVersion\Explorer\mailto",
                "prog_id": "mailto"
            },
            "text_editor": {
                "key": r"Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.txt\UserChoice",
                "prog_id": "txtfile"
            },
            "image_viewer": {
                "key": r"Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jpg\UserChoice",
                "prog_id": "jpgfile"
            }
        }
        
        if app_type not in registry_mappings:
            return {
                "success": False,
                "error": f"Unsupported: {app_type}",
                "message": f"❌ Unsupported app type. Supported: {list(registry_mappings.keys())}"
            }
        
        mapping = registry_mappings[app_type]
        reg = ConnectRegistry(None, HKEY_CURRENT_USER)
        key = OpenKey(reg, mapping["key"], 0, 0x20002)
        SetValueEx(key, "Progid", 0, REG_SZ, mapping["prog_id"])
        key.Close()
        
        return {
            "success": True,
            "message": f"✅ Default {app_type} set to: {Path(app_path).name}",
            "app_type": app_type,
            "app_path": app_path
        }
    except PermissionError:
        return {
            "success": False,
            "error": "PERM_DENIED",
            "message": f"❌ Permission denied.",
            "workaround": "Right-click PowerShell → Run as Administrator",
            "manual_option": "Or set in Windows Settings > Apps > Default apps"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)[:30],
            "message": f"❌ Failed: {str(e)[:50]}"
        }



def manage_startup_apps(app_name: str, action: str) -> dict:
    """
    Add or remove app from startup.
    
    Args:
        app_name: Application name
        action: 'enable' or 'disable'
    
    Returns:
        dict with success status
    """
    try:
        startup_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        reg = ConnectRegistry(None, HKEY_CURRENT_USER)
        
        if action.lower() == "enable":
            key = OpenKey(reg, startup_key, 0, 0x20002)
            SetValueEx(key, app_name, 0, REG_SZ, f"C:\\Program Files\\{app_name}\\{app_name}.exe")
            key.Close()
            
            return {
                "success": True,
                "message": f"✅ {app_name} added to startup",
                "app": app_name,
                "action": "enabled"
            }
        
        elif action.lower() == "disable":
            key = OpenKey(reg, startup_key, 0, 0x20002)
            # Delete the value if it exists
            try:
                import winreg
                winreg.DeleteValue(key, app_name)
            except:
                pass
            key.Close()
            
            return {
                "success": True,
                "message": f"✅ {app_name} removed from startup",
                "app": app_name,
                "action": "disabled"
            }
        
        else:
            return {
                "success": False,
                "error": "Action must be 'enable' or 'disable'",
                "message": "❌ Invalid action"
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to manage startup app: {str(e)}"
        }


# ============================================================================
# PERSONALIZATION RECIPES (Preset Configurations)
# ============================================================================

def apply_theme_preset(preset_name: str) -> dict:
    """
    Apply a preset personalization theme.
    
    Args:
        preset_name: 'dark', 'light', 'office', 'gaming', 'minimal'
    
    Returns:
        dict with applied settings
    """
    presets = {
        "dark": {
            "dark_mode": True,
            "accent_color": "0066CC",
            "brightness": 50,
            "description": "Dark theme with cool accent"
        },
        "light": {
            "dark_mode": False,
            "accent_color": "00A0FF",
            "brightness": 100,
            "description": "Light theme for bright environments"
        },
        "office": {
            "dark_mode": False,
            "accent_color": "2E5090",
            "brightness": 80,
            "description": "Professional office theme"
        },
        "gaming": {
            "dark_mode": True,
            "accent_color": "FF0066",
            "brightness": 100,
            "description": "High contrast gaming theme"
        },
        "minimal": {
            "dark_mode": True,
            "accent_color": "808080",
            "brightness": 60,
            "description": "Minimal grayscale theme"
        }
    }
    
    if preset_name not in presets:
        return {
            "success": False,
            "error": f"Preset '{preset_name}' not found",
            "available_presets": list(presets.keys()),
            "message": f"❌ Unknown preset"
        }
    
    preset = presets[preset_name]
    results = []
    
    # Apply dark mode
    result = toggle_dark_mode(preset["dark_mode"])
    results.append(result)
    
    # Apply accent color
    result = set_accent_color(preset["accent_color"])
    results.append(result)
    
    # Apply brightness
    result = set_display_brightness(preset["brightness"])
    results.append(result)
    
    return {
        "success": True,
        "preset": preset_name,
        "description": preset["description"],
        "applied_settings": preset,
        "results": results,
        "message": f"✅ Theme '{preset_name}' applied successfully"
    }


def save_personalization_profile(profile_name: str, settings: dict) -> dict:
    """
    Save current personalization settings to a profile file.
    
    Args:
        profile_name: Name of the profile
        settings: Dict of settings to save
    
    Returns:
        dict with save status
    """
    try:
        profiles_dir = Path(__file__).parent / "profiles"
        profiles_dir.mkdir(exist_ok=True)
        
        profile_path = profiles_dir / f"{profile_name}.json"
        
        with open(profile_path, 'w') as f:
            json.dump(settings, f, indent=2)
        
        return {
            "success": True,
            "message": f"✅ Profile saved: {profile_name}",
            "profile_path": str(profile_path),
            "profile": profile_name
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to save profile: {str(e)}"
        }


def load_personalization_profile(profile_name: str) -> dict:
    """
    Load a saved personalization profile.
    
    Args:
        profile_name: Name of the profile
    
    Returns:
        dict with loaded settings
    """
    try:
        profiles_dir = Path(__file__).parent / "profiles"
        profile_path = profiles_dir / f"{profile_name}.json"
        
        if not profile_path.exists():
            return {
                "success": False,
                "error": f"Profile not found: {profile_name}",
                "message": f"❌ Profile not found"
            }
        
        with open(profile_path, 'r') as f:
            settings = json.load(f)
        
        return {
            "success": True,
            "message": f"✅ Profile loaded: {profile_name}",
            "settings": settings,
            "profile": profile_name
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to load profile: {str(e)}"
        }
