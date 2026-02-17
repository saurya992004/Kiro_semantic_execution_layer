import psutil
import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path


class SystemMonitor:
    """
    Background system monitoring with historical data tracking.
    
    This class provides continuous monitoring of system metrics (CPU, RAM, disk)
    and stores historical data for analysis.
    """
    
    def __init__(self, log_file: str = "logs/system_monitor.json"):
        """
        Initialize monitor with log file path.
        
        Args:
            log_file: Path to JSON log file for storing metrics
        """
        self.log_file = log_file
        self.monitoring = False
        self.monitor_thread = None
        self.metrics_history = []
        self.lock = threading.Lock()
        
        # Create logs directory if it doesn't exist
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing history if available
        self._load_history()
    
    def start_monitoring(self, interval_seconds: int = 60):
        """
        Start background monitoring thread.
        
        Args:
            interval_seconds: How often to collect metrics (default 60 seconds)
        """
        if self.monitoring:
            return {"status": "already_running"}
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
        
        return {
            "status": "started",
            "interval_seconds": interval_seconds,
            "log_file": self.log_file
        }
    
    def stop_monitoring(self):
        """
        Stop monitoring and save logs.
        
        Returns:
            dict: Status information
        """
        if not self.monitoring:
            return {"status": "not_running"}
        
        self.monitoring = False
        
        # Wait for thread to finish
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        # Save final state
        self._save_history()
        
        return {
            "status": "stopped",
            "metrics_collected": len(self.metrics_history)
        }
    
    def get_current_metrics(self) -> dict:
        """
        Get current system metrics.
        
        Returns:
            dict: Current CPU, RAM, and disk metrics
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage("C:\\")
            
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": cpu_percent,
                "ram_percent": ram.percent,
                "ram_used_gb": round(ram.used / (1024**3), 2),
                "ram_total_gb": round(ram.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_total_gb": round(disk.total / (1024**3), 2)
            }
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def get_historical_data(self, hours: int = 24) -> list:
        """
        Retrieve past metrics.
        
        Args:
            hours: Number of hours of history to retrieve
        
        Returns:
            list: Historical metrics within the time range
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            filtered_metrics = [
                metric for metric in self.metrics_history
                if datetime.fromisoformat(metric["timestamp"]) >= cutoff_time
            ]
        
        return filtered_metrics
    
    def get_statistics(self, hours: int = 24) -> dict:
        """
        Get statistical summary of metrics over time period.
        
        Args:
            hours: Number of hours to analyze
        
        Returns:
            dict: Statistical summary (avg, min, max)
        """
        historical_data = self.get_historical_data(hours)
        
        if not historical_data:
            return {
                "error": "No data available",
                "hours": hours
            }
        
        cpu_values = [m["cpu_percent"] for m in historical_data if "cpu_percent" in m]
        ram_values = [m["ram_percent"] for m in historical_data if "ram_percent" in m]
        disk_values = [m["disk_percent"] for m in historical_data if "disk_percent" in m]
        
        return {
            "hours": hours,
            "data_points": len(historical_data),
            "cpu": {
                "avg": round(sum(cpu_values) / len(cpu_values), 2) if cpu_values else 0,
                "min": round(min(cpu_values), 2) if cpu_values else 0,
                "max": round(max(cpu_values), 2) if cpu_values else 0
            },
            "ram": {
                "avg": round(sum(ram_values) / len(ram_values), 2) if ram_values else 0,
                "min": round(min(ram_values), 2) if ram_values else 0,
                "max": round(max(ram_values), 2) if ram_values else 0
            },
            "disk": {
                "avg": round(sum(disk_values) / len(disk_values), 2) if disk_values else 0,
                "min": round(min(disk_values), 2) if disk_values else 0,
                "max": round(max(disk_values), 2) if disk_values else 0
            }
        }
    
    def _monitor_loop(self, interval_seconds: int):
        """
        Background monitoring loop.
        
        Args:
            interval_seconds: Sleep interval between collections
        """
        while self.monitoring:
            metrics = self.get_current_metrics()
            
            with self.lock:
                self.metrics_history.append(metrics)
                
                # Keep only last 7 days of data
                cutoff_time = datetime.now() - timedelta(days=7)
                self.metrics_history = [
                    m for m in self.metrics_history
                    if datetime.fromisoformat(m["timestamp"]) >= cutoff_time
                ]
            
            # Save periodically (every 10 collections)
            if len(self.metrics_history) % 10 == 0:
                self._save_history()
            
            time.sleep(interval_seconds)
    
    def _save_history(self):
        """Save metrics history to JSON file."""
        try:
            with self.lock:
                with open(self.log_file, 'w') as f:
                    json.dump(self.metrics_history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def _load_history(self):
        """Load metrics history from JSON file."""
        try:
            if Path(self.log_file).exists():
                with open(self.log_file, 'r') as f:
                    self.metrics_history = json.load(f)
                
                # Clean old data
                cutoff_time = datetime.now() - timedelta(days=7)
                self.metrics_history = [
                    m for m in self.metrics_history
                    if datetime.fromisoformat(m["timestamp"]) >= cutoff_time
                ]
        except Exception as e:
            print(f"Error loading history: {e}")
            self.metrics_history = []


# Singleton instance for easy access
_monitor_instance = None


def get_monitor_instance(log_file: str = "logs/system_monitor.json") -> SystemMonitor:
    """
    Get or create singleton SystemMonitor instance.
    
    Args:
        log_file: Path to log file
    
    Returns:
        SystemMonitor: Singleton instance
    """
    global _monitor_instance
    
    if _monitor_instance is None:
        _monitor_instance = SystemMonitor(log_file)
    
    return _monitor_instance
