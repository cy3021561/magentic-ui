#!/usr/bin/env python3
import os
import sys
import time

# Set environment variables
os.environ['DISPLAY'] = ':99'
os.environ['XAUTHORITY'] = '/root/.Xauthority'

print("=== X11 Environment Test ===")
print(f"DISPLAY: {os.environ.get('DISPLAY', 'NOT SET')}")
print(f"XAUTHORITY: {os.environ.get('XAUTHORITY', 'NOT SET')}")

try:
    import pyautogui
    print("✅ PyAutoGUI imported successfully")
    
    # Test screen info
    screen_width, screen_height = pyautogui.size()
    print(f"✅ Screen size: {screen_width}x{screen_height}")
    
    # Test mouse position
    x, y = pyautogui.position()
    print(f"✅ Current mouse position: ({x}, {y})")
    
    # Test a simple mouse movement
    print("Testing mouse movement...")
    pyautogui.moveTo(100, 100, duration=1)
    time.sleep(0.5)
    pyautogui.moveTo(200, 200, duration=1)
    print("✅ Mouse movement test successful")
    
except ImportError as e:
    print(f"❌ Failed to import PyAutoGUI: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ PyAutoGUI test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("✅ All X11 tests passed!") 