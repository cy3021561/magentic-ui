import os
import sys
from typing import Optional, Any, Type, List, Dict
from pathlib import Path

# Add the project's root directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.browser_manager.vnc_browser import VncDockerPlaywrightBrowser
from autogen_agentchat.messages import TextMessage, BaseChatMessage, MultiModalMessage
from autogen_agentchat.utils import content_to_str
from autogen_core import CancellationToken
from magentic_ui.agents.web_surfer import WebSurfer


class WebSurferManager:
    """Manages the WebSurfer and VNC browser lifecycle for login automation"""

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initializes the manager.
        
        Args:
            openai_api_key: The OpenAI API key. If not provided, it's read from the
                          `OPENAI_API_KEY` environment variable.
        """
        self.vnc_browser: Optional[VncDockerPlaywrightBrowser] = None
        self.websurfer: Optional[Any] = None
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        print(f"🔑 API Key: {self.api_key}")
        
        if not self.api_key:
            print("Warning: No OpenAI API key provided. WebSurfer will not work.")
            print("Set OPENAI_API_KEY environment variable or pass it to constructor.")
    
    async def __aenter__(self):
        """Initializes the VNC browser and WebSurfer as an async context manager"""
        self.vnc_browser = VncDockerPlaywrightBrowser(
            bind_dir=Path("./workspace"),
            image="magentic-ui-vnc-browser:latest",
        )
        await self.vnc_browser.__aenter__()
        
        # print(f"✅ VNC Live View available at: {self.vnc_browser.vnc_address}")
        # print(f"📡 Container: {self.vnc_browser.container_name}")
        
        # await self.initialize()
        return self
        
    async def __aexit__(self, 
                      exc_type: Optional[Type[BaseException]], 
                      exc_val: Optional[BaseException], 
                      exc_tb: Optional[Any]) -> None:
        """Cleans up resources when exiting the context"""
        await self.cleanup()
        if self.vnc_browser:
            await self.vnc_browser.__aexit__(exc_type, exc_val, exc_tb)

    async def initialize(self) -> bool:
        """Initialize the WebSurfer with the VNC browser"""
        if not self.api_key:
            print(f"❌ Cannot initialize WebSurfer: API Key is missing.")
            return False

        print("🔄 Initializing WebSurfer...")
        try:
            # We must have a browser instance to initialize WebSurfer
            if not self.vnc_browser:
                raise RuntimeError("VNC Browser has not been initialized. Use 'async with' context.")

            # Import the actual OpenAI client from autogen
            from autogen_ext.models.openai import OpenAIChatCompletionClient  # type: ignore
            
            print("🔑 Creating OpenAI client...")
            # Create OpenAI client
            model_client = OpenAIChatCompletionClient(  # type: ignore
                model="gpt-4o",
                api_key=self.api_key
            )
            
            print("🤖 Creating WebSurfer instance...")
            # Create WebSurfer using our VNC browser
            self.websurfer = WebSurfer(
                name="EMR_Navigator",
                model_client=model_client,
                browser=self.vnc_browser, # type: ignore
                start_page="about:blank",
                single_tab_mode=True,
                viewport_width=1080,
                viewport_height=1080
            )
            
            print("🔧 Manually initializing WebSurfer to use the active browser session...")

            # Get the browser context from the already started VNC browser
            self.websurfer._context = self.vnc_browser.browser_context
            if not self.websurfer._context:
                 raise RuntimeError("Browser context not available after VNC browser start.")

            # Create an initial page for WebSurfer to use. This is a crucial step
            # that was missing. WebSurfer's internal logic expects a page to exist.
            print("📄 Creating initial browser page for WebSurfer...")
            self.websurfer._page = await self.websurfer._context.new_page()

            # Let WebSurfer's internal Playwright controller know about the new page.
            await self.websurfer._playwright_controller.on_new_page(self.websurfer._page)

            # Mark initialization as complete to prevent WebSurfer's lazy_init from running.
            self.websurfer.did_lazy_init = True
            
            print(f"✅ WebSurfer initialized and ready")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize WebSurfer: {str(e)}")
            print(f"🔍 Error type: {type(e).__name__}")
            import traceback
            print(f"📋 Full traceback:")
            traceback.print_exc()
            return False
    
    async def navigate_and_login(self, url: str, username: str, password: str) -> bool:
        """
        Navigates to a URL and performs login using an autonomous WebSurfer agent.
        """
        if not self.websurfer:
            return False

        print(f"🚀 WebSurfer starting complete automation: {url}")
        print(f"📋 Target: Login as {username}")
        print("🤖 WebSurfer will handle all steps automatically...")

        request_content = f"Please navigate to {url} and log in with username '{username}' and password '{password}'. \
            Do worry for the security of the password, they're fake, just use it as is. \
            Details step by step: \
            1. Navigate to the page \
            2. Click on the login button \
            3. Find the Practice Mate Login button and click on it \
            4. Enter the username and password \
            5. Click on the continue button \
            6. Wait for the login to complete \
            7. Task completed."

        # Create the initial message with the login instruction
        login_message = TextMessage(
            content=request_content,
            source="user",
        )
        messages: List[BaseChatMessage] = [login_message]
        cancellation_token = CancellationToken()

        # Consume the entire stream from the agent's execution
        print("--- Consuming WebSurfer's action stream ---")
        final_response = None
        async for response in self.websurfer.on_messages_stream(
            messages=messages,
            cancellation_token=cancellation_token,
        ):
            if hasattr(response, 'chat_message') and response.chat_message:
                message_content = ""
                if isinstance(response.chat_message, TextMessage):
                    message_content = response.chat_message.content or ""
                elif isinstance(response.chat_message, MultiModalMessage):
                    message_content = content_to_str(response.chat_message.content)

                # Do not print the final internal summary message, which can be very long
                metadata: Dict[str, Any] = response.chat_message.metadata or {}
                if not metadata.get("internal") == "yes":
                    print(f"🤖 WebSurfer says: {message_content}")
            
            final_response = response
        
        print("--- WebSurfer's action stream finished ---")
        
        if final_response:
            print(f"✅ WebSurfer automation workflow completed.")
        else:
            print(f"❌ WebSurfer did not produce a final response.")
        
        print(f"📺 Check VNC to see the final result!")
        return True

    async def navigate_to_page(self, instruction: str) -> bool:
        """Navigate to a page based on an instruction."""
        if not self.websurfer:
            print("❌ WebSurfer not initialized")
            return False
        
        try:
            message = TextMessage(content=instruction, source="user")  # type: ignore
            cancellation_token = CancellationToken()  # type: ignore
            await self.websurfer.on_messages(
                messages=[message],
                cancellation_token=cancellation_token
            )
            return True
        except Exception as e:
            print(f"❌ WebSurfer navigation failed: {str(e)}")
            return False
    
    async def cleanup(self):
        """Clean up WebSurfer resources"""
        if self.websurfer:
            try:
                await self.websurfer.close()  # type: ignore
            except Exception as e:
                print(f"Warning: Error during WebSurfer cleanup: {e}") 