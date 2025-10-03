"""
Display manager for monitor detection, window creation, and cursor management.
"""
import logging
import time
from typing import List, Optional, Tuple
import pygame
import pygame.display

from src.config.models import MonitorInfo, DisplayConfig
from src.error_handling.error_handler import (
    handle_display_error, handle_system_error, error_handler,
    ErrorCategory, ErrorInfo, ErrorSeverity
)


logger = logging.getLogger(__name__)


class DisplayManager:
    """
    Manages display operations including monitor detection, window creation,
    and cursor management for the slideshow application.
    """
    
    def __init__(self, config: DisplayConfig):
        """
        Initialize the display manager.
        
        Args:
            config: Display configuration settings
        """
        self.config = config
        self.screen: Optional[pygame.Surface] = None
        self.selected_monitor: Optional[MonitorInfo] = None
        self.cursor_hidden = False
        self.last_mouse_activity = time.time()
        
        # Initialize pygame display
        pygame.display.init()
        
    def get_monitors(self) -> List[MonitorInfo]:
        """
        Detect and enumerate all available monitors with error handling.
        
        Returns:
            List of MonitorInfo objects representing available monitors
        """
        monitors = []
        
        try:
            # Initialize pygame display if not already done
            if not pygame.get_init():
                pygame.init()
            
            if not pygame.display.get_init():
                pygame.display.init()
            
            # Use retry logic for monitor detection
            success, result = error_handler.retry_operation(
                self._detect_monitors_internal,
                ErrorCategory.DISPLAY_ERROR
            )
            
            if success:
                monitors = result
            else:
                # Fallback to default monitor
                logger.warning("Monitor detection failed, using fallback monitor")
                monitors = [self._create_fallback_monitor()]
                
        except Exception as e:
            handle_display_error(e, {'operation': 'get_monitors'})
            monitors = [self._create_fallback_monitor()]
            
        logger.info(f"Detected {len(monitors)} monitor(s)")
        for monitor in monitors:
            logger.debug(f"Monitor {monitor.index}: {monitor.width}x{monitor.height} "
                        f"at ({monitor.x}, {monitor.y}), primary: {monitor.is_primary}")
            
        return monitors
    
    def _detect_monitors_internal(self) -> List[MonitorInfo]:
        """Internal monitor detection implementation."""
        monitors = []
        
        try:
            # Get display info from pygame
            display_info = pygame.display.Info()
            
            if display_info.current_w <= 0 or display_info.current_h <= 0:
                raise Exception("Invalid display dimensions detected")
            
            # Create primary monitor
            primary_monitor = MonitorInfo(
                index=0,
                x=0,
                y=0,
                width=display_info.current_w,
                height=display_info.current_h,
                is_primary=True
            )
            monitors.append(primary_monitor)
            
            # Try to detect additional monitors
            try:
                desktop_modes = pygame.display.list_modes()
                if desktop_modes and len(desktop_modes) > 1:
                    # Create a secondary monitor entry (simplified approach)
                    secondary_monitor = MonitorInfo(
                        index=1,
                        x=display_info.current_w,  # Assume side-by-side layout
                        y=0,
                        width=display_info.current_w,
                        height=display_info.current_h,
                        is_primary=False
                    )
                    monitors.append(secondary_monitor)
                    
            except Exception as e:
                logger.debug(f"Could not detect secondary monitors: {e}")
                
        except Exception as e:
            raise Exception(f"Failed to detect monitors: {e}")
            
        return monitors
    
    def _create_fallback_monitor(self) -> MonitorInfo:
        """Create a fallback monitor configuration."""
        return MonitorInfo(
            index=0,
            x=0,
            y=0,
            width=1920,  # Default resolution
            height=1080,
            is_primary=True
        )
        
    def select_monitor(self, monitors: List[MonitorInfo], preferred_index: int) -> MonitorInfo:
        """
        Select a monitor based on the preferred index with fallback logic.
        
        Args:
            monitors: List of available monitors
            preferred_index: Preferred monitor index from configuration
            
        Returns:
            Selected MonitorInfo object
        """
        if not monitors:
            raise RuntimeError("No monitors detected")
            
        # Try to use the preferred monitor index
        for monitor in monitors:
            if monitor.index == preferred_index:
                logger.info(f"Selected preferred monitor {preferred_index}")
                return monitor
                
        # Fallback 1: Use the largest non-primary monitor
        non_primary_monitors = [m for m in monitors if not m.is_primary]
        if non_primary_monitors:
            largest_monitor = max(non_primary_monitors, 
                                key=lambda m: m.width * m.height)
            logger.warning(f"Preferred monitor {preferred_index} not found, "
                          f"using largest non-primary monitor {largest_monitor.index}")
            return largest_monitor
            
        # Fallback 2: Use the largest available monitor
        largest_monitor = max(monitors, key=lambda m: m.width * m.height)
        logger.warning(f"No non-primary monitors found, "
                      f"using largest available monitor {largest_monitor.index}")
        return largest_monitor
        
    def create_fullscreen_window(self, monitor: MonitorInfo) -> pygame.Surface:
        """
        Create a fullscreen borderless window on the specified monitor with error handling.
        
        Args:
            monitor: Monitor to create the window on
            
        Returns:
            pygame.Surface representing the created window
        """
        try:
            # Use retry logic for window creation
            success, result = error_handler.retry_operation(
                self._create_window_internal,
                ErrorCategory.DISPLAY_ERROR,
                monitor
            )
            
            if success:
                self.screen = result
                self.selected_monitor = monitor
                logger.info(f"Created fullscreen window on monitor {monitor.index} "
                           f"({monitor.width}x{monitor.height})")
                return self.screen
            else:
                # Try fallback window creation
                logger.warning("Primary window creation failed, trying fallback")
                return self._create_fallback_window(monitor)
                
        except Exception as e:
            handle_display_error(e, {
                'operation': 'create_fullscreen_window',
                'monitor_index': monitor.index,
                'monitor_size': f"{monitor.width}x{monitor.height}"
            })
            return self._create_fallback_window(monitor)
    
    def _create_window_internal(self, monitor: MonitorInfo) -> pygame.Surface:
        """Internal window creation implementation."""
        try:
            # Set the window position (platform-specific)
            import os
            os.environ['SDL_VIDEO_WINDOW_POS'] = f'{monitor.x},{monitor.y}'
            
            # Validate monitor dimensions
            if monitor.width <= 0 or monitor.height <= 0:
                raise Exception(f"Invalid monitor dimensions: {monitor.width}x{monitor.height}")
            
            # Create fullscreen window
            flags = pygame.NOFRAME
            if self.config.always_on_top:
                # Note: pygame doesn't directly support always-on-top
                # This would need platform-specific implementation
                pass
                
            screen = pygame.display.set_mode(
                (monitor.width, monitor.height),
                flags
            )
            
            if screen is None:
                raise Exception("pygame.display.set_mode returned None")
            
            # Set window caption
            pygame.display.set_caption("Dual Carousel Slideshow")
            
            # Fill with background color
            bg_color = self._parse_color(self.config.background_color)
            screen.fill(bg_color)
            pygame.display.flip()
            
            return screen
            
        except pygame.error as e:
            raise Exception(f"Pygame display error: {e}")
        except Exception as e:
            raise Exception(f"Window creation error: {e}")
    
    def _create_fallback_window(self, monitor: MonitorInfo) -> pygame.Surface:
        """Create a fallback window with reduced functionality."""
        try:
            logger.warning("Creating fallback window")
            
            # Try with basic settings
            fallback_size = (min(monitor.width, 1920), min(monitor.height, 1080))
            screen = pygame.display.set_mode(fallback_size, 0)  # No special flags
            
            if screen is None:
                raise Exception("Fallback window creation failed")
            
            pygame.display.set_caption("Dual Carousel Slideshow (Fallback Mode)")
            
            # Fill with background color
            bg_color = self._parse_color(self.config.background_color)
            screen.fill(bg_color)
            pygame.display.flip()
            
            self.screen = screen
            self.selected_monitor = monitor
            
            logger.warning(f"Created fallback window: {fallback_size[0]}x{fallback_size[1]}")
            return screen
            
        except Exception as e:
            logger.critical(f"Fallback window creation failed: {e}")
            raise Exception(f"All window creation attempts failed: {e}")
            
    def set_window_properties(self, always_on_top: bool = None, hide_cursor: bool = None):
        """
        Set window properties like always-on-top and cursor visibility.
        
        Args:
            always_on_top: Whether window should stay on top (platform-specific)
            hide_cursor: Whether to hide the cursor
        """
        if always_on_top is not None:
            # Note: pygame doesn't have built-in always-on-top support
            # This would require platform-specific implementation using ctypes
            logger.debug(f"Always-on-top requested: {always_on_top}")
            
        if hide_cursor is not None:
            pygame.mouse.set_visible(not hide_cursor)
            self.cursor_hidden = hide_cursor
            logger.debug(f"Cursor visibility set to: {not hide_cursor}")
            
    def update_cursor_visibility(self):
        """
        Update cursor visibility based on inactivity timeout.
        Should be called regularly from the main loop.
        """
        current_time = time.time()
        mouse_pos = pygame.mouse.get_pos()
        
        # Check if mouse has moved (simple activity detection)
        if hasattr(self, '_last_mouse_pos'):
            if mouse_pos != self._last_mouse_pos:
                self.last_mouse_activity = current_time
                if self.cursor_hidden:
                    pygame.mouse.set_visible(True)
                    self.cursor_hidden = False
                    logger.debug("Mouse activity detected, showing cursor")
        
        self._last_mouse_pos = mouse_pos
        
        # Hide cursor after inactivity period
        inactivity_ms = (current_time - self.last_mouse_activity) * 1000
        if (not self.cursor_hidden and 
            inactivity_ms > self.config.hide_cursor_after_ms):
            pygame.mouse.set_visible(False)
            self.cursor_hidden = True
            logger.debug("Hiding cursor due to inactivity")
            
    def handle_mouse_activity(self):
        """
        Handle mouse activity events to reset the cursor timer.
        Call this when processing mouse events.
        """
        self.last_mouse_activity = time.time()
        if self.cursor_hidden:
            pygame.mouse.set_visible(True)
            self.cursor_hidden = False
            
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Get the current screen size.
        
        Returns:
            Tuple of (width, height)
        """
        if self.selected_monitor:
            return (self.selected_monitor.width, self.selected_monitor.height)
        elif self.screen:
            return self.screen.get_size()
        else:
            return (1920, 1080)  # Default fallback
            
    def cleanup(self):
        """
        Clean up display resources.
        """
        if self.screen:
            pygame.display.quit()
            self.screen = None
            logger.info("Display resources cleaned up")
            
    def _parse_color(self, color_str: str) -> Tuple[int, int, int]:
        """
        Parse a color string (hex format) to RGB tuple.
        
        Args:
            color_str: Color in hex format (e.g., "#000000")
            
        Returns:
            RGB tuple (r, g, b)
        """
        try:
            if color_str.startswith('#'):
                color_str = color_str[1:]
            
            if len(color_str) == 6:
                r = int(color_str[0:2], 16)
                g = int(color_str[2:4], 16)
                b = int(color_str[4:6], 16)
                return (r, g, b)
            else:
                raise ValueError(f"Invalid color format: {color_str}")
                
        except Exception as e:
            logger.warning(f"Failed to parse color '{color_str}': {e}, using black")
            return (0, 0, 0)  # Default to black