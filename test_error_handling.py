#!/usr/bin/env python3
"""
Test script for the error handling system.
"""
import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import pygame
from error_handling.integration import initialize_error_handling
from error_handling.error_handler import ErrorCategory, ErrorInfo, ErrorSeverity
from images.image_manager import ImageManager
from carousel.carousel_manager import Carousel, CarouselManager
from config.models import CarouselMode, PlaybackConfig, FolderConfig


def test_error_handling():
    """Test the error handling system."""
    print("Testing error handling system...")
    
    # Initialize pygame for testing
    pygame.init()
    
    # Initialize error handling
    error_integration = initialize_error_handling()
    error_integration.initialize((1920, 1080))
    
    print("✓ Error handling initialized")
    
    # Test 1: Empty folder handling
    print("\n1. Testing empty folder handling...")
    empty_folder_surface = error_integration.handle_empty_folder("/nonexistent/folder", "day")
    if empty_folder_surface:
        print("✓ Empty folder fallback display created")
    else:
        print("✗ Failed to create empty folder display")
    
    # Test 2: Image loading error
    print("\n2. Testing image loading error...")
    try:
        image_manager = ImageManager()
        result = image_manager.load_image("/nonexistent/image.jpg")
        if result is None:
            print("✓ Image loading error handled correctly")
        else:
            print("✗ Image loading should have failed")
    except Exception as e:
        print(f"✗ Unexpected exception: {e}")
    
    # Test 3: Folder scanning with nonexistent folder
    print("\n3. Testing folder scanning error...")
    try:
        image_manager = ImageManager()
        images = image_manager.scan_folder("/nonexistent/folder")
        if len(images) == 0:
            print("✓ Folder scanning error handled correctly")
        else:
            print("✗ Should have returned empty list")
    except Exception as e:
        print(f"✗ Unexpected exception: {e}")
    
    # Test 4: Carousel with empty folder
    print("\n4. Testing carousel with empty folder...")
    try:
        playback_config = PlaybackConfig()
        folder_config = FolderConfig(day="/nonexistent/day", night="/nonexistent/night")
        carousel_manager = CarouselManager(playback_config, folder_config, image_manager)
        
        info = carousel_manager.get_current_image_info()
        if info['is_empty']:
            print("✓ Empty carousel handled correctly")
        else:
            print("✗ Carousel should be empty")
    except Exception as e:
        print(f"✗ Unexpected exception: {e}")
    
    # Test 5: System health monitoring
    print("\n5. Testing system health monitoring...")
    health_info = error_integration.get_system_health_info()
    print(f"System health: {health_info['system_health']}")
    print(f"Components monitored: {len(health_info['components'])}")
    
    if health_info['system_health'] == 'healthy':
        print("✓ System health monitoring working")
    else:
        print("✗ System health should be healthy initially")
    
    # Test 6: Retry display
    print("\n6. Testing retry display...")
    retry_surface = error_integration.create_retry_display("image loading", 2, 3, 1.5)
    if retry_surface:
        print("✓ Retry display created")
    else:
        print("✗ Failed to create retry display")
    
    # Cleanup
    error_integration.cleanup()
    pygame.quit()
    
    print("\n✓ Error handling tests completed")


if __name__ == "__main__":
    test_error_handling()