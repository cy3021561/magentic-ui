import asyncio
import os
import sys
from pathlib import Path

# Add the project's root directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


async def main():
    """Main function to run the browser automation"""
    # Get the OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ Missing OPENAI_API_KEY environment variable. WebSurfer will be disabled.")

    # Use the WebSurferManager as a context manager
    try:
        async with WebSurferManager(openai_api_key=os.getenv("OPENAI_API_KEY")) as websurfer_manager:
            # Initialization is now handled inside the manager's context entry
            if await websurfer_manager.initialize():
                print("✅ WebSurfer initialized successfully")

                # Get login credentials
                username = "cyang513"
                password = "SACFbridgent12345"
                
                # VNC link is now available from the manager's browser instance
                if websurfer_manager.vnc_browser:
                    print(f"✅ VNC Live View available at: {websurfer_manager.vnc_browser.vnc_address}")
                    print(f"📡 Container: {websurfer_manager.vnc_browser.container_name}")

                # Perform login
                print("🚀 Starting login process...")
                success = await websurfer_manager.navigate_and_login(
                    url="https://www.officeally.com",
                    username=username,
                    password=password
                )
                
                if success:
                    print("✅ Login successful!")
                else:
                    print("❌ Login failed.")

            else:
                print("WebSurfer could not be initialized. Please check your API key and dependencies.")
            
            # Keep the container running until keyboard interrupt
            print("🕒 Script finished. Press Ctrl+C to exit...")
            try:
                await asyncio.Event().wait()  # Wait indefinitely until interrupted
            except KeyboardInterrupt:
                print("\n👋 Received keyboard interrupt, shutting down...")
            
    except Exception as e:
        print(f"An error occurred in the main execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Since this file is in 'src', we need to adjust the path to import from 'browser_manager'
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from browser_manager.websurfer_manager import WebSurferManager
    asyncio.run(main())
