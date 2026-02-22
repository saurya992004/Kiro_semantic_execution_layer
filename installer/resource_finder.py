"""
Resource Finder for Installer Agent
====================================
Searches the internet for required resources (wallpapers, software, images, etc.)
"""

import logging
import requests
from typing import List, Dict, Optional
from llm.groq_client import GroqClient

logger = logging.getLogger(__name__)


class ResourceFinder:
    """
    Finds downloadable resources online using:
    1. Web search (via LLM)
    2. Specific APIs (Unsplash, Pexels for wallpapers)
    3. LLM reasoning (to pick best option)
    """
    
    def __init__(self):
        """Initialize resource finder."""
        self.llm = GroqClient()
        
        # API keys for specific services
        self.unsplash_api_key = self._get_api_key("unsplash")
        self.pexels_api_key = self._get_api_key("pexels")
    
    def _get_api_key(self, service: str) -> Optional[str]:
        """Get API key from environment or return None."""
        import os
        return os.getenv(f"{service.upper()}_API_KEY")
    
    def find_resource(self, query: str, resource_type: str) -> Optional[Dict]:
        """
        Find a resource online.
        
        Args:
            query: "sunset wallpaper" or "python 3.12"
            resource_type: "wallpaper", "software", "image", "document"
            
        Returns:
            {
                "name": "Beautiful Sunset",
                "url": "https://...",
                "size": "2.5MB",
                "quality": "high",
                "format": "jpg",
                "source": "unsplash",
                "filename": "beautiful_sunset.jpg"
            }
            or None if not found
        """
        logger.info(f"Finding {resource_type}: {query}")
        
        try:
            if resource_type == "wallpaper":
                return self.search_wallpapers(query)
            elif resource_type == "software":
                return self.search_software(query)
            elif resource_type == "image":
                return self.search_images(query)
            else:
                return self.search_generic(query, resource_type)
        
        except Exception as e:
            logger.error(f"Resource search failed: {e}")
            return None
    
    def search_wallpapers(self, query: str) -> Optional[Dict]:
        """
        Search for wallpapers from free sources.
        Priority: Unsplash > Pexels > Pixabay > Google Images
        """
        logger.info(f"Searching wallpapers: {query}")
        
        # Try Unsplash first (highest quality)
        if self.unsplash_api_key:
            result = self._search_unsplash(query)
            if result:
                return result
        
        # Try Pexels
        if self.pexels_api_key:
            result = self._search_pexels(query)
            if result:
                return result
        
        # Fallback: Use web search via LLM
        return self._search_generic_wallpaper(query)
    
    def _search_unsplash(self, query: str) -> Optional[Dict]:
        """Search Unsplash API for images."""
        try:
            url = "https://api.unsplash.com/search/photos"
            params = {
                "query": query,
                "client_id": self.unsplash_api_key,
                "per_page": 1,
                "orientation": "landscape"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get("results"):
                result = data["results"][0]
                return {
                    "name": result.get("description", query),
                    "url": result["urls"]["full"],
                    "download_url": result["links"]["download"],
                    "size": "high resolution",
                    "quality": "high",
                    "format": "jpg",
                    "source": "unsplash",
                    "author": result.get("user", {}).get("name", "Unknown"),
                    "filename": f"{query.replace(' ', '_')}_unsplash.jpg"
                }
        
        except Exception as e:
            logger.warning(f"Unsplash search failed: {e}")
        
        return None
    
    def _search_pexels(self, query: str) -> Optional[Dict]:
        """Search Pexels API for images."""
        try:
            url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": self.pexels_api_key}
            params = {
                "query": query,
                "per_page": 1,
                "orientation": "landscape"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get("photos"):
                result = data["photos"][0]
                return {
                    "name": query,
                    "url": result["src"]["original"],
                    "size": f"{result['width']}x{result['height']}",
                    "quality": "high",
                    "format": "jpg",
                    "source": "pexels",
                    "photographer": result.get("photographer", "Unknown"),
                    "filename": f"{query.replace(' ', '_')}_pexels.jpg"
                }
        
        except Exception as e:
            logger.warning(f"Pexels search failed: {e}")
        
        return None
    
    def _search_generic_wallpaper(self, query: str) -> Optional[Dict]:
        """Fallback: Use LLM to find wallpaper sources."""
        logger.info(f"Using fallback wallpaper search for: {query}")
        
        prompt = f"""
You are a resource finder. Find a high-quality wallpaper for: {query}

Search for free wallpaper sources and return the BEST ONE with a direct download URL.
Popular sources: unsplash.com, pexels.com, pixabay.com, wallpaperscraft.com

Return ONLY valid JSON (no other text):
{{
  "name": "image name",
  "url": "direct download URL",
  "quality": "high|medium",
  "format": "jpg|png",
  "source": "source name",
  "filename": "filename.jpg"
}}
"""
        
        try:
            response = self.llm.generate(prompt)
            from utils.json_parser import extract_json
            result = extract_json(response)
            
            if isinstance(result, dict) and "url" in result:
                return result
        
        except Exception as e:
            logger.error(f"Fallback wallpaper search failed: {e}")
        
        return None
    
    def search_software(self, query: str) -> Optional[Dict]:
        """
        Search for software installers.
        Priority: Official repos > GitHub > SourceForge > Direct downloads
        """
        logger.info(f"Searching software: {query}")
        
        prompt = f"""
You are a software finder. Find an installer for: {query}

IMPORTANT:
- Only search official sources and reputable repositories
- Prefer direct downloads from official websites
- GitHub releases for open source
- SourceForge for verified software

Return ONLY valid JSON:
{{
  "name": "software name",
  "version": "version number",
  "url": "direct installer download URL",
  "format": "exe|msi|zip|dmg",
  "source": "official/github/sourceforge",
  "size": "approximate size",
  "filename": "installer_name.exe"
}}
"""
        
        try:
            response = self.llm.generate(prompt)
            from utils.json_parser import extract_json
            result = extract_json(response)
            
            if isinstance(result, dict) and "url" in result:
                return result
        
        except Exception as e:
            logger.error(f"Software search failed: {e}")
        
        return None
    
    def search_images(self, query: str) -> Optional[Dict]:
        """Search for general images."""
        logger.info(f"Searching images: {query}")
        
        # Try wallpaper methods first (same as wallpapers)
        return self.search_wallpapers(query)
    
    def search_generic(self, query: str, resource_type: str) -> Optional[Dict]:
        """
        Generic search for any resource type using LLM.
        """
        logger.info(f"Generic search for {resource_type}: {query}")
        
        prompt = f"""
Find a downloadable {resource_type} for: {query}

Return ONLY valid JSON with direct download URL:
{{
  "name": "resource name",
  "url": "direct download URL",
  "type": "{resource_type}",
  "format": "file format",
  "source": "source name",
  "filename": "filename"
}}
"""
        
        try:
            response = self.llm.generate(prompt)
            from utils.json_parser import extract_json
            result = extract_json(response)
            
            if isinstance(result, dict) and "url" in result:
                return result
        
        except Exception as e:
            logger.error(f"Generic search failed: {e}")
        
        return None
    
    def rank_results(self, results: List[Dict]) -> Optional[Dict]:
        """Use LLM to pick the best result from multiple options."""
        if not results:
            return None
        
        if len(results) == 1:
            return results[0]
        
        logger.info(f"Ranking {len(results)} results")
        
        prompt = f"""
Pick the BEST resource from these options based on quality, size, and source reliability:

{results}

Return ONLY the chosen option in JSON format (no explanation).
"""
        
        try:
            response = self.llm.generate(prompt)
            from utils.json_parser import extract_json
            result = extract_json(response)
            
            if isinstance(result, dict) and "url" in result:
                return result
        
        except Exception as e:
            logger.error(f"Ranking failed: {e}")
        
        # Fallback: return first result
        return results[0]
