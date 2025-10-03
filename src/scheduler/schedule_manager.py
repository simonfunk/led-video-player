"""
Schedule manager for integrating scheduler with the application.

This module provides a higher-level interface for managing scheduling
and integrating with other application components.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable

from .scheduler import Scheduler
from ..config.models import CarouselMode, ScheduleConfig


class ScheduleManager:
    """
    High-level manager for scheduling functionality.
    
    Provides integration between the scheduler and application components,
    including automatic mode switching and callback notifications.
    """
    
    def __init__(self, config: ScheduleConfig, mode_change_callback: Optional[Callable[[CarouselMode], None]] = None):
        """
        Initialize the schedule manager.
        
        Args:
            config: Schedule configuration
            mode_change_callback: Optional callback function called when mode changes
        """
        self.scheduler = Scheduler(config)
        self.mode_change_callback = mode_change_callback
        self.logger = logging.getLogger(__name__)
        
        self._current_mode: Optional[CarouselMode] = None
        self._last_check_time: Optional[datetime] = None
        self._next_switch_time: Optional[datetime] = None
        
        # Initialize current mode
        self._update_current_mode()
        
    def get_current_mode(self) -> CarouselMode:
        """
        Get the current carousel mode.
        
        Returns:
            Current carousel mode
        """
        return self._current_mode or CarouselMode.DAY
    
    def check_for_mode_change(self, current_time: Optional[datetime] = None) -> bool:
        """
        Check if the mode should change and update if necessary.
        
        Args:
            current_time: Current time (defaults to now if not provided)
            
        Returns:
            True if mode changed, False otherwise
        """
        if current_time is None:
            current_time = datetime.now()
            
        # Update sun times daily if using sun schedule
        if (self._last_check_time is None or 
            current_time.date() != self._last_check_time.date()):
            self.scheduler.update_sun_times(current_time)
            
        # Check if mode has changed
        new_mode = self.scheduler.get_current_mode(current_time)
        mode_changed = new_mode != self._current_mode
        
        if mode_changed:
            old_mode = self._current_mode
            self._current_mode = new_mode
            self._next_switch_time = self.scheduler.calculate_next_switch_time(current_time)
            
            self.logger.info(f"Mode changed from {old_mode} to {new_mode}")
            
            # Notify callback if provided
            if self.mode_change_callback:
                try:
                    self.mode_change_callback(new_mode)
                except Exception as e:
                    self.logger.error(f"Error in mode change callback: {e}")
        
        self._last_check_time = current_time
        return mode_changed
    
    def get_next_switch_time(self) -> Optional[datetime]:
        """
        Get the time of the next scheduled mode switch.
        
        Returns:
            Next switch time or None if not calculated yet
        """
        return self._next_switch_time
    
    def get_time_until_next_switch(self, current_time: Optional[datetime] = None) -> Optional[timedelta]:
        """
        Get the time remaining until the next mode switch.
        
        Args:
            current_time: Current time (defaults to now if not provided)
            
        Returns:
            Time remaining until next switch or None if not available
        """
        if current_time is None:
            current_time = datetime.now()
            
        if self._next_switch_time is None:
            self._next_switch_time = self.scheduler.calculate_next_switch_time(current_time)
            
        if self._next_switch_time:
            return self._next_switch_time - current_time
        return None
    
    def force_day_mode(self):
        """Force day mode until the next scheduled change."""
        self.scheduler.set_manual_override(CarouselMode.DAY)
        self._update_current_mode()
        
        if self.mode_change_callback and self._current_mode == CarouselMode.DAY:
            try:
                self.mode_change_callback(CarouselMode.DAY)
            except Exception as e:
                self.logger.error(f"Error in mode change callback: {e}")
    
    def force_night_mode(self):
        """Force night mode until the next scheduled change."""
        self.scheduler.set_manual_override(CarouselMode.NIGHT)
        self._update_current_mode()
        
        if self.mode_change_callback and self._current_mode == CarouselMode.NIGHT:
            try:
                self.mode_change_callback(CarouselMode.NIGHT)
            except Exception as e:
                self.logger.error(f"Error in mode change callback: {e}")
    
    def clear_manual_override(self):
        """Clear any manual mode override."""
        self.scheduler.clear_manual_override()
        old_mode = self._current_mode
        self._update_current_mode()
        
        # Notify if mode changed after clearing override
        if self.mode_change_callback and self._current_mode != old_mode:
            try:
                self.mode_change_callback(self._current_mode)
            except Exception as e:
                self.logger.error(f"Error in mode change callback: {e}")
    
    def _update_current_mode(self):
        """Update the current mode from the scheduler."""
        self._current_mode = self.scheduler.get_current_mode()
        self._next_switch_time = self.scheduler.calculate_next_switch_time()