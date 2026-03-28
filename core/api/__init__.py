"""
API Layer
FastAPI REST endpoints with WebSocket support
"""

from core.api.auth import AuthManager, get_auth_manager, setup_auth
from core.api.models import (
    CommandRequest,
    ExecutionResult,
    ErrorResponse,
    HealthResponse,
    PolicyUpdateRequest,
    AuditQueryRequest,
    AuditQueryResponse,
    User,
    StreamEvent,
    EventType,
)
from core.api.websocket import WebSocketManager, get_ws_manager

# Note: JARVISServer and create_jarvis_server require FastAPI
# They can be imported optionally when FastAPI is available:
#   from core.api.server import JARVISServer, create_jarvis_server


__all__ = [
    # Auth
    "AuthManager",
    "get_auth_manager",
    "setup_auth",
    
    # Models
    "CommandRequest",
    "ExecutionResult",
    "ErrorResponse",
    "HealthResponse",
    "PolicyUpdateRequest",
    "AuditQueryRequest",
    "AuditQueryResponse",
    "User",
    "StreamEvent",
    "EventType",
    
    # WebSocket
    "WebSocketManager",
    "get_ws_manager",
]
