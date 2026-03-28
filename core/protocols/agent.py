"""
Agent Protocol
Defines the interface for agent implementations
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, AsyncGenerator


class Agent(ABC):
    """
    Abstract base class for agent implementations.
    An agent receives user input and orchestrates LLM + tools to solve it.
    
    Usage:
        agent = JARVISAgent(llm_router, tool_router, memory)
        result = await agent.process_command("speed up my PC")
    """
    
    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Name of this agent"""
        pass
    
    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Unique ID of this agent instance"""
        pass
    
    @abstractmethod
    async def process_command(self, command: str, user_id: str) -> Dict[str, Any]:
        """
        Process a user command end-to-end
        
        Args:
            command: User input (e.g., "speed up my PC")
            user_id: User making the request
            
        Returns:
            Dict with:
            - goal: Extracted goal
            - tasks: Task plan
            - execution_result: Final result
            - tools_used: List of tools called
            - duration_ms: Total time
            - success: Was it successful?
            - error: Error message if failed
        """
        pass
    
    @abstractmethod
    async def stream_command(self, command: str, user_id: str) -> AsyncGenerator[str, None]:
        """
        Process command with real-time streaming updates
        
        Yields:
            str: JSON-encoded event messages as they happen
            Format: {"type": "goal_extracted|planning|executing|complete", "data": {...}}
        """
        pass
    
    @abstractmethod
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an in-progress execution"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if agent is healthy and ready"""
        pass
