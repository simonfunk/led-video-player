"""
Main UI controller for event handling, hotkeys, and application flow.
"""
import logging
import time
from typing import Optional, Callable, Dict, Any
from datetime import datetime, timedelta
import pygame

from src.config.models import AppConfig, CarouselMode, PlaybackConfig
from src.display.display_manager import DisplayManager
from src.carousel.carousel_manager import CarouselManager
from src.images.image_manager import ImageManager
from src.ui.renderer import ImageRenderer, TransitionEngine
from src.ui.event_handler import EventHandler, HotkeyAction, MouseActivityTracker, PauseManager


logger = logging.getLogger(__name__)


class UIController:
    """
    Main UI controller managing the event loop, hotkeys, and user interactions.
    """
    
    def __init__(self, config: AppConfig, display_manager: DisplayManager, 
                 carousel_manager: CarouselManager, image_manager: ImageManager):
        """
        Initialize the UI controller.
        
        Args:
            config: Application configuration
            display_manager: Display manager instance
            carousel_manager: Carousel manager instance
            image_manager: Image manager instance
        """
        self.config = config
        self.display_manager = display_manager
        self.carousel_manager = carousel_manager
        self.image_manager = image_manager
        
        # UI state
        self.is_running = False
        self.manual_override: Optional[CarouselMode] = None
        self.last_image_change = time.time()
        self.current_image_surface: Optional[pygame.Surface] = None
        
        # Event handling components
        self.event_handler = EventHandler()
        self.mouse_tracker = MouseActivityTracker()
        self.pause_manager = PauseManager()
        
        # Rendering components
        self.renderer: Optional[ImageRenderer] = None
        self.transition_engine: Optional[TransitionEngine] = None
        
        # Setup event callbacks
        self._setup_event_callbacks()
        
        # Callbacks for external control
        self.on_mode_change: Optional[Callable[[CarouselMode], None]] = None
        self.on_exit: Optional[Callable[[], None]] = None
        
        # Initialize pygame
        pygame.init()
        pygame.key.set_repeat()  # Disable key repeat for better control
    
    def _setup_event_callbacks(self) -> None:
        """Setup callbacks for event handler actions."""
        self.event_handler.register_callback(HotkeyAction.EXIT, self._handle_exit)
        self.event_handler.register_callback(HotkeyAction.TOGGLE_PAUSE, self._handle_toggle_pause)
        self.event_handler.register_callback(HotkeyAction.NEXT_IMAGE, self._handle_next_image)
        self.event_handler.register_callback(HotkeyAction.PREVIOUS_IMAGE, self._handle_previous_image)
        self.event_handler.register_callback(HotkeyAction.FORCE_DAY, self._handle_force_day)
        self.event_handler.register_callback(HotkeyAction.FORCE_NIGHT, self._handle_force_night)
        
    def initialize_rendering(self, screen: pygame.Surface) -> None:
        """
        Initialize rendering components after screen is created.
        
        Args:
            screen: pygame Surface for rendering
        """
        background_color = self.display_manager._parse_color(self.config.display.background_color)
        self.renderer = ImageRenderer(screen, self.config.playback, background_color)
        self.transition_engine = TransitionEngine(screen, self.config.playback)
        
        logger.info("UI rendering components initialized")
    
    def run_main_loop(self) -> None:
        """
        Run the main event loop for the slideshow application.
        """
        if not self.renderer or not self.transition_engine:
            raise RuntimeError("Rendering components not initialized. Call initialize_rendering() first.")
        
        self.is_running = True
        logger.info("Starting main UI loop")
        
        # Load and display initial image
        self._load_and_display_current_image()
        
        # Main event loop
        clock = pygame.time.Clock()
        
        try:
            while self.is_running:
                # Handle events
                if not self._handle_events():
                    break
                
                # Update cursor visibility
                self.display_manager.update_cursor_visibility()
                
                # Check if it's time to advance to next image (if not paused)
                if not self.pause_manager.is_paused:
                    self._check_image_advance()
                
                # Update display
                pygame.display.flip()
                
                # Control frame rate
                clock.tick(60)  # 60 FPS
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            raise
        finally:
            self.is_running = False
            logger.info("Main UI loop ended")
    
    def _handle_events(self) -> bool:
        """
        Handle pygame events including hotkeys and system events.
        
        Returns:
            True to continue running, False to exit
        """
        # Process events through event handler
        event_result = self.event_handler.process_events()
        
        # Handle mouse activity
        if event_result['mouse_activity'] or self.mouse_tracker.update():
            self.display_manager.handle_mouse_activity()
        
        # Check if exit was requested
        return not event_result['quit_requested']
    
    def _handle_exit(self) -> None:
        """Handle exit action."""
        logger.info("Exit requested via hotkey")
        if self.on_exit:
            self.on_exit()
        self.stop()
    
    def _handle_toggle_pause(self) -> None:
        """Handle toggle pause action."""
        was_paused = self.pause_manager.is_paused
        self.pause_manager.toggle_pause()
        
        if not was_paused and self.pause_manager.is_paused:
            # Just paused - reset image change timer when resuming
            pass
        elif was_paused and not self.pause_manager.is_paused:
            # Just resumed - reset timer to prevent immediate image change
            self.last_image_change = time.time()
    
    def _handle_next_image(self) -> None:
        """Handle next image action."""
        self._advance_to_next_image()
        logger.debug("Advanced to next image (hotkey)")
    
    def _handle_previous_image(self) -> None:
        """Handle previous image action."""
        self._go_to_previous_image()
        logger.debug("Went to previous image (hotkey)")
    
    def _handle_force_day(self) -> None:
        """Handle force day mode action."""
        self._set_manual_override(CarouselMode.DAY)
        logger.info("Forced day mode (hotkey)")
    
    def _handle_force_night(self) -> None:
        """Handle force night mode action."""
        self._set_manual_override(CarouselMode.NIGHT)
        logger.info("Forced night mode (hotkey)")
    
    def _check_image_advance(self) -> None:
        """Check if it's time to automatically advance to the next image."""
        current_time = time.time()
        interval = self.config.playback.interval_seconds
        
        if current_time - self.last_image_change >= interval:
            self._advance_to_next_image()
    
    def _advance_to_next_image(self) -> None:
        """Advance to the next image in the current carousel."""
        next_image_path = self.carousel_manager.advance_image()
        self._transition_to_image(next_image_path)
        self.last_image_change = time.time()
    
    def _go_to_previous_image(self) -> None:
        """Go to the previous image in the current carousel."""
        prev_image_path = self.carousel_manager.previous_image()
        self._transition_to_image(prev_image_path)
        self.last_image_change = time.time()
    
    def _set_manual_override(self, mode: CarouselMode) -> None:
        """
        Set manual override for carousel mode.
        
        Args:
            mode: CarouselMode to force
        """
        self.manual_override = mode
        self.carousel_manager.switch_carousel(mode)
        
        # Load and display image from new carousel
        current_image_path = self.carousel_manager.get_current_image_path()
        self._transition_to_image(current_image_path)
        
        # Notify external components
        if self.on_mode_change:
            self.on_mode_change(mode)
    
    def clear_manual_override(self) -> None:
        """Clear manual override and return to automatic scheduling."""
        self.manual_override = None
        logger.info("Cleared manual override - returning to automatic scheduling")
    
    def switch_carousel_mode(self, mode: CarouselMode) -> None:
        """
        Switch carousel mode (called by scheduler).
        
        Args:
            mode: CarouselMode to switch to
        """
        # Only switch if no manual override is active
        if self.manual_override is None:
            current_mode = self.carousel_manager.current_mode
            if current_mode != mode:
                self.carousel_manager.switch_carousel(mode)
                
                # Load and display image from new carousel
                current_image_path = self.carousel_manager.get_current_image_path()
                self._transition_to_image(current_image_path)
                
                logger.info(f"Switched to {mode.value} mode via scheduler")
    
    def _load_and_display_current_image(self) -> None:
        """Load and display the current image without transition."""
        current_image_path = self.carousel_manager.get_current_image_path()
        
        if current_image_path:
            # Load image with proper scaling
            screen_size = self.renderer.get_screen_size()
            image_surface = self.image_manager.get_cached_image(
                current_image_path, screen_size, self.config.playback.fit_mode
            )
            
            if image_surface:
                self.current_image_surface = image_surface
                self.renderer.render_image(image_surface)
                logger.debug(f"Displayed image: {current_image_path}")
            else:
                self._display_error_message(f"Failed to load: {current_image_path}")
        else:
            self._display_empty_carousel_message()
    
    def _transition_to_image(self, image_path: Optional[str]) -> None:
        """
        Transition to a new image with crossfade effect.
        
        Args:
            image_path: Path to the new image, or None if no image available
        """
        if image_path:
            # Load new image
            screen_size = self.renderer.get_screen_size()
            new_image_surface = self.image_manager.get_cached_image(
                image_path, screen_size, self.config.playback.fit_mode
            )
            
            if new_image_surface:
                # Perform transition
                background_color = self.display_manager._parse_color(self.config.display.background_color)
                self.transition_engine.crossfade_transition(
                    self.current_image_surface,
                    new_image_surface,
                    background_color
                )
                
                self.current_image_surface = new_image_surface
                logger.debug(f"Transitioned to image: {image_path}")
            else:
                self._display_error_message(f"Failed to load: {image_path}")
        else:
            # No image available, show empty carousel message
            self._display_empty_carousel_message()
    
    def _display_empty_carousel_message(self) -> None:
        """Display a message when the current carousel is empty."""
        carousel_info = self.carousel_manager.get_current_image_info()
        mode = carousel_info['mode']
        message = f"No images found in {mode} folder"
        
        self.renderer.render_fallback_message(message)
        self.current_image_surface = None
        logger.warning(f"Displayed empty carousel message: {message}")
    
    def _display_error_message(self, error_text: str) -> None:
        """
        Display an error message on screen.
        
        Args:
            error_text: Error message to display
        """
        self.renderer.render_fallback_message(f"Error: {error_text}")
        logger.error(f"Displayed error message: {error_text}")
    
    def pause_slideshow(self) -> None:
        """Pause the slideshow."""
        self.pause_manager.pause()
    
    def resume_slideshow(self) -> None:
        """Resume the slideshow."""
        self.pause_manager.resume()
        self.last_image_change = time.time()  # Reset timer
    
    def toggle_pause(self) -> None:
        """Toggle pause state."""
        was_paused = self.pause_manager.is_paused
        self.pause_manager.toggle_pause()
        
        if was_paused and not self.pause_manager.is_paused:
            # Just resumed - reset timer
            self.last_image_change = time.time()
    
    def stop(self) -> None:
        """Stop the UI controller."""
        self.is_running = False
        logger.info("UI controller stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current UI status information.
        
        Returns:
            Dictionary with current status
        """
        carousel_info = self.carousel_manager.get_current_image_info()
        
        pause_info = self.pause_manager.get_pause_info()
        event_stats = self.event_handler.get_event_statistics()
        
        return {
            'is_running': self.is_running,
            'is_paused': pause_info['is_paused'],
            'manual_override': self.manual_override.value if self.manual_override else None,
            'current_mode': carousel_info['mode'],
            'current_image_index': carousel_info['current_index'],
            'total_images': carousel_info['total_images'],
            'current_image_path': carousel_info['current_image_path'],
            'last_image_change': datetime.fromtimestamp(self.last_image_change).isoformat(),
            'time_until_next_image': max(0, self.config.playback.interval_seconds - (time.time() - self.last_image_change)),
            'pause_info': pause_info,
            'event_stats': event_stats,
            'hotkey_bindings': self.event_handler.get_hotkey_info()
        }
    
    def preload_next_images(self, count: int = 3) -> None:
        """
        Preload upcoming images for better performance.
        
        Args:
            count: Number of images to preload
        """
        try:
            carousel = self.carousel_manager.get_current_carousel()
            screen_size = self.renderer.get_screen_size()
            
            # Get paths of upcoming images
            upcoming_paths = []
            for i in range(1, count + 1):
                next_index = (carousel.current_index + i) % len(carousel.shuffle_order)
                image_path = carousel.get_image_path_at_index(next_index)
                if image_path:
                    upcoming_paths.append(image_path)
            
            # Start preloading
            if upcoming_paths:
                self.image_manager.preload_images(
                    upcoming_paths, screen_size, self.config.playback.fit_mode, count
                )
                logger.debug(f"Started preloading {len(upcoming_paths)} images")
                
        except Exception as e:
            logger.error(f"Error preloading images: {e}")
    
    def cleanup(self) -> None:
        """Clean up UI resources."""
        logger.info("Cleaning up UI controller")
        self.stop()
        
        # Clean up pygame
        try:
            pygame.quit()
        except Exception as e:
            logger.error(f"Error cleaning up pygame: {e}")
        
        logger.info("UI controller cleanup completed")