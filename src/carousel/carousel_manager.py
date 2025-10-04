"""
Carousel management system for the dual carousel slideshow.

This module handles:
- Carousel state management for day and night collections
- Shuffle and sequential ordering logic
- Navigation functionality (next, previous, jump to index)
- Resume state persistence between application runs
- Auto-reload functionality with periodic folder scanning
"""
import os
import json
import random
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from threading import Lock, Thread, Event
import time

from src.config.models import CarouselMode, CarouselState, PlaybackConfig, FolderConfig
from src.images.image_manager import ImageManager
from src.error_handling.error_handler import (
    handle_folder_error, error_handler, ErrorCategory, ErrorInfo, ErrorSeverity
)


logger = logging.getLogger(__name__)


class Carousel:
    """Represents a single carousel (day or night) with its images and state."""
    
    def __init__(self, mode: CarouselMode, folder_path: str, shuffle: bool = True):
        """
        Initialize a carousel.
        
        Args:
            mode: CarouselMode (DAY or NIGHT)
            folder_path: Path to the folder containing images
            shuffle: Whether to shuffle the image order
        """
        self.mode = mode
        self.folder_path = folder_path
        self.shuffle = shuffle
        self.image_paths: List[str] = []
        self.shuffle_order: List[int] = []
        self.current_index = 0
        self.last_reload_time: Optional[datetime] = None
        self._lock = Lock()
    
    def load_images(self, image_manager: ImageManager, include_subfolders: bool = True) -> int:
        """
        Load images from the folder with comprehensive error handling.
        
        Args:
            image_manager: ImageManager instance for scanning folders
            include_subfolders: Whether to include subfolders
            
        Returns:
            Number of images loaded
        """
        with self._lock:
            try:
                # Check if folder exists
                if not os.path.exists(self.folder_path):
                    error_info = ErrorInfo(
                        category=ErrorCategory.FOLDER_ACCESS,
                        severity=ErrorSeverity.MEDIUM,
                        message=f"Carousel folder does not exist: {self.folder_path}",
                        context={
                            'carousel_mode': self.mode.value,
                            'folder_path': self.folder_path,
                            'operation': 'load_images'
                        }
                    )
                    error_handler.handle_error(error_info)
                    self.image_paths = []
                    self.shuffle_order = []
                    self.current_index = 0
                    return 0
                
                # Scan folder for images
                self.image_paths = image_manager.scan_folder(self.folder_path, include_subfolders)
                self.last_reload_time = datetime.now()
                
                # Handle empty folder case
                if not self.image_paths:
                    error_info = ErrorInfo(
                        category=ErrorCategory.FOLDER_ACCESS,
                        severity=ErrorSeverity.MEDIUM,
                        message=f"No images found in {self.mode.value} folder: {self.folder_path}",
                        context={
                            'carousel_mode': self.mode.value,
                            'folder_path': self.folder_path,
                            'include_subfolders': include_subfolders,
                            'operation': 'load_images'
                        }
                    )
                    error_handler.handle_error(error_info)
                    self.current_index = 0
                    self.shuffle_order = []
                    logger.warning(f"Empty {self.mode.value} carousel: {self.folder_path}")
                    return 0
                
                # Generate shuffle order and validate index
                self._generate_shuffle_order()
                if self.current_index >= len(self.image_paths):
                    self.current_index = 0
                
                logger.info(f"Loaded {len(self.image_paths)} images for {self.mode.value} carousel")
                return len(self.image_paths)
                
            except Exception as e:
                handle_folder_error(self.folder_path, e)
                self.image_paths = []
                self.shuffle_order = []
                self.current_index = 0
                return 0
    
    def _generate_shuffle_order(self):
        """Generate a new shuffle order for the images."""
        if not self.image_paths:
            self.shuffle_order = []
            return
        
        if self.shuffle:
            # Create shuffled order
            self.shuffle_order = list(range(len(self.image_paths)))
            random.shuffle(self.shuffle_order)
        else:
            # Sequential order
            self.shuffle_order = list(range(len(self.image_paths)))
    
    def get_current_image_path(self) -> Optional[str]:
        """Get the path of the current image with error handling."""
        with self._lock:
            return self._get_current_image_path_internal(max_attempts=len(self.image_paths) + 1)
    
    def _get_current_image_path_internal(self, max_attempts: int) -> Optional[str]:
        """Internal method to get current image path with recursion limit."""
        try:
            if not self.image_paths or self.current_index >= len(self.shuffle_order) or max_attempts <= 0:
                return None
            
            actual_index = self.shuffle_order[self.current_index]
            if actual_index >= len(self.image_paths):
                logger.error(f"Invalid image index {actual_index} for {len(self.image_paths)} images")
                self.current_index = 0
                if self.shuffle_order:
                    actual_index = self.shuffle_order[0]
                    return self.image_paths[actual_index] if actual_index < len(self.image_paths) else None
                return None
            
            image_path = self.image_paths[actual_index]
            
            # Verify the image file still exists
            if not os.path.exists(image_path):
                logger.warning(f"Image file no longer exists: {image_path}")
                # Remove from list and try next image
                self.image_paths.pop(actual_index)
                self._generate_shuffle_order()
                if self.current_index >= len(self.shuffle_order):
                    self.current_index = 0
                # Recursive call with decremented attempts counter
                return self._get_current_image_path_internal(max_attempts - 1)
            
            return image_path
            
        except Exception as e:
            logger.error(f"Error getting current image path: {e}")
            return None
    
    def get_image_path_at_index(self, index: int) -> Optional[str]:
        """Get the path of the image at the specified index."""
        with self._lock:
            if not self.image_paths or index < 0 or index >= len(self.shuffle_order):
                return None
            
            actual_index = self.shuffle_order[index]
            return self.image_paths[actual_index]
    
    def advance(self) -> Optional[str]:
        """Advance to the next image and return its path."""
        with self._lock:
            if not self.image_paths:
                return None
            
            self.current_index = (self.current_index + 1) % len(self.shuffle_order)
            # Call internal method to avoid nested lock acquisition
            return self._get_current_image_path_internal(max_attempts=len(self.image_paths) + 1)
    
    def previous(self) -> Optional[str]:
        """Go to the previous image and return its path."""
        with self._lock:
            if not self.image_paths:
                return None
            
            self.current_index = (self.current_index - 1) % len(self.shuffle_order)
            # Call internal method to avoid nested lock acquisition
            return self._get_current_image_path_internal(max_attempts=len(self.image_paths) + 1)
    
    def jump_to_index(self, index: int) -> Optional[str]:
        """Jump to a specific index and return the image path."""
        with self._lock:
            if not self.image_paths or index < 0 or index >= len(self.shuffle_order):
                return None
            
            self.current_index = index
            # Call internal method to avoid nested lock acquisition
            return self._get_current_image_path_internal(max_attempts=len(self.image_paths) + 1)
    
    def get_state(self) -> CarouselState:
        """Get the current state of the carousel."""
        with self._lock:
            return CarouselState(
                current_index=self.current_index,
                image_paths=self.image_paths.copy(),
                shuffle_order=self.shuffle_order.copy(),
                last_reload_time=self.last_reload_time.isoformat() if self.last_reload_time else None
            )
    
    def set_state(self, state: CarouselState):
        """Set the carousel state from a CarouselState object."""
        with self._lock:
            self.current_index = state.current_index
            self.image_paths = state.image_paths.copy()
            self.shuffle_order = state.shuffle_order.copy()
            
            if state.last_reload_time:
                try:
                    self.last_reload_time = datetime.fromisoformat(state.last_reload_time)
                except ValueError:
                    self.last_reload_time = None
            else:
                self.last_reload_time = None
            
            # Validate current index
            if self.current_index >= len(self.shuffle_order):
                self.current_index = 0
    
    def get_image_count(self) -> int:
        """Get the total number of images in the carousel."""
        with self._lock:
            return len(self.image_paths)
    
    def is_empty(self) -> bool:
        """Check if the carousel has no images."""
        with self._lock:
            return len(self.image_paths) == 0


