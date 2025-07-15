import asyncio
import logging
from typing import Optional

from .core import WebSocketManager, TaskManager
from .tools import VisionTool

class Client:
    """Main client class that orchestrates the WebSocket tool client."""
    
    def __init__(self, emr_system: str = "office_ally"):
        # Setup logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Initialize components
        self.ws_manager = WebSocketManager()
        self.task_manager = TaskManager()
        
        # Initialize and register vision tool
        self.vision_tool = VisionTool(emr_system)
        self.task_manager.register_tool('vision', self.vision_tool)
        
        # Connect components
        self.ws_manager.set_task_manager(self.task_manager)
    
    async def run(self) -> None:
        """Start the client."""
        try:
            await self.ws_manager.start()
        except Exception as e:
            self.logger.error(f"Client error: {e}")
            raise

def main():
    """Entry point for the client."""
    client = Client()
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        print("\nShutting down client...")
    except Exception as e:
        print(f"Error running client: {e}")

# Under webscoket_chat, run python -m client.client
if __name__ == "__main__":
    main()