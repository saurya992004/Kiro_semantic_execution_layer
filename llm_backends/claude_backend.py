"""
Claude LLM Backend Implementation (Anthropic)
Implements the LLMBackend protocol for Claude API

Shows how easily new backends can be added (no core changes needed!)
"""

import asyncio
import logging
import time
from typing import List, Optional

try:
    from anthropic import AsyncAnthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    logger = logging.getLogger(__name__)
    logger.warning("Anthropic SDK not installed. Install with: pip install anthropic")

from ..protocols import LLMBackend, LLMRequest, LLMResponse


logger = logging.getLogger(__name__)


class ClaudeBackend(LLMBackend):
    """
    Anthropic Claude LLM backend implementation
    
    To use, install: pip install anthropic
    
    Usage:
        backend = ClaudeBackend(api_key="sk-ant-...")
        response = await backend.generate(LLMRequest(prompt="Hello"))
    """
    
    AVAILABLE_MODELS = [
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",
    ]
    
    DEFAULT_MODEL = "claude-3-sonnet"
    
    def __init__(self, api_key: str, default_model: str = DEFAULT_MODEL):
        """Initialize Claude backend"""
        if not HAS_ANTHROPIC:
            raise RuntimeError("Anthropic SDK not installed. Run: pip install anthropic")
        
        self.api_key = api_key
        self._default_model = default_model
        self._client = AsyncAnthropic(api_key=api_key)
        self._cost_per_token = 0.00015  # Approximate
    
    @property
    def backend_name(self) -> str:
        return "claude"
    
    @property
    def available_models(self) -> List[str]:
        return self.AVAILABLE_MODELS
    
    @property
    def default_model(self) -> str:
        return self._default_model
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Claude API"""
        start_time = time.time()
        
        try:
            messages = [{"role": "user", "content": request.prompt}]
            
            response = await self._client.messages.create(
                model=self._default_model,
                max_tokens=request.max_tokens or 1024,
                system=request.system_prompt,
                messages=messages,
                temperature=request.temperature,
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            text = response.content[0].text
            tokens = response.usage.output_tokens + response.usage.input_tokens
            cost = tokens * self._cost_per_token
            
            return LLMResponse(
                text=text,
                model=self._default_model,
                backend="claude",
                tokens_used=tokens,
                stop_reason="end_turn",
                latency_ms=latency_ms,
                cost=cost,
                request_id=request.request_id,
            )
        
        except Exception as e:
            logger.error(f"Claude generation failed: {e}")
            raise RuntimeError(f"Claude API error: {e}")
    
    async def stream(self, request: LLMRequest):
        """Stream response from Claude"""
        messages = [{"role": "user", "content": request.prompt}]
        
        try:
            async with await self._client.messages.stream(
                model=self._default_model,
                max_tokens=request.max_tokens or 1024,
                system=request.system_prompt,
                messages=messages,
                temperature=request.temperature,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        
        except Exception as e:
            logger.error(f"Claude streaming failed: {e}")
            raise RuntimeError(f"Claude streaming error: {e}")
    
    def supports_vision(self) -> bool:
        return True
    
    async def health_check(self) -> bool:
        """Check if Claude API is available"""
        try:
            response = await self._client.messages.create(
                model=self._default_model,
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}],
            )
            return bool(response)
        except Exception as e:
            logger.error(f"Claude health check failed: {e}")
            return False
    
    async def validate_request(self, request: LLMRequest) -> tuple[bool, Optional[str]]:
        """Validate request"""
        if not request.prompt:
            return False, "Prompt required"
        if len(request.prompt) > 10000:
            return False, "Prompt too long"
        return True, None
    
    def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate cost"""
        prompt_tokens = len(request.prompt) / 1.3
        output_tokens = request.max_tokens or 1024
        return (prompt_tokens + output_tokens) * self._cost_per_token
