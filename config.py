"""
Configuration Management
Load and manage integration settings
"""

import json
import os
import logging
from typing import Any

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager"""
    
    # Default values
    DEFAULTS = {
        'ecwid_store_id': '',
        'ecwid_api_token': '',
        'shiprocket_email': '',
        'shiprocket_password': '',
        'shiprocket_pickup_location_id': 0,
        'shiprocket_channel_id': 0,
        'default_package_length': 10,
        'default_package_breadth': 10,
        'default_package_height': 10,
        'default_package_weight': 0.5,
        'sync_interval_hours': 24,
        'auto_sync_enabled': False,
        'notify_on_failure': True,
        'webhook_url': '',
    }
    
    def __init__(self, config_path: str = 'config.json'):
        """Initialize configuration"""
        self.config_path = config_path
        self.config = self.DEFAULTS.copy()
        
        # Load from file if exists
        if os.path.exists(config_path):
            self._load_from_file()
        
        # Override with environment variables
        self._load_from_env()
        
        logger.info(f"✓ Configuration loaded")
    
    def _load_from_file(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                file_config = json.load(f)
                self.config.update(file_config)
            logger.info(f"Loaded config from {self.config_path}")
        except Exception as e:
            logger.warning(f"Could not load config file: {str(e)}")
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        env_mappings = {
            'ECWID_STORE_ID': 'ecwid_store_id',
            'ECWID_API_TOKEN': 'ecwid_api_token',
            'SHIPROCKET_EMAIL': 'shiprocket_email',
            'SHIPROCKET_PASSWORD': 'shiprocket_password',
            'SHIPROCKET_PICKUP_LOCATION_ID': 'shiprocket_pickup_location_id',
            'SHIPROCKET_CHANNEL_ID': 'shiprocket_channel_id',
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                # Convert to int if applicable
                if config_key in ['ecwid_store_id', 'shiprocket_pickup_location_id', 'shiprocket_channel_id']:
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                self.config[config_key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    @property
    def ecwid_store_id(self) -> str:
        return self.config['ecwid_store_id']
    
    @property
    def ecwid_api_token(self) -> str:
        return self.config['ecwid_api_token']
    
    @property
    def shiprocket_email(self) -> str:
        return self.config['shiprocket_email']
    
    @property
    def shiprocket_password(self) -> str:
        return self.config['shiprocket_password']
    
    @property
    def shiprocket_pickup_location_id(self) -> int:
        return self.config['shiprocket_pickup_location_id']
    
    @property
    def shiprocket_channel_id(self) -> int:
        return self.config['shiprocket_channel_id']
    
    @property
    def default_package_length(self) -> float:
        return self.config['default_package_length']
    
    @property
    def default_package_breadth(self) -> float:
        return self.config['default_package_breadth']
    
    @property
    def default_package_height(self) -> float:
        return self.config['default_package_height']
    
    @property
    def default_package_weight(self) -> float:
        return self.config['default_package_weight']
