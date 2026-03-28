"""
Audit Log - Immutable record of all system actions
Used for compliance, debugging, and security analysis

Features:
- Immutable append-only log
- Cryptographic integrity (hash chain)
- Event filtering and search
- Export capabilities
- Retention policies
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json


logger = logging.getLogger(__name__)


@dataclass
class AuditEvent:
    """A single audited event"""
    
    event_id: str  # Unique ID
    timestamp: datetime  # When it happened
    user_id: str  # Who did it
    action: str  # What was done (e.g., "tool_executed", "policy_check_failed")
    resource: str  # What was acted upon (e.g., tool name, user)
    result: str  # Outcome: "success", "failure", "denied"
    details: Dict[str, Any] = field(default_factory=dict)  # Extra info
    
    # Hash chain for integrity
    previous_hash: Optional[str] = None
    event_hash: Optional[str] = None  # Hash of this event
    
    def compute_hash(self) -> str:
        """Compute hash of this event (for integrity checking)"""
        # Create hashable representation
        data = {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "action": self.action,
            "resource": self.resource,
            "result": self.result,
            "details": self.details,
            "previous_hash": self.previous_hash,
        }
        
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "action": self.action,
            "resource": self.resource,
            "result": self.result,
            "details": self.details,
            "previous_hash": self.previous_hash,
            "event_hash": self.event_hash,
        }


class AuditLog:
    """
    Immutable audit log for all system actions
    
    Provides:
    - Append-only event logging
    - Hash chain integrity
    - Event searching and filtering
    - Compliance reports
    
    Usage:
        log = AuditLog()
        
        # Record an action
        log.record(
            user_id="user_1",
            action="tool_executed",
            resource="system_diagnostic",
            result="success",
            details={"duration_ms": 2000}
        )
        
        # Search events
        events = log.search(user_id="user_1", action="tool_executed")
        
        # Get statistics
        stats = log.get_stats()
    """
    
    def __init__(self, retention_days: int = 90):
        """
        Initialize audit log
        
        Args:
            retention_days: How long to keep logs before archiving
        """
        self._events: List[AuditEvent] = []
        self._retention_days = retention_days
        self._last_hash = None  # Hash of last event (for chain)
        self._event_count = 0
    
    def record(
        self,
        user_id: str,
        action: str,
        resource: str,
        result: str,  # "success", "failure", "denied"
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """
        Record an audited action
        
        Args:
            user_id: User performing action
            action: Type of action (e.g., "tool_executed", "policy_violated")
            resource: What was acted upon
            result: Outcome of action
            details: Additional information
            
        Returns:
            The recorded AuditEvent
        """
        
        self._event_count += 1
        event_id = f"audit_{self._event_count}"
        
        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=action,
            resource=resource,
            result=result,
            details=details or {},
            previous_hash=self._last_hash,
        )
        
        # Compute and set hash
        event.event_hash = event.compute_hash()
        self._last_hash = event.event_hash
        
        # Append to immutable log
        self._events.append(event)
        
        # Log for monitoring
        log_level = logging.ERROR if result == "failure" else logging.INFO
        logger.log(
            log_level,
            f"AUDIT: {user_id} {action} on {resource}: {result}",
            extra={"event_id": event_id}
        )
        
        return event
    
    def search(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        result: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[AuditEvent]:
        """
        Search audit log
        
        Args:
            user_id: Filter by user
            action: Filter by action type
            resource: Filter by resource
            result: Filter by result (success/failure/denied)
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Max results to return
            
        Returns:
            List of matching events
        """
        
        results = []
        
        for event in self._events:
            # Apply filters
            if user_id and event.user_id != user_id:
                continue
            if action and event.action != action:
                continue
            if resource and resource.lower() not in event.resource.lower():
                continue
            if result and event.result != result:
                continue
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            
            results.append(event)
            
            if len(results) >= limit:
                break
        
        return results
    
    def verify_integrity(self) -> tuple[bool, Optional[str]]:
        """
        Verify hash chain integrity
        
        Returns:
            (is_intact: bool, error_message: optional)
        """
        
        previous_hash = None
        
        for i, event in enumerate(self._events):
            # Check hash chain
            if event.previous_hash != previous_hash:
                return False, f"Hash chain broken at event {i} ({event.event_id})"
            
            # Recompute hash and verify
            expected_hash = event.compute_hash()
            if event.event_hash != expected_hash:
                return False, f"Hash mismatch at event {i} ({event.event_id})"
            
            previous_hash = event.event_hash
        
        return True, None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit log statistics"""
        
        total = len(self._events)
        
        if total == 0:
            return {
                "total_events": 0,
                "unique_users": 0,
                "success_rate": 0.0,
                "actions": {},
            }
        
        successes = len([e for e in self._events if e.result == "success"])
        failures = len([e for e in self._events if e.result == "failure"])
        denied = len([e for e in self._events if e.result == "denied"])
        
        users = set(e.user_id for e in self._events)
        
        actions = {}
        for event in self._events:
            if event.action not in actions:
                actions[event.action] = 0
            actions[event.action] += 1
        
        return {
            "total_events": total,
            "unique_users": len(users),
            "successful_events": successes,
            "failed_events": failures,
            "denied_events": denied,
            "success_rate": successes / total if total > 0 else 0,
            "actions_breakdown": actions,
            "date_range": {
                "start": self._events[0].timestamp.isoformat(),
                "end": self._events[-1].timestamp.isoformat(),
            },
        }
    
    def get_user_activity_summary(self, user_id: str) -> Dict[str, Any]:
        """Get activity summary for a specific user"""
        
        user_events = [e for e in self._events if e.user_id == user_id]
        
        if not user_events:
            return {"user_id": user_id, "total_events": 0}
        
        successes = len([e for e in user_events if e.result == "success"])
        failures = len([e for e in user_events if e.result == "failure"])
        denied = len([e for e in user_events if e.result == "denied"])
        
        actions = {}
        for event in user_events:
            if event.action not in actions:
                actions[event.action] = {"count": 0, "success": 0}
            actions[event.action]["count"] += 1
            if event.result == "success":
                actions[event.action]["success"] += 1
        
        return {
            "user_id": user_id,
            "total_events": len(user_events),
            "successful_events": successes,
            "failed_events": failures,
            "denied_events": denied,
            "action_breakdown": actions,
            "first_activity": user_events[0].timestamp.isoformat(),
            "last_activity": user_events[-1].timestamp.isoformat(),
        }
    
    def export_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Export events for external audit/compliance
        
        Returns:
            List of event dicts in JSON-serializable format
        """
        
        events = self.search(start_time=start_time, end_time=end_time, limit=999999)
        return [e.to_dict() for e in events]
    
    def get_event_count(self) -> int:
        """Get total number of events"""
        return len(self._events)
    
    def get_events_by_date(self, date: datetime) -> List[AuditEvent]:
        """Get all events for a specific date"""
        
        start = datetime(date.year, date.month, date.day, 0, 0, 0)
        end = start + timedelta(days=1)
        
        return self.search(start_time=start, end_time=end, limit=999999)
