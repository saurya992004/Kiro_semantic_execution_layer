"""
LLM Router - Routes requests to appropriate LLM backend
Manages multiple backends (Groq, Claude, OpenAI, Ollama, etc.)
Provides caching, fallback, and intelligent routing.
"""

import asyncio
import logging
from typing import Dict, Optional, List, Callable
from datetime import datetime, timedelta
import hashlib
import json
from dataclasses import dataclass

from ..protocols import LLMBackend, LLMRequest, LLMResponse, EventType, Event, EventBus


logger = logging.getLogger(__name__)


@dataclass
class CachedResponse:
    """Cached LLM response"""
    response: LLMResponse
    timestamp: datetime
    
    def is_expired(self, ttl_seconds: int = 3600) -> bool:
        """Check if cache entry is expired"""
        return datetime.utcnow() - self.timestamp > timedelta(seconds=ttl_seconds)
    
    @staticmethod
    def get_cache_key(request: LLMRequest) -> str:
        """Generate cache key from request"""
        key_data = {
            "prompt": request.prompt,
            "system_prompt": request.system_prompt,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()


class LLMRouter:
    """
    Manages multiple LLM backends and routes requests intelligently.
    
    Features:
    - Backend registration and discovery
    - Intelligent routing (choose best backend for task)
    - Fallback if primary fails
    - Response caching
    - Cost tracking
    - Health monitoring
    
    Usage:
        router = LLMRouter(event_bus)
        router.register_backend("groq", groq_backend)
        router.register_backend("claude", claude_backend)
        
        response = await router.generate(request)
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None, cache_ttl_seconds: int = 3600):
        """
        Initialize LLM Router
        
        Args:
            event_bus: Event bus for publishing events
            cache_ttl_seconds: Cache entry time-to-live
        """
        self._backends: Dict[str, LLMBackend] = {}
        self._backend_health: Dict[str, bool] = {}
        self._primary_backend: Optional[str] = None
        self._response_cache: Dict[str, CachedResponse] = {}
        self._cache_ttl_seconds = cache_ttl_seconds
        self._event_bus = event_bus
        self._usage_stats = {
            "total_requests": 0,
            "total_cost": 0.0,
            "backend_usage": {},
            "cached_hits": 0,
        }
    
    def register_backend(self, backend_name: str, backend: LLMBackend, is_primary: bool = False) -> None:
        """
        Register an LLM backend
        
        Args:
            backend_name: Unique name for this backend
            backend: LLMBackend instance
            is_primary: Set as primary/default backend?
        """
        self._backends[backend_name] = backend
        self._backend_health[backend_name] = True
        if is_primary or self._primary_backend is None:
            self._primary_backend = backend_name
        logger.info(f"Registered LLM backend: {backend_name}")
    
    def get_backend(self, backend_name: str) -> Optional[LLMBackend]:
        """Get a specific backend by name"""
        return self._backends.get(backend_name)
    
    def list_backends(self) -> List[str]:
        """List all registered backends"""
        return list(self._backends.keys())
    
    def list_healthy_backends(self) -> List[str]:
        """List backends that are healthy"""
        return [name for name, healthy in self._backend_health.items() if healthy]
    
    async def generate(
        self, 
        request: LLMRequest, 
        preferred_backend: Optional[str] = None,
        use_cache: bool = True
    ) -> LLMResponse:
        """
        Generate a response by routing to appropriate backend
        
        Args:
            request: LLMRequest with prompt and parameters
            preferred_backend: Specific backend to use (if available)
            use_cache: Check cache first?
            
        Returns:
            LLMResponse from the backend
            
        Raises:
            ValueError: No healthy backends available
            RuntimeError: All backends failed
        """
        # Check cache first
        if use_cache:
            cache_key = CachedResponse.get_cache_key(request)
            if cache_key in self._response_cache:
                cached = self._response_cache[cache_key]
                if not cached.is_expired(self._cache_ttl_seconds):
                    self._usage_stats["cached_hits"] += 1
                    logger.debug(f"Cache hit for request")
                    cached.response.cached = True
                    return cached.response
                else:
                    del self._response_cache[cache_key]
        
        # Publish LLM requested event
        if self._event_bus:
            await self._event_bus.publish(Event(
                event_type=EventType.LLM_REQUESTED,
                data={"prompt_length": len(request.prompt)},
                source="llm_router",
                user_id=request.user_id,
                request_id=request.request_id,
            ))
        
        # Select backend
        backend_name = preferred_backend or self._primary_backend
        if not backend_name or backend_name not in self._backends:
            healthy = self.list_healthy_backends()
            if not healthy:
                raise ValueError("No healthy LLM backends available")
            backend_name = healthy[0]
        
        # Try primary backend, fallback to others if needed
        backends_to_try = [backend_name]
        if backend_name != self._primary_backend and self._primary_backend:
            backends_to_try.append(self._primary_backend)
        backends_to_try.extend([b for b in self.list_healthy_backends() if b not in backends_to_try])
        
        last_error = None
        for attempted_backend in backends_to_try:
            try:
                backend = self._backends[attempted_backend]
                
                # Validate request
                is_valid, error = await backend.validate_request(request)
                if not is_valid:
                    raise ValueError(f"Invalid request for {attempted_backend}: {error}")
                
                # Generate response
                response = await asyncio.wait_for(
                    backend.generate(request),
                    timeout=request.timeout or 30.0
                )
                
                # Update tracking
                self._usage_stats["total_requests"] += 1
                if attempted_backend not in self._usage_stats["backend_usage"]:
                    self._usage_stats["backend_usage"][attempted_backend] = 0
                self._usage_stats["backend_usage"][attempted_backend] += 1
                if response.cost:
                    self._usage_stats["total_cost"] += response.cost
                
                # Cache the response
                if use_cache:
                    cache_key = CachedResponse.get_cache_key(request)
                    self._response_cache[cache_key] = CachedResponse(response, datetime.utcnow())
                
                # Publish success event
                if self._event_bus:
                    await self._event_bus.publish(Event(
                        event_type=EventType.LLM_RESPONSE,
                        data={
                            "backend": response.backend,
                            "model": response.model,
                            "tokens": response.tokens_used,
                            "latency_ms": response.latency_ms,
                        },
                        source="llm_router",
                        user_id=request.user_id,
                        request_id=request.request_id,
                    ))
                
                return response
                
            except Exception as e:
                logger.warning(f"Backend {attempted_backend} failed: {e}")
                last_error = e
                self._backend_health[attempted_backend] = False
                continue
        
        raise RuntimeError(f"All LLM backends failed. Last error: {last_error}")
    
    async def stream(
        self,
        request: LLMRequest,
        preferred_backend: Optional[str] = None
    ):
        """
        Stream a response from an LLM backend
        
        Yields:
            str: Response tokens as they arrive
        """
        backend_name = preferred_backend or self._primary_backend
        if not backend_name or backend_name not in self._backends:
            healthy = self.list_healthy_backends()
            if not healthy:
                raise ValueError("No healthy LLM backends available")
            backend_name = healthy[0]
        
        backend = self._backends[backend_name]
        async for token in backend.stream(request):
            yield token
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all backends"""
        health_status = {}
        for name, backend in self._backends.items():
            try:
                is_healthy = await asyncio.wait_for(backend.health_check(), timeout=5.0)
                health_status[name] = is_healthy
                self._backend_health[name] = is_healthy
            except Exception as e:
                logger.warning(f"Health check failed for {name}: {e}")
                health_status[name] = False
                self._backend_health[name] = False
        
        return health_status
    
    def clear_cache(self) -> None:
        """Clear response cache"""
        self._response_cache.clear()
        logger.info("LLM response cache cleared")
    
    def get_stats(self) -> Dict:
        """Get usage statistics"""
        return {
            **self._usage_stats,
            "backends": len(self._backends),
            "healthy_backends": len(self.list_healthy_backends()),
        }
