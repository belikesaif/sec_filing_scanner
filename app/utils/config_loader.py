# app/utils/config_loader.py
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ConfigLoader:
    """Utility class to load configuration from config.yaml and .env files"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the config loader with an optional custom config path"""
        # Default config path is in the project root
        if config_path is None:
            # Get the project root directory (2 levels up from this file)
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config.yaml"
        
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from the YAML file"""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Config file not found at {self.config_path}. Using default values.")
                return {}
            
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config
        except Exception as e:
            logger.error(f"Error loading config from {self.config_path}: {e}")
            return {}
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value from a specific section"""
        try:
            return self.config.get(section, {}).get(key, default)
        except Exception as e:
            logger.error(f"Error getting config value for {section}.{key}: {e}")
            return default
    
    def get_section(self, section: str, default: Any = None) -> Dict[str, Any]:
        """Get an entire configuration section"""
        try:
            return self.config.get(section, default or {})
        except Exception as e:
            logger.error(f"Error getting config section {section}: {e}")
            return default or {}
    
    def reload(self) -> None:
        """Reload the configuration from the file"""
        self.config = self._load_config()
        logger.info("Configuration reloaded")

# Create a singleton instance for global use
config = ConfigLoader()