# Image Cropping Functionality

This extension adds image cropping capabilities to the existing VNC browser setup. You can crop screen sections while navigating through webpages via VNC.

## Setup

1. **Build the Docker image** (if you haven't already):

   ```bash
   docker build -t magentic-ui-vnc-browser:latest ./docker_assets/browser
   ```

2. **Run the cropping test**:
   ```bash
   python test_cropping.py
   ```

## How It Works

The cropping service runs inside the Docker container alongside the existing PyAutoGUI service. It monitors for triggers and captures cropped screenshots at the current mouse position.

### Workflow

1. **Start Cropping Mode**: Create a trigger file from the host machine:

   ```bash
   docker exec <container_name> touch /workspace/crop_trigger.txt
   ```

2. **Navigate and Crop**: Once cropping mode is activated:
   - Open the VNC URL in your browser
   - Navigate to the area you want to crop
   - Press `c` to crop at current mouse position
   - Press `q` to exit cropping mode

### Image Output

Cropped images are automatically saved to the `workspace/` directory on your host machine with timestamped filenames:

- Format: `cropped_screenshot_<timestamp>.png`
- Size: 300x150 pixels (configurable in `cropping_script.py`)
- Location: `vision_tool_test/workspace/`

## Configuration

You can modify the cropping parameters in `docker_assets/browser/cropping_script.py`:

```python
# Parameters for the cropping region
CROP_WIDTH = 300   # Width of the cropping region
CROP_HEIGHT = 150  # Height of the cropping region
```

## Usage Example

1. Start the test script:

   ```bash
   python test_cropping.py
   ```

2. Open the VNC URL in your browser

3. Navigate to a webpage (e.g., Google.com)

4. Start cropping mode:

   ```bash
   docker exec <container_name> touch /workspace/crop_trigger.txt
   ```

5. Navigate and crop:

   - Press 'c' in the VNC window to crop at current mouse position
   - Press 'q' to exit cropping mode

6. Check the `workspace/` directory for new cropped images

## Troubleshooting

- **No images created**: Check the container logs for X11 authentication issues
- **Keyboard not working**: Use the file trigger method instead
- **Wrong crop area**: Adjust the mouse position in VNC before triggering

## Files Modified

- `docker_assets/browser/Dockerfile` - Added Pillow and keyboard dependencies
- `docker_assets/browser/supervisord.conf` - Added cropping service
- `docker_assets/browser/cropping_script.py` - New cropping service script
- `test_cropping.py` - New test script for cropping functionality
