import os
import json
import platform
import time, asyncio
import logging
import numpy as np
import cv2
from typing import List, Optional, Dict, Any
from vision_assistant.computer.control import Control
from vision_assistant.template_alignment.template_alignment import TemplateAligner
from vision_assistant.data.emr_data import EMRData


class EMRError(Exception):
    """Base exception class for EMR Assistant errors"""
    pass

class ConfigurationError(EMRError):
    """Raised when there's an error in configuration"""
    pass

class TemplateError(EMRError):
    """Raised when there's an error with templates"""
    pass

class ActionError(EMRError):
    """Raised when there's an error executing an action"""
    pass

class EMRAssistant:
    SCROLL_VALUE = 5
    BACK_TO_TOP_SCROLLING_AMOUNT = 3500
    SCREEN_WIDTH = 1680
    SCREEN_HEIGHT = 1050

    def __init__(self, page="general", input_data=None, template_base_path=None):
        """
        Initialize the assistant with page type and optional custom template directories.
        """
        try:
            self.operating_system = platform.system()
            self.current_emr = None
            self.page = page
            self.template_base_path = template_base_path
            self.cur_page_screenshots = []
            self.config_path = None
            self.emr_data = EMRData()
            self.modifier_key = self._initialize_modifier_key()
            self.scroll_total_clicks_current_page = None
            self.scroll_click_now = 0
            self.control = Control(modifier_key=self.modifier_key)
            self.aligner = TemplateAligner()
            self.page_elements_coors = {}
            self.config_data = None
            self.general_img_dir = None
            self.general_config_dir = None
            self.template_img_dir = None
            self.template_config_dir = None
            
            if input_data is not None:
                self.emr_data.update(input_data)
            
            if template_base_path:
                self.update_emr_path(template_base_path)
            
        except Exception as e:
            raise e
    
    def _check_os_resolution(self):
        success = False
        try:
            self.aligner.get_screen_dimensions()
            screen_w, screen_h = self.aligner.screen_width, self.aligner.screen_height
            if screen_w == self.SCREEN_WIDTH and screen_h == self.SCREEN_HEIGHT:
                success = True
    
        except Exception as e:
            raise EMRError(f"EMR assistant initailize failed. {str(e)}")
        
        if not success:
            raise EMRError(f"Wrong screen resolution, please change to 1920 X 1080 and reopen the tool.")
             
    def _initialize_modifier_key(self):
        """
        Check os version the determine modifier key
        """
        if self.operating_system.lower() == "darwin":
            return "command"
        else:
            return "ctrl"

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Loads the JSON configuration file with error handling.
        """
        try:
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Configuration file not found at {config_path}")
            
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Normalize path separators for cross-platform compatibility
            config_data = self._normalize_path_separators(config_data)
            
            return config_data
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in {config_path}: {str(e)}")
        except Exception as e:
            raise ConfigurationError(f"Error loading config from {config_path}: {str(e)}")
    
    def _normalize_path_separators(self, data):
        """
        Recursively normalize path separators in configuration data for cross-platform compatibility.
        """
        if isinstance(data, dict):
            normalized = {}
            for key, value in data.items():
                if key in ["images", "configs"] and isinstance(value, str):
                    # Replace Windows backslashes with forward slashes for cross-platform compatibility
                    normalized[key] = value.replace("\\", "/")
                else:
                    normalized[key] = self._normalize_path_separators(value)
            return normalized
        elif isinstance(data, list):
            return [self._normalize_path_separators(item) for item in data]
        else:
            return data
    
    def save_debug_screenshots(self, debug_dir="debug_screenshots"):
        """
        Save the current page screenshots to disk for debugging purposes.
        """
        try:
            # Create debug directory if it doesn't exist
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            # Generate timestamp for unique folder name
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            session_dir = os.path.join(debug_dir, f"scrolling_session_{timestamp}")
            os.makedirs(session_dir, exist_ok=True)
            
            # Save each screenshot with scroll information
            for i, (screenshot, scroll_amount) in enumerate(self.cur_page_screenshots):
                if screenshot is not None:
                    filename = f"screenshot_{i:03d}_scroll_{scroll_amount}.png"
                    filepath = os.path.join(session_dir, filename)
                    cv2.imwrite(filepath, screenshot)
            
            # Save metadata
            metadata = {
                "total_screenshots": len(self.cur_page_screenshots),
                "scroll_amounts": [scroll for _, scroll in self.cur_page_screenshots],
                "total_scroll": self.scroll_total_clicks_current_page,
                "page": self.page,
                "timestamp": timestamp
            }
            
            metadata_file = os.path.join(session_dir, "metadata.json")
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Debug screenshots saved to: {session_dir}")
            print(f"Total screenshots saved: {len(self.cur_page_screenshots)}")
            
        except Exception as e:
            print(f"Error saving debug screenshots: {str(e)}")

    def _handle_array_loop(self, actions, skip_in_last_loop, array_values):
        """
        Handle iteration over simple arrays
        """
        try:
            values_length = len(array_values)
            actions_length = len(actions)
            for i, value in enumerate(array_values):
                for j, step in enumerate(actions):
                    # Skip redundent actions for the last loop
                    if i + 1 == values_length and (actions_length - skip_in_last_loop) == j:
                        break
                    action_name, action_params = step
                    # Set text directly for keyboard_write actions
                    if action_name == "keyboard_write":
                        action_params = action_params.copy()  # Create a copy to avoid modifying original
                        action_params["text"] = value
                    self.execute_action(action_name, action_params, value)
        except Exception as e:
            raise ActionError(f"Array loop failed: {str(e)}")

    def _handle_tuple_array_loop(self, actions, skip_in_last_loop, tuple_array):
        """
        Handle iteration over arrays of tuples
        """
        try:
            values_length = len(tuple_array)
            actions_length = len(actions)
            for i, tuple_value in enumerate(tuple_array):
                for j, step in enumerate(actions):
                    # Skip redundent actions for the last loop
                    if i + 1 == values_length and (actions_length - skip_in_last_loop) == j:
                        break
                    action_name, action_params = step
                    # For keyboard_write, use tuple_index to get the right value
                    if action_name == "keyboard_write":
                        action_params = action_params.copy()  # Create a copy to avoid modifying original
                        index = action_params.get("tuple_index", 0)
                        action_params["text"] = tuple_value[index]
                    self.execute_action(action_name, action_params, tuple_value)
        except Exception as e:
            raise ActionError(f"Tuple array loop failed: {str(e)}")

    def update_emr_path(self, emr_path:str):
        try:
            self.page = "general"
            self.template_base_path = emr_path
            self.config_path = os.path.join(self.template_base_path, "general", "configs", "config.json")
            self.config_data = self._load_config(self.config_path)
            self.general_img_dir = os.path.join(self.template_base_path, "general", "images")
            self.general_config_dir = os.path.join(self.template_base_path, "general", "configs")
            self.template_img_dir, self.template_config_dir = self.set_template_dir_from_config(self.config_data)

        except FileNotFoundError as e:
            raise ConfigurationError(f"Configuration file not found: {str(e)}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration: {str(e)}")
        except Exception as e:
            raise ConfigurationError(f"Configuration error: {str(e)}")
    
    def to_normal_scale(self):
        success = False
        try:
            if self.get_coordinates(column_name="homepage", img_dir=self.general_img_dir):
                self.control.mouse_move(self.aligner.current_x, self.aligner.current_y)
                self.control.mouse_click()
                self.control.mouse_move(self.aligner.screen_width // 2, self.aligner.screen_height // 2)
                self.control.keyboard_hotkey([self.modifier_key, "0"])
                success = True
        except Exception as e:
            raise EMRError(f"Failed to zoom 100% scale in the browser. {str(e)}")
        
        if not success:
            raise EMRError(f"Failed to find the homepage button.")

    def back_to_top(self):
        """
        Back to top of the page
        """
        self.control.mouse_move(self.aligner.screen_width // 2, self.aligner.screen_height // 2)
        self.control.mouse_scroll(self.BACK_TO_TOP_SCROLLING_AMOUNT)
        self.scroll_click_now = 0

    def set_template_dir_from_config(self, config_data):
        """
        Initializes template directories from JSON config.
        """
        try:
            page_dirs = config_data["pages"]

            if self.page not in page_dirs:
                raise ValueError(f"Invalid page type: {self.page}")
            
            page_info = page_dirs[self.page]
            img_dir = os.path.join(self.template_base_path, page_info["images"])
            config_dir = os.path.join(self.template_base_path, page_info["configs"])

            return img_dir, config_dir
        except Exception as e:
            raise ConfigurationError(f"Error setting template directory: {str(e)}")
    
    def get_all_fields_name(self):
        """
        Returns a list of all PNG file names in the specified folder.
        """
        try:
            folder_path = self.template_img_dir
                
            if not os.path.exists(folder_path):
                raise FileNotFoundError(f"Folder not found: {folder_path}")
            
            # Get all files in the folder and filter for .png extension
            png_names = [
                os.path.splitext(file)[0]  # splitext splits filename and extension
                for file in os.listdir(folder_path)
                if file.lower().endswith('.png')
            ]
            
            return png_names
        except Exception as e:
            raise TemplateError(f"Error getting field names: {str(e)}")

    def get_scrolling_parameters(self, threshold=0.95):
        """
        Try to reach the end of the page
        """
        def compare_two_imgs(img1, img2):
            """
            Compare two screenshots and return a similarity score between 0 and 1.
            
            Args:
                img1 (numpy.ndarray): First image array
                img2 (numpy.ndarray): Second image array
                
            Returns:
                float: Similarity score between 0 and 1
            """
            if img1 is None or img2 is None:
                return 0.0
            
            if img1.shape != img2.shape:
                return 0.0
            
            # Convert to grayscale if images are in color
            if len(img1.shape) == 3:
                img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
                img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            else:
                img1_gray = img1
                img2_gray = img2
            
            # Calculate pixel-wise difference
            diff = np.abs(img1_gray.astype(float) - img2_gray.astype(float))
            mse = np.mean(diff ** 2)
            normalized_mse = mse / (255.0 ** 2)
            
            # Calculate percentage of similar pixels
            similar_pixels_ratio = np.sum(diff < 10) / diff.size
            
            # Calculate histogram similarity
            hist1 = cv2.calcHist([img1_gray], [0], None, [256], [0, 256])
            hist2 = cv2.calcHist([img2_gray], [0], None, [256], [0, 256])
            hist_similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            
            # Template matching score
            result = cv2.matchTemplate(img1_gray, img2_gray, cv2.TM_CCOEFF_NORMED)
            template_match_score = np.max(result)
            
            # Weighted combination of metrics
            final_score = (
                0.35 * similar_pixels_ratio +
                0.35 * template_match_score +
                0.2 * max(0, hist_similarity) +
                0.1 * (1 - normalized_mse)
            )
            
            return final_score
        
        try:
            # Back to top
            self.back_to_top()

            # Reset screenshot candidates
            self.cur_page_screenshots = []
            screenshot_now = self.aligner.get_screenshot()
            screenshot_pre = None
            self.cur_page_screenshots.append((screenshot_now, 0)) # (screenshot image, scrolling amount)

            # Start reaching the end at the page
            total_scroll = 0
            while not compare_two_imgs(screenshot_now, screenshot_pre) > threshold:
                self.control.mouse_scroll(-self.SCROLL_VALUE)
                screenshot_pre = screenshot_now
                screenshot_now = self.aligner.get_screenshot()
                total_scroll += self.SCROLL_VALUE
                logging.info(f"Scrolling: {total_scroll} with value: {self.SCROLL_VALUE}")
                self.cur_page_screenshots.append((screenshot_now, total_scroll))
                time.sleep(0.5)
            
            self.scroll_total_clicks_current_page = total_scroll
            # for nps in self.cur_page_screenshots:
            #     self.aligner._show_image(nps[0])
            # exit()
            # Back to top
            self.control.mouse_scroll(self.scroll_total_clicks_current_page)
            
            # Save debug screenshots
            # self.save_debug_screenshots()
            
        except Exception as e:
            raise ActionError(f"Error getting scrolling parameters: {str(e)}")
    
    def initialize_task(self, task_name):
        """
        Navigate to the initial page of the task
        """
        try:
            if task_name not in self.config_data["task_route"]:
                raise ValueError(f"Invalid task: {task_name}")
            route_items = self.config_data["task_route"][task_name]
            
            # Back to top
            self.back_to_top()
            self.to_normal_scale()

            # Back to home page first
            if self.get_coordinates(column_name="homepage", img_dir=self.general_img_dir):
                self.control.mouse_move(self.aligner.current_x, self.aligner.current_y)
                self.control.mouse_click(clicks=1)
                self.check_loading(template_name="load_homepage")
                
                for img_name in route_items:
                    if self.get_coordinates(column_name=img_name, img_dir=self.general_img_dir):
                        self.control.mouse_move(self.aligner.current_x, self.aligner.current_y)
                        self.control.mouse_click(clicks=1)
                        self.check_loading(template_name="load_" + img_name)
                    else:
                        raise RuntimeError(f"Failed for assigning new task, step {img_name}")
            else:
                raise RuntimeError(f"Failed for assigning new task, step {task_name}")
        except Exception as e:
            raise ActionError(f"Error assigning task: {str(e)}")

    def change_page_info(self, target_page=None):
        """
        Change page information for the instance
        """
        try:
            self.page = target_page
            self.template_img_dir, self.template_config_dir = self.set_template_dir_from_config(self.config_data)
        
        except Exception as e:
            raise ActionError(f"Erorr changing page info: {str(e)}")

    def change_page_within_task(self, target_page=None):
        """
        Click and change to sub page
        """
        try:
            if self.get_coordinates(target_page, img_dir=self.general_img_dir):
                self.control.mouse_move(self.aligner.current_x, self.aligner.current_y)
                self.control.mouse_click(clicks=2)
                self.change_page_info(target_page)
            else:
                raise RuntimeError(f"An error occurred while changing page.")
        except Exception as e:
            raise ActionError(f"Error changing page: {str(e)}")
    
    # If ICD9, change to ICD10
    def change_to_sub_page(self, target_button=None):
        """
        Click the button to change to right sub page
        """
        try:
            column_name = target_button # Need a more comprehensive method for this in the future
            if self.get_coordinates(column_name, img_dir=self.general_img_dir):
                self.control.mouse_move(self.aligner.current_x, self.aligner.current_y)
                self.control.mouse_click(clicks=2)
        except Exception as e:
            raise ActionError(f"Error changing to sub page: {str(e)}")
        
    def scroll_and_get_coors(self, column_name):
        """
        Get the coordinates based on right scrolling clicks
        """
        try:
            target_scroll_click, coor_x, coor_y = self.page_elements_coors[column_name]
            print(target_scroll_click, coor_x, coor_y)
            if target_scroll_click != self.scroll_click_now:
                self.control.mouse_scroll(self.BACK_TO_TOP_SCROLLING_AMOUNT)
                self.control.mouse_scroll(-target_scroll_click)
                self.scroll_click_now = target_scroll_click
            return coor_x, coor_y
        except Exception as e:
            raise ActionError(f"Error getting coordinates for {column_name}: {str(e)}")

    def get_coordinates(self, column_name: str, img_dir: Optional[str] = None, 
                        screenshot_np: Optional[np.ndarray] = None, custom_scale: Optional[float] = None) -> bool:
        """
        Detect template matched coordinates by aligner with enhanced error handling.
        """
        try:
            if not img_dir:
                img_pth = os.path.join(self.template_img_dir, column_name + ".png")
            else:
                img_pth = os.path.join(img_dir, column_name + ".png")
            
            if not os.path.exists(img_pth):
                raise TemplateError(f"Template image not found: {img_pth}")
            
            if not screenshot_np is None:
                return self.aligner.align(template_image_path=img_pth, target_img_np=screenshot_np, custom_scale=custom_scale)
                
            else:
                return self.aligner.align(img_pth, custom_scale=custom_scale)
            
        except Exception as e:
            logging.error(f"Error getting coordinates for {column_name}: {str(e)}")
            return False
    
    def get_all_coordinates_on_page(self):
        """
        Get all field coordinates on current page
        """
        try:
            self.page_elements_coors = {}
            template_names = self.get_all_fields_name()
            close_scales = np.geomspace(self.aligner.best_scale * 0.5, self.aligner.best_scale * 1.5, 30)
            # close_scales = np.linspace(0.3, 1.9, 100)
            scales = [1.0, self.aligner.best_scale]
            scales.extend([s for s in close_scales])
            # NEW ALGO
            for template in template_names:
                print(template)
                for scale in scales:
                    for cur_screenshot, cur_scroll in self.cur_page_screenshots:
                        if template not in self.page_elements_coors and self.get_coordinates(template, screenshot_np=cur_screenshot, custom_scale=scale):
                            self.page_elements_coors[template] = (cur_scroll, self.aligner.current_x, self.aligner.current_y)
                            # Found all template coors
                            if len(self.page_elements_coors) == len(template_names):
                                self.back_to_top()
                                return template_names
            
            # Missing coors
            if len(self.page_elements_coors) != len(template_names) and len(template_names) != 0:
                print(self.page_elements_coors.keys())
                raise ActionError(f"Can't find all element mataches on current page.")
        
        except Exception as e:
            raise ActionError(f"Error getting all coordinates: {str(e)}")
    
    # TODO
    def check_filled_content(self, columm_value):
        """
        Crop the section based on coordinates, and use ocr to check the content
        """
        pass

    def check_loading(self, template_name, attempt_time=3, close_window=False, select_result=False):
        """
        Check the page or pop out window is fully loaded or not
        """
        success = False
        try:
            print(template_name)
            time.sleep(2)
            for _ in range(attempt_time):
                if self.get_coordinates(template_name, img_dir=self.general_img_dir):
                    success = True
                    if select_result:
                        self.control.mouse_move(self.aligner.current_x, self.aligner.current_y)
                        self.control.mouse_click()
                    break
                time.sleep(3)

        except Exception as e:
            raise ActionError(f"{str(e)}")

        if not success:
            if close_window:
                self.control.keyboard_hotkey(self.modifier_key, 'w')
            raise ActionError("Page loading failed.")

    def get_selection_options(self, column_name):
        """
        Check the options in the selection menu
        """
        try:
            config_pth = os.path.join(self.template_config_dir, column_name + ".json")
            selection_options = self._load_config(config_pth)
            return selection_options
        except Exception as e:
            raise ActionError(f"Error checking selection options: {str(e)}")

    def execute_action(self, action_name: str, params: Dict[str, Any], field_value: Any = None) -> bool:
        """
        Execute a single action with enhanced error handling.
        """
        try:
            def process_text_value(params, field_value):
                try:
                    if isinstance(field_value, dict):
                        return field_value.get(params.get("text_key", ""))
                    elif isinstance(field_value, (list, tuple)):
                        if "tuple_index" in params:
                            return field_value[params.get("tuple_index")]
                        return field_value
                    return field_value
                except Exception as e:
                    raise ActionError(f"Error processing text value: {str(e)}")

            action_map = {
                "mouse_move": lambda p: self.control.mouse_move(
                    coor_x=p.get("x"),
                    coor_y=p.get("y"),
                    smooth=p.get("smooth", True)
                ),
                
                "mouse_click": lambda p: self.control.mouse_click(
                    button=p.get("button", "left"),
                    clicks=p.get("clicks", 1),
                    interval=p.get("interval", 0.1)
                ),
                
                "keyboard_write": lambda p: self.control.keyboard_write(
                    text=p.get("text") if "text" in p else process_text_value(p, field_value),
                    interval=p.get("interval", 0.01),
                    copy_paste=p.get("can_paste", True)
                ),
                
                "keyboard_press": lambda p: self.control.keyboard_press(
                    button=p.get("key"),
                    presses=p.get("presses", 1),
                    interval=p.get("interval", 0.1)
                ),
                
                "keyboard_hotkey": lambda p: self.control.keyboard_hotkey(
                    *(self.modifier_key if key == "<MODIFIER_KEY>" else key 
                    for key in p.get("keys", [])),
                    presses=p.get("presses", 1),
                    interval=p.get("interval", 0.1)
                ),
                
                "keyboard_release_all_keys": lambda p: self.control.keyboard_release_all_keys(),
                
                "mouse_scroll": lambda p: self.control.mouse_scroll(
                    clicks=p.get("clicks", 0)
                ),

                "loop_array": lambda p: self._handle_array_loop(
                    p.get("loop_actions", []),
                    p.get("skip_in_last_loop", 0),
                    field_value
                ),

                "loop_tuple_array": lambda p: self._handle_tuple_array_loop(
                    p.get("loop_actions", []),
                    p.get("skip_in_last_loop", 0),
                    field_value
                ),
                
                "wait": lambda p: time.sleep(p.get("seconds", 1)),

                "check_loading": lambda p: self.check_loading(
                    template_name = p.get("template_name", []),
                    close_window = p.get("close_window", False),
                    select_result = p.get("select_result", False)
                ),

                "back_to_top": lambda p: self.back_to_top()
            }

            if action_name not in action_map:
                raise ActionError(f"Unknown action: {action_name}")

            try:
                action_map[action_name](params)
            except Exception as e:
                raise ActionError(f"Failed to execute {action_name}: {str(e)}")

            # if action_name == "wait_for_template":
            #     return bool(result)
            
            return True

        except ActionError as e:
            logging.error(f"Action error: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in execute_action: {str(e)}")
            raise ActionError(f"Unexpected error in execute_action: {str(e)}")

    def execute_page(self):
        """
        Execute the page actions with comprehensive error handling.
        """
        try:
            yield {"status": "standard", "message": "Starting page actions..."}
            
            try:
                yield {"status": "standard", "message": "Initializing scrolling parameters..."}
                self.get_scrolling_parameters()
            except Exception as e:
                yield {"status": "critical", "message": f"Failed to initialize scrolling: {str(e)}"}
                raise
            
            try:
                yield {"status": "standard", "message": "Detecting page elements..."}
                self.get_all_coordinates_on_page()
            except Exception as e:
                yield {"status": "critical", "message": f"Failed to detect page elements: {str(e)}"}
                raise

            try:
                step_config = self._load_config(os.path.join(self.template_config_dir, "steps.json"))
            except Exception as e:
                yield {"status": "critical", "message": f"Failed to load step configuration: {str(e)}"}
                raise
            
            total_items = len(step_config)
            for i, step_name in enumerate(step_config.keys(), 1):
                try:
                    yield {"status": "standard", "message": f"Processing field ({i}/{total_items}): {step_name}"}
                    
                    if step_name not in self.page_elements_coors:
                        yield {"status": "critical", "message": f"No element found for configured step: {step_name}"}
                        continue
                    
                    # Check if all required data exist for certain page
                    require_data = step_config[step_name]["require_data"]
                    if not self.emr_data.check_action_data(require_data):
                        yield {"status": "critical", "message": f"Missing {require_data} for action: {step_name}"}
                        continue

                    actions = step_config[step_name]["actions"]
                    field_value = ""
                    
                    try:
                        x, y = self.scroll_and_get_coors(step_name)
                    except Exception as e:
                        yield {"status": "critical", "message": f"Failed to get coordinates for {step_name}: {str(e)}"}
                        continue

                    selection_options = None
                    total_actions = len(actions)
                    for j, action_step in enumerate(actions, 1):
                        try:
                            action_name, action_params = action_step
                            
                            # Read the drop down menu options
                            if action_name == "get_selection_options":
                                selection_options = self.get_selection_options(step_name)
                                continue

                            # Read the corresponding data for used
                            if "data_name" in action_params:
                                data_name = action_params["data_name"]
                                field_value = self.emr_data.get_value(data_name)
                                if not field_value or field_value == "":
                                    raise ValueError(f"Missing value: {data_name}") 

                            if action_name == "mouse_move" and x is not None and y is not None:
                                action_params = {"x": x, "y": y, "smooth": action_params.get("smooth", True)}

                            elif action_name == "keyboard_write":
                                if isinstance(field_value, dict):
                                    action_params["text_key"] = action_params.get("text_key", "")
                                else:
                                    action_params["text"] = field_value
                                action_params["can_paste"] = action_params.get("can_paste", True)

                            elif action_name == "keyboard_press" and selection_options and j == total_actions:
                                print(field_value)
                                press_key, press_time = selection_options[field_value]
                                print(press_key, press_time)
                                action_params = {"key": press_key, "presses": press_time}
                                selection_options = None

                            success = self.execute_action(action_name, action_params, field_value)
                            if not success:
                                yield {"status": "critical", "message": f"Action {action_name} returned False"}
                            
                            time.sleep(0.1)
                            
                        except Exception as e:
                            logging.error(f"Action failed: {action_name}{str(e)}")
                            raise

                except Exception as e:
                    logging.error(f"Error processing field {step_name}: {str(e)}")
                    raise

            try:
                # Back to top when done
                # self.control.mouse_scroll(self.scroll_click_now + 10)
                # self.control.mouse_move(self.aligner.screen_width // 2, self.aligner.screen_height // 2)
                self.back_to_top()

            except Exception as e:
                yield {"status": "critical", "message": f"Failed to reset page position: {str(e)}"}

            yield {"status": "standard", "message": "Page completed successfully"}
            
        except Exception as e:
            logging.error(f"Page execution failed: {str(e)}")
            raise

    def run(self, task_name: str):
        """
        Execute a task and yield progress updates.
        """
        try:
            # Check screen resoultion
            # self._check_os_resolution()

            if task_name not in self.config_data.get('tasks', {}):
                raise ConfigurationError(f"Task '{task_name}' not found in configuration")

            task_config = self.config_data['tasks'][task_name]
            self.change_page_info(task_config['initial_page'])
            
            time.sleep(0.1)  # Small delay for stability
            yield {"status": "standard", "message": f"Starting task: {task_name}"}
            
            for operation in task_config['operations']:
                try:
                    method_name = operation['method']
                    args = operation.get('args', [])
                    kwargs = operation.get('kwargs', {})
                    
                    if not hasattr(self, method_name):
                        raise ValueError(f"Unknown method: {method_name}")
                        
                    yield {"status": "standard", "message": f"Executing: {method_name}"}
                    
                    method = getattr(self, method_name)
                    if method_name == "execute_page":
                        # For sync generator, we need to iterate normally
                        for status in method(*args, **kwargs):
                            yield status
                    else:
                        # Other methods are simple sync operations
                        method(*args, **kwargs)
                    # yield {"status": "standard", "message": f"Completed: {method_name}"}
                    
                    time.sleep(0.1)  # Small delay between operations
                    
                except Exception as e:
                    logging.error(f"Operation failed - {method_name}: {str(e)}")
                    raise
            
            yield {"status": "standard", "message": f"Task '{task_name}' completed successfully"}
            
        except Exception as e:
            yield {"status": "critical", "message": f"Task execution failed: {str(e)}"}
            raise
