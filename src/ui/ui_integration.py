"""
Integration utilities for UI components with other system modules.
"""
import logging
from typing import Optional, Callable
from src.config.models import AppConfig, CarouselMode
from src.display.display_manager import DisplayManager
from src.carousel.carousel_manager import CarouselManager
from src.images.image_manager import ImageManager
from src.ui.ui_controller import UIController


logger = logging.getLogger(__name__)


class UIIntegrationManager:
    """
    Manages integration between UI components and other system modules.
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize the UI integration manager.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.ui_controller: Optional[UIController] = None
        self.scheduler_callback: Optional[Callable[[CarouselMode], None]] = None
        
    def setup_ui_system(self, display_manager: DisplayManager, 
                       carousel_manager: CarouselManager, 
                       image_manager: ImageManager) -> UIController:
        """
        Set up the complete UI system with all components.
        
        Args:
            display_manager: Display manager instance
            carousel_manager: Carousel manager instance
            image_manager: Image manager instance
            
        Returns:
            Configured UIController instance
        """
        # Create UI controller
        self.ui_controller = UIController(
            self.config, display_manager, carousel_manager, image_manager
        )
        
        # Set up callbacks for external integration
        self.ui_controller.on_mode_change = self._handle_mode_change
        self.ui_controller.on_exit = self._handle_exit_request
        
        logger.info("UI system setup completed")
        return self.ui_controller
    
    def initialize_display_and_ui(self, display_manager: DisplayManager) -> None:
        """
        Initialize display and UI rendering components.
        
        Args:
            display_manager: Display manager instance
        """
        if not self.ui_controller:
            raise RuntimeError("UI controller not set up. Call setup_ui_system() first.")
        
        # Get monitors and select target monitor
        monitors = display_manager.get_monitors()
        selected_monitor = display_manager.select_monitor(monitors, self.config.display.monitor_index)
        
        # Create fullscreen window
        screen = display_manager.create_fullscreen_window(selected_monitor)
        
        # Set window properties
        display_manager.set_window_properties(
            always_on_top=self.config.display.always_on_top,
            hide_cursor=False  # Will be managed by cursor timeout
        )
        
        # Initialize UI rendering
        self.ui_controller.initialize_rendering(screen)
        
        logger.info(f"Display and UI initialized on monitor {selected_monitor.index}")
    
    def register_scheduler_callback(self, callback: Callable[[CarouselMode], None]) -> None:
        """
        Register a callback for scheduler-initiated mode changes.
        
        Args:
            callback: Function to call when scheduler requests mode change
        """
        self.scheduler_callback = callback
        logger.debug("Registered scheduler callback")
    
    def handle_scheduler_mode_change(self, mode: CarouselMode) -> None:
        """
        Handle mode change request from scheduler.
        
        Args:
            mode: CarouselMode to switch to
        """
        if self.ui_controller:
            self.ui_controller.switch_carousel_mode(mode)
            logger.info(f"Handled scheduler mode change to {mode.value}")
    
    def _handle_mode_change(self, mode: CarouselMode) -> None:
        """
        Handle mode change from UI (manual override).
        
        Args:
            mode: CarouselMode that was manually selected
        """
        if self.scheduler_callback:
            self.scheduler_callback(mode)
        logger.debug(f"Notified scheduler of manual mode change to {mode.value}")
    
    def _handle_exit_request(self) -> None:
        """Handle exit request from UI."""
        logger.info("Exit request received from UI")
        # This will be handled by the main application controller
    
    def start_ui_loop(self) -> None:
        """Start the main UI event loop."""
        if not self.ui_controller:
            raise RuntimeError("UI controller not set up. Call setup_ui_system() first.")
        
        logger.info("Starting UI main loop")
        
        # Start preloading for better performance
        self.ui_controller.preload_next_images(3)
        
        # Run the main loop
        self.ui_controller.run_main_loop()
    
    def stop_ui_system(self) -> None:
        """Stop the UI system gracefully."""
        if self.ui_controller:
            self.ui_controller.stop()
            logger.info("UI system stopped")
    
    def cleanup_ui_system(self) -> None:
        """Clean up UI system resources."""
        if self.ui_controller:
            self.ui_controller.cleanup()
            self.ui_controller = None
            logger.info("UI system cleaned up")
    
    def get_ui_status(self) -> dict:
        """
        Get current UI system status.
        
        Returns:
            Dictionary with UI status information
        """
        if self.ui_controller:
            return self.ui_controller.get_status()
        else:
            return {'error': 'UI controller not initialized'}
    
    def pause_ui(self) -> None:
        """Pause the UI slideshow."""
        if self.ui_controller:
            self.ui_controller.pause_slideshow()
    
    def resume_ui(self) -> None:
        """Resume the UI slideshow."""
        if self.ui_controller:
            self.ui_controller.resume_slideshow()
    
    def toggle_ui_pause(self) -> None:
        """Toggle UI pause state."""
        if self.ui_controller:
            self.ui_controller.toggle_pause()
    
    def force_ui_mode(self, mode: CarouselMode) -> None:
        """
        Force UI to a specific mode.
        
        Args:
            mode: CarouselMode to force
        """
        if self.ui_controller:
            if mode == CarouselMode.DAY:
                self.ui_controller._handle_force_day()
            elif mode == CarouselMode.NIGHT:
                self.ui_controller._handle_force_night()
    
    def clear_ui_manual_override(self) -> None:
        """Clear manual override in UI."""
        if self.ui_controller:
            self.ui_controller.clear_manual_override()


def create_ui_system(config: AppConfig, display_manager: DisplayManager,
                    carousel_manager: CarouselManager, image_manager: ImageManager) -> UIIntegrationManager:
    """
    Convenience function to create and set up a complete UI system.
    
    Args:
        config: Application configuration
        display_manager: Display manager instance
        carousel_manager: Carousel manager instance
        image_manager: Image manager instance
        
    Returns:
        Configured UIIntegrationManager
    """
    ui_integration = UIIntegrationManager(config)
    ui_integration.setup_ui_system(display_manager, carousel_manager, image_manager)
    ui_integration.initialize_display_and_ui(display_manager)
    
    logger.info("Complete UI system created and initialized")
    return ui_integration