"""
Main Installer Agent
====================
Orchestrates downloading and installing resources via the Master Agent system.
"""

import os
import logging
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
    
    def install_software(
        self,
        app_name: str,
        folder: str = None
    ) -> Dict:
        """
        Find and download software installer.
        
        Args:
            app_name: Application name (e.g., "vlc media player", "python 3.12")
            folder: Save to this folder (default: Downloads/Installers)
            
        Example:
            install_software("vlc media player")
            install_software("python 3.12")
            
        Returns:
            {
                "status": "success|failed",
                "installer_path": "/path/to/installer.exe",
                "message": "Downloaded vlc_installer.exe",
                "next_step": "User should run installer manually"
            }
        """
        logger.info(f"Finding software: {app_name}")
        
        # Generate cache key
        cache_key = f"software_{app_name.lower().replace(' ', '_')}"
        
        # Check cache first
        cached = self.cache.get_cached_resource(cache_key)
        if cached:
            logger.info(f"Found software installer in cache: {cached['path']}")
            return {
                "status": "success",
                "installer_path": cached["path"],
                "from_cache": True,
                "message": f"Found cached installer (installation requires manual run)"
            }
        
        # Find resource
        print(f"🔍 Searching for '{app_name}'...")
        resource = self.finder.find_resource(app_name, "software")
        
        if not resource:
            logger.warning(f"No installer found for: {app_name}")
            return {
                "status": "failed",
                "message": f"No installer found for '{app_name}'"
            }
        
        logger.info(f"Found software: {resource.get('name')}")
        
        # Set download folder
        folder = folder or str(Path.home() / "Downloads" / "Installers")
        os.makedirs(folder, exist_ok=True)
        
        # Download
        filename = resource.get("filename", f"{app_name.replace(' ', '_')}_installer.exe")
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
            "app_name": app_name,
            "source": resource.get("source"),
            "version": resource.get("version")
        })
        
        logger.info(f"Installer cached: {filepath}")
        
        return {
            "status": "success",
            "installer_path": filepath,
            "from_cache": False,
            "message": result.get("message"),
            "next_step": f"⚠️  Please run the installer manually: {filename}"
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
