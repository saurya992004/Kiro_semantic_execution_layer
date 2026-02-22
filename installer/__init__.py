"""
Installer Agent Module
======================
Download and install resources from the internet.

Usage:
    from installer.installer import InstallerAgent
    
    agent = InstallerAgent()
    result = agent.install_wallpaper("sunset landscape")
    
    result = agent.install_software("vlc media player")
    
    result = agent.download_resource("python 3.12", "software")
"""

from installer.installer import InstallerAgent
from installer.resource_finder import ResourceFinder
from installer.downloader import Downloader
from installer.cache_manager import CacheManager

__all__ = [
    "InstallerAgent",
    "ResourceFinder",
    "Downloader",
    "CacheManager"
]
