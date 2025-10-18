"""
Scheduling system for day/night carousel switching.

This module handles time-based mode determination using either fixed schedules
or astronomical sunrise/sunset calculations with support for manual overrides.
"""
import logging
from datetime import datetime, time, timedelta
from typing import Optional, Tuple
from astral import LocationInfo
from astral.sun import sun

from ..config.models import CarouselMode, ScheduleMode, ScheduleConfig


class Scheduler:
    """
    Manages day/night scheduling with support for fixed times and astronomical calculations.
    
    Handles:
    - Fixed schedule time calculations
    - Astronomical sunrise/sunset calculations using Astral
    - Manual override functionality
    - Daily sun time recalculation logic
    - Midnight boundary crossing logic
    - Offset support for sunrise/sunset times
    """
    
    def __init__(self, config: ScheduleConfig):
        """
        Initialize the scheduler with configuration.
        
        Args:
            config: Schedule configuration containing mode and schedule details
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._manual_override: Optional[CarouselMode] = None
        self._manual_override_until: Optional[datetime] = None
        self._cached_sun_times: Optional[Tuple[datetime, datetime]] = None
        self._cached_sun_date: Optional[datetime] = None
        
        # Create location info for astronomical calculations
        if config.mode == ScheduleMode.SUN.value:
            self._location = LocationInfo(
                name="Slideshow Location",
                region="Custom",
                timezone="UTC",  # We'll work in local time
                latitude=config.sun_schedule.latitude,
                longitude=config.sun_schedule.longitude
            )
        else:
            self._location = None
            
        self.logger.info(f"Scheduler initialized with mode: {config.mode}")
    
    def get_current_mode(self, current_time: Optional[datetime] = None) -> CarouselMode:
        """
        Determine the current carousel mode based on time and configuration.
        
        Args:
            current_time: Current time (defaults to now if not provided)
            
        Returns:
            Current carousel mode (DAY or NIGHT)
        """
        if current_time is None:
            current_time = datetime.now()
            
        # Check for active manual override
        if self._manual_override and self._is_manual_override_active(current_time):
            self.logger.debug(f"Using manual override: {self._manual_override.value}")
            return self._manual_override
            
        # Clear expired manual override
        if self._manual_override and not self._is_manual_override_active(current_time):
            self.logger.info("Manual override expired, returning to scheduled mode")
            self._manual_override = None
            self._manual_override_until = None
            
        # Determine mode based on schedule type
        if self.config.mode == ScheduleMode.FIXED.value:
            return self._get_fixed_schedule_mode(current_time)
        elif self.config.mode == ScheduleMode.SUN.value:
            return self._get_sun_schedule_mode(current_time)
        else:
            self.logger.warning(f"Unknown schedule mode: {self.config.mode}, defaulting to DAY")
            return CarouselMode.DAY
    
    def calculate_next_switch_time(self, current_time: Optional[datetime] = None) -> datetime:
        """
        Calculate when the next mode switch will occur.
        
        Args:
            current_time: Current time (defaults to now if not provided)
            
        Returns:
            Datetime of the next scheduled mode switch
        """
        if current_time is None:
            current_time = datetime.now()
            
        # If manual override is active, next switch is when it expires
        if self._manual_override and self._is_manual_override_active(current_time):
            return self._manual_override_until
            
        if self.config.mode == ScheduleMode.FIXED.value:
            return self._calculate_next_fixed_switch(current_time)
        elif self.config.mode == ScheduleMode.SUN.value:
            return self._calculate_next_sun_switch(current_time)
        else:
            # Default to checking again in 1 hour
            return current_time + timedelta(hours=1)
    
    def set_manual_override(self, mode: CarouselMode, current_time: Optional[datetime] = None):
        """
        Set manual override mode until the next scheduled change.
        
        Args:
            mode: Carousel mode to force
            current_time: Current time (defaults to now if not provided)
        """
        if current_time is None:
            current_time = datetime.now()
            
        next_switch = self.calculate_next_switch_time(current_time)
        self._manual_override = mode
        self._manual_override_until = next_switch
        
        self.logger.info(f"Manual override set to {mode.value} until {next_switch}")
    
    def clear_manual_override(self):
        """Clear any active manual override."""
        if self._manual_override:
            self.logger.info(f"Clearing manual override: {self._manual_override.value}")
            self._manual_override = None
            self._manual_override_until = None
    
    def update_sun_times(self, date: Optional[datetime] = None):
        """
        Update cached sun times for the specified date.
        
        Args:
            date: Date to calculate sun times for (defaults to today)
        """
        if self.config.mode != ScheduleMode.SUN.value or not self._location:
            return
            
        if date is None:
            date = datetime.now()
            
        # Only recalculate if we don't have cached times for this date
        if (self._cached_sun_date is None or 
            self._cached_sun_date.date() != date.date()):
            
            try:
                sun_times = sun(self._location.observer, date=date.date())
                
                # Get sunrise and sunset times
                sunrise_utc = sun_times['sunrise']
                sunset_utc = sun_times['sunset']
                
                # For simplicity, we'll assume the user wants local solar time
                # Convert UTC to local time by applying timezone offset
                # This is a simplified approach - for production use, proper timezone handling is recommended
                
                # Calculate approximate local solar time offset based on longitude
                # Each 15 degrees of longitude represents 1 hour of time difference from UTC
                longitude_offset_hours = self.config.sun_schedule.longitude / 15.0
                longitude_offset = timedelta(hours=longitude_offset_hours)
                
                # Apply longitude offset to get approximate local solar time
                sunrise = sunrise_utc + longitude_offset
                sunset = sunset_utc + longitude_offset
                
                # Remove timezone info for local comparison
                sunrise = sunrise.replace(tzinfo=None)
                sunset = sunset.replace(tzinfo=None)
                
                # Ensure both times are on the same date as requested
                sunrise = sunrise.replace(year=date.year, month=date.month, day=date.day)
                sunset = sunset.replace(year=date.year, month=date.month, day=date.day)
                
                # Handle edge case where sunset might be before sunrise (shouldn't happen with proper calculation)
                if sunset <= sunrise:
                    sunset = sunset + timedelta(days=1)
                
                # Apply user-defined offsets
                sunrise += timedelta(minutes=self.config.sun_schedule.day_offset_minutes)
                sunset += timedelta(minutes=self.config.sun_schedule.night_offset_minutes)
                
                self._cached_sun_times = (sunrise, sunset)
                self._cached_sun_date = date
                
                self.logger.info(f"Updated sun times for {date.date()}: "
                               f"sunrise={sunrise.time()}, sunset={sunset.time()}")
                               
            except Exception as e:
                self.logger.error(f"Failed to calculate sun times: {e}")
                # Fallback to previous cached times or default times
                if self._cached_sun_times is None:
                    # Use default times as fallback
                    default_sunrise = datetime.combine(date.date(), time(6, 0))
                    default_sunset = datetime.combine(date.date(), time(18, 0))
                    self._cached_sun_times = (default_sunrise, default_sunset)
                    self._cached_sun_date = date
    
    def _is_manual_override_active(self, current_time: datetime) -> bool:
        """Check if manual override is still active."""
        return (self._manual_override is not None and 
                self._manual_override_until is not None and
                current_time < self._manual_override_until)
    
    def _get_fixed_schedule_mode(self, current_time: datetime) -> CarouselMode:
        """
        Determine mode based on fixed schedule times.
        
        Args:
            current_time: Current time
            
        Returns:
            Current carousel mode based on fixed schedule
        """
        try:
            day_start = time.fromisoformat(self.config.fixed_schedule.day_start)
            night_start = time.fromisoformat(self.config.fixed_schedule.night_start)
        except ValueError as e:
            self.logger.error(f"Invalid time format in fixed schedule: {e}")
            return CarouselMode.DAY
            
        current_time_only = current_time.time()

        # Handle normal case where day_start < night_start (e.g., 06:00 to 18:00)
        if day_start < night_start:
            if day_start <= current_time_only < night_start:
                self.logger.info(f"Schedule check: {current_time_only} is between {day_start} and {night_start} → DAY mode")
                return CarouselMode.DAY
            else:
                self.logger.info(f"Schedule check: {current_time_only} is outside {day_start}-{night_start} → NIGHT mode")
                return CarouselMode.NIGHT
        # Handle midnight crossing case where night_start < day_start (e.g., 18:00 to 06:00)
        else:
            if night_start <= current_time_only or current_time_only < day_start:
                self.logger.info(f"Schedule check (midnight crossing): {current_time_only} → NIGHT mode")
                return CarouselMode.NIGHT
            else:
                self.logger.info(f"Schedule check (midnight crossing): {current_time_only} → DAY mode")
                return CarouselMode.DAY
    
    def _get_sun_schedule_mode(self, current_time: datetime) -> CarouselMode:
        """
        Determine mode based on astronomical sunrise/sunset times.
        
        Args:
            current_time: Current time
            
        Returns:
            Current carousel mode based on sun schedule
        """
        # Ensure we have current sun times
        self.update_sun_times(current_time)
        
        if not self._cached_sun_times:
            self.logger.warning("No sun times available, defaulting to DAY mode")
            return CarouselMode.DAY
            
        sunrise, sunset = self._cached_sun_times
        
        # Convert to same date as current_time for comparison
        sunrise = sunrise.replace(year=current_time.year, 
                                month=current_time.month, 
                                day=current_time.day)
        sunset = sunset.replace(year=current_time.year, 
                              month=current_time.month, 
                              day=current_time.day)
        
        # Determine mode based on sun times
        if sunrise <= current_time < sunset:
            return CarouselMode.DAY
        else:
            return CarouselMode.NIGHT
    
    def _calculate_next_fixed_switch(self, current_time: datetime) -> datetime:
        """
        Calculate next switch time for fixed schedule.
        
        Args:
            current_time: Current time
            
        Returns:
            Next switch time
        """
        try:
            day_start = time.fromisoformat(self.config.fixed_schedule.day_start)
            night_start = time.fromisoformat(self.config.fixed_schedule.night_start)
        except ValueError as e:
            self.logger.error(f"Invalid time format in fixed schedule: {e}")
            return current_time + timedelta(hours=1)
            
        current_date = current_time.date()
        current_time_only = current_time.time()
        
        # Create datetime objects for today's switch times
        today_day_start = datetime.combine(current_date, day_start)
        today_night_start = datetime.combine(current_date, night_start)
        
        # Handle normal case where day_start < night_start
        if day_start < night_start:
            if current_time_only < day_start:
                return today_day_start
            elif current_time_only < night_start:
                return today_night_start
            else:
                # Next switch is tomorrow's day start
                return today_day_start + timedelta(days=1)
        # Handle midnight crossing case
        else:
            if current_time_only < day_start:
                return today_day_start
            elif current_time_only < night_start:
                return today_night_start
            else:
                # Next switch is tomorrow's day start
                return today_day_start + timedelta(days=1)
    
    def _calculate_next_sun_switch(self, current_time: datetime) -> datetime:
        """
        Calculate next switch time for sun schedule.
        
        Args:
            current_time: Current time
            
        Returns:
            Next switch time
        """
        # Ensure we have current sun times
        self.update_sun_times(current_time)
        
        if not self._cached_sun_times:
            # Fallback to checking again in 1 hour
            return current_time + timedelta(hours=1)
            
        sunrise, sunset = self._cached_sun_times
        
        # Convert to same date as current_time
        today_sunrise = sunrise.replace(year=current_time.year,
                                      month=current_time.month,
                                      day=current_time.day)
        today_sunset = sunset.replace(year=current_time.year,
                                    month=current_time.month,
                                    day=current_time.day)
        
        # Determine next switch time
        if current_time < today_sunrise:
            return today_sunrise
        elif current_time < today_sunset:
            return today_sunset
        else:
            # Next switch is tomorrow's sunrise
            tomorrow = current_time + timedelta(days=1)
            self.update_sun_times(tomorrow)
            if self._cached_sun_times:
                tomorrow_sunrise, _ = self._cached_sun_times
                return tomorrow_sunrise.replace(year=tomorrow.year,
                                              month=tomorrow.month,
                                              day=tomorrow.day)
            else:
                # Fallback
                return current_time + timedelta(hours=1)