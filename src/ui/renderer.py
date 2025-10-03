"""
Rendering system for image display with scaling, positioning, and transitions.
"""
import logging
import time
from typing import Optional, Tuple
import pygame
from src.config.models import PlaybackConfig


logger = logging.getLogger(__name__)


class ImageRenderer:
    """Handles image rendering with proper scaling, positioning, and background support."""
    
    def __init__(self, screen: pygame.Surface, playback_config: PlaybackConfig, background_color: Tuple[int, int, int]):
        """
        Initialize the image renderer.
        
        Args:
            screen: pygame Surface to render to
            playback_config: Playback configuration
            background_color: RGB tuple for background color
        """
        self.screen = screen
        self.playback_config = playback_config
        self.background_color = background_color
        self.screen_size = screen.get_size()
        
    def render_image(self, image_surface: pygame.Surface, center: bool = True) -> None:
        """
        Render an image on the screen with proper positioning.
        
        Args:
            image_surface: pygame Surface containing the image to render
            center: Whether to center the image on screen
        """
        # Clear screen with background color
        self.screen.fill(self.background_color)
        
        if image_surface is None:
            return
        
        # Calculate position
        if center:
            image_rect = image_surface.get_rect()
            screen_rect = self.screen.get_rect()
            image_rect.center = screen_rect.center
            position = image_rect.topleft
        else:
            position = (0, 0)
        
        # Blit the image to screen
        self.screen.blit(image_surface, position)
    
    def render_fallback_message(self, message: str, font_size: int = 48) -> None:
        """
        Render a fallback text message when no images are available.
        
        Args:
            message: Text message to display
            font_size: Font size for the message
        """
        # Clear screen with background color
        self.screen.fill(self.background_color)
        
        try:
            # Initialize font
            pygame.font.init()
            font = pygame.font.Font(None, font_size)
            
            # Create text surface
            text_color = (255, 255, 255)  # White text
            text_surface = font.render(message, True, text_color)
            
            # Center the text
            text_rect = text_surface.get_rect()
            screen_rect = self.screen.get_rect()
            text_rect.center = screen_rect.center
            
            # Render the text
            self.screen.blit(text_surface, text_rect)
            
        except Exception as e:
            logger.error(f"Failed to render fallback message: {e}")
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get the screen size."""
        return self.screen_size


class TransitionEngine:
    """Handles smooth transitions between images with crossfade support."""
    
    def __init__(self, screen: pygame.Surface, playback_config: PlaybackConfig):
        """
        Initialize the transition engine.
        
        Args:
            screen: pygame Surface to render to
            playback_config: Playback configuration containing transition settings
        """
        self.screen = screen
        self.playback_config = playback_config
        self.transition_duration_ms = playback_config.transition_ms
        
    def crossfade_transition(self, from_surface: Optional[pygame.Surface], 
                           to_surface: Optional[pygame.Surface],
                           background_color: Tuple[int, int, int],
                           progress_callback: Optional[callable] = None) -> None:
        """
        Perform a crossfade transition between two images.
        
        Args:
            from_surface: Source image surface (can be None)
            to_surface: Target image surface (can be None)
            background_color: RGB tuple for background color
            progress_callback: Optional callback function called with progress (0.0 to 1.0)
        """
        if self.transition_duration_ms <= 0:
            # No transition, just show the target image
            self.screen.fill(background_color)
            if to_surface:
                self._center_blit(to_surface)
            return
        
        start_time = time.time()
        duration_seconds = self.transition_duration_ms / 1000.0
        
        # Create surfaces for blending if needed
        screen_size = self.screen.get_size()
        
        # Prepare surfaces for blending
        if from_surface:
            from_surface = self._prepare_surface_for_blending(from_surface, screen_size)
        if to_surface:
            to_surface = self._prepare_surface_for_blending(to_surface, screen_size)
        
        while True:
            current_time = time.time()
            elapsed = current_time - start_time
            
            if elapsed >= duration_seconds:
                # Transition complete
                progress = 1.0
            else:
                # Calculate progress (0.0 to 1.0)
                progress = elapsed / duration_seconds
            
            # Apply easing function for smoother transition
            eased_progress = self._ease_in_out(progress)
            
            # Render the blended frame
            self._render_crossfade_frame(from_surface, to_surface, eased_progress, background_color)
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(progress)
            
            # Update display
            pygame.display.flip()
            
            if progress >= 1.0:
                break
            
            # Small delay to control frame rate
            time.sleep(0.016)  # ~60 FPS
    
    def _prepare_surface_for_blending(self, surface: pygame.Surface, target_size: Tuple[int, int]) -> pygame.Surface:
        """
        Prepare a surface for blending by ensuring it's the right size and format.
        
        Args:
            surface: Source surface
            target_size: Target size (width, height)
            
        Returns:
            Prepared surface ready for blending
        """
        # Create a new surface with the target size
        prepared_surface = pygame.Surface(target_size, pygame.SRCALPHA)
        prepared_surface = prepared_surface.convert_alpha()
        
        # Center the original surface on the prepared surface
        surface_rect = surface.get_rect()
        target_rect = prepared_surface.get_rect()
        surface_rect.center = target_rect.center
        
        prepared_surface.blit(surface, surface_rect)
        
        return prepared_surface
    
    def _render_crossfade_frame(self, from_surface: Optional[pygame.Surface], 
                               to_surface: Optional[pygame.Surface], 
                               progress: float,
                               background_color: Tuple[int, int, int]) -> None:
        """
        Render a single frame of the crossfade transition.
        
        Args:
            from_surface: Source image surface
            to_surface: Target image surface
            progress: Transition progress (0.0 to 1.0)
            background_color: RGB tuple for background color
        """
        # Clear screen
        self.screen.fill(background_color)
        
        if from_surface is None and to_surface is None:
            return
        
        if from_surface is None:
            # Only target image, fade in
            if to_surface:
                alpha = int(255 * progress)
                to_surface.set_alpha(alpha)
                self.screen.blit(to_surface, (0, 0))
        elif to_surface is None:
            # Only source image, fade out
            alpha = int(255 * (1.0 - progress))
            from_surface.set_alpha(alpha)
            self.screen.blit(from_surface, (0, 0))
        else:
            # Both images, crossfade
            from_alpha = int(255 * (1.0 - progress))
            to_alpha = int(255 * progress)
            
            from_surface.set_alpha(from_alpha)
            to_surface.set_alpha(to_alpha)
            
            self.screen.blit(from_surface, (0, 0))
            self.screen.blit(to_surface, (0, 0))
    
    def _center_blit(self, surface: pygame.Surface) -> None:
        """Center and blit a surface to the screen."""
        surface_rect = surface.get_rect()
        screen_rect = self.screen.get_rect()
        surface_rect.center = screen_rect.center
        self.screen.blit(surface, surface_rect)
    
    def _ease_in_out(self, t: float) -> float:
        """
        Apply ease-in-out easing function for smoother transitions.
        
        Args:
            t: Input value (0.0 to 1.0)
            
        Returns:
            Eased value (0.0 to 1.0)
        """
        # Cubic ease-in-out function
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    def instant_transition(self, to_surface: Optional[pygame.Surface], 
                          background_color: Tuple[int, int, int]) -> None:
        """
        Perform an instant transition (no animation).
        
        Args:
            to_surface: Target image surface
            background_color: RGB tuple for background color
        """
        self.screen.fill(background_color)
        if to_surface:
            self._center_blit(to_surface)
        pygame.display.flip()