#!/usr/bin/env python3
"""
Simple test script to demonstrate the cropping functionality.
This script shows how to trigger cropping from the host machine.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.browser_manager.vnc_browser import VncDockerPlaywrightBrowser


async def main():
    """
    Test the cropping functionality:
    1. Start the VNC browser container
    2. Load a webpage
    3. Demonstrate how to trigger cropping
    4. Show how to access the cropped images
    """
    print("🚀 Starting cropping test...")
    print("Reminder: Make sure you have built the Docker image first.")
    print("Run: docker build -t magentic-ui-vnc-browser:latest ./docker_assets/browser")

    # Define the workspace directory
    workspace_dir = Path("./workspace").resolve()
    workspace_dir.mkdir(exist_ok=True)
    
    # Clean up any existing trigger files
    trigger_file = workspace_dir / "crop_trigger.txt"
    if trigger_file.exists():
        print(f"🧹 Cleaning up existing trigger file: {trigger_file}")
        trigger_file.unlink()

    browser_manager = VncDockerPlaywrightBrowser(
        bind_dir=workspace_dir,
        image="magentic-ui-vnc-browser:latest",
    )

    try:
        async with browser_manager as bm:
            print(f"✅ VNC Live View available at: {bm.vnc_address}")
            print(f"   Container name: {bm.container_name}")
            print(f"   Workspace directory: {workspace_dir}")

            # Use Playwright to set up the initial browser state
            page = await bm.browser_context.new_page()
            await page.goto("https://www.google.com")
            print("✅ Browser setup complete - Google.com loaded.")

            print("\n=== CROPPING INSTRUCTIONS ===")
            print("The cropping service is now running inside the container.")
            print("Workflow:")
            print("1. Create trigger file to start cropping mode:")
            print(f"   docker exec {bm.container_name} touch /workspace/crop_trigger.txt")
            print()
            print("2. Once cropping mode is activated:")
            print("   - Open VNC at the URL above")
            print("   - Navigate to the area you want to crop")
            print("   - Press 'c' to crop at current mouse position")
            print("   - Press 'q' to exit cropping mode")
            print()
            print("3. Cropped images will be saved to:")
            print(f"   {workspace_dir}/cropped_screenshot_*.png")
            print()
            print("=== TESTING CROPPING ===")
            
            # Wait a bit for the user to read instructions
            await asyncio.sleep(5)
            
            # Demonstrate file-based triggering
            print("🎯 Testing file-based cropping trigger...")
            trigger_file.touch()
            print(f"✅ Created trigger file: {trigger_file}")
            print("Cropping mode should now be activated!")
            
            print("\n=== MANUAL TESTING ===")
            print("Now you can manually test the cropping:")
            print("1. Open the VNC URL in your browser")
            print("2. Navigate around the webpage")
            print("3. Press 'c' to crop at current mouse position")
            print("4. Press 'q' to exit cropping mode")
            print("5. Check the workspace directory for new images")
            print()
            print("The container will run for 60 seconds for manual testing...")
            
            # Keep the container running for manual testing
            await asyncio.sleep(60000)

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🧹 Cleaning up...")
        # Clean up trigger file if it still exists
        if trigger_file.exists():
            trigger_file.unlink()
        print("✅ Test completed. Container will be stopped automatically.")


if __name__ == "__main__":
    asyncio.run(main()) 