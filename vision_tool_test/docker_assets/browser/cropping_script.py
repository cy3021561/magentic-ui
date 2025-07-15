import pyautogui
import time
from PIL import ImageGrab
import os
from datetime import datetime
from pynput import keyboard as pynput_keyboard

# Docker environment setup
os.environ['DISPLAY'] = ':99'
os.environ['XAUTHORITY'] = '/root/.Xauthority'

# Parameters for the cropping region
CROP_WIDTH = 300  # Width of the cropping region
CROP_HEIGHT = 150  # Height of the cropping region

CROP_AT_FILE = "/workspace/crop_at.txt"


def log(message: str) -> None:
    """Helper function to log messages with timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[CROPPING] [{timestamp}] {message}", flush=True)

def capture_screenshot(center_x: int, center_y: int, width: int, height: int):
    """Capture a cropped screenshot at the specified coordinates."""
    try:
        # Get screen size
        screen_width, screen_height = pyautogui.size()
        log(f"Screen dimensions: {screen_width}x{screen_height}")

        # Get the scale factor between the actual screen size and the image size captured by ImageGrab
        screenshot = ImageGrab.grab()
        img_width, img_height = screenshot.size
        scale_x = img_width / screen_width
        scale_y = img_height / screen_height

        # Scale the center coordinates
        scaled_center_x = int(center_x * scale_x)
        scaled_center_y = int(center_y * scale_y)

        # Calculate the bounding box of the region to crop
        left = max(0, scaled_center_x - int(width * scale_x) // 2)
        top = max(0, scaled_center_y - int(height * scale_y) // 2)
        right = min(img_width, scaled_center_x + int(width * scale_x) // 2)
        bottom = min(img_height, scaled_center_y + int(height * scale_y) // 2)

        # Crop the screenshot to the desired region
        cropped_image = screenshot.crop((left, top, right, bottom))

        # Save the cropped image to workspace directory
        timestamp = int(time.time())
        filename = f"cropped_screenshot_{timestamp}.png"
        filepath = f"/workspace/{filename}"
        cropped_image.save(filepath)
        log(f"Saved cropped screenshot as {filename}")
        return filepath
    except Exception as e:
        log(f"Error capturing screenshot: {e}")
        return None

def main():
    """Main function that monitors for triggers and handles cropping."""
    log("Cropping service started successfully!")
    log(f"DISPLAY: {os.environ.get('DISPLAY', 'NOT SET')}")
    log(f"XAUTHORITY: {os.environ.get('XAUTHORITY', 'NOT SET')}")
    log("\nUSAGE INSTRUCTIONS:")
    log("1. To start cropping mode, create the trigger file: /workspace/crop_trigger.txt")
    log("2. In cropping mode:")
    log("   - Press 'c' in the VNC window to crop at the current mouse position")
    log("   - Press 'q' to exit cropping mode")
    log("   - OR, to crop at a specific coordinate, create /workspace/crop_at.txt with contents: x,y (e.g., 400,300)")
    log("     Example: echo '400,300' > /workspace/crop_at.txt")
    log("   - Cropped images will be saved to /workspace/cropped_screenshot_<timestamp>.png\n")

    # Global variables for keyboard handling
    crop_mode_active = False
    crop_count = 0

    def on_key_press(key):
        nonlocal crop_mode_active, crop_count
        if not crop_mode_active:
            return
        try:
            if hasattr(key, 'char') and key.char == 'c':
                crop_count += 1
                log(f"CROP #{crop_count} - Capturing screenshot at mouse position...")
                x, y = pyautogui.position()
                log(f"Mouse position: ({x}, {y})")
                result = capture_screenshot(int(x), int(y), CROP_WIDTH, CROP_HEIGHT)
                if result:
                    log(f"✅ Cropping completed successfully: {result}")
                else:
                    log("❌ Cropping failed")
            elif hasattr(key, 'char') and key.char == 'q':
                log("Exiting cropping mode...")
                crop_mode_active = False
                return False  # Stop listener
        except Exception as e:
            log(f"Error handling key press: {e}")

    # Start keyboard listener
    listener = pynput_keyboard.Listener(on_press=on_key_press)
    listener.start()

    while True:
        try:
            # Check for trigger file to start cropping mode
            if os.path.exists("/workspace/crop_trigger.txt"):
                log("🎯 CROPPING MODE ACTIVATED!")
                log("Now you can press 'c' in VNC window to crop at current mouse position")
                log("Press 'q' to quit cropping mode")
                log("Or create /workspace/crop_at.txt with coordinates to crop at a specific location.")
                try:
                    os.remove("/workspace/crop_trigger.txt")
                    log("Trigger file removed")
                except FileNotFoundError:
                    log("Trigger file was already removed")
                crop_mode_active = True
                crop_count = 0
                log("Cropping mode active! Press 'c' to crop at current mouse position, 'q' to quit, or use crop_at.txt for coordinate cropping.")
                while crop_mode_active:
                    # Check for coordinate cropping file
                    if os.path.exists(CROP_AT_FILE):
                        try:
                            with open(CROP_AT_FILE, 'r') as f:
                                content = f.read().strip()
                            if ',' in content:
                                x_str, y_str = content.split(',', 1)
                                x = int(float(x_str.strip()))
                                y = int(float(y_str.strip()))
                                crop_count += 1
                                log(f"CROP #{crop_count} - Capturing screenshot at coordinates ({x}, {y})...")
                                result = capture_screenshot(x, y, CROP_WIDTH, CROP_HEIGHT)
                                if result:
                                    log(f"✅ Cropping completed successfully: {result}")
                                else:
                                    log("❌ Cropping failed")
                            else:
                                log(f"Invalid format in {CROP_AT_FILE}. Expected: x,y")
                        except Exception as e:
                            log(f"Error reading {CROP_AT_FILE}: {e}")
                        finally:
                            try:
                                os.remove(CROP_AT_FILE)
                                log(f"{CROP_AT_FILE} removed")
                            except Exception:
                                pass
                    time.sleep(0.1)
                log("Back to waiting for trigger file...")
            time.sleep(1)
        except Exception as e:
            log(f"Error in main loop: {e}")
            time.sleep(5)  # Wait longer on error

if __name__ == "__main__":
    main() 