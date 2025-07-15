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

            # Use Playwright to set up the initial browser state
            page = await bm.browser_context.new_page()
            await page.goto("https://officeally.com/")
            print("✅ Browser setup complete - Officeally.com loaded.")

            await asyncio.sleep(30000)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("\nAll tasks finished. The container will be stopped automatically.")


if __name__ == "__main__":
    asyncio.run(main())
