"""
Main Installer Agent
====================
Orchestrates downloading and installing resources via the Master Agent system.
"""

import os
import logging
import subprocess
import zipfile
from pathlib import Path
from typing import Dict, Callable, Optional
import uuid

from installer.resource_finder import ResourceFinder
from installer.downloader import Downloader
from installer.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class InstallerAgent:
    """
    Download and install resources:
    - Wallpapers (auto-set as background)
    - Software installers
    - Themes
    - Documents
    - Any internet-accessible resource
    
    Features:
    - Smart search via LLM
    - Caching to avoid re-downloads
    - Progress tracking
    - Auto-setup (e.g., set wallpaper after download)
    """
    
    def __init__(self):
        """Initialize installer agent."""
        self.finder = ResourceFinder()
        self.downloader = Downloader()
        self.cache = CacheManager()
        
        logger.info("Installer Agent initialized")
    
    def install_wallpaper(
        self,
        query: str,
        folder: str = None,
        auto_set: bool = False
    ) -> Dict:
        """
        Find and download wallpaper, optionally set as desktop background.
        
        Args:
            query: Wallpaper description (e.g., "sunset landscape", "mountain")
            folder: Save to this folder (default: Pictures/Wallpapers)
            auto_set: Automatically set as desktop background
            
        Example:
            install_wallpaper("sunset landscape")
            install_wallpaper("mountain", auto_set=True)
            
        Returns:
            {
                "status": "success|failed",
                "wallpaper_path": "/path/to/wallpaper.jpg",
                "from_cache": bool,
                "auto_set": bool,
                "message": "Downloaded sunset.jpg"
            }
        """
        logger.info(f"Finding wallpaper: {query}")
        
        # Generate cache key
        cache_key = f"wallpaper_{query.lower().replace(' ', '_')}"
        
        # Check cache first
        cached = self.cache.get_cached_resource(cache_key)
        if cached:
            logger.info(f"Found wallpaper in cache: {cached['path']}")
            
            result = {
                "status": "success",
                "wallpaper_path": cached["path"],
                "from_cache": True,
                "auto_set": False,
                "message": f"Found cached wallpaper (cached at {cached['cached_at']})"
            }
            
            # Auto-set wallpaper if requested
            if auto_set:
                set_result = self._set_wallpaper(cached["path"])
                result["auto_set"] = set_result["status"] == "success"
                if result["auto_set"]:
                    result["message"] += " and set as background"
            
            return result
        
        # Find resource
        print(f"🔍 Searching for '{query}'...")
        resource = self.finder.find_resource(query, "wallpaper")
        
        if not resource:
            logger.warning(f"No wallpaper found for: {query}")
            return {
                "status": "failed",
                "message": f"No wallpaper found for '{query}'"
            }
        
        logger.info(f"Found wallpaper: {resource.get('name')}")
        
        # Set download folder
        folder = folder or str(Path.home() / "Pictures" / "Wallpapers")
        os.makedirs(folder, exist_ok=True)
        
        # Download
        filename = resource.get("filename", f"{query.replace(' ', '_')}.jpg")
        print(f"⬇️  Downloading {filename}...")
        
        result = self.downloader.download_file(
            url=resource["url"],
            filename=filename,
            folder=folder,
            show_progress=True
        )
        
        if result["status"] != "success":
            logger.error(f"Download failed: {result.get('message')}")
            return result
        
        # Cache it
        filepath = result["path"]
        self.cache.cache_resource(cache_key, filepath, {
            "query": query,
            "source": resource.get("source"),
            "author": resource.get("author")
        })
        
        logger.info(f"Wallpaper cached: {filepath}")
        
        # Prepare response
        response = {
            "status": "success",
            "wallpaper_path": filepath,
            "from_cache": False,
            "auto_set": False,
            "message": result.get("message")
        }
        
        # Auto-set wallpaper if requested
        if auto_set:
            set_result = self._set_wallpaper(filepath)
            response["auto_set"] = set_result["status"] == "success"
            if response["auto_set"]:
                response["message"] += " and set as background"
        
        return response
    
    # ------------------------------------------------------------------
    # Winget helpers
    # ------------------------------------------------------------------

    def _winget_search(self, app_name: str) -> Optional[str]:
        """
        Run `winget search <app_name>` and return the best package ID.
        Returns None if winget is not available or nothing matched.
        """
        try:
            result = subprocess.run(
                ["winget", "search", "--name", app_name, "--accept-source-agreements"],
                capture_output=True, text=True, timeout=20
            )
            lines = result.stdout.splitlines()
            # Skip header lines (first 2-3 lines are the table header)
            data_lines = [l for l in lines if l.strip() and "---" not in l]
            if len(data_lines) <= 2:
                return None  # only header rows

            # First data line after header — columns: Name  Id  Version  Source
            for line in data_lines[2:]:
                parts = line.split()
                if len(parts) >= 2:
                    pkg_id = parts[1]  # the Id column
                    if "." in pkg_id:   # winget IDs always have a . (e.g. VideoLAN.VLC)
                        logger.info(f"winget found package: {pkg_id}")
                        return pkg_id
        except FileNotFoundError:
            logger.warning("winget not available on this system")
        except Exception as e:
            logger.warning(f"winget search failed: {e}")
        return None

    def winget_install(self, app_name: str) -> Dict:
        """
        Search for and install an app via winget.

        Args:
            app_name: e.g. "VLC", "Python", "7-Zip"

        Returns:
            {"status": "success|failed", "message": "..."}
        """
        print(f"🔍 Searching winget for: {app_name}")
        pkg_id = self._winget_search(app_name)

        if not pkg_id:
            return {
                "status": "failed",
                "message": f"'{app_name}' not found in winget catalog"
            }

        print(f"📦 Installing {pkg_id} via winget (silent)...")
        logger.info(f"Running: winget install --id {pkg_id}")

        def _run_winget(extra_args=None):
            cmd = [
                "winget", "install",
                "--id", pkg_id,
                "--silent",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ]
            if extra_args:
                cmd += extra_args
            return subprocess.run(cmd, capture_output=False, timeout=600)

        try:
            # First try with --source winget (avoids msstore certificate errors)
            result = _run_winget(["--source", "winget"])

            # If package not in winget source, retry without --source flag
            if result.returncode not in (0, -1978335189) and result.returncode == 2316632222:  # no package on that source
                logger.info("Package not found on winget source alone — retrying without --source")
                result = _run_winget()

            if result.returncode == 0:
                msg = f"{app_name} installed successfully via winget (id: {pkg_id})"
                logger.info(msg)
                return {"status": "success", "message": f"✅ {msg}", "package_id": pkg_id}
            elif result.returncode == -1978335189:   # WINGET_E_ALREADY_INSTALLED
                msg = f"{app_name} is already installed"
                logger.info(msg)
                return {"status": "success", "message": f"ℹ️  {msg}", "package_id": pkg_id}
            else:
                msg = f"winget exited with code {result.returncode}"
                logger.warning(msg)  # no emoji - avoids cp1252 UnicodeEncodeError
                return {"status": "failed", "message": f"⚠️  {msg}", "package_id": pkg_id}

        except subprocess.TimeoutExpired:
            return {"status": "failed", "message": "Installation timed out (>10 min)"}
        except Exception as e:
            logger.error(f"winget install failed: {e}")
            return {"status": "failed", "message": str(e)}

    # ------------------------------------------------------------------
    # Software install (winget-first, LLM-download fallback)
    # ------------------------------------------------------------------

    def install_software(
        self,
        app_name: str,
        folder: str = None
    ) -> Dict:
        """
        Install software — tries winget first, then falls back to LLM-URL download.

        Args:
            app_name: Application name (e.g., "vlc media player", "python 3.12")
            folder: Fallback download folder (default: Downloads/Installers)

        Returns:
            {"status": "success|failed", "message": "..."}
        """
        logger.info(f"Finding software: {app_name}")
        print(f"🔍 Finding software: {app_name}")

        # ── 1. Try winget (fastest + most reliable on Windows) ─────────
        winget_result = self.winget_install(app_name)
        if winget_result.get("status") == "success":
            return winget_result

        print(f"⚠️  winget didn't work ({winget_result.get('message')}). Trying download fallback...")
        logger.info("Falling back to LLM-URL download method")

        # ── 2. Fallback: LLM finds download URL, we download + run installer ──
        # Check cache first
        cache_key = f"software_{app_name.lower().replace(' ', '_')}"
        cached = self.cache.get_cached_resource(cache_key)
        if cached and os.path.exists(cached.get("path", "")):
            logger.info(f"Found cached installer: {cached['path']}")
            return {
                "status": "success",
                "installer_path": cached["path"],
                "from_cache": True,
                "message": f"Found cached installer (run it to install)"
            }

        print(f"🔍 Searching online for '{app_name}'...")
        resource = self.finder.find_resource(app_name, "software")
        if not resource:
            return {
                "status": "failed",
                "message": (
                    f"Could not find '{app_name}' via winget or online search.\n"
                    f"Tip: try running  winget search {app_name}  manually."
                )
            }

        logger.info(f"Found installer online: {resource.get('name')}")
        folder = folder or str(Path.home() / "Downloads" / "Installers")
        os.makedirs(folder, exist_ok=True)

        filename = resource.get("filename", f"{app_name.replace(' ', '_')}_installer.exe")
        print(f"⬇️  Downloading {filename}...")

        dl = self.downloader.download_file(
            url=resource["url"],
            filename=filename,
            folder=folder,
            show_progress=True
        )

        if dl.get("status") != "success":
            logger.error(f"Download failed: {dl.get('message')}")
            return dl

        filepath = dl["path"]
        self.cache.cache_resource(cache_key, filepath, {
            "app_name": app_name,
            "source": resource.get("source"),
            "version": resource.get("version")
        })

        return {
            "status": "success",
            "installer_path": filepath,
            "from_cache": False,
            "message": dl.get("message"),
            "can_execute": True,
            "next_step": f"⚠️  Ready to install: {filename}"
        }

    
    # ------------------------------------------------------------------
    # Fuzzy installer finder
    # ------------------------------------------------------------------

    def _fuzzy_find_installer(self, installer_path: str) -> Optional[str]:
        """
        When the exact installer path doesn't exist, search the same directory
        for any .exe / .msi / .zip whose filename contains the key words from
        the intended filename.

        Example:
            installer_path = "C:/Users/.../Installers/Discord.exe"
            → finds "C:/Users/.../Installers/Discord Setup.exe" ✅

        Returns the resolved path, or None if nothing was found.
        """
        import re
        directory = os.path.dirname(os.path.abspath(installer_path)) if os.path.dirname(installer_path) else str(Path.home() / "Downloads" / "Installers")
        if not os.path.isdir(directory):
            return None

        stem = Path(installer_path).stem.lower()   # e.g. "discord"
        keywords = [w for w in re.split(r'[\s_\-]+', stem) if len(w) > 2]

        best_match: Optional[str] = None
        best_score = 0

        for fname in os.listdir(directory):
            fpath = os.path.join(directory, fname)
            if not os.path.isfile(fpath):
                continue
            ext = Path(fname).suffix.lower()
            if ext not in ('.exe', '.msi', '.zip'):
                continue

            fname_lower = fname.lower()
            score = sum(1 for kw in keywords if kw in fname_lower)
            if score > best_score:
                best_score = score
                best_match = fpath

        if best_match and best_score > 0:
            logger.info(f"Fuzzy match: '{installer_path}' -> '{best_match}' (score={best_score})")
            return best_match

        return None

    def execute_installer(self, installer_path: str) -> Dict:
        """
        Execute downloaded installer with elevation if needed.
        
        Supports:
        - .exe files (Windows executables)
        - .msi files (Windows installer packages)
        - .zip files (Extract to folder)
        
        Args:
            installer_path: Path to the installer file (fuzzy-matched if not found exactly)
            
        Returns:
            {
                "status": "success|failed|extract",
                "message": "...",
                "extracted_to": "/path/to/extraction" (if .zip)
            }
        """
        logger.info(f"Executing installer: {installer_path}")
        
        if not os.path.exists(installer_path):
            # Try fuzzy match before giving up
            resolved = self._fuzzy_find_installer(installer_path)
            if resolved:
                print(f"🔍 Exact file not found — using closest match: {os.path.basename(resolved)}")
                installer_path = resolved
            else:
                logger.error(f"Installer not found: {installer_path}")
                return {
                    "status": "failed",
                    "message": f"Installer file not found: {installer_path}"
                }

        
        filename = os.path.basename(installer_path)
        file_ext = os.path.splitext(installer_path)[1].lower()
        
        try:
            if file_ext == ".exe":
                return self._execute_exe(installer_path, filename)
            
            elif file_ext == ".msi":
                return self._execute_msi(installer_path, filename)
            
            elif file_ext == ".zip":
                return self._extract_zip(installer_path)
            
            else:
                logger.warning(f"Unknown file type: {file_ext}")
                return {
                    "status": "failed",
                    "message": f"Unsupported file type: {file_ext}"
                }
        
        except Exception as e:
            logger.error(f"Installation failed: {e}")
            return {
                "status": "failed",
                "message": f"Installation error: {str(e)}"
            }
    
    def _execute_exe(self, filepath: str, filename: str) -> Dict:
        """
        Execute .exe installer with elevation.
        
        Uses 'runas' on Windows to request admin privileges.
        """
        logger.info(f"Executing .exe installer: {filepath}")
        
        try:
            # Try to execute with admin privileges
            print(f"🚀 Starting installation of {filename}...")
            print(f"   ℹ️  Admin privileges may be requested")
            
            # Use runas verb to elevate privileges (Windows)
            import ctypes
            
            # Try creating a process with elevation
            try:
                subprocess.Popen([filepath], shell=True)
                logger.info("Installer launched successfully")
                
                return {
                    "status": "success",
                    "message": f"✅ Installation started: {filename}",
                    "instructions": "Please follow the installer prompts to complete installation"
                }
            
            except Exception as e:
                logger.warning(f"Standard launch failed, trying alternate method: {e}")
                
                # Fallback: use os.startfile (Windows only)
                os.startfile(filepath)
                
                return {
                    "status": "success",
                    "message": f"✅ Installer opened: {filename}",
                    "instructions": "Please follow the installer prompts to complete installation"
                }
        
        except Exception as e:
            logger.error(f"Failed to execute .exe: {e}")
            return {
                "status": "failed",
                "message": f"Failed to start installer: {str(e)}",
                "manual_instruction": f"Please manually run: {filepath}"
            }
    
    def _execute_msi(self, filepath: str, filename: str) -> Dict:
        """
        Execute .msi installer.
        
        Uses msiexec.exe on Windows to install MSI packages.
        """
        logger.info(f"Executing .msi installer: {filepath}")
        
        try:
            print(f"🚀 Starting installation of {filename}...")
            
            # Use msiexec to install MSI package
            command = f'msiexec /i "{filepath}" /quiet /norestart'
            
            # For interactive install:
            # command = f'msiexec /i "{filepath}"'
            
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = process.communicate(timeout=300)  # 5 min timeout
            
            logger.info("MSI installation completed")
            
            if process.returncode == 0:
                return {
                    "status": "success",
                    "message": f"✅ Installation completed: {filename}",
                    "return_code": process.returncode
                }
            else:
                logger.warning(f"MSI installer returned code {process.returncode}")
                return {
                    "status": "failed",
                    "message": f"Installation may have failed (exit code: {process.returncode})",
                    "return_code": process.returncode
                }
        
        except subprocess.TimeoutExpired:
            logger.error("MSI installer timeout")
            return {
                "status": "failed",
                "message": "Installation timeout (>5 minutes). Please check if installer is still running."
            }
        
        except Exception as e:
            logger.error(f"Failed to execute .msi: {e}")
            return {
                "status": "failed",
                "message": f"Failed to start installer: {str(e)}",
                "manual_instruction": f"Please manually run: msiexec /i \"{filepath}\""
            }
    
    def _extract_zip(self, filepath: str) -> Dict:
        """
        Extract .zip file to a folder.
        
        Args:
            filepath: Path to .zip file
            
        Returns:
            {
                "status": "extract|failed",
                "extracted_to": "/path/to/extraction",
                "message": "..."
            }
        """
        logger.info(f"Extracting .zip: {filepath}")
        
        try:
            # Create extraction folder
            extract_folder = os.path.splitext(filepath)[0]
            os.makedirs(extract_folder, exist_ok=True)
            
            print(f"📦 Extracting {os.path.basename(filepath)}...")
            
            # Extract zip file
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(extract_folder)
            
            logger.info(f"Extracted to: {extract_folder}")
            
            # Count extracted files
            file_count = sum(len(files) for _, _, files in os.walk(extract_folder))
            
            return {
                "status": "extract",
                "extracted_to": extract_folder,
                "file_count": file_count,
                "message": f"✅ Extracted {file_count} files to: {extract_folder}",
                "instructions": "Please check the extracted folder for executable files or documentation"
            }
        
        except Exception as e:
            logger.error(f"Failed to extract .zip: {e}")
            return {
                "status": "failed",
                "message": f"Failed to extract: {str(e)}"
            }
    
    def download_resource(
        self,
        query: str,
        resource_type: str,
        folder: str = None,
        on_progress: Callable = None
    ) -> Dict:
        """
        Generic download for any resource type.
        
        Args:
            query: Search query (e.g., "sunset wallpaper", "python 3.12")
            resource_type: "wallpaper", "software", "image", "document"
            folder: Download to this folder
            on_progress: Progress callback function(downloaded, total, percent)
            
        Returns:
            {
                "status": "success|failed",
                "path": "/path/to/file",
                "size": 1234567,
                "message": "Downloaded file.ext"
            }
        """
        logger.info(f"Downloading {resource_type}: {query}")
        
        # Generate cache key
        cache_key = f"{resource_type}_{query.lower().replace(' ', '_')}"
        
        # Check cache
        cached = self.cache.get_cached_resource(cache_key)
        if cached:
            logger.info(f"Found {resource_type} in cache: {cached['path']}")
            return {
                "status": "success",
                "path": cached["path"],
                "from_cache": True,
                "message": f"Found cached {resource_type}"
            }
        
        # Find resource
        print(f"🔍 Searching for {resource_type}: {query}...")
        resource = self.finder.find_resource(query, resource_type)
        
        if not resource:
            logger.warning(f"No {resource_type} found for: {query}")
            return {
                "status": "failed",
                "message": f"No {resource_type} found for '{query}'"
            }
        
        logger.info(f"Found {resource_type}: {resource.get('name')}")
        
        # Set download folder
        folder = folder or str(Path.home() / "Downloads")
        
        # Download
        filename = resource.get("filename")
        print(f"⬇️  Downloading {filename or query}...")
        
        result = self.downloader.download_file(
            url=resource["url"],
            filename=filename,
            folder=folder,
            on_progress=on_progress,
            show_progress=True
        )
        
        if result["status"] == "success":
            # Cache it
            self.cache.cache_resource(cache_key, result["path"], resource)
            logger.info(f"{resource_type.capitalize()} cached: {result['path']}")
        
        return result
    
    def _set_wallpaper(self, filepath: str) -> Dict:
        """
        Set wallpaper as desktop background using personalisation tools.
        
        Args:
            filepath: Path to wallpaper file
            
        Returns:
            {
                "status": "success|failed",
                "message": "..."
            }
        """
        try:
            from personalisation.personalisation_tools import set_wallpaper
            
            logger.info(f"Setting wallpaper: {filepath}")
            result = set_wallpaper(filepath)
            
            if result.get("success"):
                logger.info("Wallpaper set successfully")
                return {
                    "status": "success",
                    "message": result.get("message", "Wallpaper set")
                }
            else:
                logger.error(f"Failed to set wallpaper: {result.get('error')}")
                return {
                    "status": "failed",
                    "message": result.get("message", "Failed to set wallpaper")
                }
        
        except Exception as e:
            logger.error(f"Error setting wallpaper: {e}")
            return {
                "status": "failed",
                "message": f"Error: {str(e)}"
            }
    
    def get_cache_info(self) -> Dict:
        """Get cache statistics."""
        return self.cache.get_cache_size()
    
    def clear_cache(self, query: str = None) -> Dict:
        """
        Clear cache.
        
        Args:
            query: Clear specific item (None = clear all)
            
        Returns:
            {
                "status": "success|failed",
                "message": "..."
            }
        """
        if query:
            cache_key = f"*{query}*"
            # Find matching items
            results = self.cache.search_cache(query)
            removed = 0
            for resource_id in results.keys():
                if self.cache.remove_cached_resource(resource_id):
                    removed += 1
            
            return {
                "status": "success",
                "message": f"Cleared {removed} cached items"
            }
        else:
            if self.cache.clear_cache():
                return {
                    "status": "success",
                    "message": "Cache cleared completely"
                }
            else:
                return {
                    "status": "failed",
                    "message": "Failed to clear cache"
                }
