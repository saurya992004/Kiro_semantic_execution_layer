"""
Event System Protocol
Event-driven message bus for loose coupling and observability
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, Callable, Awaitable
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Types of events in the system"""
    
    # Lifecycle
    SYSTEM_STARTED = "system.started"
    SYSTEM_STOPPED = "system.stopped"
    SYSTEM_ERROR = "system.error"
    
    # Command processing
    COMMAND_RECEIVED = "command.received"
    COMMAND_COMPLETED = "command.completed"
    COMMAND_FAILED = "command.failed"
    COMMAND_CANCELLED = "command.cancelled"
    
    # Goal/Planning
    GOAL_EXTRACTED = "goal.extracted"
    PLAN_GENERATED = "plan.generated"
    PLAN_INVALID = "plan.invalid"
    
    # Execution
    EXECUTION_STARTED = "execution.started"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    
    # Tool
    TOOL_CALLED = "tool.called"
    TOOL_RESULT = "tool.result"
    TOOL_ERROR = "tool.error"
    
    # LLM
    LLM_REQUESTED = "llm.requested"
    LLM_RESPONSE = "llm.response"
    
    # Memory
    EXECUTION_STORED = "execution.stored"
    
    # Safety
    POLICY_CHECK = "policy.check"
    POLICY_VIOLATION = "policy.violation"
    
    # User
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"


@dataclass
class Event:
    """A single event in the system"""
    
    event_type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = "system"  # Which component emitted this?
    user_id: Optional[str] = None
    execution_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "event_type": self.event_type.value,
            "data": self.data,
            "source": self.source,
            "user_id": self.user_id,
            "execution_id": self.execution_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class EventBus(ABC):
    """
    Central message bus for events.
    Enables loose coupling: components publish events, others subscribe.
    
    Usage:
        bus = EventBus()
        
        # Subscribe to events
        @bus.on(EventType.COMMAND_RECEIVED)
        async def log_command(event: Event):
            print(f"User {event.user_id} sent: {event.data['command']}")
        
        # Publish events
        await bus.publish(Event(
            event_type=EventType.COMMAND_RECEIVED,
            data={"command": "speed up my PC"},
            user_id="user_123"
        ))
    """
    
    @abstractmethod
    def on(self, event_type: EventType) -> Callable:
        """
        Decorator to register handler for event type
        
        @bus.on(EventType.COMMAND_COMPLETED)
        async def handle(event: Event):
            ...
        """
        pass
    
    @abstractmethod
    def off(self, event_type: EventType, handler: Callable) -> None:
        """Unregister a handler"""
        pass
    
    @abstractmethod
    async def publish(self, event: Event) -> None:
        """Publish an event, all subscribers will be called"""
        pass
    
    @abstractmethod
    async def publish_batch(self, events: list[Event]) -> None:
        """Publish multiple events efficiently"""
        pass
    
    @abstractmethod
    async def wait_for(self, event_type: EventType, timeout: float = 30.0) -> Optional[Event]:
        """
        Wait for next event of this type
        Returns None if timeout expires
        """
        pass
    
    @abstractmethod
    async def get_history(
        self, 
        event_type: Optional[EventType] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> list[Event]:
        """Retrieve historical events"""
        pass
    
    @abstractmethod
    async def clear_history(self) -> None:
        """Clear all history"""
        pass
