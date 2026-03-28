"""
Tool Server Protocol
Defines the interface all tools must implement.
Tools auto-register with the ToolRegistry.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
from enum import Enum
from datetime import datetime


class ToolCategory(str, Enum):
    """Categories tools can belong to"""
    FILE_MANAGEMENT = "file_management"
    SYSTEM = "system"
    DIAGNOSTICS = "diagnostics"
    VISION = "vision"
    WEB = "web"
    COMMUNICATION = "communication"
    AUTOMATION = "automation"
    CUSTOM = "custom"


@dataclass
class ToolDefinition:
    """Metadata describing a tool"""
    
    name: str  # Unique tool identifier (e.g., "find_large_files")
    display_name: str  # Human-readable name
    description: str  # What does this tool do?
    category: ToolCategory
    parameters: Dict[str, Dict[str, Any]]  # JSON schema for parameters
    returns: Dict[str, Any]  # JSON schema for return value
    requires_user_approval: bool = False  # Needs confirmation before execution
    is_safe: bool = True  # Safe to Auto-execute
    version: str = "1.0.0"
    author: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category.value,
            "parameters": self.parameters,
            "returns": self.returns,
            "requires_user_approval": self.requires_user_approval,
            "is_safe": self.is_safe,
            "version": self.version,
            "author": self.author,
            "metadata": self.metadata,
        }


@dataclass
class ToolInput:
    """Input to a tool"""
    
    tool_name: str
    parameters: Dict[str, Any]
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    timeout: Optional[float] = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolOutput:
    """Output from a tool"""
    
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class ToolServer(ABC):
    """
    Abstract base class for tool servers (tool containers).
    Each tool server hosts one or more related tools.
    
    Example:
        class FileToolServer(ToolServer):
            def list_tools(self):
                return [
                    ToolDefinition("find_large_files", ...),
                    ToolDefinition("organize_files", ...),
                ]
            
            async def execute(self, tool_input):
                if tool_input.tool_name == "find_large_files":
                    return await find_large_files(...)
    """
    
    @property
    @abstractmethod
    def server_name(self) -> str:
        """Unique name for this tool server (e.g., 'file_tools', 'system_tools')"""
        pass
    
    @abstractmethod
    def list_tools(self) -> List[ToolDefinition]:
        """Return list of tools this server provides"""
        pass
    
    @abstractmethod
    async def execute(self, tool_input: ToolInput) -> ToolOutput:
        """
        Execute a tool on this server
        
        Args:
            tool_input: Specifies which tool and with what parameters
            
        Returns:
            ToolOutput with result or error
            
        Raises:
            ValueError: If tool not found or params invalid
            TimeoutError: If execution exceeds timeout
            RuntimeError: If underlying service fails
        """
        pass
    
    @abstractmethod
    async def validate_tool(self, tool_name: str, parameters: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate tool input without executing
        Return (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if this tool server is healthy"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Clean shutdown of tool server"""
        pass
    
    def get_tool_definition(self, tool_name: str) -> Optional[ToolDefinition]:
        """Helper: get single tool definition by name"""
        tools = self.list_tools()
        for tool in tools:
            if tool.name == tool_name:
                return tool
        return None
