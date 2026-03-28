"""
Tool Registry & Router
Replaces the old monolithic intent_router.py
Tools are self-registered, not hardcoded
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

from ..protocols import ToolServer, ToolInput, ToolOutput, ToolDefinition, EventType, Event, EventBus


logger = logging.getLogger(__name__)


@dataclass
class RegisteredTool:
    """A tool registered in the system"""
    tool_name: str
    definition: ToolDefinition
    server: ToolServer


class ToolRegistry:
    """
    Central registry of all available tools.
    Tools self-register via register_server(), not hardcoded.
    
    Replaces old intent_router.py with 300+ lines of if/elif.
    New approach: Register servers at startup, discover tools automatically.
    
    Usage:
        registry = ToolRegistry()
        
        # At startup, mount tool servers
        file_server = FileToolServer()
        await registry.register_server(file_server)
        
        system_server = SystemToolServer()
        await registry.register_server(system_server)
        
        # Now route a tool call
        output = await registry.execute(ToolInput(
            tool_name="find_large_files",
            parameters={"path": "/home", "min_size_mb": 100}
        ))
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        Initialize tool registry
        
        Args:
            event_bus: Event bus for publishing events
        """
        self._servers: Dict[str, ToolServer] = {}  # server_name -> server
        self._tools: Dict[str, RegisteredTool] = {}  # tool_name -> tool info
        self._event_bus = event_bus
        self._execution_stats = {
            "total_executions": 0,
            "successful": 0,
            "failed": 0,
            "tool_usage": {},
        }
    
    async def register_server(self, server: ToolServer) -> None:
        """
        Register a tool server and discover its tools
        
        Args:
            server: ToolServer instance
        """
        server_name = server.server_name
        
        # Check health
        if not await server.health_check():
            logger.warning(f"Tool server {server_name} failed health check")
            return
        
        self._servers[server_name] = server
        
        # Discover and register all tools
        tools = server.list_tools()
        for tool_def in tools:
            self._tools[tool_def.name] = RegisteredTool(
                tool_name=tool_def.name,
                definition=tool_def,
                server=server,
            )
            logger.info(f"Registered tool: {tool_def.name} (from {server_name})")
        
        logger.info(f"Tool server registered: {server_name} ({len(tools)} tools)")
    
    async def unregister_server(self, server_name: str) -> None:
        """Unregister a tool server and its tools"""
        if server_name not in self._servers:
            return
        
        server = self._servers[server_name]
        
        # Remove all tools from this server
        tools_to_remove = [
            name for name, tool in self._tools.items() 
            if tool.server == server
        ]
        for tool_name in tools_to_remove:
            del self._tools[tool_name]
        
        # Shutdown server
        try:
            await server.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down {server_name}: {e}")
        
        del self._servers[server_name]
        logger.info(f"Tool server unregistered: {server_name}")
    
    def list_servers(self) -> List[str]:
        """List registered tool servers"""
        return list(self._servers.keys())
    
    def list_tools(self, server_name: Optional[str] = None) -> List[ToolDefinition]:
        """
        List available tools
        
        Args:
            server_name: Filter by server (if provided)
            
        Returns:
            List of ToolDefinition
        """
        if server_name:
            return [
                tool.definition for tool in self._tools.values()
                if tool.server.server_name == server_name
            ]
        return [tool.definition for tool in self._tools.values()]
    
    def get_tool(self, tool_name: str) -> Optional[ToolDefinition]:
        """Get a specific tool definition"""
        if tool_name in self._tools:
            return self._tools[tool_name].definition
        return None
    
    async def execute(self, tool_input: ToolInput) -> ToolOutput:
        """
        Execute a tool
        
        Args:
            tool_input: Specifies which tool and with what parameters
            
        Returns:
            ToolOutput with result or error
            
        Raises:
            ValueError: Tool not found
            RuntimeError: Tool execution failed
        """
        tool_name = tool_input.tool_name
        
        if tool_name not in self._tools:
            raise ValueError(f"Tool not found: {tool_name}")
        
        registered = self._tools[tool_name]
        server = registered.server
        
        # Publish tool called event
        if self._event_bus:
            await self._event_bus.publish(Event(
                event_type=EventType.TOOL_CALLED,
                data={
                    "tool_name": tool_name,
                    "parameter_count": len(tool_input.parameters),
                },
                source="tool_registry",
                user_id=tool_input.user_id,
                request_id=tool_input.request_id,
            ))
        
        self._execution_stats["total_executions"] += 1
        if tool_name not in self._execution_stats["tool_usage"]:
            self._execution_stats["tool_usage"][tool_name] = 0
        self._execution_stats["tool_usage"][tool_name] += 1
        
        # Validate before execution
        is_valid, error = await server.validate_tool(tool_name, tool_input.parameters)
        if not is_valid:
            raise ValueError(f"Invalid tool input: {error}")
        
        try:
            # Execute tool
            output = await server.execute(tool_input)
            
            if output.success:
                self._execution_stats["successful"] += 1
                
                # Publish success event
                if self._event_bus:
                    await self._event_bus.publish(Event(
                        event_type=EventType.TOOL_RESULT,
                        data={
                            "tool_name": tool_name,
                            "latency_ms": output.latency_ms,
                        },
                        source="tool_registry",
                        user_id=tool_input.user_id,
                        request_id=tool_input.request_id,
                    ))
            else:
                self._execution_stats["failed"] += 1
                
                # Publish error event
                if self._event_bus:
                    await self._event_bus.publish(Event(
                        event_type=EventType.TOOL_ERROR,
                        data={
                            "tool_name": tool_name,
                            "error": output.error,
                        },
                        source="tool_registry",
                        user_id=tool_input.user_id,
                        request_id=tool_input.request_id,
                    ))
            
            return output
            
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name}: {e}", exc_info=True)
            self._execution_stats["failed"] += 1
            
            raise RuntimeError(f"Tool execution failed: {e}")
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all tools servers"""
        health = {}
        for server_name, server in self._servers.items():
            try:
                health[server_name] = await server.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {server_name}: {e}")
                health[server_name] = False
        return health
    
    async def shutdown_all(self) -> None:
        """Shutdown all tool servers gracefully"""
        for server_name in list(self._servers.keys()):
            await self.unregister_server(server_name)
    
    def get_stats(self) -> Dict:
        """Get usage statistics"""
        return {
            **self._execution_stats,
            "total_tools": len(self._tools),
            "total_servers": len(self._servers),
        }
