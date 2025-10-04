"""
Event handling system for pygame events and hotkey management.
"""
import logging
from typing import Dict, Callable, Optional, Any
from enum import Enum
import pygame

from src.config.models import CarouselMode


logger = logging.getLogger(__name__)


class HotkeyAction(Enum):
    """Enumeration of available hotkey actions."""
    EXIT = "exit"
    TOGGLE_PAUSE = "toggle_pause"
    NEXT_IMAGE = "next_image"
    PREVIOUS_IMAGE = "previous_image"
    FORCE_DAY = "force_day"
    FORCE_NIGHT = "force_night"
    BRING_TO_FRONT = "bring_to_front"


class EventHandler:
    """
    Handles pygame events and manages hotkey bindings.
    """
    
    def __init__(self):
        """Initialize the event handler with default hotkey bindings."""
        self.hotkey_bindings: Dict[int, HotkeyAction] = {
            pygame.K_ESCAPE: HotkeyAction.EXIT,
            pygame.K_SPACE: HotkeyAction.TOGGLE_PAUSE,
            pygame.K_RIGHT: HotkeyAction.NEXT_IMAGE,
            pygame.K_LEFT: HotkeyAction.PREVIOUS_IMAGE,
            pygame.K_d: HotkeyAction.FORCE_DAY,
            pygame.K_n: HotkeyAction.FORCE_NIGHT,
            pygame.K_f: HotkeyAction.BRING_TO_FRONT,
        }
        
        # Action callbacks
        self.action_callbacks: Dict[HotkeyAction, Callable] = {}
        
        # Event statistics
        self.event_stats = {
            'total_events': 0,
            'hotkey_events': 0,
            'mouse_events': 0,
            'system_events': 0
        }
        
    def register_callback(self, action: HotkeyAction, callback: Callable) -> None:
        """
        Register a callback function for a hotkey action.
        
        Args:
            action: HotkeyAction to bind
            callback: Function to call when action is triggered
        """
        self.action_callbacks[action] = callback
        logger.debug(f"Registered callback for {action.value}")
    
    def set_hotkey_binding(self, key: int, action: HotkeyAction) -> None:
        """
        Set or update a hotkey binding.
        
        Args:
            key: pygame key constant
            action: HotkeyAction to bind to the key
        """
        self.hotkey_bindings[key] = action
        logger.debug(f"Bound key {key} to action {action.value}")
    
    def remove_hotkey_binding(self, key: int) -> None:
        """
        Remove a hotkey binding.
        
        Args:
            key: pygame key constant to unbind
        """
        if key in self.hotkey_bindings:
            action = self.hotkey_bindings[key]
            del self.hotkey_bindings[key]
            logger.debug(f"Removed binding for key {key} (was {action.value})")
    
    def process_events(self) -> Dict[str, Any]:
        """
        Process all pending pygame events.
        
        Returns:
            Dictionary with event processing results
        """
        events_processed = 0
        quit_requested = False
        mouse_activity = False
        actions_triggered = []
        
        for event in pygame.event.get():
            self.event_stats['total_events'] += 1
            events_processed += 1
            
            if event.type == pygame.QUIT:
                quit_requested = True
                self.event_stats['system_events'] += 1
                logger.info("Quit event received")
            
            elif event.type == pygame.KEYDOWN:
                action = self._handle_keydown(event.key)
                if action:
                    actions_triggered.append(action.value)
                    if action == HotkeyAction.EXIT:
                        quit_requested = True
                self.event_stats['hotkey_events'] += 1
            
            elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                mouse_activity = True
                self.event_stats['mouse_events'] += 1
            
            elif event.type in (pygame.ACTIVEEVENT, pygame.VIDEOEXPOSE, pygame.WINDOWCLOSE, 
                               pygame.WINDOWRESIZED, pygame.WINDOWMOVED, pygame.WINDOWFOCUSGAINED, 
                               pygame.WINDOWFOCUSLOST):
                self.event_stats['system_events'] += 1
        
        return {
            'events_processed': events_processed,
            'quit_requested': quit_requested,
            'mouse_activity': mouse_activity,
            'actions_triggered': actions_triggered
        }
    
    def _handle_keydown(self, key: int) -> Optional[HotkeyAction]:
        """
        Handle a keydown event and trigger appropriate action.
        
        Args:
            key: pygame key constant
            
        Returns:
            HotkeyAction that was triggered, or None
        """
        if key in self.hotkey_bindings:
            action = self.hotkey_bindings[key]
            
            # Call registered callback if available
            if action in self.action_callbacks:
                try:
                    self.action_callbacks[action]()
                    logger.debug(f"Executed callback for {action.value}")
                except Exception as e:
                    logger.error(f"Error executing callback for {action.value}: {e}")
            else:
                logger.warning(f"No callback registered for action {action.value}")
            
            return action
        else:
            logger.debug(f"Unbound key pressed: {key}")
            return None
    
    def get_hotkey_info(self) -> Dict[str, str]:
        """
        Get information about current hotkey bindings.
        
        Returns:
            Dictionary mapping key names to action descriptions
        """
        key_names = {
            pygame.K_ESCAPE: "Escape",
            pygame.K_SPACE: "Space",
            pygame.K_RIGHT: "Right Arrow",
            pygame.K_LEFT: "Left Arrow",
            pygame.K_d: "D",
            pygame.K_n: "N",
        }
        
        action_descriptions = {
            HotkeyAction.EXIT: "Exit application",
            HotkeyAction.TOGGLE_PAUSE: "Toggle pause/resume",
            HotkeyAction.NEXT_IMAGE: "Next image",
            HotkeyAction.PREVIOUS_IMAGE: "Previous image",
            HotkeyAction.FORCE_DAY: "Force day mode",
            HotkeyAction.FORCE_NIGHT: "Force night mode",
        }
        
        hotkey_info = {}
        for key, action in self.hotkey_bindings.items():
            key_name = key_names.get(key, f"Key {key}")
            description = action_descriptions.get(action, action.value)
            hotkey_info[key_name] = description
        
        return hotkey_info
    
    def get_event_statistics(self) -> Dict[str, int]:
        """
        Get event processing statistics.
        
        Returns:
            Dictionary with event statistics
        """
        return self.event_stats.copy()
    
    def reset_statistics(self) -> None:
        """Reset event statistics counters."""
        for key in self.event_stats:
            self.event_stats[key] = 0
        logger.debug("Reset event statistics")


