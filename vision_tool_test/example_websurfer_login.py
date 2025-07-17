#!/usr/bin/env python3
"""
Example: WebSurfer Login Integration with Vision Assistant

This example demonstrates how to use WebSurfer for intelligent login automation
while keeping the vision assistant running for precise form filling tasks.

Setup:
1. Set environment variables:
   export OPENAI_API_KEY="your-openai-api-key"
   export EMR_USERNAME="your-emr-username"
   export EMR_PASSWORD="your-emr-password"

2. Run the example:
   python example_websurfer_login.py

What it does:
- Starts VNC Docker container with browser
- Initializes WebSurfer for AI-driven navigation
- Performs login to officeally.com
- Keeps vision assistant running for WebSocket connections
- Provides VNC access for visual monitoring
"""

import asyncio
import os

# Example usage
if __name__ == "__main__":
    print("🚀 WebSurfer + Vision Assistant Integration Example")
    print("="*60)
    
    # Check for required environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    username = os.getenv("EMR_USERNAME")
    password = os.getenv("EMR_PASSWORD")
    
    if not api_key:
        print("❌ Missing OPENAI_API_KEY environment variable")
        print("Set it with: export OPENAI_API_KEY='your-openai-api-key'")
        exit(1)
    
    if not username or not password:
        print("⚠️  EMR credentials not set, will run in demo mode")
        print("For full login demo, set:")
        print("export EMR_USERNAME='your-username'")
        print("export EMR_PASSWORD='your-password'")
    
    print("\n📋 Configuration:")
    print(f"OpenAI API Key: {'✅ Set' if api_key else '❌ Missing'}")
    print(f"EMR Username: {username or 'Not set (demo mode)'}")
    print(f"EMR Password: {'***' if password else 'Not set (demo mode)'}")
    
    print("\n🏁 Starting main application...")
    
    # Import and run the main function
    from src.main import main
    asyncio.run(main()) 