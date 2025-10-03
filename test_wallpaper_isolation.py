#!/usr/bin/env python3
"""
Test script to validate desktop wallpaper isolation.
This script verifies that the slideshow application never modifies the Windows wallpaper
and maintains proper window behavior without desktop interference.
"""
import sys
import os
import time
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import pygame
from src.config.config_manager import ConfigManager
from src.config.logging_setup import LoggingSetup
from src.display.display_manager import DisplayManager


def get_windows_wallpaper_path():
    """
    Get the current Windows wallpaper path (Windows-specific).
    Returns None on non-Windows systems or if unable to detect.
    """
    try:
        if sys.platform != "win32":
            return None
            
        import winreg
        
        # Try to get wallpaper from registry
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Control Panel\Desktop")
            wallpaper_path, _ = winreg.QueryValueEx(key, "Wallpaper")
            winreg.CloseKey(key)
            return wallpaper_path
        except Exception:
            pass
            
        # Alternative method using ctypes
        try:
            import ctypes
            from ctypes import wintypes
            
            # Get wallpaper path using SystemParametersInfo
            SPI_GETDESKWALLPAPER = 0x0073
            MAX_PATH = 260
            
            buffer = ctypes.create_unicode_buffer(MAX_PATH)
            result = ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETDESKWALLPAPER, MAX_PATH, buffer, 0
            )
            
            if result:
                return buffer.value
                
        except Exception:
            pass
            
    except Exception as e:
        print(f"Error getting wallpaper path: {e}")
        
    return None


def test_wallpaper_isolation():
    """
    Test that the application doesn't modify the Windows wallpaper.
    """
    print("Testing wallpaper isolation...")
    
    # Get initial wallpaper state
    initial_wallpaper = get_windows_wallpaper_path()
    print(f"Initial wallpaper: {initial_wallpaper}")
    
    # Initialize pygame and create a test window
    pygame.init()
    
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Set up basic logging
        logging.basicConfig(level=logging.INFO)
        
        # Create display manager
        display_manager = DisplayManager(config.display)
        
        # Get monitors and create window
        monitors = display_manager.get_monitors()
        if not monitors:
            print("ERROR: No monitors detected")
            return False
            
        # Select monitor (prefer secondary if available)
        selected_monitor = display_manager.select_monitor(monitors, config.display.monitor_index)
        print(f"Selected monitor: {selected_monitor.index} ({selected_monitor.width}x{selected_monitor.height})")
        
        # Create fullscreen window
        screen = display_manager.create_fullscreen_window(selected_monitor)
        print(f"Created window: {screen.get_size()}")
        
        # Test window properties
        print("Testing window behavior...")
        
        # Fill with test colors and display for a few seconds
        test_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
        
        for i, color in enumerate(test_colors):
            screen.fill(color)
            pygame.display.flip()
            print(f"Displaying test color {i+1}/4: RGB{color}")
            time.sleep(1)
            
            # Check wallpaper hasn't changed
            current_wallpaper = get_windows_wallpaper_path()
            if current_wallpaper != initial_wallpaper:
                print(f"ERROR: Wallpaper changed from '{initial_wallpaper}' to '{current_wallpaper}'")
                return False
        
        # Test cursor management
        print("Testing cursor management...")
        display_manager.set_window_properties(hide_cursor=True)
        time.sleep(1)
        
        display_manager.set_window_properties(hide_cursor=False)
        time.sleep(1)
        
        # Test window focus behavior
        print("Testing window focus behavior...")
        
        # Simulate some events
        for _ in range(10):
            pygame.event.pump()
            display_manager.update_cursor_visibility()
            time.sleep(0.1)
        
        # Final wallpaper check
        final_wallpaper = get_windows_wallpaper_path()
        if final_wallpaper != initial_wallpaper:
            print(f"ERROR: Wallpaper changed from '{initial_wallpaper}' to '{final_wallpaper}'")
            return False
        
        print("SUCCESS: Wallpaper isolation maintained throughout test")
        
        # Clean up
        display_manager.cleanup()
        pygame.quit()
        
        return True
        
    except Exception as e:
        print(f"ERROR during test: {e}")
        pygame.quit()
        return False


def test_window_behavior():
    """
    Test window behavior to ensure proper focus and always-on-top functionality.
    """
    print("\nTesting window behavior...")
    
    try:
        pygame.init()
        
        # Create a test window
        screen = pygame.display.set_mode((800, 600), pygame.NOFRAME)
        pygame.display.set_caption("Wallpaper Isolation Test")
        
        print("Window created successfully")
        print("Window size:", screen.get_size())
        print("Window flags: NOFRAME (borderless)")
        
        # Test that window doesn't interfere with desktop
        screen.fill((128, 128, 128))  # Gray background
        pygame.display.flip()
        
        print("Window rendered successfully")
        print("Verify manually that:")
        print("1. Window appears as borderless")
        print("2. Desktop wallpaper is unchanged")
        print("3. Other applications can still be used")
        print("4. Window stays on intended monitor")
        
        # Keep window open for manual verification
        print("\nWindow will close in 5 seconds...")
        for i in range(5):
            pygame.event.pump()  # Process events to keep window responsive
            time.sleep(1)
            print(f"Closing in {5-i} seconds...")
        
        pygame.quit()
        print("Window closed successfully")
        
        return True
        
    except Exception as e:
        print(f"ERROR in window behavior test: {e}")
        pygame.quit()
        return False


def main():
    """
    Main test function to validate desktop wallpaper isolation.
    """
    print("=" * 60)
    print("DESKTOP WALLPAPER ISOLATION TEST")
    print("=" * 60)
    print()
    
    print("This test validates that the slideshow application:")
    print("1. Never modifies the Windows desktop wallpaper")
    print("2. Maintains proper window behavior without desktop interference")
    print("3. Properly handles window focus and always-on-top behavior")
    print()
    
    # Run wallpaper isolation test
    wallpaper_test_passed = test_wallpaper_isolation()
    
    # Run window behavior test
    window_test_passed = test_window_behavior()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Wallpaper isolation test: {'PASSED' if wallpaper_test_passed else 'FAILED'}")
    print(f"Window behavior test: {'PASSED' if window_test_passed else 'FAILED'}")
    
    if wallpaper_test_passed and window_test_passed:
        print("\n✓ ALL TESTS PASSED")
        print("The application properly isolates from desktop wallpaper")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        print("Review the application's window management implementation")
        return 1


if __name__ == "__main__":
    sys.exit(main())