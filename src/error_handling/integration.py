"""
Integration module for error handling across the slideshow application.

This module provides:
- Integration points for error handling in existing components
- Centralized error reporting and recovery coordination
- Application-wide error handling setup
"""
import logging
from typing import Optional, Dict, Any, Callable
import pygame

from .error_handler import error_handler, ErrorCategory, ErrorInfo, ErrorSeverity
from .recovery_manager import initialize_recovery_manager, get_recovery_manager
from .fallback_display import FallbackDisplay, create_fallback_surface


logger = logging.getLogger(__name__)


class ErrorHandlingIntegration:
    """
    Provides integration points for error handling throughout the application.
    """
    
    def __init__(self):
        """Initialize the error handling integration."""
        self.recovery_manager = initialize_recovery_manager(error_handler)
        self.fallback_display: Optional[FallbackDisplay] = None
        self.screen_size = (1920, 1080)  # Default, will be updated
        
        # Setup recovery strategies
        self._setup_recovery_strategies()
    
    def initialize(self, screen_size: tuple, background_color: tuple = (0, 0, 0)):
        """
        Initialize error handling for the application.
        
        Args:
            screen_size: (width, height) of the display
            background_color: RGB background color
        """
        self.screen_size = screen_size
        self.fallback_display = FallbackDisplay(screen_size, background_color)
        
        # Start system monitoring
        self.recovery_manager.start_monitoring()
        
        logger.info("Error handling integration initialized")
    
    def _setup_recovery_strategies(self):
        """Setup recovery strategies for different components."""
        
        def recover_image_manager():
            """Recovery strategy for image manager."""
            try:
                # Clear cache and reset error counts
                error_handler.reset_error_counts(ErrorCategory.IMAGE_LOADING)
                logger.info("Image manager recovery: cleared cache and reset error counts")
                return True
            except Exception as e:
                logger.error(f"Image manager recovery failed: {e}")
                return False
        
        def recover_display_manager():
            """Recovery strategy for display manager."""
            try:
                # Attempt to reinitialize pygame display
                pygame.display.quit()
                pygame.display.init()
                logger.info("Display manager recovery: reinitialized pygame display")
                return True
            except Exception as e:
                logger.error(f"Display manager recovery failed: {e}")
                return False
        
        def recover_carousel_manager():
            """Recovery strategy for carousel manager."""
            try:
                # Reset error counts for folder access
                error_handler.reset_error_counts(ErrorCategory.FOLDER_ACCESS)
                logger.info("Carousel manager recovery: reset folder access errors")
                return True
            except Exception as e:
                logger.error(f"Carousel manager recovery failed: {e}")
                return False
        
        # Register recovery strategies
        self.recovery_manager.register_recovery_strategy('image_manager', recover_image_manager)
        self.recovery_manager.register_recovery_strategy('display_manager', recover_display_manager)
        self.recovery_manager.register_recovery_strategy('carousel_manager', recover_carousel_manager)
    
    def handle_empty_folder(self, folder_path: str, carousel_mode: str) -> pygame.Surface:
        """
        Handle empty folder scenario with fallback display.
        
        Args:
            folder_path: Path to the empty folder
            carousel_mode: "day" or "night"
            
        Returns:
            pygame.Surface with fallback message
        """
        if self.fallback_display:
            return self.fallback_display.create_empty_folder_message(folder_path, carousel_mode)
        else:
            return create_fallback_surface(
                self.screen_size, 
                f"No {carousel_mode} images found in {folder_path}"
            )
    
    def handle_image_loading_error(self, image_path: str, error: Exception) -> Optional[pygame.Surface]:
        """
        Handle image loading errors with fallback.
        
        Args:
            image_path: Path to the image that failed to load
            error: The exception that occurred
            
        Returns:
            Optional pygame.Surface with error message or None to skip
        """
        # Report to recovery manager
        error_info = ErrorInfo(
            category=ErrorCategory.IMAGE_LOADING,
            severity=ErrorSeverity.LOW,
            message=f"Failed to load image: {image_path}",
            exception=error,
            context={'image_path': image_path}
        )
        
        should_continue = self.recovery_manager.report_component_error('image_manager', error_info)
        
        if not should_continue:
            # Create error display
            if self.fallback_display:
                return self.fallback_display.create_error_message(
                    "Image Loading Failed",
                    f"Cannot load: {image_path}",
                    ["Check file permissions", "Verify file format", "Check disk space"]
                )
        
        return None  # Skip this image
    
    def handle_display_error(self, error: Exception, context: Dict[str, Any] = None) -> bool:
        """
        Handle display system errors.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            
        Returns:
            bool: True if application should continue
        """
        error_info = ErrorInfo(
            category=ErrorCategory.DISPLAY_ERROR,
            severity=ErrorSeverity.HIGH,
            message="Display system error",
            exception=error,
            context=context or {}
        )
        
        return self.recovery_manager.report_component_error('display_manager', error_info)
    
    def handle_folder_access_error(self, folder_path: str, error: Exception) -> bool:
        """
        Handle folder access errors.
        
        Args:
            folder_path: Path to the folder that failed to access
            error: The exception that occurred
            
        Returns:
            bool: True if application should continue
        """
        error_info = ErrorInfo(
            category=ErrorCategory.FOLDER_ACCESS,
            severity=ErrorSeverity.MEDIUM,
            message=f"Folder access error: {folder_path}",
            exception=error,
            context={'folder_path': folder_path}
        )
        
        return self.recovery_manager.report_component_error('carousel_manager', error_info)
    
    def create_retry_display(self, operation: str, attempt: int, max_attempts: int, 
                           next_retry_seconds: float) -> pygame.Surface:
        """
        Create a retry operation display.
        
        Args:
            operation: Name of the operation being retried
            attempt: Current attempt number
            max_attempts: Maximum number of attempts
            next_retry_seconds: Seconds until next retry
            
        Returns:
            pygame.Surface with retry information
        """
        if self.fallback_display:
            return self.fallback_display.create_retry_message(
                operation, attempt, max_attempts, next_retry_seconds
            )
        else:
            return create_fallback_surface(
                self.screen_size,
                f"Retrying {operation} ({attempt}/{max_attempts})"
            )
    
    def create_system_info_display(self) -> pygame.Surface:
        """
        Create a system information display.
        
        Returns:
            pygame.Surface with system information
        """
        system_status = self.recovery_manager.get_system_status()
        
        if self.fallback_display:
            return self.fallback_display.create_system_info_display(system_status)
        else:
            return create_fallback_surface(
                self.screen_size,
                f"System Health: {system_status['system_health']}"
            )
    
    def get_system_health_info(self) -> Dict[str, Any]:
        """
        Get comprehensive system health information.
        
        Returns:
            Dictionary containing system health data
        """
        return self.recovery_manager.get_system_status()
    
    def force_component_recovery(self, component_name: str) -> bool:
        """
        Force recovery for a specific component.
        
        Args:
            component_name: Name of the component to recover
            
        Returns:
            bool: True if recovery was attempted
        """
        return self.recovery_manager.force_recovery(component_name)
    
    def reset_component_errors(self, component_name: str):
        """
        Reset error status for a component.
        
        Args:
            component_name: Name of the component to reset
        """
        self.recovery_manager.reset_component_status(component_name)
    
    def cleanup(self):
        """Clean up error handling resources."""
        logger.info("Cleaning up error handling integration")
        
        if self.recovery_manager:
            self.recovery_manager.cleanup()
        
        logger.info("Error handling integration cleanup completed")


