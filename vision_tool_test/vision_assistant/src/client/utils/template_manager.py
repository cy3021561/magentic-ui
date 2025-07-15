import os
from pathlib import Path
from typing import Optional

class TemplatePathManager:
    """Manages EMR template paths and validation."""
    
    @staticmethod
    def get_default_path() -> Optional[str]:
        """
        Get the default template path from environment or common locations.
        """
        if env_path := os.getenv('VISION_ASSISTANT_TEMPLATES'):
            if os.path.exists(env_path):
                return env_path
        
        possible_locations = [
            os.path.join(os.getcwd(), 'emr_templates'),
            os.path.join(str(Path.home()), 'emr_templates'),
            os.path.join(os.path.dirname(os.getcwd()), 'emr_templates')
        ]
        
        return next((loc for loc in possible_locations if os.path.exists(loc)), None)
    
    @staticmethod
    def validate_emr_path(base_path: str, emr_system: str) -> str:
        """
        Validate EMR system path and structure.
        """
        if not base_path:
            raise ValueError("No template base directory found")
        
        emr_path = os.path.join(base_path, emr_system)
        if not os.path.exists(emr_path):
            raise ValueError(f"EMR system directory not found: {emr_path}")
        
        config_path = os.path.join(emr_path, "general/configs/config.json")
        if not os.path.exists(config_path):
            raise ValueError(
                f"Invalid EMR system structure. Expected: {config_path}\n"
                "Please ensure proper directory structure:\n"
                f"  {emr_path}/\n"
                "    └── general/\n"
                "        └── configs/\n"
                "            └── config.json"
            )
        
        return emr_path