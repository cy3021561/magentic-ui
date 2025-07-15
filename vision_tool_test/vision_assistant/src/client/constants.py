from pathlib import Path

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Schema path for response validation
SCHEMA_PATH = BASE_DIR / "schema" / "response_schema.json"

# Tool tasks constants
# TOOL_TASKS = ["add_new_patient", "add_new_visit"]
TOOL_TASKS = ["add_new_patient"]

# WebSocket configuration
DEFAULT_PORT = 5050
WEBSOCKET_PATH = "/connect-tool"
NGROK_URL="https://7b56-98-154-38-6.ngrok-free.app"

# Verify schema file exists
if not SCHEMA_PATH.exists():
    raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")