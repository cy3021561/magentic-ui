import time
import os
import sys
from pathlib import Path
from datetime import datetime

# Ensure X11 environment is properly set
os.environ['DISPLAY'] = ':99'
os.environ['XAUTHORITY'] = '/root/.Xauthority'

def log(message: str) -> None:
    """Helper function to log messages with timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

# Wait for X11 to be fully ready before importing pyautogui
log("PyAutoGUI service initializing...")
log("Waiting for X11 setup to complete...")

# Wait for Xauthority file
for i in range(30):  # Wait up to 30 seconds
    if os.path.exists('/root/.Xauthority'):
        log(f"✅ Xauthority file found after {i+1} seconds")
        break
    time.sleep(1)
else:
    log("⚠️  WARNING: Xauthority file not found after 30 seconds")

# Wait for X11 socket to be available
log("Waiting for X11 socket to be available...")
for i in range(30):  # Wait up to 30 seconds
    if os.path.exists('/tmp/.X11-unix/X99'):
        log(f"✅ X11 socket found after {i+1} seconds")
        break
    time.sleep(1)
else:
    log("⚠️  WARNING: X11 socket not found after 30 seconds")

time.sleep(2)  # Additional safety delay

# Now try to import pyautogui
try:
    log("Attempting to import PyAutoGUI...")
    import pyautogui
    log("✅ PyAutoGUI imported successfully")
except Exception as e:
    log(f"❌ Failed to import PyAutoGUI: {e}")
    sys.exit(1)

def do_automation_task():
    """
    Automation task that interacts with Yahoo.com search bar:
    1. Move cursor to search bar coordinates
    2. Click on search bar
    3. Select all text (Ctrl+A)
    4. Delete content
    5. Type "I'm working."
    """
    log("🎯 Yahoo search bar automation task started!")
    log(f"📺 DISPLAY: {os.environ.get('DISPLAY', 'NOT SET')}")
    log(f"🔐 XAUTHORITY: {os.environ.get('XAUTHORITY', 'NOT SET')}")
    
    try:
        # Give it a few seconds for the user to connect via VNC
        log("⏳ Waiting 3 seconds for VNC connection...")
        time.sleep(3)

        # Get screen dimensions
        screenWidth, screenHeight = pyautogui.size()
        log(f"🖥️  Screen dimensions: {screenWidth}x{screenHeight}")

        # Approximate coordinates for Yahoo search bar (may need adjustment)
        # Yahoo search bar is typically in the top-center area
        search_bar_x = 360  # Center horizontally
        search_bar_y = 120  # About 150 pixels from top
        
        log(f"🎯 Target search bar coordinates: ({search_bar_x}, {search_bar_y})")
        
        # Step 1: Move cursor to search bar
        current_pos = pyautogui.position()
        log(f"📍 Moving from ({current_pos.x}, {current_pos.y}) to search bar at ({search_bar_x}, {search_bar_y})")
        pyautogui.moveTo(search_bar_x, search_bar_y, duration=1.0)
        new_pos = pyautogui.position()
        log(f"✅ Moved to search bar at ({new_pos.x}, {new_pos.y})")
        
        # Step 2: Click on search bar
        log("🖱️  Clicking on search bar...")
        pyautogui.click()
        time.sleep(0.5)
        log("✅ Clicked on search bar")
        
        # Step 3: Select all text (Ctrl+A)
        log("⌨️  Selecting all text with Ctrl+A...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        log("✅ Selected all text")
        
        # Step 4: Delete content (Backspace or Delete)
        log("🗑️  Deleting selected content...")
        pyautogui.press('backspace')
        time.sleep(0.5)
        log("✅ Deleted content")
        
        # Step 5: Type "I'm working."
        log("⌨️  Typing 'I'm working.'...")
        pyautogui.typewrite("I'm working.")
        time.sleep(0.5)
        log("✅ Typed 'I'm working.'")
        
        # Final confirmation
        log("🎉 Yahoo search bar automation completed successfully!")
        log("📝 The search bar should now contain: 'I'm working.'")

    except Exception as e:
        log(f"❌ An error occurred during automation: {e}")
        import traceback
        traceback.print_exc()

def log_cursor_position():
    """Log the current cursor position."""
    try:
        current_pos = pyautogui.position()
        log(f"📍 Cursor position: ({current_pos.x}, {current_pos.y})")
    except Exception as e:
        log(f"❌ Error getting cursor position: {e}")

def main():
    """
    Main loop for the long-running service.
    Waits for a trigger file to appear, then runs the automation.
    Also logs cursor position periodically.
    """
    log("🚀 PyAutoGUI service started successfully!")
    log("👀 Monitoring for trigger file: /workspace/trigger.txt")
    log("📍 Cursor position logging enabled (every 5 seconds)")
    trigger_file = Path("/workspace/trigger.txt")
    trigger_count = 0
    last_cursor_log = time.time()

    while True:
        current_time = time.time()
        
        # Log cursor position every 5 seconds
        if current_time - last_cursor_log >= 5:
            log_cursor_position()
            last_cursor_log = current_time
        
        if trigger_file.exists():
            trigger_count += 1
            log(f"🎯 TRIGGER #{trigger_count} DETECTED! Starting automation...")
            log(f"📁 Trigger file: {trigger_file} (exists: {trigger_file.exists()})")
            
            # Log cursor position before starting automation
            log("📍 Logging cursor position before automation:")
            log_cursor_position()
            
            # Perform the automation
            do_automation_task()

            # Clean up the trigger file so it doesn't run again immediately
            try:
                trigger_file.unlink()
                log(f"🗑️  Trigger file removed. Waiting for next trigger...")
            except FileNotFoundError:
                log("⚠️  Trigger file was already removed.")
        
        # Wait for a short period before checking again
        time.sleep(5)

if __name__ == "__main__":
    main() 