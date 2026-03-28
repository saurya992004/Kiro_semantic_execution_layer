"""
Kiro Notifier — Proactive Desktop Notifications
=================================================
Background health monitor that pushes Windows toast notifications
for critical system alerts and Ghost Mode findings.
"""

import os
import sys
import time
import threading
import logging
from datetime import datetime
from pathlib import Path

JARVIS_ROOT = Path(__file__).parent
sys.path.insert(0, str(JARVIS_ROOT))

logger = logging.getLogger("kiro.notifier")


class KiroNotifier:
    """Background notification system for Kiro OS."""
    
    def __init__(self, check_interval=60):
        self.check_interval = check_interval  # seconds
        self._running = False
        self._thread = None
        self._last_alerts = {}
    
    def start(self):
        """Start the background notification thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Kiro Notifier started")
    
    def stop(self):
        """Stop the background notification thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Kiro Notifier stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                self._check_and_notify()
            except Exception as e:
                logger.error(f"Notifier error: {e}")
            time.sleep(self.check_interval)
    
    def _check_and_notify(self):
        """Check system health and send notifications for alerts."""
        try:
            from tools.diagnostics_tools import get_cpu_usage, get_ram_usage, get_disk_usage, check_health_alerts
            
            cpu = get_cpu_usage()
            ram = get_ram_usage()
            disk = get_disk_usage("C:")
            alerts = check_health_alerts()
            
            cpu_pct = cpu.get("cpu_percent", 0)
            ram_pct = ram.get("percent", 0)
            disk_pct = disk.get("percent", 0)
            
            # CPU alert
            if cpu_pct > 90 and self._should_alert("cpu_high"):
                self._send_notification(
                    "🔥 High CPU Usage",
                    f"CPU is at {cpu_pct}%! Your system may be slow. Consider running PC Speedup.",
                )
                self._last_alerts["cpu_high"] = time.time()
            
            # RAM alert
            if ram_pct > 90 and self._should_alert("ram_high"):
                self._send_notification(
                    "💾 High Memory Usage",
                    f"RAM is at {ram_pct}%. Close unused applications or run PC Speedup.",
                )
                self._last_alerts["ram_high"] = time.time()
            
            # Disk alert
            if disk_pct > 85 and self._should_alert("disk_high"):
                # Try to estimate cleanable space
                try:
                    from tools.diagnostics_tools import scan_cleanup_files
                    cleanup = scan_cleanup_files()
                    total_cleanable = cleanup.get("total_cleanable_gb", 0)
                    msg = f"Disk is at {disk_pct}%. "
                    if total_cleanable > 0:
                        msg += f"Found {total_cleanable}GB of cleanable files. Open Kiro to clean up."
                    else:
                        msg += "Consider removing large files."
                    self._send_notification("🗂️ Disk Space Critical", msg)
                except:
                    self._send_notification(
                        "🗂️ Disk Space Critical",
                        f"Disk is at {disk_pct}%. Open Kiro OS dashboard to clean up.",
                    )
                self._last_alerts["disk_high"] = time.time()
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
    
    def _should_alert(self, alert_key: str, cooldown: int = 300) -> bool:
        """Check if enough time has passed since the last alert of this type."""
        last_time = self._last_alerts.get(alert_key, 0)
        return (time.time() - last_time) > cooldown
    
    def _send_notification(self, title: str, message: str):
        """Send a Windows toast notification."""
        logger.info(f"Notification: {title} — {message}")
        
        # Try plyer first (cross-platform)
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                app_name="Kiro OS",
                timeout=10,
            )
            return
        except Exception as e:
            logger.debug(f"Plyer notification failed: {e}")
        
        # Fallback: PowerShell toast notification
        try:
            import subprocess
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
            $template = "<toast><visual><binding template='ToastGeneric'><text>{title}</text><text>{message}</text></binding></visual></toast>"
            $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
            $xml.LoadXml($template)
            $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Kiro OS").Show($toast)
            '''
            subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True, timeout=10
            )
            return
        except Exception as e:
            logger.debug(f"PowerShell toast failed: {e}")
        
        # Last resort: print to console
        print(f"\n🔔 KIRO NOTIFICATION: {title}\n   {message}\n")
    
    def send_custom_notification(self, title: str, message: str):
        """Send a custom notification (public API)."""
        self._send_notification(title, message)


# Singleton instance
_notifier = None

def get_notifier() -> KiroNotifier:
    """Get or create the singleton notifier instance."""
    global _notifier
    if _notifier is None:
        _notifier = KiroNotifier()
    return _notifier


def start_notifications():
    """Start background notifications."""
    notifier = get_notifier()
    notifier.start()
    return notifier


def stop_notifications():
    """Stop background notifications."""
    notifier = get_notifier()
    notifier.stop()


if __name__ == "__main__":
    print("🔔 Kiro Notifier — Starting background health monitor...")
    notifier = start_notifications()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Stopping notifier...")
        stop_notifications()
