"""Configuration loader for navigation system."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

# PyYAML is optional - falls back to defaults if not installed
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("Warning: PyYAML not installed. Run: pip install pyyaml")


class Config:
    """Configuration manager with dot-notation access."""

    def __init__(self, config_dict: Dict[str, Any]):
        self._config = config_dict

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot-notation key (e.g., 'navigation.lane_enter_threshold')."""
        keys = key.split('.')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def __getattr__(self, name: str) -> Any:
        """Allow attribute-style access to top-level config sections."""
        if name.startswith('_'):
            return super().__getattribute__(name)
        if name in self._config:
            value = self._config[name]
            if isinstance(value, dict):
                return Config(value)
            return value
        raise AttributeError(f"Config has no attribute '{name}'")


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. If None, looks for config.yaml
                    in the project root (same directory as hybrid_navigation.py)

    Returns:
        Config object with loaded settings
    """
    if config_path is None:
        # Default to config.yaml in project root
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        print(f"Warning: Config file not found at {config_path}, using defaults")
        return Config(_get_default_config())

    if not YAML_AVAILABLE:
        print("Warning: PyYAML not available, using default config")
        return Config(_get_default_config())

    with open(config_path, 'r') as f:
        config_dict = yaml.safe_load(f)

    return Config(config_dict or _get_default_config())


def _get_default_config() -> Dict[str, Any]:
    """Return default configuration when YAML is unavailable."""
    return {
        'navigation': {
            'lane_enter_threshold': 0.25,
            'lane_exit_threshold': 0.10,
            'min_mode_duration': 1.0,
            'arrival_threshold': 0.25,
            'arrival_stable_frames': 5,
            'waypoint_threshold': 0.3,
        },
        'speed': {
            'max_speed': 0.35,
            'min_speed': 0.0,
            'accel_rate': 0.15,
            'decel_rate': 0.25,
            'roundabout_speed': 0.20,
            'intersection_speed': 0.15,
            'approach_speed': 0.15,
        },
        'lane_detection': {
            'pid_kp': 0.8,
            'pid_ki': 0.05,
            'pid_kd': 0.3,
        },
        'safety': {
            'stuck_threshold': 5.0,
            'min_total_movement': 0.1,
        },
        'telemetry': {
            'enabled': True,
            'log_directory': 'logs',
            'save_video': True,
            'video_fps': 15,
        },
    }


# Global config instance (lazy loaded)
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global config instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config(config_path: Optional[str] = None) -> Config:
    """Reload configuration from file."""
    global _config
    _config = load_config(config_path)
    return _config
