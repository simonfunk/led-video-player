"""
Data models for configuration using dataclasses for type safety.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class CarouselMode(Enum):
    """Enum for carousel modes."""
    DAY = "day"
    NIGHT = "night"


class ScheduleMode(Enum):
    """Enum for schedule modes."""
    FIXED = "fixed"
    SUN = "sun"


class FitMode(Enum):
    """Enum for image fit modes."""
    COVER = "cover"
    FIT = "fit"


@dataclass
class FixedScheduleConfig:
    """Configuration for fixed time schedule."""
    day_start: str = "06:00"
    night_start: str = "18:00"


@dataclass
class SunScheduleConfig:
    """Configuration for sun-based schedule."""
    latitude: float = 40.7128
    longitude: float = -74.0060
    day_offset_minutes: int = 0
    night_offset_minutes: int = 0


@dataclass
class DisplayConfig:
    """Configuration for display settings."""
    monitor_index: int = 1
    always_on_top: bool = True
    hide_cursor_after_ms: int = 2000
    background_color: str = "#000000"


@dataclass
class ScheduleConfig:
    """Configuration for scheduling."""
    mode: str = "fixed"
    fixed_schedule: FixedScheduleConfig = field(default_factory=FixedScheduleConfig)
    sun_schedule: SunScheduleConfig = field(default_factory=SunScheduleConfig)


@dataclass
class PlaybackConfig:
    """Configuration for playback settings."""
    interval_seconds: int = 60
    shuffle: bool = True
    fit_mode: str = "cover"
    transition_ms: int = 300
    reload_images_every_seconds: int = 300
    resume_index_between_runs: bool = True


@dataclass
class FolderConfig:
    """Configuration for image folders."""
    day: str = "./images/day"
    night: str = "./images/night"
    include_subfolders: bool = True


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    level: str = "INFO"
    log_to_file: bool = True
    log_file_path: str = "./logs/slideshow.log"
    max_file_size_mb: int = 10
    backup_count: int = 5
    log_to_console: bool = True


@dataclass
class AppConfig:
    """Main application configuration."""
    display: DisplayConfig = field(default_factory=DisplayConfig)
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)
    playback: PlaybackConfig = field(default_factory=PlaybackConfig)
    folders: FolderConfig = field(default_factory=FolderConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


@dataclass
class MonitorInfo:
    """Information about a monitor."""
    index: int
    x: int
    y: int
    width: int
    height: int
    is_primary: bool


@dataclass
class CarouselState:
    """State of a carousel."""
    current_index: int = 0
    image_paths: List[str] = field(default_factory=list)
    shuffle_order: List[int] = field(default_factory=list)
    last_reload_time: Optional[str] = None


@dataclass
class ApplicationState:
    """Application runtime state."""
    current_mode: str = "day"
    is_paused: bool = False
    manual_override: Optional[str] = None
    last_image_change: Optional[str] = None
    day_carousel: CarouselState = field(default_factory=CarouselState)
    night_carousel: CarouselState = field(default_factory=CarouselState)