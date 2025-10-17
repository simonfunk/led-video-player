"""
Configuration manager for loading and validating application configuration.
"""
import argparse
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

from .models import (
    AppConfig, DisplayConfig, ScheduleConfig, PlaybackConfig,
    FolderConfig, LoggingConfig, FixedScheduleConfig, SunScheduleConfig, WebConfig
)


class ConfigManager:
    """Manages application configuration loading and validation."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._config: Optional[AppConfig] = None
    
    def load_config(self, config_path: Optional[str] = None, cli_args: Optional[Dict[str, Any]] = None) -> AppConfig:
        """
        Load configuration from file and CLI arguments.
        
        Args:
            config_path: Path to configuration file (YAML or JSON)
            cli_args: Dictionary of CLI arguments to override config values
            
        Returns:
            AppConfig: Loaded and validated configuration
        """
        # Start with default configuration
        config_dict = self._get_default_config()
        
        # Load from file if provided
        if config_path and os.path.exists(config_path):
            try:
                file_config = self._load_config_file(config_path)
                config_dict = self._merge_configs(config_dict, file_config)
                self.logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                self.logger.error(f"Failed to load config file {config_path}: {e}")
                self.logger.info("Using default configuration")
        elif config_path:
            self.logger.warning(f"Config file {config_path} not found, using defaults")
        
        # Apply CLI overrides
        if cli_args:
            config_dict = self._apply_cli_overrides(config_dict, cli_args)
        
        # Validate and create config object
        self._config = self._create_config_object(config_dict)
        self._validate_config(self._config)
        
        return self._config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration as dictionary."""
        default_config = AppConfig()
        return {
            'display': {
                'monitor_index': default_config.display.monitor_index,
                'always_on_top': default_config.display.always_on_top,
                'hide_cursor_after_ms': default_config.display.hide_cursor_after_ms,
                'background_color': default_config.display.background_color
            },
            'schedule': {
                'mode': default_config.schedule.mode,
                'fixed_schedule': {
                    'day_start': default_config.schedule.fixed_schedule.day_start,
                    'night_start': default_config.schedule.fixed_schedule.night_start
                },
                'sun_schedule': {
                    'latitude': default_config.schedule.sun_schedule.latitude,
                    'longitude': default_config.schedule.sun_schedule.longitude,
                    'day_offset_minutes': default_config.schedule.sun_schedule.day_offset_minutes,
                    'night_offset_minutes': default_config.schedule.sun_schedule.night_offset_minutes
                }
            },
            'playback': {
                'interval_seconds': default_config.playback.interval_seconds,
                'shuffle': default_config.playback.shuffle,
                'fit_mode': default_config.playback.fit_mode,
                'transition_ms': default_config.playback.transition_ms,
                'reload_images_every_seconds': default_config.playback.reload_images_every_seconds,
                'resume_index_between_runs': default_config.playback.resume_index_between_runs
            },
            'folders': {
                'day': default_config.folders.day,
                'night': default_config.folders.night,
                'include_subfolders': default_config.folders.include_subfolders
            },
            'logging': {
                'level': default_config.logging.level,
                'log_to_file': default_config.logging.log_to_file,
                'log_file_path': default_config.logging.log_file_path,
                'max_file_size_mb': default_config.logging.max_file_size_mb,
                'backup_count': default_config.logging.backup_count,
                'log_to_console': default_config.logging.log_to_console
            }
        }
    
    def _load_config_file(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML or JSON file."""
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.lower().endswith(('.yml', '.yaml')):
                return yaml.safe_load(f) or {}
            elif config_path.lower().endswith('.json'):
                return json.load(f) or {}
            else:
                raise ValueError(f"Unsupported config file format: {config_path}")
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_cli_overrides(self, config: Dict[str, Any], cli_args: Dict[str, Any]) -> Dict[str, Any]:
        """Apply CLI argument overrides to configuration."""
        result = config.copy()
        
        # Map CLI arguments to config paths
        cli_mappings = {
            'monitor_index': ('display', 'monitor_index'),
            'day_folder': ('folders', 'day'),
            'night_folder': ('folders', 'night'),
            'interval': ('playback', 'interval_seconds'),
            'shuffle': ('playback', 'shuffle'),
            'no_shuffle': ('playback', 'shuffle'),  # Special case for negation
            'log_level': ('logging', 'level'),
            'force_day': None,  # Handled separately
            'force_night': None,  # Handled separately
        }
        
        for cli_key, config_path in cli_mappings.items():
            if cli_key in cli_args and cli_args[cli_key] is not None and cli_args[cli_key] is not False:
                if config_path:
                    section, key = config_path
                    if section not in result:
                        result[section] = {}
                    
                    # Special handling for no_shuffle
                    if cli_key == 'no_shuffle':
                        result[section][key] = False
                    else:
                        result[section][key] = cli_args[cli_key]
        
        return result
    
    def _create_config_object(self, config_dict: Dict[str, Any]) -> AppConfig:
        """Create AppConfig object from dictionary."""
        try:
            # Create nested config objects
            display_config = DisplayConfig(**config_dict.get('display', {}))
            
            schedule_dict = config_dict.get('schedule', {})
            fixed_schedule = FixedScheduleConfig(**schedule_dict.get('fixed_schedule', {}))
            sun_schedule = SunScheduleConfig(**schedule_dict.get('sun_schedule', {}))
            schedule_config = ScheduleConfig(
                mode=schedule_dict.get('mode', 'fixed'),
                fixed_schedule=fixed_schedule,
                sun_schedule=sun_schedule
            )
            
            playback_config = PlaybackConfig(**config_dict.get('playback', {}))
            folder_config = FolderConfig(**config_dict.get('folders', {}))
            logging_config = LoggingConfig(**config_dict.get('logging', {}))
            web_config = WebConfig(**config_dict.get('web', {}))

            return AppConfig(
                display=display_config,
                schedule=schedule_config,
                playback=playback_config,
                folders=folder_config,
                logging=logging_config,
                web=web_config
            )
        except Exception as e:
            self.logger.error(f"Failed to create config object: {e}")
            self.logger.info("Using default configuration")
            return AppConfig()
    
    def _validate_config(self, config: AppConfig) -> None:
        """Validate configuration values."""
        errors = []
        
        # Validate display settings
        if config.display.monitor_index < 0:
            errors.append("monitor_index must be >= 0")
        
        if config.display.hide_cursor_after_ms < 0:
            errors.append("hide_cursor_after_ms must be >= 0")
        
        # Validate schedule settings
        if config.schedule.mode not in ['fixed', 'sun']:
            errors.append("schedule.mode must be 'fixed' or 'sun'")
        
        # Validate playback settings
        if config.playback.interval_seconds <= 0:
            errors.append("interval_seconds must be > 0")
        
        if config.playback.fit_mode not in ['cover', 'fit']:
            errors.append("fit_mode must be 'cover' or 'fit'")
        
        if config.playback.transition_ms < 0:
            errors.append("transition_ms must be >= 0")
        
        # Validate folder paths
        day_path = Path(config.folders.day)
        night_path = Path(config.folders.night)
        
        if not day_path.exists():
            self.logger.warning(f"Day folder does not exist: {config.folders.day}")
        
        if not night_path.exists():
            self.logger.warning(f"Night folder does not exist: {config.folders.night}")
        
        # Validate logging settings
        if config.logging.level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            errors.append("logging.level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        
        if config.logging.max_file_size_mb <= 0:
            errors.append("max_file_size_mb must be > 0")
        
        if config.logging.backup_count < 0:
            errors.append("backup_count must be >= 0")
        
        if errors:
            error_msg = "Configuration validation errors: " + "; ".join(errors)
            self.logger.error(error_msg)
            raise ValueError(error_msg)
    
    @property
    def config(self) -> Optional[AppConfig]:
        """Get the current configuration."""
        return self._config


def create_cli_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Dual Carousel Slideshow - Display images from day/night folders on secondary monitor"
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration file (YAML or JSON)'
    )
    
    parser.add_argument(
        '--monitor-index',
        type=int,
        help='Monitor index to display on (0=primary, 1=secondary, etc.)'
    )
    
    parser.add_argument(
        '--day-folder',
        type=str,
        help='Path to day images folder'
    )
    
    parser.add_argument(
        '--night-folder',
        type=str,
        help='Path to night images folder'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        help='Image display interval in seconds'
    )
    
    parser.add_argument(
        '--shuffle',
        action='store_true',
        help='Enable shuffle mode'
    )
    
    parser.add_argument(
        '--no-shuffle',
        action='store_true',
        help='Disable shuffle mode'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level'
    )
    
    parser.add_argument(
        '--force-day',
        action='store_true',
        help='Force day mode (for Task Scheduler integration)'
    )
    
    parser.add_argument(
        '--force-night',
        action='store_true',
        help='Force night mode (for Task Scheduler integration)'
    )
    
    return parser