import logging
import json
import asyncio
import websockets
import ssl
from ..constants import WEBSOCKET_PATH, NGROK_URL

class WebSocketManager:
    """
    Manages WebSocket connection and message routing.
    Handles connection lifecycle and message distribution.
    """
    def __init__(self):
        self.task_manager = None
        self.server_url = NGROK_URL.replace('https://', 'wss://') + WEBSOCKET_PATH
        self.logger = logging.getLogger(__name__)
        # Create SSL context that doesn't verify certificates
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    def set_task_manager(self, task_manager) -> None:
        """Set the task manager for message routing."""
        self.task_manager = task_manager
    
    async def start(self) -> None:
        """Start the WebSocket client and maintain connection."""
        while True:
            try:
                self.logger.info(f"Connecting to server at: {self.server_url}")
                
                async with websockets.connect(
                    self.server_url,
                    ssl=self.ssl_context
                ) as websocket:
                    self.logger.info("Connected to WebSocket server")
                    while True:
                        try:
                            message = json.loads(await websocket.recv())
                            if message.get('type') == 'kill':
                                await self.task_manager.kill_current_task('vision')
                            else:
                                await self.task_manager.queue_task('vision', message, websocket)
                        except json.JSONDecodeError:
                            self.logger.error("Invalid JSON received")
                            continue
                
            except websockets.ConnectionClosed:
                self.logger.warning("Connection closed, attempting to reconnect...")
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
                await asyncio.sleep(5)