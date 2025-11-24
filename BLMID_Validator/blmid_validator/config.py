"""
Configuration module for BLMID Validator.
Loads settings from config.yaml or environment variables.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for BLMID Validator."""

    # Defaults
    DEFAULTS = {
        "database": {
            "type": "postgresql",
            "connection_uri": "postgresql://user:password@localhost:5432/database_name",
            "table_name": "blmid_reference",
            "columns": {
                "blmid": "blmid",
                "latitude": "latitude",
                "longitude": "longitude",
            },
        },
        "excel": {
            "sheet_name": None,  # None = first sheet
            "columns": {
                "blmid": "A",
                "latitude": "B",
                "longitude": "C",
            },
            "header_row": 1,
        },
        "pdf": {
            "ocr_enabled": True,
            "ocr_fallback": True,  # Use OCR only if text extraction fails
            "tesseract_path": None,  # Auto-detect if None
            "regex_patterns": {
                "blmid": r"BLM[\s-]*(?:ID)?[\s-]*([A-Z0-9]+)",
                "latitude": r"(lat[a-z]*|latitude)[\s:]*(-?\d+\.?\d*)",
                "longitude": r"(lon[a-z]*|longitude)[\s:]*(-?\d+\.?\d*)",
            },
        },
        "validation": {
            "coordinate_tolerance": 0.0001,  # degrees
            "latitude_min": -90,
            "latitude_max": 90,
            "longitude_min": -180,
            "longitude_max": 180,
            "check_duplicates": True,
        },
        "output": {
            "directory": "./output",
            "updated_excel_prefix": "Updated_BLMID",
            "corrections_log_prefix": "Corrections_Log",
        },
        "logging": {
            "level": "INFO",
            "log_dir": "./output/logs",
            "error_log": "error.log",
            "process_log": "process.log",
        },
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to config.yaml or config.json. If None, uses defaults.
        """
        self.config: Dict[str, Any] = self._deep_copy(self.DEFAULTS)
        self.config_path = config_path

        if config_path and os.path.exists(config_path):
            self._load_from_file(config_path)
            logger.info(f"Configuration loaded from {config_path}")
        else:
            logger.warning("No config file provided; using defaults.")

    @staticmethod
    def _deep_copy(d: Dict) -> Dict:
        """Deep copy a dictionary."""
        import copy
        return copy.deepcopy(d)

    def _load_from_file(self, path: str) -> None:
        """Load configuration from YAML or JSON file."""
        ext = Path(path).suffix.lower()
        try:
            if ext == ".yaml" or ext == ".yml":
                with open(path, "r") as f:
                    user_config = yaml.safe_load(f) or {}
            elif ext == ".json":
                with open(path, "r") as f:
                    user_config = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {ext}")

            self._merge_config(user_config)
        except Exception as e:
            logger.error(f"Failed to load config file {path}: {e}")
            raise

    def _merge_config(self, user_config: Dict[str, Any]) -> None:
        """
        Recursively merge user config into defaults.
        User values override defaults.
        """
        for key, value in user_config.items():
            if isinstance(value, dict) and key in self.config:
                self._merge_config_dict(self.config[key], value)
            else:
                self.config[key] = value

    @staticmethod
    def _merge_config_dict(target: Dict, source: Dict) -> None:
        """Recursively merge source dict into target dict."""
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                Config._merge_config_dict(target[key], value)
            else:
                target[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        Example: get("database.connection_uri")
        """
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.
        Example: set("database.connection_uri", "postgresql://...")
        """
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def to_dict(self) -> Dict[str, Any]:
        """Return full config as dictionary."""
        return self._deep_copy(self.config)

    def to_json(self) -> str:
        """Return config as JSON string."""
        return json.dumps(self.config, indent=2)

    def save_to_file(self, path: str, format: str = "yaml") -> None:
        """Save current config to file (yaml or json)."""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            if format.lower() in ["yaml", "yml"]:
                with open(path, "w") as f:
                    yaml.dump(self.config, f, default_flow_style=False)
            elif format.lower() == "json":
                with open(path, "w") as f:
                    json.dump(self.config, f, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")
            logger.info(f"Configuration saved to {path}")
        except Exception as e:
            logger.error(f"Failed to save config to {path}: {e}")
            raise
