import asyncio
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.browser_manager.vnc_browser import (
    VncDockerPlaywrightBrowser,
)


async def main():
    """
    Orchestrates the browser automation task.
    1. Starts a VNC-enabled browser container.
    2. Uses Playwright to connect and set up the browser.
    3. Executes the pyautogui script inside the container using `docker exec`.
    4. Cleans up all resources automatically.
    """
    print("Reminder: Make sure you have built the Docker image first.")
    print("Run: docker build -t magentic-ui-vnc-browser:latest ./vision_tool_test/docker_assets/browser")

    # Define the workspace directory. This will be mounted into the container.
    workspace_dir = Path("./workspace").resolve()
    workspace_dir.mkdir(exist_ok=True)
    
    # Clean up any existing trigger files from previous runs
    trigger_file = workspace_dir / "trigger.txt"
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
            print(f"   Playwright Endpoint: {bm.browser_address}")
            print(f"   Container name: {bm.container_name}")
            print(f"   noVNC port: {bm.novnc_port}")
            print(f"   Playwright port: {bm.playwright_port}")

            # Use Playwright to set up the initial browser state
            page = await bm.browser_context.new_page()
            await page.goto("https://www.yahoo.com")
            print("✅ Browser setup complete - Yahoo.com loaded.")

            print("\nRunning PyAutoGUI script inside the container...")
            # Get the container object from the browser manager
            container = bm.container
            if container:
                # First, test X11 connectivity
                print("Testing X11 connectivity...")
                exit_code, output = await asyncio.to_thread(
                    container.exec_run, "python3 /app/test_x11.py" # type: ignore
                )
                print("--- X11 Test Output ---")
                print(output.decode("utf-8"))
                print("----------------------")
                
                if exit_code == 0:
                    print("✅ X11 test passed!")
                    print("✅ PyAutoGUI service is running and ready for triggers!")
                else:
                    print(f"❌ X11 test failed with exit code {exit_code}.")
                    print("This indicates an X11 authentication or setup issue.")
            else:
                print("❌ Could not find the container to trigger the script.")

            print("\n=== PyAutoGUI Trigger Instructions ===")
            print("To trigger the PyAutoGUI automation:")
            print("1. Open a new terminal")
            print("2. Run: docker exec <container_name> touch /workspace/trigger.txt")
            print(f"   Container name: {bm.container_name}")
            print("3. Watch the VNC screen for mouse movements")
            print("4. You can trigger it multiple times!")
            
            print("\nAutomation finished. The browser will remain open for 300 seconds (5 minutes).")
            print("You can trigger PyAutoGUI multiple times during this period.")
            await asyncio.sleep(10)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("\nAll tasks finished. The container will be stopped automatically.")


if __name__ == "__main__":
    asyncio.run(main())
