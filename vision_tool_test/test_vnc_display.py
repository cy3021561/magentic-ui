#!/usr/bin/env python3
"""
Simple test to verify VNC display works properly.
This helps diagnose if WebSurfer is interfering with the browser display.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.browser_manager.vnc_browser import VncDockerPlaywrightBrowser


async def test_vnc_display():
    """Test basic VNC display without WebSurfer"""
    workspace_dir = Path("./workspace").resolve()
    workspace_dir.mkdir(exist_ok=True)

    browser_manager = VncDockerPlaywrightBrowser(
        bind_dir=workspace_dir,
        image="magentic-ui-vnc-browser:latest",
    )

    try:
        async with browser_manager as bm:
            print(f"✅ VNC Display Test")
            print(f"📺 VNC URL: {bm.vnc_address}")
            print(f"📡 Container: {bm.container_name}")
            
            print("\n🌐 Creating browser page...")
            page = await bm.browser_context.new_page()
            
            print("🚀 Navigating to OfficeAlly...")
            await page.goto("https://officeally.com/")
            
            print("⏳ Waiting for page to load...")
            await asyncio.sleep(3)
            
            # Get page info
            try:
                title = await page.title()
                url = page.url
                print(f"✅ Page loaded: '{title}' at {url}")
            except Exception as e:
                print(f"❌ Failed to get page info: {e}")
            
            print(f"\n📺 Open VNC at: {bm.vnc_address}")
            print("🔍 You should see the OfficeAlly website")
            print("⏱️  Test will run for 60 seconds...")
            
            # Keep running to allow manual inspection
            for i in range(60):
                await asyncio.sleep(1)
                if i % 10 == 0:
                    print(f"⏱️  {60-i} seconds remaining...")
            
            print("✅ VNC display test completed")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🧪 VNC Display Test - No WebSurfer Interference")
    print("="*50)
    asyncio.run(test_vnc_display()) 