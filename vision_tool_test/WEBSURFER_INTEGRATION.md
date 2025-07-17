# WebSurfer Integration with Vision Assistant

This integration combines the power of WebSurfer's AI-driven browser automation with your existing vision assistant for EMR automation tasks.

## 🎯 What This Gives You

- **Intelligent Login**: WebSurfer handles complex login flows, including 2FA and dynamic forms
- **Adaptive Navigation**: AI can handle changes in website layout and navigate to EMR sections
- **Precision Automation**: Your existing vision assistant provides pixel-perfect form filling
- **Visual Monitoring**: VNC access lets you watch the automation in real-time
- **Robust Error Handling**: WebSurfer can recover from unexpected UI changes

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export OPENAI_API_KEY="your-openai-api-key"
export EMR_USERNAME="your-emr-username"     # Optional
export EMR_PASSWORD="your-emr-password"     # Optional
```

### 3. Run the Example

```bash
python example_websurfer_login.py
```

### 4. Run the Main Application

```bash
python src/main.py
```

## 📋 How It Works

### System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Your Script   │───▶│ VNC Docker       │───▶│ Vision Assistant│
│                 │    │ Container        │    │ (WebSocket)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   WebSurfer     │◀───│ Playwright       │    │ EMR Automation  │
│   AI Navigator  │    │ Browser          │    │ Tasks           │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Workflow

1. **Container Startup**: VNC Docker container starts with browser, X11, and vision assistant
2. **WebSurfer Init**: AI-powered navigation system connects to the browser
3. **Login Phase**: WebSurfer intelligently handles login forms and authentication
4. **Navigation**: WebSurfer navigates to specific EMR sections as needed
5. **Precision Tasks**: Vision assistant takes over for exact form filling via WebSocket
6. **Monitoring**: VNC provides visual feedback throughout the process

## 🔧 Configuration

### WebSurfer Settings

The WebSurfer is configured in `websurfer_manager.py`:

```python
self.websurfer = WebSurfer(
    name="EMR_Navigator",
    model_client=model_client,
    browser=self.vnc_browser,
    start_page="about:blank",
    animate_actions=True,      # Visual feedback
    max_actions_per_step=10    # Actions per AI decision
)
```

### Environment Variables

| Variable         | Required | Description                        |
| ---------------- | -------- | ---------------------------------- |
| `OPENAI_API_KEY` | Yes      | OpenAI API key for WebSurfer AI    |
| `EMR_USERNAME`   | No       | EMR system username for auto-login |
| `EMR_PASSWORD`   | No       | EMR system password for auto-login |

## 🎮 Usage Examples

### Basic Login Automation

```python
from src.browser_manager.vnc_browser import VncDockerPlaywrightBrowser
from src.browser_manager.websurfer_manager import WebSurferManager

# Start browser
browser = VncDockerPlaywrightBrowser(bind_dir=workspace_dir)
async with browser as bm:
    # Initialize WebSurfer
    websurfer = WebSurferManager(bm, openai_api_key)
    await websurfer.initialize()

    # Perform login
    await websurfer.navigate_and_login(
        url="https://officeally.com",
        username="your_username",
        password="your_password"
    )
```

### Custom Navigation

```python
# Navigate to specific sections
await websurfer.navigate_to_page(
    "Navigate to the patient management section and create a new patient record"
)
```

## 🔍 Monitoring & Debugging

### VNC Access

When the system starts, you'll see:

```
✅ VNC Live View available at: http://localhost:6080/vnc.html
```

Open this URL in your browser to watch the automation in real-time.

### Container Logs

View WebSurfer and vision assistant logs:

```bash
docker logs <container_name>
```

### Debug Mode

For detailed WebSurfer debugging, modify the configuration:

```python
self.websurfer = WebSurfer(
    # ... other config ...
    debug_dir="./debug",  # Save screenshots
    to_save_screenshots=True
)
```

## 🔄 Integration with Existing Vision Assistant

The vision assistant continues running inside the container via `supervisord` and listens for WebSocket connections. After WebSurfer completes navigation tasks, you can:

1. Send tasks to the vision assistant via WebSocket
2. Use the existing EMR automation templates
3. Perform precise form filling and data entry

### Example Task Flow

1. **WebSurfer**: "Navigate to officeally.com and log in"
2. **WebSurfer**: "Go to the patient records section"
3. **Vision Assistant**: "Fill in patient form with provided data"
4. **Vision Assistant**: "Submit the form and verify success"

## 🛠 Troubleshooting

### Common Issues

1. **WebSurfer Not Available**

   - Check `OPENAI_API_KEY` is set
   - Verify dependencies are installed
   - System falls back to basic Playwright

2. **Login Fails**

   - Check credentials in environment variables
   - Website may have changed login flow
   - Use VNC to observe what WebSurfer is doing

3. **Container Issues**
   - Ensure Docker is running
   - Check port conflicts (6080, playwright port)
   - Rebuild container if needed

### Fallback Mode

If WebSurfer is unavailable, the system automatically falls back to basic Playwright navigation while keeping the vision assistant active.

## 🎯 Next Steps

1. **Test Login**: Run with your EMR credentials
2. **Custom Navigation**: Add specific navigation tasks for your EMR workflow
3. **Integrate Tasks**: Connect WebSurfer navigation with vision assistant precision tasks
4. **Monitor Performance**: Use VNC to optimize the automation flow

The integration is designed to be simple and robust - WebSurfer handles the complex navigation while your existing vision assistant continues to provide precise automation capabilities.
