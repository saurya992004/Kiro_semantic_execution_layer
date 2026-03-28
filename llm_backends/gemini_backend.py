"""
Gemini LLM Backend Implementation
Implements the LLMBackend protocol for Google Gemini API
"""

import asyncio
import logging
import time
from typing import List, Optional

import google.generativeai as genai

from ..protocols import LLMBackend, LLMRequest, LLMResponse


logger = logging.getLogger(__name__)


class GeminiBackend(LLMBackend):
    """
    Google Gemini LLM backend implementation
    Uses official Google Generative AI SDK
    
    Usage:
        backend = GeminiBackend(api_key="AIza...")
        request = LLMRequest(prompt="What is Python?")
        response = await backend.generate(request)
    """
    
    AVAILABLE_MODELS = [
        "gemini-pro",
        "gemini-pro-vision",
    ]
    
    DEFAULT_MODEL = "gemini-pro"
    
    def __init__(self, api_key: str, default_model: str = DEFAULT_MODEL):
        """
        Initialize Gemini backend
        
        Args:
            api_key: Google API key
            default_model: Default model
        """
        self.api_key = api_key
        self._default_model = default_model
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(default_model)
        self._cost_per_token = 0.000125  # Approximate
    
    @property
    def backend_name(self) -> str:
        return "gemini"
    
    @property
    def available_models(self) -> List[str]:
        return self.AVAILABLE_MODELS
    
    @property
    def default_model(self) -> str:
        return self._default_model
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Gemini API"""
        start_time = time.time()
        
        try:
            # Gemini handles system prompt differently
            prompt = request.prompt
            if request.system_prompt:
                prompt = f"{request.system_prompt}\n\n{request.prompt}"
            
            # Call Gemini API (synchronous, so run in executor)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=request.temperature,
                        max_output_tokens=request.max_tokens,
                    ),
                )
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            text = response.text
            # Gemini doesn't provide token count, estimate it
            total_tokens = len(prompt.split()) // 4 + len(text.split()) // 4
            cost = total_tokens * self._cost_per_token
            
            return LLMResponse(
                text=text,
                model=self._default_model,
                backend="gemini",
                tokens_used=total_tokens,
                stop_reason="stop",
                latency_ms=latency_ms,
                cost=cost,
                request_id=request.request_id,
            )
        
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise RuntimeError(f"Gemini API error: {e}")
    
    async def stream(self, request: LLMRequest):
        """Stream response from Gemini"""
        prompt = request.prompt
        if request.system_prompt:
            prompt = f"{request.system_prompt}\n\n{request.prompt}"
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._model.generate_content(
                    prompt,
                    stream=True,
                    generation_config=genai.types.GenerationConfig(
                        temperature=request.temperature,
                        max_output_tokens=request.max_tokens,
                    ),
                )
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        
        except Exception as e:
            logger.error(f"Gemini streaming failed: {e}")
            raise RuntimeError(f"Gemini streaming error: {e}")
    
    def supports_vision(self) -> bool:
        """Gemini supports vision"""
        return True
    
    async def health_check(self) -> bool:
        """Check if Gemini API is available"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._model.generate_content("hi", generation_config=genai.types.GenerationConfig(max_output_tokens=1))
            )
            return bool(response)
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")
            return False
    
    async def validate_request(self, request: LLMRequest) -> tuple[bool, Optional[str]]:
        """Validate request"""
        if not request.prompt:
            return False, "Prompt cannot be empty"
        
        if len(request.prompt) > 1000000:
            return False, "Prompt exceeds maximum length"
        
        return True, None
    
    def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate cost"""
        prompt_tokens = len(request.prompt) / 1.33
        output_tokens = request.max_tokens or 256
        return (prompt_tokens + output_tokens) * self._cost_per_token
