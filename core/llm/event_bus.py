"""
In-Memory Event Bus Implementation
"""

import asyncio
import logging
from typing import Dict, List, Callable, Optional
from datetime import datetime

from ..protocols import EventBus, Event, EventType


logger = logging.getLogger(__name__)


class InMemoryEventBus(EventBus):
    """
    Simple in-memory event bus implementation.
    For production, use Redis-based bus for multi-process scenarios.
    
    Features:
    - Subscribe/publish events
    - Handler registration
    - Event history
    - Wait for specific events
    """
    
    def __init__(self, max_history: int = 10000):
        """
        Initialize event bus
        
        Args:
            max_history: Max events to keep in history
        """
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._history: List[Event] = []
        self._max_history = max_history
        self._waiters: Dict[EventType, List[asyncio.Event]] = {}
    
    def on(self, event_type: EventType) -> Callable:
        """Register handler for event type"""
        def decorator(handler: Callable) -> Callable:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)
            logger.debug(f"Registered handler for {event_type.value}")
            return handler
        return decorator
    
    def off(self, event_type: EventType, handler: Callable) -> None:
        """Unregister handler"""
        if event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
    
    async def publish(self, event: Event) -> None:
        """Publish an event"""
        # Add to history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        
        logger.debug(f"Event published: {event.event_type.value}")
        
        # Notify all handlers
        if event.event_type in self._handlers:
            tasks = []
            for handler in self._handlers[event.event_type]:
                try:
                    result = handler(event)
                    if asyncio.iscoroutine(result):
                        tasks.append(result)
                except Exception as e:
                    logger.error(f"Handler error: {e}", exc_info=True)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        
        # Notify waiters
        if event.event_type in self._waiters:
            for waiter in self._waiters[event.event_type]:
                waiter.set()
    
    async def publish_batch(self, events: list[Event]) -> None:
        """Publish multiple events"""
        tasks = [self.publish(event) for event in events]
        await asyncio.gather(*tasks)
    
    async def wait_for(self, event_type: EventType, timeout: float = 30.0) -> Optional[Event]:
        """Wait for next event of this type"""
        event_obj = asyncio.Event()
        
        if event_type not in self._waiters:
            self._waiters[event_type] = []
        self._waiters[event_type].append(event_obj)
        
        try:
            await asyncio.wait_for(event_obj.wait(), timeout=timeout)
            # Find the event
            for event in reversed(self._history):
                if event.event_type == event_type:
                    return event
        except asyncio.TimeoutError:
            return None
        finally:
            if event_obj in self._waiters[event_type]:
                self._waiters[event_type].remove(event_obj)
    
    async def get_history(
        self,
        event_type: Optional[EventType] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> list[Event]:
        """Get historical events"""
        events = self._history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        
        return events[-limit:]
    
    async def clear_history(self) -> None:
        """Clear event history"""
        self._history.clear()
        logger.info("Event history cleared")
