"""
Fallback display system for error conditions and empty folders.

This module provides:
- Fallback messages for empty folders
- Error display screens
- System status information display
"""
import logging
from typing import Optional, Tuple, Dict, Any
import pygame
from datetime import datetime

logger = logging.getLogger(__name__)


class FallbackDisplay:
    """
    Handles fallback display scenarios when normal operation is not possible.
    """
    
    def __init__(self, screen_size: Tuple[int, int], background_color: Tuple[int, int, int] = (0, 0, 0)):
        """
        Initialize the fallback display system.
        
        Args:
            screen_size: (width, height) of the display
            background_color: RGB background color
        """
        self.screen_size = screen_size
        self.background_color = background_color
        self.font_large: Optional[pygame.font.Font] = None
        self.font_medium: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None
        
        self._initialize_fonts()
    
    def _initialize_fonts(self):
        """Initialize fonts for text rendering."""
        try:
            pygame.font.init()
            
            # Try to load system fonts, fall back to pygame default
            try:
                self.font_large = pygame.font.Font(None, 72)
                self.font_medium = pygame.font.Font(None, 48)
                self.font_small = pygame.font.Font(None, 32)
            except Exception as e:
                logger.warning(f"Could not load preferred fonts: {e}")
                # Use pygame default font
                self.font_large = pygame.font.Font(None, 72)
                self.font_medium = pygame.font.Font(None, 48)
                self.font_small = pygame.font.Font(None, 32)
                
        except Exception as e:
            logger.error(f"Failed to initialize fonts: {e}")
            # Set to None, will be handled in render methods
            self.font_large = None
            self.font_medium = None
            self.font_small = None
    
    def create_empty_folder_message(self, folder_path: str, carousel_mode: str) -> pygame.Surface:
        """
        Create a fallback message for empty folders.
        
        Args:
            folder_path: Path to the empty folder
            carousel_mode: "day" or "night"
            
        Returns:
            pygame.Surface with the fallback message
        """
        surface = pygame.Surface(self.screen_size)
        surface.fill(self.background_color)
        
        if not self.font_large or not self.font_medium or not self.font_small:
            logger.error("Fonts not available for fallback display")
            return surface
        
        try:
            # Main message
            title_text = f"No {carousel_mode.title()} Images Found"
            title_color = (255, 255, 255)  # White
            
            # Subtitle with folder path
            subtitle_text = f"Folder: {folder_path}"
            subtitle_color = (200, 200, 200)  # Light gray
            
            # Instructions
            instructions = [
                "Please add image files to the folder:",
                "• Supported formats: JPG, PNG, BMP",
                "• The folder will be scanned automatically",
                "",
                f"Current time: {datetime.now().strftime('%H:%M:%S')}"
            ]
            instruction_color = (150, 150, 150)  # Gray
            
            # Render title
            title_surface = self.font_large.render(title_text, True, title_color)
            title_rect = title_surface.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 3))
            surface.blit(title_surface, title_rect)
            
            # Render subtitle
            subtitle_surface = self.font_medium.render(subtitle_text, True, subtitle_color)
            subtitle_rect = subtitle_surface.get_rect(center=(self.screen_size[0] // 2, title_rect.bottom + 40))
            surface.blit(subtitle_surface, subtitle_rect)
            
            # Render instructions
            y_offset = subtitle_rect.bottom + 60
            for instruction in instructions:
                if instruction:  # Skip empty lines
                    instruction_surface = self.font_small.render(instruction, True, instruction_color)
                    instruction_rect = instruction_surface.get_rect(center=(self.screen_size[0] // 2, y_offset))
                    surface.blit(instruction_surface, instruction_rect)
                y_offset += 40
            
            logger.debug(f"Created empty folder message for {carousel_mode} mode")
            
        except Exception as e:
            logger.error(f"Failed to create empty folder message: {e}")
            # Return a simple colored surface as last resort
            surface.fill((50, 0, 0))  # Dark red to indicate error
        
        return surface
    
    def create_error_message(self, error_title: str, error_details: str, 
                           suggestions: Optional[list] = None) -> pygame.Surface:
        """
        Create an error message display.
        
        Args:
            error_title: Main error title
            error_details: Detailed error information
            suggestions: Optional list of suggestions to resolve the error
            
        Returns:
            pygame.Surface with the error message
        """
        surface = pygame.Surface(self.screen_size)
        surface.fill((20, 0, 0))  # Dark red background for errors
        
        if not self.font_large or not self.font_medium or not self.font_small:
            return surface
        
        try:
            # Colors
            title_color = (255, 100, 100)  # Light red
            details_color = (255, 200, 200)  # Lighter red
            suggestion_color = (200, 255, 200)  # Light green
            
            # Render title
            title_surface = self.font_large.render(error_title, True, title_color)
            title_rect = title_surface.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 4))
            surface.blit(title_surface, title_rect)
            
            # Render details
            details_surface = self.font_medium.render(error_details, True, details_color)
            details_rect = details_surface.get_rect(center=(self.screen_size[0] // 2, title_rect.bottom + 40))
            surface.blit(details_surface, details_rect)
            
            # Render suggestions if provided
            if suggestions:
                y_offset = details_rect.bottom + 60
                suggestion_title = self.font_medium.render("Suggestions:", True, suggestion_color)
                suggestion_title_rect = suggestion_title.get_rect(center=(self.screen_size[0] // 2, y_offset))
                surface.blit(suggestion_title, suggestion_title_rect)
                
                y_offset = suggestion_title_rect.bottom + 20
                for suggestion in suggestions:
                    suggestion_surface = self.font_small.render(f"• {suggestion}", True, suggestion_color)
                    suggestion_rect = suggestion_surface.get_rect(center=(self.screen_size[0] // 2, y_offset))
                    surface.blit(suggestion_surface, suggestion_rect)
                    y_offset += 35
            
            logger.debug(f"Created error message: {error_title}")
            
        except Exception as e:
            logger.error(f"Failed to create error message: {e}")
        
        return surface
    
    def create_loading_message(self, message: str = "Loading...") -> pygame.Surface:
        """
        Create a loading message display.
        
        Args:
            message: Loading message to display
            
        Returns:
            pygame.Surface with the loading message
        """
        surface = pygame.Surface(self.screen_size)
        surface.fill(self.background_color)
        
        if not self.font_large:
            return surface
        
        try:
            text_color = (255, 255, 255)  # White
            
            # Render loading message
            text_surface = self.font_large.render(message, True, text_color)
            text_rect = text_surface.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 2))
            surface.blit(text_surface, text_rect)
            
            # Add timestamp
            timestamp = datetime.now().strftime('%H:%M:%S')
            time_surface = self.font_small.render(timestamp, True, text_color)
            time_rect = time_surface.get_rect(center=(self.screen_size[0] // 2, text_rect.bottom + 40))
            surface.blit(time_surface, time_rect)
            
        except Exception as e:
            logger.error(f"Failed to create loading message: {e}")
        
        return surface
    
    def create_system_info_display(self, info: Dict[str, Any]) -> pygame.Surface:
        """
        Create a system information display.
        
        Args:
            info: Dictionary containing system information
            
        Returns:
            pygame.Surface with system information
        """
        surface = pygame.Surface(self.screen_size)
        surface.fill((0, 20, 0))  # Dark green background
        
        if not self.font_medium or not self.font_small:
            return surface
        
        try:
            title_color = (100, 255, 100)  # Light green
            info_color = (200, 255, 200)   # Lighter green
            
            # Title
            title_surface = self.font_medium.render("System Information", True, title_color)
            title_rect = title_surface.get_rect(center=(self.screen_size[0] // 2, 50))
            surface.blit(title_surface, title_rect)
            
            # Information items
            y_offset = title_rect.bottom + 40
            for key, value in info.items():
                info_text = f"{key}: {value}"
                info_surface = self.font_small.render(info_text, True, info_color)
                info_rect = info_surface.get_rect(center=(self.screen_size[0] // 2, y_offset))
                surface.blit(info_surface, info_rect)
                y_offset += 35
            
        except Exception as e:
            logger.error(f"Failed to create system info display: {e}")
        
        return surface
    
    def create_retry_message(self, operation: str, attempt: int, max_attempts: int, 
                           next_retry_seconds: float) -> pygame.Surface:
        """
        Create a retry operation message.
        
        Args:
            operation: Name of the operation being retried
            attempt: Current attempt number
            max_attempts: Maximum number of attempts
            next_retry_seconds: Seconds until next retry
            
        Returns:
            pygame.Surface with retry information
        """
        surface = pygame.Surface(self.screen_size)
        surface.fill((20, 20, 0))  # Dark yellow background
        
        if not self.font_large or not self.font_medium:
            return surface
        
        try:
            title_color = (255, 255, 100)  # Light yellow
            info_color = (255, 255, 200)   # Lighter yellow
            
            # Main message
            title_text = f"Retrying {operation}"
            title_surface = self.font_large.render(title_text, True, title_color)
            title_rect = title_surface.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 3))
            surface.blit(title_surface, title_rect)
            
            # Attempt info
            attempt_text = f"Attempt {attempt} of {max_attempts}"
            attempt_surface = self.font_medium.render(attempt_text, True, info_color)
            attempt_rect = attempt_surface.get_rect(center=(self.screen_size[0] // 2, title_rect.bottom + 40))
            surface.blit(attempt_surface, attempt_rect)
            
            # Next retry info
            if next_retry_seconds > 0:
                retry_text = f"Next retry in {next_retry_seconds:.1f} seconds"
                retry_surface = self.font_medium.render(retry_text, True, info_color)
                retry_rect = retry_surface.get_rect(center=(self.screen_size[0] // 2, attempt_rect.bottom + 30))
                surface.blit(retry_surface, retry_rect)
            
        except Exception as e:
            logger.error(f"Failed to create retry message: {e}")
        
        return surface


def create_fallback_surface(screen_size: Tuple[int, int], message: str, 
                          background_color: Tuple[int, int, int] = (50, 50, 50)) -> pygame.Surface:
    """
    Create a simple fallback surface with a message.
    
    Args:
        screen_size: (width, height) of the surface
        message: Message to display
        background_color: RGB background color
        
    Returns:
        pygame.Surface with the message
    """
    surface = pygame.Surface(screen_size)
    surface.fill(background_color)
    
    try:
        pygame.font.init()
        font = pygame.font.Font(None, 48)
        text_surface = font.render(message, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(screen_size[0] // 2, screen_size[1] // 2))
        surface.blit(text_surface, text_rect)
    except Exception as e:
        logger.error(f"Failed to create fallback surface: {e}")
    
    return surface