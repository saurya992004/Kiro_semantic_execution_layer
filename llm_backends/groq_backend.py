"""
Groq LLM Backend Implementation
Implements the LLMBackend protocol for Groq API
"""

import asyncio
import logging
import time
from typing import List, Optional, Dict, Any

from groq import AsyncGroq

from ..protocols import LLMBackend, LLMRequest, LLMResponse


logger = logging.getLogger(__name__)


class GroqBackend(LLMBackend):
    """
    Groq LLM backend implementation
    Uses official AsyncGroq client
    
    Usage:
        backend = GroqBackend(api_key="gsk_...")
        request = LLMRequest(prompt="What is Python?")
        response = await backend.generate(request)
    """
    
    # Available Groq models (as of 2025)
    AVAILABLE_MODELS = [
        "mixtral-8x7b-32768",
        "llama-2-70b-chat",
        "gemma-7b-it",
    ]
    
    DEFAULT_MODEL = "mixtral-8x7b-32768"
    
    def __init__(self, api_key: str, default_model: str = DEFAULT_MODEL):
        """
        Initialize Groq backend
        
        Args:
            api_key: Groq API key
            default_model: Default model to use
        """
        self.api_key = api_key
        self._default_model = default_model if default_model in self.AVAILABLE_MODELS else self.DEFAULT_MODEL
        self._client = AsyncGroq(api_key=api_key)
        self._cost_per_token = 0.0001  # Approximate USD per token
    
    @property
    def backend_name(self) -> str:
        return "groq"
    
    @property
    def available_models(self) -> List[str]:
        return self.AVAILABLE_MODELS
    
    @property
    def default_model(self) -> str:
        return self._default_model
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Groq API"""
        start_time = time.time()
        
        try:
            # Prepare system message
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            
            messages.append({"role": "user", "content": request.prompt})
            
            # Call Groq API
            response = await self._client.chat.completions.create(
                model=self._default_model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stop=request.stop_sequences or None,
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract response
            text = response.choices[0].message.content
            tokens_used = response.usage.completion_tokens + response.usage.prompt_tokens
            cost = tokens_used * self._cost_per_token
            
            return LLMResponse(
                text=text,
                model=self._default_model,
                backend="groq",
                tokens_used=tokens_used,
                stop_reason="stop",  # Groq always returns "stop"
                latency_ms=latency_ms,
                cost=cost,
                request_id=request.request_id,
            )
        
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            raise RuntimeError(f"Groq API error: {e}")
    
    async def stream(self, request: LLMRequest):
        """Stream response tokens from Groq"""
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        
        try:
            stream = await self._client.chat.completions.create(
                model=self._default_model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            logger.error(f"Groq streaming failed: {e}")
            raise RuntimeError(f"Groq streaming error: {e}")
    
    def supports_vision(self) -> bool:
        """Groq doesn't support vision currently"""
        return False
    
    async def health_check(self) -> bool:
        """Check if Groq API is available"""
        try:
            # Try a minimal API call
            response = await self._client.chat.completions.create(
                model=self._default_model,
                messages=[{"role": "user", "content": "hi"}],
                temperature=1.0,
                max_tokens=1,
                timeout=5.0,
            )
            return bool(response)
        except Exception as e:
            logger.error(f"Groq health check failed: {e}")
            return False
    
    async def validate_request(self, request: LLMRequest) -> tuple[bool, Optional[str]]:
        """Validate request before execution"""
        if not request.prompt or len(request.prompt) == 0:
            return False, "Prompt cannot be empty"
        
        if len(request.prompt) > 100000:
            return False, "Prompt exceeds maximum length (100k characters)"
        
        if request.temperature < 0 or request.temperature > 2:
            return False, "Temperature must be between 0 and 2"
        
        if request.max_tokens and request.max_tokens > 4096:
            return False, "Max tokens exceeds Groq limit (4096)"
        
        return True, None
    
    def estimate_cost(self, request: LLMRequest) -> float:
        """Rough cost estimate"""
        # Assume 1 prompt token = 1.33 input chars, 1 output token = cost
        prompt_tokens = len(request.prompt) / 1.33
        output_tokens = (request.max_tokens or 256)
        total_tokens = prompt_tokens + output_tokens
        return total_tokens * self._cost_per_token
