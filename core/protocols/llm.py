"""
LLM Backend Protocol
Defines the interface all LLM backends must implement (Groq, Claude, OpenAI, Ollama, etc.)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
from datetime import datetime


@dataclass
class LLMRequest:
    """Request to send to an LLM backend"""
    
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stop_sequences: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    timeout: Optional[float] = 30.0


@dataclass
class LLMResponse:
    """Response from an LLM backend"""
    
    text: str
    model: str
    backend: str
    tokens_used: int
    stop_reason: str  # "stop", "length", "stop_sequence", "error"
    latency_ms: float
    cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    cost: Optional[float] = None


class LLMBackend(ABC):
    """
    Abstract base class for LLM backends.
    Any new LLM (Claude, OpenAI, Ollama, etc.) must implement this interface.
    
    Usage:
        backend = GroqBackend(api_key="xxx")
        request = LLMRequest(prompt="What is Python?")
        response = await backend.generate(request)
        print(response.text)
    """
    
    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Unique identifier for this backend (e.g., 'groq', 'claude', 'openai')"""
        pass
    
    @property
    @abstractmethod
    def available_models(self) -> List[str]:
        """List of available models for this backend"""
        pass
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model to use if none specified"""
        pass
    
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate a response from this LLM backend
        
        Args:
            request: LLMRequest with prompt and parameters
            
        Returns:
            LLMResponse with generated text and metadata
            
        Raises:
            TimeoutError: If request exceeds timeout
            ValueError: If prompt is invalid or too long
            RuntimeError: If backend service is unavailable
        """
        pass
    
    @abstractmethod
    async def stream(self, request: LLMRequest):
        """
        Stream response tokens from this LLM backend (async generator)
        
        Yields:
            str: Token chunks as they arrive
            
        Raises:
            Same as generate()
        """
        pass
    
    @abstractmethod
    def supports_vision(self) -> bool:
        """Whether this backend can process images"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if backend service is available and responsive"""
        pass
    
    @abstractmethod
    async def validate_request(self, request: LLMRequest) -> tuple[bool, Optional[str]]:
        """
        Validate request without executing it.
        Return (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate cost in USD for this request"""
        pass
