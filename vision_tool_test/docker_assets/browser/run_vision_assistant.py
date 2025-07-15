import asyncio
import sys
import time

# Add both the src directory and the vision_assistant directory to the Python path
sys.path.insert(0, '/app/vision_assistant/src')
sys.path.insert(0, '/app/vision_assistant')

# Now the client package and vision_assistant package are both available
from client.client import main as vision_main

if __name__ == "__main__":
    # A small delay to ensure the X11 server is fully ready before the assistant starts.
    time.sleep(5)
    asyncio.run(vision_main()) 