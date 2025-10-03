#!/usr/bin/env python3
"""
Visual test for the carousel system - displays images on screen.
This test will show the carousel functionality working with real image display.
"""
import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.abspath('.'))

import pygame
from src.config.models import PlaybackConfig, FolderConfig, CarouselMode, DisplayConfig
from src.images.image_manager import ImageManager
from src.carousel.carousel_manager import CarouselManager
from src.display.display_manager import DisplayManager


def test_visual_carousel():
    """Test carousel with actual visual display."""
    print("Starting visual carousel test...")
    print("Controls:")
    print("  SPACE - Next image")
    print("  BACKSPACE - Previous image")
    print("  N - Switch to Night mode")
    print("  D - Switch to Day mode")
    print("  R - Reload images")
    print("  ESC or Q - Quit")
    print("  1,2,3... - Jump to image index")
    
    # Initialize pygame
    pygame.init()
    
    # Configuration
    display_config = DisplayConfig(
        monitor_index=0,  # Use primary monitor for testing
        always_on_top=False,
        hide_cursor_after_ms=3000,
        background_color="#000000"
    )
    
    playback_config = PlaybackConfig(
        shuffle=False,  # Sequential for easier testing
        resume_index_between_runs=True,
        reload_images_every_seconds=0,  # Disable auto-reload
        interval_seconds=3,  # 3 second auto-advance for demo
        fit_mode="cover",
        transition_ms=300
    )
    
    folder_config = FolderConfig(
        day="./images/day",
        night="./images/night",
        include_subfolders=True
    )
    
    try:
        # Create managers
        image_manager = ImageManager()
        display_manager = DisplayManager(display_config)
        carousel_manager = CarouselManager(
            playback_config, 
            folder_config, 
            image_manager,
            "./test_visual_state.json"
        )
        
        # Set up display
        monitors = display_manager.get_monitors()
        selected_monitor = display_manager.select_monitor(monitors, display_config.monitor_index)
        screen = display_manager.create_fullscreen_window(selected_monitor)
        
        # Get screen size for image scaling
        screen_size = display_manager.get_screen_size()
        print(f"Display size: {screen_size[0]}x{screen_size[1]}")
        
        # Display initial info
        info = carousel_manager.get_carousel_info()
        print(f"Day images: {info['day_carousel']['image_count']}")
        print(f"Night images: {info['night_carousel']['image_count']}")
        
        if info['day_carousel']['image_count'] == 0 and info['night_carousel']['image_count'] == 0:
            print("No images found! Make sure there are images in ./images/day and ./images/night")
            return
        
        # Main display loop
        clock = pygame.time.Clock()
        running = True
        last_auto_advance = time.time()
        current_image_surface = None
        
        # Load and display first image
        def load_and_display_current_image():
            nonlocal current_image_surface
            current_path = carousel_manager.get_current_image_path()
            if current_path:
                print(f"Loading: {os.path.basename(current_path)}")
                current_image_surface = image_manager.get_cached_image(
                    current_path, screen_size, playback_config.fit_mode
                )
                if current_image_surface:
                    # Clear screen with background color
                    bg_color = display_manager._parse_color(display_config.background_color)
                    screen.fill(bg_color)
                    
                    # Center the image on screen
                    img_rect = current_image_surface.get_rect()
                    screen_rect = screen.get_rect()
                    img_rect.center = screen_rect.center
                    
                    screen.blit(current_image_surface, img_rect)
                    pygame.display.flip()
                    
                    # Show current status
                    current_info = carousel_manager.get_current_image_info()
                    print(f"Displaying: {current_info['mode']} mode, "
                          f"image {current_info['current_index'] + 1}/{current_info['total_images']}")
                else:
                    print(f"Failed to load image: {current_path}")
            else:
                print("No current image available")
        
        # Load initial image
        load_and_display_current_image()
        
        while running:
            current_time = time.time()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        running = False
                    
                    elif event.key == pygame.K_SPACE:
                        # Next image
                        carousel_manager.advance_image()
                        load_and_display_current_image()
                        last_auto_advance = current_time  # Reset auto-advance timer
                    
                    elif event.key == pygame.K_BACKSPACE:
                        # Previous image
                        carousel_manager.previous_image()
                        load_and_display_current_image()
                        last_auto_advance = current_time
                    
                    elif event.key == pygame.K_n:
                        # Switch to night mode
                        carousel_manager.switch_carousel(CarouselMode.NIGHT)
                        load_and_display_current_image()
                        print("Switched to NIGHT mode")
                    
                    elif event.key == pygame.K_d:
                        # Switch to day mode
                        carousel_manager.switch_carousel(CarouselMode.DAY)
                        load_and_display_current_image()
                        print("Switched to DAY mode")
                    
                    elif event.key == pygame.K_r:
                        # Reload images
                        print("Reloading images...")
                        result = carousel_manager.reload_images()
                        print(f"Reloaded: {result}")
                        load_and_display_current_image()
                    
                    elif event.key >= pygame.K_1 and event.key <= pygame.K_9:
                        # Jump to specific index (1-9)
                        index = event.key - pygame.K_1
                        carousel_manager.jump_to_index(index)
                        load_and_display_current_image()
                        last_auto_advance = current_time
                
                elif event.type == pygame.MOUSEMOTION:
                    display_manager.handle_mouse_activity()
            
            # Auto-advance images
            if current_time - last_auto_advance >= playback_config.interval_seconds:
                carousel_manager.advance_image()
                load_and_display_current_image()
                last_auto_advance = current_time
            
            # Update cursor visibility
            display_manager.update_cursor_visibility()
            
            # Control frame rate
            clock.tick(60)
        
        print("Visual test completed")
        
    except Exception as e:
        print(f"Error in visual test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if 'carousel_manager' in locals():
            carousel_manager.cleanup()
        if 'display_manager' in locals():
            display_manager.cleanup()
        if 'image_manager' in locals():
            image_manager.cleanup()
        pygame.quit()


def test_quick_visual():
    """Quick visual test that just shows a few images then exits."""
    print("Quick visual test - will show 3 images then exit...")
    
    pygame.init()
    
    # Simple configuration
    display_config = DisplayConfig(monitor_index=0, background_color="#222222")
    playback_config = PlaybackConfig(shuffle=False, fit_mode="cover")
    folder_config = FolderConfig(day="./images/day", night="./images/night")
    
    try:
        # Create managers
        image_manager = ImageManager()
        display_manager = DisplayManager(display_config)
        carousel_manager = CarouselManager(playback_config, folder_config, image_manager)
        
        # Set up display
        monitors = display_manager.get_monitors()
        selected_monitor = display_manager.select_monitor(monitors, 0)
        screen = display_manager.create_fullscreen_window(selected_monitor)
        screen_size = display_manager.get_screen_size()
        
        # Show info
        info = carousel_manager.get_carousel_info()
        print(f"Found {info['day_carousel']['image_count']} day images, "
              f"{info['night_carousel']['image_count']} night images")
        
        if info['day_carousel']['image_count'] > 0 or info['night_carousel']['image_count'] > 0:
            # Show 3 images with 2 second intervals
            for i in range(3):
                current_path = carousel_manager.get_current_image_path()
                if current_path:
                    print(f"Showing image {i+1}: {os.path.basename(current_path)}")
                    
                    # Load and display image
                    image_surface = image_manager.get_cached_image(
                        current_path, screen_size, playback_config.fit_mode
                    )
                    
                    if image_surface:
                        # Clear and center image
                        bg_color = display_manager._parse_color(display_config.background_color)
                        screen.fill(bg_color)
                        
                        img_rect = image_surface.get_rect()
                        screen_rect = screen.get_rect()
                        img_rect.center = screen_rect.center
                        
                        screen.blit(image_surface, img_rect)
                        pygame.display.flip()
                        
                        # Wait 2 seconds
                        time.sleep(2)
                        
                        # Advance to next image
                        carousel_manager.advance_image()
                    else:
                        print(f"Failed to load image: {current_path}")
                        break
                else:
                    print("No more images")
                    break
            
            print("Quick test completed!")
        else:
            print("No images found to display")
    
    except Exception as e:
        print(f"Error in quick test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if 'carousel_manager' in locals():
            carousel_manager.cleanup()
        if 'display_manager' in locals():
            display_manager.cleanup()
        if 'image_manager' in locals():
            image_manager.cleanup()
        pygame.quit()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        test_quick_visual()
    else:
        test_visual_carousel()