"""
Downloader Engine for Installer Agent
=====================================
Robust file download with progress tracking, resume capability, and verification.
"""

import os
import sys
import requests
from pathlib import Path
from typing import Dict, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class Downloader:
    """
    Download files with:
    - Progress tracking with callbacks
    - Resume capability for large files
    - Timeout protection
    - File verification
    - Automatic retry
    """
    
    def __init__(self, default_folder: str = None):
        """
        Initialize downloader.
        
        Args:
            default_folder: Default download location (Desktop or Downloads)
        """
        self.default_folder = default_folder or str(Path.home() / "Desktop")
        self.timeout = 30
        self.max_retries = 3
        self.chunk_size = 8192  # 8KB chunks
    
    def download_file(
        self, 
        url: str, 
        filename: str = None,
        folder: str = None,
        on_progress: Callable = None,
        show_progress: bool = True
    ) -> Dict:
        """
        Download file with progress callback.
        
        Args:
            url: File URL
            filename: Save as this name (auto-detect from URL if None)
            folder: Save to this folder (default: Desktop)
            on_progress: Callback function(downloaded, total, percent)
            show_progress: Print progress to console
            
        Returns:
            {
                "status": "success|failed",
                "path": "/path/to/file",
                "size": 2500000,
                "message": "Downloaded 2.5MB"
            }
        """
        folder = folder or self.default_folder
        os.makedirs(folder, exist_ok=True)
        
        if not filename:
            filename = self._extract_filename(url)
        
        filepath = os.path.join(folder, filename)
        
        logger.info(f"Downloading: {url} -> {filepath}")
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                result = self._download_with_resume(
                    url, 
                    filepath, 
                    on_progress, 
                    show_progress
                )
                
                if result["status"] == "success":
                    logger.info(f"Downloaded successfully: {filepath}")
                    return result
            
            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying... ({attempt + 2}/{self.max_retries})")
                    continue
        
        # All retries failed
        logger.error(f"Download failed after {self.max_retries} attempts")
        return {
            "status": "failed",
            "message": f"Failed to download after {self.max_retries} attempts"
        }
    
    def _download_with_resume(
        self,
        url: str,
        filepath: str,
        on_progress: Callable = None,
        show_progress: bool = True
    ) -> Dict:
        """
        Download file with resume capability.
        """
        headers = {}
        mode = "wb"
        resume_from = 0
        
        # Check if file exists and supports resume
        if os.path.exists(filepath):
            resume_from = os.path.getsize(filepath)
            headers["Range"] = f"bytes={resume_from}-"
            mode = "ab"
            logger.info(f"Resuming download from byte {resume_from}")
        
        try:
            response = requests.get(
                url,
                headers=headers,
                stream=True,
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Get total file size
            total_size = int(response.headers.get('content-length', 0))
            if resume_from:
                total_size += resume_from
            
            downloaded = resume_from
            
            # Download with progress tracking
            with open(filepath, mode) as f:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Progress callback
                        if on_progress and total_size:
                            percent = (downloaded / total_size) * 100
                            on_progress(downloaded, total_size, percent)
                        
                        # Console progress
                        if show_progress and total_size:
                            percent = (downloaded / total_size) * 100
                            self._print_progress(downloaded, total_size, percent)
            
            # Verify file
            if not os.path.exists(filepath):
                return {
                    "status": "failed",
                    "message": "File not found after download"
                }
            
            final_size = os.path.getsize(filepath)
            
            return {
                "status": "success",
                "path": filepath,
                "size": final_size,
                "message": f"Downloaded {self._format_size(final_size)}"
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Download request failed: {e}")
            return {
                "status": "failed",
                "message": f"Download error: {str(e)}"
            }
        
        except IOError as e:
            logger.error(f"File I/O error: {e}")
            return {
                "status": "failed",
                "message": f"File error: {str(e)}"
            }
    
    def _extract_filename(self, url: str) -> str:
        """Extract filename from URL."""
        # Remove query parameters
        clean_url = url.split('?')[0]
        # Get last part of path
        filename = clean_url.split('/')[-1]
        
        if not filename:
            filename = "downloaded_file"
        
        return filename
    
    def _print_progress(self, downloaded: int, total: int, percent: float):
        """Print progress bar to console."""
        bar_length = 40
        filled = int(bar_length * percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        downloaded_mb = downloaded / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        
        sys.stdout.write(
            f'\r⬇️  [{bar}] {percent:.1f}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)'
        )
        sys.stdout.flush()
        
        if percent >= 100:
            sys.stdout.write('\n')
    
    def _format_size(self, size_bytes: int) -> str:
        """Format bytes to human readable size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"
    
    def verify_file(self, filepath: str, expected_size: int = None) -> bool:
        """
        Verify downloaded file.
        
        Args:
            filepath: Path to file
            expected_size: Expected file size in bytes (optional)
            
        Returns:
            True if file is valid, False otherwise
        """
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            return False
        
        if os.path.getsize(filepath) == 0:
            logger.warning(f"File is empty: {filepath}")
            return False
        
        if expected_size and os.path.getsize(filepath) != expected_size:
            logger.warning(
                f"File size mismatch: {os.path.getsize(filepath)} != {expected_size}"
            )
            return False
        
        logger.info(f"File verified: {filepath}")
        return True
    
    def cleanup_partial(self, filepath: str, keep_attempts: int = 3):
        """
        Remove partial download file if retry limit exceeded.
        
        Args:
            filepath: Path to partial file
            keep_attempts: Number of retry attempts before cleanup
        """
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Cleaned up partial file: {filepath}")
