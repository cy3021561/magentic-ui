import cv2
import os
import pyautogui
import numpy as np
import logging
from PIL import Image
import time
import traceback
from functools import wraps
from typing import Tuple, Optional

class TemplateAlignmentError(Exception):
    """Base exception class for template alignment errors"""
    pass

class ImageProcessingError(TemplateAlignmentError):
    """Raised when there's an error processing images"""
    pass

class MatchingError(TemplateAlignmentError):
    """Raised when there's an error in template matching"""
    pass

class ScreenCaptureError(TemplateAlignmentError):
    """Raised when there's an error capturing the screen"""
    pass

class TemplateAligner:
    DEFAULT_TEMPLATE_MATCHING_THRESHOLD = 0.8

    def __init__(self, debug=False, screen_width=None, screen_height=None):
        """
        Initialize the TemplateAligner instance with error handling.
        """
        try:
            self.debug = debug
            self.screen_width = None
            self.screen_height = None
            self.current_x = None
            self.current_y = None
            self.best_scale = 1.0
            self.get_screen_dimensions(screen_width, screen_height)
                
        except Exception as e:
            raise TemplateAlignmentError(f"Failed to initialize TemplateAligner: {str(e)}")

    def _show_image(self, np_image: np.ndarray) -> None:
        """
        Display an image using OpenCV with error handling.
        """
        try:
            if np_image is None:
                raise ValueError("Invalid image: np_image is None")
                
            cv2.imshow("tmp", np_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        except Exception as e:
            raise ImageProcessingError(f"Failed to display image: {str(e)}")

    def get_screen_dimensions(self, screen_w: Optional[int] = None, screen_h: Optional[int] = None) -> Tuple[int, int]:
        """
        Get the screen dimensions with error handling.
        """
        try:
            if screen_w is not None and screen_h is not None:
                if screen_w <= 0 or screen_h <= 0:
                    raise ValueError("Screen dimensions must be positive")
                self.screen_width, self.screen_height = screen_w, screen_h
            
            self.screen_width, self.screen_height = pyautogui.size()
        except Exception as e:
            raise TemplateAlignmentError(f"Failed to get screen dimensions: {str(e)}")
    
    def get_screenshot(self) -> np.ndarray:
        """
        Capture a screenshot with error handling.
        """
        try:
            screenshot = pyautogui.screenshot()
            if screenshot is None:
                raise ScreenCaptureError("Failed to capture screenshot")
                
            screenshot_np = np.array(screenshot)
            screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)
            # self._show_image(screenshot_gray)
            return screenshot_gray
            
        except Exception as e:
            raise ScreenCaptureError(f"Failed to capture or process screenshot: {str(e)}")

    def get_screen_coordinates(self, screenshot_image: np.ndarray, coor_x: int, coor_y: int) -> Tuple[int, int]:
        """
        Convert image coordinates to screen coordinates with error handling.
        """
        try:
            if screenshot_image is None:
                raise ValueError("Invalid screenshot image")
            if not isinstance(coor_x, (int, float)) or not isinstance(coor_y, (int, float)):
                raise ValueError("Coordinates must be numeric")

            img_width, img_height = screenshot_image.shape[::-1]
            if img_width == 0 or img_height == 0:
                raise ValueError("Invalid image dimensions")

            scale_x = img_width / self.screen_width
            scale_y = img_height / self.screen_height

            scaled_center_x = int(coor_x / scale_x)
            scaled_center_y = int(coor_y / scale_y)

            return scaled_center_x, scaled_center_y
            
        except Exception as e:
            raise TemplateAlignmentError(f"Failed to convert coordinates: {str(e)}")

    def template_match(self, screenshot_img: np.ndarray, template_img: np.ndarray, custom_scale: float = None) -> Tuple[float, Tuple[int, int]]:
        """
        Perform template matching.
        """
        try:
            if template_img is None or screenshot_img is None:
                raise ValueError("Invalid input images")
            # self._show_image(template_img)

            if custom_scale: # Typically for get_all_coordinates_on_page
                scale = custom_scale
                width = int(template_img.shape[1] * scale)
                height = int(template_img.shape[0] * scale)
                    
                scaled_template = cv2.resize(template_img, (width, height), interpolation=cv2.INTER_AREA)
                result = cv2.matchTemplate(screenshot_img, scaled_template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                print(f"Scale: {custom_scale}; Prob: {max_val}")

                if max_val > self.DEFAULT_TEMPLATE_MATCHING_THRESHOLD:
                    self.best_scale = scale
                    return max_loc
            
            else: # Deep scaling search
                regular_scales = np.linspace(0.5, 1.5, 30)
                scales = [1.0, self.best_scale]
                scales.extend([s for s in regular_scales if abs(s - self.best_scale) > 0.001])

                best_match = (-1, None, 1.0)

                for scale in scales:
                    width = int(template_img.shape[1] * scale)
                    height = int(template_img.shape[0] * scale)
                    if width <= 0 or height <= 0:
                        continue
                        
                    scaled_template = cv2.resize(template_img, (width, height), interpolation=cv2.INTER_AREA)
                    result = cv2.matchTemplate(screenshot_img, scaled_template, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, max_loc = cv2.minMaxLoc(result)
                    print(f"Scale: {scale}; Prob: {max_val}")

                    if max_val > self.DEFAULT_TEMPLATE_MATCHING_THRESHOLD and max_val > best_match[0]:
                        self.best_scale = scale
                        return max_loc

            raise MatchingError("No valid match found")
        
        except Exception as e:
            raise MatchingError(f"Template matching failed: {str(e)}")

    def align(self, template_image_path: str, target_image_path: Optional[str] = None, 
              target_img_np: Optional[np.ndarray] = None, custom_scale: Optional[float] = None
              ) -> bool:
        """
        Align template image on the target image.
        """
        try:
            logging.info("Aligning template image: %s", template_image_path)
            template_img = cv2.imread(template_image_path, cv2.IMREAD_GRAYSCALE)
            if template_img is None:
                raise ImageProcessingError(f"Failed to load template image: {template_image_path}")

            if target_image_path:
                target_img = cv2.imread(target_image_path, cv2.IMREAD_GRAYSCALE)
                if target_img is None:
                    raise ImageProcessingError(f"Failed to load target image: {target_image_path}")
            else:
                target_img = self.get_screenshot()

            if not target_img_np is None:
                target_img = target_img_np
            
            # Template Matching and return the location
            if not custom_scale:
                max_loc = self.template_match(target_img, template_img)
            else:
                max_loc = self.template_match(target_img, template_img, custom_scale=custom_scale)

            # Generate real position on the screen scale
            w = int(template_img.shape[1] * self.best_scale)
            h = int(template_img.shape[0] * self.best_scale)
            self.current_x, self.current_y = self.get_screen_coordinates(
                target_img, max_loc[0] + w // 2, max_loc[1] + h // 2
            )
            return True
            
        except Exception as e:
            traceback.print_exc()
            return False
    
    def show_matched_region(self, template_image_path: str, margin: int = 20) -> None:
        """
        Display the matched region with the template overlaid and a margin around it.
        
        Args:
            template_image_path (str): Path to the template image file
            margin (int): Number of pixels to add around the matched region (default: 20)
        
        Raises:
            ImageProcessingError: If there's an error processing or displaying the images
            TemplateAlignmentError: If template matching fails
        """
        try:
            # Load template in color for visualization
            template_img_color = cv2.imread(template_image_path, cv2.IMREAD_COLOR)
            if template_img_color is None:
                raise ImageProcessingError(f"Failed to load template image: {template_image_path}")
            
            # Get current screenshot in color
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            screenshot_color = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            
            # Perform template matching to get location
            if not self.align(template_image_path, custom_scale=1.0):
                raise TemplateAlignmentError("Failed to find template match")
            
            # Calculate the region coordinates
            scaled_width = int(template_img_color.shape[1] * self.best_scale)
            scaled_height = int(template_img_color.shape[0] * self.best_scale)
            
            # Convert screen coordinates back to image coordinates
            img_height, img_width = screenshot_color.shape[:2]
            scale_x = img_width / self.screen_width
            scale_y = img_height / self.screen_height
            
            center_x = int(self.current_x * scale_x)
            center_y = int(self.current_y * scale_y)
            
            # Calculate region boundaries with margin
            x1 = max(0, center_x - scaled_width//2 - margin)
            y1 = max(0, center_y - scaled_height//2 - margin)
            x2 = min(img_width, center_x + scaled_width//2 + margin)
            y2 = min(img_height, center_y + scaled_height//2 + margin)
            
            # Extract and show the region
            matched_region = screenshot_color[y1:y2, x1:x2].copy()
            
            # Draw rectangle around the matched template
            inner_x1 = scaled_width//2 + margin - scaled_width//2
            inner_y1 = scaled_height//2 + margin - scaled_height//2
            cv2.rectangle(matched_region,
                        (inner_x1, inner_y1),
                        (inner_x1 + scaled_width, inner_y1 + scaled_height),
                        (0, 255, 0), 2)
            
            # Show confidence score
            cv2.putText(matched_region,
                    f"Scale: {self.best_scale:.2f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2)
            
            # Display both original template and matched region
            cv2.imshow("Template", template_img_color)
            cv2.imshow("Matched Region", matched_region)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
        except Exception as e:
            raise ImageProcessingError(f"Failed to show matched region: {str(e)}")



if __name__ == "__main__":
    import time
    time.sleep(2)

    aligner = TemplateAligner(debug=True)
    aligner.show_matched_region("/Users/chun/Documents/Bridgent/vision_assistant/emr_templates/office_ally/general/images/homepage.png", margin=30)