"""
API Request/Response Models
Simple data classes for type validation and documentation
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# Request Models
# ============================================================================

@dataclass
class CommandRequest:
    """User command request"""
    command: str
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self):
        """Convert to dict"""
        return asdict(self)


@dataclass
class ExecutionResult:
    """Execution result"""
    execution_id: str
    status: str  # success, failed, in_progress
    result: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        """Convert to dict"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class PolicyUpdateRequest:
    """Policy update request (admin only)"""
    user_id: str
    rate_limits: Optional[Dict[str, Dict[str, int]]] = None
    allowed_tools: Optional[List[str]] = None
    blocked_tools: Optional[List[str]] = None
    max_daily_cost: Optional[float] = None
    
    def to_dict(self):
        """Convert to dict"""
        return asdict(self)


@dataclass
class AuditQueryRequest:
    """Audit log query request"""
    user_id: Optional[str] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    result: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100
    
    def validate_limit(self):
        """Validate limit is in valid range"""
        return max(1, min(1000, self.limit))


# ============================================================================
# Response Models
# ============================================================================

@dataclass
class ErrorResponse:
    """Standard error response"""
    error: str
    code: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        """Convert to dict"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class ExecutionStatusResponse:
    """Execution status response"""
    execution_id: str
    status: str
    progress: Optional[float] = None
    current_step: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def to_dict(self):
        """Convert to dict"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data


@dataclass
class HistoryResponse:
    """Execution history response"""
    executions: List[ExecutionStatusResponse]
    total: int
    page: int
    page_size: int
    
    def to_dict(self):
        """Convert to dict"""
        return {
            'executions': [e.to_dict() for e in self.executions],
            'total': self.total,
            'page': self.page,
            'page_size': self.page_size,
        }


@dataclass
class PolicyResponse:
    """Current policy response"""
    user_id: str
    rate_limits: Dict[str, Dict[str, int]]
    allowed_tools: List[str]
    blocked_tools: List[str]
    max_daily_cost: float
    current_cost: float
    violations: int
    
    def to_dict(self):
        """Convert to dict"""
        return asdict(self)


@dataclass
class AuditEvent:
    """Audit event response"""
    event_id: str
    timestamp: datetime
    user_id: str
    action: str
    resource: str
    result: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self):
        """Convert to dict"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class AuditQueryResponse:
    """Audit query response"""
    events: List[AuditEvent]
    total: int
    start_time: datetime
    end_time: datetime
    
    def to_dict(self):
        """Convert to dict"""
        return {
            'events': [e.to_dict() for e in self.events],
            'total': self.total,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
        }


@dataclass
class StatisticsResponse:
    """System statistics response"""
    total_executions: int
    successful: int
    failed: int
    average_duration_seconds: float
    total_cost: float
    active_users: int
    policy_violations: int
    audit_events: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        """Convert to dict"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class HealthResponse:
    """Health check response"""
    status: str  # healthy, degraded, unhealthy
    version: str
    components: Dict[str, str]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        """Convert to dict"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


# ============================================================================
# Event Models (for WebSocket)
# ============================================================================

class EventType(str, Enum):
    """Event types for real-time streaming"""
    EXECUTION_STARTED = "execution_started"
    EXECUTION_PROGRESS = "execution_progress"
    TASK_COMPLETED = "task_completed"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    POLICY_CHECK = "policy_check"
    AUDIT_RECORDED = "audit_recorded"
    ERROR = "error"


@dataclass
class StreamEvent:
    """Event sent over WebSocket"""
    event_type: EventType
    execution_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        """Convert to dict"""
        return {
            'event_type': self.event_type.value,
            'execution_id': self.execution_id,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
        }


# ============================================================================
# Authentication Models
# ============================================================================

@dataclass
class TokenData:
    """JWT token payload"""
    user_id: str
    role: str  # "user" or "admin"
    exp: int  # expiration timestamp


@dataclass
class User:
    """Authenticated user"""
    user_id: str
    role: str  # "user" or "admin"
    is_admin: bool = False
    
    def __post_init__(self):
        self.is_admin = self.role == "admin"
