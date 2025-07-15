import asyncio
import concurrent.futures
import json
from typing import Dict, Any
from jsonschema import validate, ValidationError

from ..core import BaseTool
from ..utils import TemplatePathManager
from ..constants import SCHEMA_PATH, TOOL_TASKS
from vision_assistant.emr_assistant import EMRAssistant

class VisionTool(BaseTool):
    """Vision tool implementation for EMR processing."""
    
    def __init__(self, emr_system: str = "office_ally"):
        super().__init__()
        self.emr_system = emr_system
        self.assistant = None
        self.cur_patient_name = ""
        self.template_manager = TemplatePathManager()
        self._initialize_assistant()
        # Add a flag to track if we're currently processing messages
        self.is_processing = False
    
    def _initialize_assistant(self) -> None:
        """Initialize the EMR assistant with proper templates."""
        default_path = self.template_manager.get_default_path()
        if not default_path:
            raise ValueError("No template directory found")
        
        emr_path = self.template_manager.validate_emr_path(default_path, self.emr_system)
        self.assistant = EMRAssistant(template_base_path=emr_path)
    
    def is_still_processing(self) -> bool:
        """Check if the tool is still processing messages."""
        return self.is_processing or not self.queue.empty()

    async def send_response(self, websocket, to_user: str, message: dict) -> None:
        """Send formatted and validated response through websocket."""
        response = {
            'to_user': to_user,
            'patient_name': self.cur_patient_name,
            'executed_action': message["message"],
            'type': message["status"]
        }
        
        try:
            with open(SCHEMA_PATH, "r") as f:
                response_schema = json.load(f)
                await websocket.ping()
                # validate(instance=response, schema=response_schema)
                await websocket.send(json.dumps(response))
        except ValidationError as e:
            self.logger.error(f"Response validation failed: {e.message}")
        except Exception as e:
            self.logger.error(f"Error sending response: {e}")
    
    def _execute_emr_task(self, task_name: str, message_queue: asyncio.Queue) -> None:
        """Execute a single EMR task and put status updates in the queue."""
        try:
            for status in self.assistant.run(task_name):
                message_queue.put_nowait(status)
        except Exception as e:
            self.logger.error(f"Error executing task {task_name}: {e}")
            message_queue.put_nowait({
                "message": f"Task error: {str(e)}", 
                "status": "critical"
            })
    
    async def process_message(self, message: Dict[str, Any], websocket) -> None:
        """Process a single message through the EMR system."""
        from_user = message.get('from_user')
        client_data = message.get('data')
        
        if not all([from_user, client_data]):
            await self.send_response(
                websocket,
                None,
                {"message": "Invalid message format", "status": "critical"}
            )
            return
        
        # Set processing flag
        self.is_processing = True
        
        # Handle either single item or list of items
        data_items = client_data if isinstance(client_data, list) else [client_data]
        
        # Since the EMR task's cost is high, we want use a new thread pool.
        # Still running the tasks in parallel and avoid blocking the main thread.
        with concurrent.futures.ThreadPoolExecutor() as pool:
            for data_item in data_items:
                if self.current_task and self.current_task.cancelled():
                    break
                
                try:
                    # Update EMR system if needed
                    if emr := data_item.get('selected_emr'):
                        if emr != self.emr_system:
                            self.emr_system = emr
                            default_path = self.template_manager.get_default_path()
                            emr_path = self.template_manager.validate_emr_path(default_path, emr)
                            self.assistant.update_emr_path(emr_path)
                    
                    # Update and process EMR data
                    self.assistant.emr_data.update(data_item)
                    self.assistant.emr_data.display()
                    self.cur_patient_name = (f"{self.assistant.emr_data.person_first_name} "
                                           f"{self.assistant.emr_data.person_last_name}")
                    
                    # Execute each task for this data item
                    for task_name in TOOL_TASKS:
                        if self.current_task and self.current_task.cancelled():
                            break
                        
                        message_queue = asyncio.Queue()
                        task_future = asyncio.get_running_loop().run_in_executor(
                            pool,
                            self._execute_emr_task,
                            task_name,
                            message_queue
                        )
                        
                        # Handle status updates while task is running
                        try:
                            while not task_future.done() or not message_queue.empty():
                                if not message_queue.empty():
                                    status = await message_queue.get()
                                    print(status)
                                    await self.send_response(websocket, from_user, status)
                                    # Check if the status indicates a failure
                                    if status.get('status') == 'critical' or status.get('error'):
                                        task_future.cancel()  # Cancel the current task
                                        raise  # Break the for loop entirely
                                await asyncio.sleep(0.1)
                            
                            # Get the final result
                            result = await asyncio.wrap_future(task_future)
                            if isinstance(result, dict) and (result.get('status') == 'critical' or result.get('error')):
                                break  # Break the loop if the task failed
                        
                        except Exception as e:
                            # Handle any exceptions that might occur during task execution
                            await self.send_response(websocket, from_user, {
                                'status': 'failed',
                                'error': str(e)
                            })
                            break  # Break the loop on any exception
                
                except Exception as e:
                    await self.send_response(
                        websocket,
                        from_user,
                        {"message": f"Error: {str(e)}", "status": "critical"}
                    )
                    self.logger.error(f"Error processing data item: {e}")
                
                finally:
                    await self.send_response(
                        websocket,
                        from_user,
                        {"message": "Current tasks finished", "status": "complete"}
                    )
        
        # Check if queue is empty before sending all_done
        if self.queue.empty():
            self.is_processing = False
            await self.send_response(
                websocket,
                from_user,
                {"message": "All tasks finished", "status": "all_done"}
            )