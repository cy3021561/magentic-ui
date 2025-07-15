import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    """
    Abstract base class for all tools.
    Provides queue management and basic tool lifecycle.
    """
    def __init__(self):
        self.queue = asyncio.Queue()
        self.current_task = None
        self.logger = logging.getLogger(__name__)
    
    async def queue_message(self, message: Dict[str, Any], websocket) -> None:
        """Add a message to the tool's processing queue."""
        await self.queue.put((message, websocket))
    
    async def process_queue(self) -> None:
        """Process all messages in the queue."""
        while not self.queue.empty():
            message, websocket = await self.queue.get()
            try:
                self.current_task = asyncio.create_task(
                    self.process_message(message, websocket)
                )
                await self.current_task
            except asyncio.CancelledError:
                self.logger.info("Task cancelled")
            finally:
                self.current_task = None
    
    async def kill_current_task(self) -> None:
        """Cancel the currently executing task if any."""
        if self.current_task:
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                pass
    
    @abstractmethod
    async def process_message(self, message: Dict[str, Any], websocket) -> None:
        """Process a single message. Must be implemented by concrete tools."""
        pass