class MouseActivityTracker:
    """
    Tracks mouse activity for cursor management.
    """
    
    def __init__(self):
        """Initialize the mouse activity tracker."""
        self.last_position = pygame.mouse.get_pos()
        self.activity_detected = False
        
    def update(self) -> bool:
        """
        Update mouse activity tracking.
        
        Returns:
            True if mouse activity was detected since last update
        """
        current_position = pygame.mouse.get_pos()
        
        if current_position != self.last_position:
            self.activity_detected = True
            self.last_position = current_position
            return True
        
        # Reset activity flag after checking
        activity = self.activity_detected
        self.activity_detected = False
        return activity
    
    def force_activity(self) -> None:
        """Force mouse activity detection (for button clicks, etc.)."""
        self.activity_detected = True


class PauseManager:
    """
    Manages pause/resume state with additional functionality.
    """
    
    def __init__(self):
        """Initialize the pause manager."""
        self.is_paused = False
        self.pause_start_time: Optional[float] = None
        self.total_pause_time = 0.0
        
    def toggle_pause(self) -> bool:
        """
        Toggle pause state.
        
        Returns:
            New pause state (True if paused, False if resumed)
        """
        if self.is_paused:
            self.resume()
        else:
            self.pause()
        return self.is_paused
    
    def pause(self) -> None:
        """Pause the system."""
        if not self.is_paused:
            self.is_paused = True
            self.pause_start_time = pygame.time.get_ticks() / 1000.0
            logger.info("System paused")
    
    def resume(self) -> None:
        """Resume the system."""
        if self.is_paused:
            self.is_paused = False
            if self.pause_start_time is not None:
                pause_duration = (pygame.time.get_ticks() / 1000.0) - self.pause_start_time
                self.total_pause_time += pause_duration
                self.pause_start_time = None
            logger.info("System resumed")
    
    def get_pause_info(self) -> Dict[str, Any]:
        """
        Get information about pause state.
        
        Returns:
            Dictionary with pause information
        """
        current_pause_duration = 0.0
        if self.is_paused and self.pause_start_time is not None:
            current_pause_duration = (pygame.time.get_ticks() / 1000.0) - self.pause_start_time
        
        return {
            'is_paused': self.is_paused,
            'current_pause_duration': current_pause_duration,
            'total_pause_time': self.total_pause_time
        }
    
    def reset_pause_time(self) -> None:
        """Reset pause time tracking."""
        self.total_pause_time = 0.0
        self.pause_start_time = None
        logger.debug("Reset pause time tracking")