# Global integration instance
error_integration: Optional[ErrorHandlingIntegration] = None


def initialize_error_handling() -> ErrorHandlingIntegration:
    """
    Initialize the global error handling integration.
    
    Returns:
        ErrorHandlingIntegration: The initialized integration instance
    """
    global error_integration
    error_integration = ErrorHandlingIntegration()
    return error_integration


def get_error_integration() -> Optional[ErrorHandlingIntegration]:
    """Get the global error handling integration instance."""
    return error_integration


# Convenience functions for use throughout the application

def report_image_error(image_path: str, error: Exception) -> Optional[pygame.Surface]:
    """Report an image loading error and get fallback surface if needed."""
    if error_integration:
        return error_integration.handle_image_loading_error(image_path, error)
    return None


def report_folder_error(folder_path: str, error: Exception) -> bool:
    """Report a folder access error."""
    if error_integration:
        return error_integration.handle_folder_access_error(folder_path, error)
    return True


def report_display_error(error: Exception, context: Dict[str, Any] = None) -> bool:
    """Report a display system error."""
    if error_integration:
        return error_integration.handle_display_error(error, context)
    return True


def get_empty_folder_display(folder_path: str, carousel_mode: str) -> Optional[pygame.Surface]:
    """Get a fallback display for empty folders."""
    if error_integration:
        return error_integration.handle_empty_folder(folder_path, carousel_mode)
    return None


def get_system_health() -> Dict[str, Any]:
    """Get system health information."""
    if error_integration:
        return error_integration.get_system_health_info()
    return {'system_health': 'unknown', 'components': {}}