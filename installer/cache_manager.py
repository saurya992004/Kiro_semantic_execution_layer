"""
Cache Manager for Installer Agent
==================================
Manage cached downloads to avoid re-downloading same resources.
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Cache downloaded resources with:
    - Metadata storage (JSON)
    - Expiration tracking
    - Space management
    - Quick lookup
    """
    
    def __init__(self, cache_folder: str = None):
        """
        Initialize cache manager.
        
        Args:
            cache_folder: Cache directory (default: ~/.jarvis_cache)
        """
        self.cache_folder = cache_folder or str(Path.home() / ".jarvis_cache" / "installer")
        self.metadata_file = os.path.join(self.cache_folder, "cache_metadata.json")
        self.default_expiry_days = 30  # Cache expires after 30 days
        
        os.makedirs(self.cache_folder, exist_ok=True)
        self.metadata = self._load_metadata()
        
        logger.info(f"Cache initialized: {self.cache_folder}")
    
    def get_cached_resource(self, resource_id: str) -> Optional[Dict]:
        """
        Get resource from cache if available and not expired.
        
        Args:
            resource_id: Unique resource identifier
            
        Returns:
            {
                "path": "/cache/file.jpg",
                "cached_at": "2026-02-23T14:30:00",
                "size": 2500000,
                "metadata": {...}
            }
            or None if not cached or expired
        """
        if resource_id not in self.metadata:
            logger.debug(f"Resource not in cache: {resource_id}")
            return None
        
        entry = self.metadata[resource_id]
        filepath = entry.get("path")
        cached_at = datetime.fromisoformat(entry.get("cached_at", ""))
        
        # Check expiration
        if datetime.now() - cached_at > timedelta(days=self.default_expiry_days):
            logger.info(f"Cache expired for: {resource_id}")
            self.remove_cached_resource(resource_id)
            return None
        
        # Check file still exists
        if not os.path.exists(filepath):
            logger.warning(f"Cached file missing: {filepath}")
            self.remove_cached_resource(resource_id)
            return None
        
        logger.info(f"Cache hit: {resource_id}")
        return {
            "path": filepath,
            "cached_at": entry.get("cached_at"),
            "size": os.path.getsize(filepath),
            "metadata": entry.get("metadata", {})
        }
    
    def cache_resource(
        self,
        resource_id: str,
        filepath: str,
        metadata: Dict = None
    ) -> bool:
        """
        Store resource in cache with metadata.
        
        Args:
            resource_id: Unique identifier
            filepath: Path to cached file
            metadata: Additional metadata to store
            
        Returns:
            True if cached successfully
        """
        if not os.path.exists(filepath):
            logger.error(f"Cannot cache non-existent file: {filepath}")
            return False
        
        try:
            self.metadata[resource_id] = {
                "path": filepath,
                "cached_at": datetime.now().isoformat(),
                "size": os.path.getsize(filepath),
                "metadata": metadata or {},
                "hash": self._hash_file(filepath)
            }
            
            self._save_metadata()
            logger.info(f"Cached resource: {resource_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to cache resource: {e}")
            return False
    
    def remove_cached_resource(self, resource_id: str) -> bool:
        """
        Remove resource from cache and disk.
        
        Args:
            resource_id: Unique identifier
            
        Returns:
            True if removed successfully
        """
        if resource_id not in self.metadata:
            return False
        
        try:
            entry = self.metadata[resource_id]
            filepath = entry.get("path")
            
            # Delete file
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Deleted cached file: {filepath}")
            
            # Remove metadata
            del self.metadata[resource_id]
            self._save_metadata()
            
            logger.info(f"Removed from cache: {resource_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to remove cached resource: {e}")
            return False
    
    def clear_old_cache(self, days: int = None) -> int:
        """
        Remove resources older than N days.
        
        Args:
            days: Remove items older than this many days (default: 30)
            
        Returns:
            Number of items removed
        """
        days = days or self.default_expiry_days
        cutoff = datetime.now() - timedelta(days=days)
        removed_count = 0
        
        to_remove = []
        for resource_id, entry in self.metadata.items():
            try:
                cached_at = datetime.fromisoformat(entry.get("cached_at", ""))
                if cached_at < cutoff:
                    to_remove.append(resource_id)
            except:
                pass
        
        for resource_id in to_remove:
            if self.remove_cached_resource(resource_id):
                removed_count += 1
        
        logger.info(f"Cache cleanup: removed {removed_count} old items")
        return removed_count
    
    def get_cache_size(self) -> Dict[str, any]:
        """
        Get cache directory size statistics.
        
        Returns:
            {
                "total_items": 5,
                "total_size": 1250000,
                "total_size_mb": 1.25,
                "oldest_item": "2026-02-15",
                "newest_item": "2026-02-23"
            }
        """
        total_size = 0
        oldest_date = None
        newest_date = None
        
        for entry in self.metadata.values():
            try:
                size = entry.get("size", 0)
                total_size += size
                
                cached_at = datetime.fromisoformat(entry.get("cached_at", ""))
                
                if oldest_date is None or cached_at < oldest_date:
                    oldest_date = cached_at
                
                if newest_date is None or cached_at > newest_date:
                    newest_date = cached_at
            except:
                continue
        
        return {
            "total_items": len(self.metadata),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_item": oldest_date.strftime("%Y-%m-%d") if oldest_date else None,
            "newest_item": newest_date.strftime("%Y-%m-%d") if newest_date else None
        }
    
    def clear_cache(self) -> bool:
        """
        Clear entire cache.
        
        Returns:
            True if successful
        """
        try:
            for resource_id in list(self.metadata.keys()):
                self.remove_cached_resource(resource_id)
            
            logger.info("Cache cleared completely")
            return True
        
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    def search_cache(self, query: str) -> Dict:
        """
        Search cache by query string.
        
        Args:
            query: Search term
            
        Returns:
            {resource_id: entry, ...}
        """
        results = {}
        query_lower = query.lower()
        
        for resource_id, entry in self.metadata.items():
            metadata = entry.get("metadata", {})
            
            # Search in resource_id and metadata
            if (query_lower in resource_id.lower() or
                query_lower in str(metadata).lower()):
                results[resource_id] = entry
        
        logger.info(f"Cache search found {len(results)} results for: {query}")
        return results
    
    def _hash_file(self, filepath: str) -> str:
        """Calculate SHA256 hash of file."""
        sha256_hash = hashlib.sha256()
        
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def _load_metadata(self) -> Dict:
        """Load cache metadata from disk."""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load metadata: {e}")
                return {}
        
        return {}
    
    def _save_metadata(self):
        """Save cache metadata to disk."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
