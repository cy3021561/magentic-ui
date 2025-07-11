# Vision Tool Test

This project demonstrates a comprehensive browser automation system with:

- **Docker container** with VNC for visual access
- **Playwright** for programmatic browser control (loads Yahoo.com)
- **PyAutoGUI** for visual automation tasks (interacts with Yahoo search bar)
- **Live VNC view** for user interaction

## Prerequisites

1. **Docker** installed and running
2. **Python 3.8+** with required packages
3. **Docker image** built (see setup instructions)

## Setup

1. **Build the Docker image**:

   ```bash
   docker build -t magentic-ui-vnc-browser:latest ./docker_assets/browser
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Run the Main Application

Start the VNC-enabled browser with PyAutoGUI automation:

```bash
python src/main.py
```

### Manual PyAutoGUI Trigger

Once the container is running, you can trigger PyAutoGUI automation manually:

```bash
docker exec <container_name> touch /workspace/trigger.txt
```

The automation will:

1. Move the cursor to the Yahoo search bar
2. Click on the search bar
3. Select all existing text (Ctrl+A)
4. Delete the content
5. Type "I'm working."

## Architecture

- **VncDockerPlaywrightBrowser**: Manages the Docker container with VNC and Playwright
- **Supervisord**: Orchestrates all processes (Xvfb, Openbox, x11vnc, noVNC, Playwright, PyAutoGUI)
- **X11 Setup**: Configures X11 authentication and desktop environment
- **PyAutoGUI**: Performs visual automation tasks
- **noVNC**: Provides web-based VNC access

## Troubleshooting

### X11 Authentication Issues

If you see X11 authentication errors:

1. Check that the Docker image was built correctly
2. Ensure all processes have proper environment variables
3. Wait for the X11 setup to complete (check logs)

### VNC Connection Issues

1. Verify the VNC address is displayed correctly
2. Check that ports are accessible
3. Ensure noVNC is running on the expected port

### PyAutoGUI Not Working

1. Check that the `.Xauthority` file exists
2. Verify X11 environment variables are set
3. Look for timing issues in the logs

## File Structure

```
vision_tool_test/
├── docker_assets/browser/     # Docker container files
├── src/                       # Python source code
│   └── browser_manager/       # Browser management classes
├── workspace/                 # Shared workspace directory
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```
