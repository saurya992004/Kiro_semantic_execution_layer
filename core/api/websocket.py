"""
WebSocket Management
Real-time event streaming for connected clients
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from core.api.models import EventType, StreamEvent


logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasts events"""
    
    def __init__(self):
        """Initialize WebSocket manager"""
        self.active_connections: Dict[str, Set[Any]] = {}  # user_id -> {connections}
        self.subscription_callbacks: List[Callable[[StreamEvent], None]] = []
    
    async def connect(self, user_id: str, websocket: Any) -> bool:
        """
        Register a WebSocket connection
        
        Args:
            user_id: User ID
            websocket: WebSocket connection object
            
        Returns:
            True if connected, False if connection failed
        """
        try:
            await websocket.accept()
            
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            
            self.active_connections[user_id].add(websocket)
            
            logger.info(f"WebSocket connected for {user_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            return False
    
    async def disconnect(self, user_id: str, websocket: Any):
        """
        Disconnect a WebSocket
        
        Args:
            user_id: User ID
            websocket: WebSocket connection
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        logger.info(f"WebSocket disconnected for {user_id}")
    
    async def broadcast_to_user(self, user_id: str, event: StreamEvent):
        """
        Broadcast event to all connections for a user
        
        Args:
            user_id: Target user ID
            event: Event to broadcast
        """
        if user_id not in self.active_connections:
            return
        
        disconnected = set()
        
        for websocket in self.active_connections[user_id]:
            try:
                # Send as JSON
                await websocket.send_json(event.model_dump(mode='json', by_alias=True))
            
            except Exception as e:
                logger.error(f"Error sending event: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected connections
        for ws in disconnected:
            await self.disconnect(user_id, ws)
    
    async def broadcast_to_all(self, event: StreamEvent):
        """
        Broadcast event to all connected users
        
        Args:
            event: Event to broadcast
        """
        for user_id in list(self.active_connections.keys()):
            await self.broadcast_to_user(user_id, event)
    
    async def send_execution_started(
        self,
        user_id: str,
        execution_id: str,
        command: str,
    ):
        """
        Send execution started event
        
        Args:
            user_id: User ID
            execution_id: Execution ID
            command: User command
        """
        event = StreamEvent(
            event_type=EventType.EXECUTION_STARTED,
            execution_id=execution_id,
            data={
                "command": command,
                "timestamp": datetime.now().isoformat(),
            }
        )
        
        await self.broadcast_to_user(user_id, event)
    
    async def send_execution_progress(
        self,
        user_id: str,
        execution_id: str,
        step: str,
        progress: float,
    ):
        """
        Send execution progress event
        
        Args:
            user_id: User ID
            execution_id: Execution ID
            step: Current step
            progress: Progress 0-100
        """
        event = StreamEvent(
            event_type=EventType.EXECUTION_PROGRESS,
            execution_id=execution_id,
            data={
                "step": step,
                "progress": progress,
                "timestamp": datetime.now().isoformat(),
            }
        )
        
        await self.broadcast_to_user(user_id, event)
    
    async def send_execution_completed(
        self,
        user_id: str,
        execution_id: str,
        result: str,
        duration: float,
    ):
        """
        Send execution completed event
        
        Args:
            user_id: User ID
            execution_id: Execution ID
            result: Result message
            duration: Duration in seconds
        """
        event = StreamEvent(
            event_type=EventType.EXECUTION_COMPLETED,
            execution_id=execution_id,
            data={
                "result": result,
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat(),
            }
        )
        
        await self.broadcast_to_user(user_id, event)
    
    async def send_execution_failed(
        self,
        user_id: str,
        execution_id: str,
        error: str,
    ):
        """
        Send execution failed event
        
        Args:
            user_id: User ID
            execution_id: Execution ID
            error: Error message
        """
        event = StreamEvent(
            event_type=EventType.EXECUTION_FAILED,
            execution_id=execution_id,
            data={
                "error": error,
                "timestamp": datetime.now().isoformat(),
            }
        )
        
        await self.broadcast_to_user(user_id, event)
    
    async def send_policy_violation(
        self,
        user_id: str,
        execution_id: str,
        operation_type: str,
        reason: str,
    ):
        """
        Send policy violation event
        
        Args:
            user_id: User ID
            execution_id: Execution ID
            operation_type: Type of operation
            reason: Reason for violation
        """
        event = StreamEvent(
            event_type=EventType.POLICY_CHECK,
            execution_id=execution_id,
            data={
                "operation_type": operation_type,
                "reason": reason,
                "allowed": False,
                "timestamp": datetime.now().isoformat(),
            }
        )
        
        await self.broadcast_to_user(user_id, event)
    
    def get_active_user_count(self) -> int:
        """Get number of active users"""
        return len(self.active_connections)
    
    def get_active_connection_count(self) -> int:
        """Get total active connections"""
        return sum(len(conns) for conns in self.active_connections.values())


# Global WebSocket manager instance
_ws_manager: Optional[WebSocketManager] = None


def get_ws_manager() -> WebSocketManager:
    """Get global WebSocket manager"""
    global _ws_manager
    
    if _ws_manager is None:
        _ws_manager = WebSocketManager()
    
    return _ws_manager
