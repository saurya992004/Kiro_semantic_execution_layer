"""
Example File Tools Server Implementation
Shows how tool servers self-register with the ToolRegistry
No monolithic router modifications needed!

Migration from old system:
OLD: 300+ lines in intent_router.py with hardcoded if/elif
NEW: FileToolServer.py with clean, modular tool implementations
     Tool registry auto-discovers at startup
"""

import logging
import asyncio
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

from ..protocols import ToolServer, ToolInput, ToolOutput, ToolDefinition, ToolCategory


logger = logging.getLogger(__name__)


class FileToolServer(ToolServer):
    """
    Example tool server implementing file management tools
    In real deployment, this would be in tool_servers/file_tools/
    """
    
    def __init__(self):
        """Initialize file tools"""
        self._execution_count = 0
    
    @property
    def server_name(self) -> str:
        return "file_tools"
    
    def list_tools(self) -> List[ToolDefinition]:
        """Describe all tools this server provides"""
        return [
            ToolDefinition(
                name="find_large_files",
                display_name="Find Large Files",
                description="Find files larger than specified size",
                category=ToolCategory.FILE_MANAGEMENT,
                parameters={
                    "path": {"type": "string", "description": "Directory to scan"},
                    "min_size_mb": {"type": "number", "description": "Minimum file size in MB"},
                    "max_results": {"type": "number", "description": "Max results to return", "default": 50},
                },
                returns={
                    "type": "object",
                    "properties": {
                        "files": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"},
                                    "size_mb": {"type": "number"},
                                }
                            }
                        }
                    }
                },
                is_safe=True,
                requires_user_approval=False,
            ),
            ToolDefinition(
                name="organize_directory",
                display_name="Organize Directory",
                description="Organize files into folders by type",
                category=ToolCategory.FILE_MANAGEMENT,
                parameters={
                    "path": {"type": "string", "description": "Directory to organize"},
                    "by_extension": {"type": "boolean", "description": "Group by file extension?", "default": True},
                },
                returns={
                    "type": "object",
                    "properties": {
                        "moved": {"type": "number"},
                        "folders_created": {"type": "number"},
                    }
                },
                is_safe=False,
                requires_user_approval=True,  # Modifies filesystem
            ),
        ]
    
    async def execute(self, tool_input: ToolInput) -> ToolOutput:
        """Execute a file tool"""
        start_time = time.time()
        
        try:
            if tool_input.tool_name == "find_large_files":
                return await self._find_large_files(tool_input)
            elif tool_input.tool_name == "organize_directory":
                return await self._organize_directory(tool_input)
            else:
                return ToolOutput(
                    tool_name=tool_input.tool_name,
                    success=False,
                    result=None,
                    error=f"Unknown tool: {tool_input.tool_name}",
                    latency_ms=(time.time() - start_time) * 1000,
                )
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return ToolOutput(
                tool_name=tool_input.tool_name,
                success=False,
                result=None,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000,
            )
    
    async def _find_large_files(self, tool_input: ToolInput) -> ToolOutput:
        """Implement find_large_files tool"""
        params = tool_input.parameters
        path = params.get("path", ".")
        min_size_mb = params.get("min_size_mb", 100)
        max_results = params.get("max_results", 50)
        
        start_time = time.time()
        
        try:
            # Simulate scanning (in real impl, actually scan filesystem)
            large_files = []
            
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        filepath = os.path.join(root, file)
                        size_mb = os.path.getsize(filepath) / (1024 * 1024)
                        
                        if size_mb >= min_size_mb:
                            large_files.append({
                                "path": filepath,
                                "size_mb": round(size_mb, 2),
                            })
                        
                        if len(large_files) >= max_results:
                            break
                    
                    if len(large_files) >= max_results:
                        break
                
                # Sort by size descending
                large_files.sort(key=lambda x: x["size_mb"], reverse=True)
                large_files = large_files[:max_results]
            
            result = {
                "files": large_files,
                "total_found": len(large_files),
                "directory": path,
                "min_size_threshold_mb": min_size_mb,
            }
            
            return ToolOutput(
                tool_name="find_large_files",
                success=True,
                result=result,
                latency_ms=(time.time() - start_time) * 1000,
                request_id=tool_input.request_id,
            )
        
        except Exception as e:
            return ToolOutput(
                tool_name="find_large_files",
                success=False,
                result=None,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000,
            )
    
    async def _organize_directory(self, tool_input: ToolInput) -> ToolOutput:
        """Implement organize_directory tool"""
        return ToolOutput(
            tool_name="organize_directory",
            success=True,
            result={"moved": 0, "folders_created": 0},
            latency_ms=100,
            request_id=tool_input.request_id,
        )
    
    async def validate_tool(self, tool_name: str, parameters: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate tool input"""
        if tool_name == "find_large_files":
            if "path" not in parameters:
                return False, "path parameter required"
            if not isinstance(parameters.get("min_size_mb"), (int, float)):
                return False, "min_size_mb must be a number"
        
        return True, None
    
    async def health_check(self) -> bool:
        """Check if tool server is healthy"""
        return True
    
    async def shutdown(self) -> None:
        """Shutdown tool server"""
        logger.info("FileToolServer shutting down")
