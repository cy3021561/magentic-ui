import asyncio
import logging
from typing import Dict, Optional
from .base_tool import BaseTool

class TaskManager:
    """
    Manages execution of multiple tools ensuring only one runs at a time.
    Handles task queuing and execution control.
    """
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.current_tool: Optional[str] = None
        self.execution_lock = asyncio.Lock()
        self.processing_task = None
        self.logger = logging.getLogger(__name__)
    
    def register_tool(self, tool_id: str, tool: BaseTool) -> None:
        """Register a new tool with the manager."""
        self.tools[tool_id] = tool
        self.logger.info(f"Registered tool: {tool_id}")
    
    async def queue_task(self, tool_id: str, message: Dict, websocket) -> None:
        """Queue a task for execution by a specific tool."""
        if tool_id not in self.tools:
            self.logger.error(f"Unknown tool ID: {tool_id}")
            return
        
        # Add message to tool's queue
        await self.tools[tool_id].queue_message(message, websocket)
        self.logger.debug(f"Queued message for tool: {tool_id}")
        
        # Start processing if not already running
        if self.processing_task is None or self.processing_task.done():
            self.processing_task = asyncio.create_task(self.process_tasks())
    
    async def process_tasks(self) -> None:
        """Continuously process tasks until all queues are empty."""
        while True:
            # Try to acquire lock
            async with self.execution_lock:
                if self.current_tool is not None:
                    # Someone else is processing, exit
                    return
                
                # Check all tools for work
                found_work = False
                for tool_id, tool in self.tools.items():
                    if not tool.queue.empty():
                        found_work = True
                        self.current_tool = tool_id
                        try:
                            await tool.process_queue()
                        finally:
                            self.current_tool = None
                
                # If no work found, exit processing loop
                if not found_work:
                    break

            # Small delay before checking queues again
            await asyncio.sleep(0.1)
    
    async def kill_current_task(self, tool_id: str) -> None:
        """Kill the currently executing task for a specific tool."""
        if tool_id in self.tools:
            self.logger.info(f"Killing current task for tool: {tool_id}")
            await self.tools[tool_id].kill_current_task()