class CarouselManager:
    """Manages day and night carousels with navigation and state persistence."""
    
    def __init__(self, playback_config: PlaybackConfig, folder_config: FolderConfig, 
                 image_manager: ImageManager, state_file_path: str = "./carousel_state.json"):
        """
        Initialize the carousel manager.
        
        Args:
            playback_config: Playback configuration
            folder_config: Folder configuration
            image_manager: ImageManager instance
            state_file_path: Path to save/load carousel state
        """
        self.playback_config = playback_config
        self.folder_config = folder_config
        self.image_manager = image_manager
        self.state_file_path = state_file_path
        
        # Create carousels
        self.day_carousel = Carousel(CarouselMode.DAY, folder_config.day, playback_config.shuffle)
        self.night_carousel = Carousel(CarouselMode.NIGHT, folder_config.night, playback_config.shuffle)
        
        self.current_mode = CarouselMode.DAY
        self._lock = Lock()
        
        # Auto-reload functionality
        self._auto_reload_thread: Optional[Thread] = None
        self._auto_reload_running = False
        self._auto_reload_event = Event()
        
        # Load initial images
        self._load_all_carousels()
        
        # Load resume state if enabled
        if self.playback_config.resume_index_between_runs:
            self.load_resume_state()
    
    def _load_all_carousels(self):
        """Load images for both carousels."""
        self.day_carousel.load_images(self.image_manager, self.folder_config.include_subfolders)
        self.night_carousel.load_images(self.image_manager, self.folder_config.include_subfolders)
    
    def get_current_carousel(self) -> Carousel:
        """Get the currently active carousel."""
        with self._lock:
            return self.day_carousel if self.current_mode == CarouselMode.DAY else self.night_carousel
    
    def switch_carousel(self, mode: CarouselMode):
        """Switch to the specified carousel mode."""
        with self._lock:
            if self.current_mode != mode:
                self.current_mode = mode
                logger.info(f"Switched to {mode.value} carousel")
    
    def get_current_image_path(self) -> Optional[str]:
        """Get the path of the current image from the active carousel."""
        return self.get_current_carousel().get_current_image_path()
    
    def advance_image(self) -> Optional[str]:
        """Advance to the next image in the current carousel."""
        return self.get_current_carousel().advance()
    
    def previous_image(self) -> Optional[str]:
        """Go to the previous image in the current carousel."""
        return self.get_current_carousel().previous()
    
    def jump_to_index(self, index: int) -> Optional[str]:
        """Jump to a specific index in the current carousel."""
        return self.get_current_carousel().jump_to_index(index)
    
    def get_current_image_info(self) -> Dict[str, Any]:
        """Get information about the current image and carousel state."""
        carousel = self.get_current_carousel()
        return {
            'mode': self.current_mode.value,
            'current_index': carousel.current_index,
            'total_images': carousel.get_image_count(),
            'current_image_path': carousel.get_current_image_path(),
            'is_empty': carousel.is_empty()
        }
    
    def save_resume_state(self):
        """Save the current carousel state to disk for resume functionality."""
        if not self.playback_config.resume_index_between_runs:
            return
        
        try:
            state_data = {
                'current_mode': self.current_mode.value,
                'day_carousel': self.day_carousel.get_state().__dict__,
                'night_carousel': self.night_carousel.get_state().__dict__,
                'saved_at': datetime.now().isoformat()
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.state_file_path), exist_ok=True)
            
            with open(self.state_file_path, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            logger.debug(f"Saved carousel state to {self.state_file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save carousel state: {e}")
    
    def load_resume_state(self):
        """Load the carousel state from disk for resume functionality."""
        if not self.playback_config.resume_index_between_runs:
            return
        
        try:
            if not os.path.exists(self.state_file_path):
                logger.debug("No resume state file found")
                return
            
            with open(self.state_file_path, 'r') as f:
                state_data = json.load(f)
            
            # Restore current mode
            if 'current_mode' in state_data:
                try:
                    self.current_mode = CarouselMode(state_data['current_mode'])
                except ValueError:
                    logger.warning(f"Invalid carousel mode in state: {state_data['current_mode']}")
            
            # Restore carousel states
            if 'day_carousel' in state_data:
                day_state = CarouselState(**state_data['day_carousel'])
                self.day_carousel.set_state(day_state)
            
            if 'night_carousel' in state_data:
                night_state = CarouselState(**state_data['night_carousel'])
                self.night_carousel.set_state(night_state)
            
            logger.info(f"Loaded carousel resume state from {self.state_file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load carousel state: {e}")
    
    def start_auto_reload(self):
        """Start the auto-reload functionality for periodic folder scanning."""
        if self.playback_config.reload_images_every_seconds <= 0:
            logger.debug("Auto-reload disabled (interval <= 0)")
            return
        
        if self._auto_reload_running:
            logger.debug("Auto-reload already running")
            return
        
        self._auto_reload_running = True
        self._auto_reload_event.clear()
        self._auto_reload_thread = Thread(target=self._auto_reload_worker, daemon=True)
        self._auto_reload_thread.start()
        
        logger.info(f"Started auto-reload with {self.playback_config.reload_images_every_seconds}s interval")
    
    def stop_auto_reload(self):
        """Stop the auto-reload functionality."""
        if not self._auto_reload_running:
            return
        
        self._auto_reload_running = False
        self._auto_reload_event.set()
        
        if self._auto_reload_thread and self._auto_reload_thread.is_alive():
            self._auto_reload_thread.join(timeout=2.0)
        
        logger.info("Stopped auto-reload")
    
    def _auto_reload_worker(self):
        """Background worker for auto-reloading images."""
        while self._auto_reload_running:
            try:
                # Wait for the reload interval or stop event
                if self._auto_reload_event.wait(timeout=self.playback_config.reload_images_every_seconds):
                    # Stop event was set
                    break
                
                if not self._auto_reload_running:
                    break
                
                # Reload images
                self.reload_images()
                
            except Exception as e:
                logger.error(f"Error in auto-reload worker: {e}")
    
    def reload_images(self) -> Dict[str, int]:
        """
        Manually reload images from folders and handle dynamic updates.
        
        Returns:
            Dictionary with reload results for each carousel
        """
        logger.info("Reloading images from folders")
        
        # Store current image paths to detect changes
        day_current_path = self.day_carousel.get_current_image_path()
        night_current_path = self.night_carousel.get_current_image_path()
        
        # Reload both carousels
        day_count = self.day_carousel.load_images(self.image_manager, self.folder_config.include_subfolders)
        night_count = self.night_carousel.load_images(self.image_manager, self.folder_config.include_subfolders)
        
        # Handle current image position after reload
        self._handle_image_list_changes(self.day_carousel, day_current_path)
        self._handle_image_list_changes(self.night_carousel, night_current_path)
        
        result = {
            'day_images': day_count,
            'night_images': night_count,
            'reloaded_at': datetime.now().isoformat()
        }
        
        logger.info(f"Reload complete: {day_count} day images, {night_count} night images")
        return result
    
    def _handle_image_list_changes(self, carousel: Carousel, previous_current_path: Optional[str]):
        """
        Handle changes to the image list during reload.
        
        Args:
            carousel: The carousel that was reloaded
            previous_current_path: The path of the image that was current before reload
        """
        if not previous_current_path or not carousel.image_paths:
            return
        
        # Try to find the previous current image in the new list
        try:
            new_index = carousel.image_paths.index(previous_current_path)
            # Find the position in shuffle order
            if new_index in carousel.shuffle_order:
                carousel.current_index = carousel.shuffle_order.index(new_index)
            else:
                # Image was removed or shuffle order changed, stay at current position
                if carousel.current_index >= len(carousel.shuffle_order):
                    carousel.current_index = 0
        except ValueError:
            # Previous image no longer exists, stay at current position
            if carousel.current_index >= len(carousel.shuffle_order):
                carousel.current_index = 0
    
    def get_carousel_info(self) -> Dict[str, Any]:
        """Get comprehensive information about both carousels."""
        return {
            'current_mode': self.current_mode.value,
            'day_carousel': {
                'image_count': self.day_carousel.get_image_count(),
                'current_index': self.day_carousel.current_index,
                'is_empty': self.day_carousel.is_empty(),
                'folder_path': self.day_carousel.folder_path,
                'last_reload': self.day_carousel.last_reload_time.isoformat() if self.day_carousel.last_reload_time else None
            },
            'night_carousel': {
                'image_count': self.night_carousel.get_image_count(),
                'current_index': self.night_carousel.current_index,
                'is_empty': self.night_carousel.is_empty(),
                'folder_path': self.night_carousel.folder_path,
                'last_reload': self.night_carousel.last_reload_time.isoformat() if self.night_carousel.last_reload_time else None
            },
            'auto_reload_running': self._auto_reload_running,
            'resume_enabled': self.playback_config.resume_index_between_runs
        }
    
    def cleanup(self):
        """Clean up resources and save state."""
        logger.info("Cleaning up carousel manager")
        
        # Stop auto-reload
        self.stop_auto_reload()
        
        # Save resume state
        self.save_resume_state()
        
        logger.info("Carousel manager cleanup completed")