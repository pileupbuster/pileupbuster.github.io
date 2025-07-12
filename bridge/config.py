"""Configuration management for QLog Bridge"""
import json
import os
from pathlib import Path
from typing import Dict, Any


class BridgeConfig:
    """Configuration management for the QLog UDP Bridge"""
    
    DEFAULT_CONFIG = {
        "udp_port": 2238,
        "websocket_port": 8765,
        "log_level": "INFO",
        "auto_start": True,
        "buffer_size": 1024,
        "reconnect_delay": 5.0,
        "max_clients": 10
    }
    
    def __init__(self, config_path: str = None):
        """Initialize configuration
        
        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path is None:
            # Use same directory as executable
            base_dir = Path(__file__).parent
            config_path = base_dir / "bridge_config.json"
        
        self.config_path = Path(config_path)
        self.config = self.DEFAULT_CONFIG.copy()
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file, create default if doesn't exist"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
                    print(f"Loaded configuration from {self.config_path}")
            else:
                self.save_config()
                print(f"Created default configuration at {self.config_path}")
        except Exception as e:
            print(f"Error loading config: {e}. Using defaults.")
    
    def save_config(self) -> None:
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            print(f"Configuration saved to {self.config_path}")
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value and save"""
        self.config[key] = value
        self.save_config()
    
    @property
    def udp_port(self) -> int:
        return self.config["udp_port"]
    
    @property
    def websocket_port(self) -> int:
        return self.config["websocket_port"]
    
    @property
    def log_level(self) -> str:
        return self.config["log_level"]
    
    @property
    def buffer_size(self) -> int:
        return self.config["buffer_size"]
    
    @property
    def reconnect_delay(self) -> float:
        return self.config["reconnect_delay"]
    
    @property
    def max_clients(self) -> int:
        return self.config["max_clients"]
