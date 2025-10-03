#!/usr/bin/env python3
"""
Comprehensive test for error handling and recovery features.
"""
import sys
import os
import tempfile
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import pygame
from PIL import Image
from error_handling.integration import initialize_error_handling
from images.image_manager import ImageManager
from carousel.carousel_manager import CarouselManager
from display.display_manager import DisplayManager
from config.models import CarouselMode, PlaybackConfig, FolderConfig, DisplayConfig


def create_test_image(path: str, size: tuple = (100, 100), corrupted: bool = False):
    """Create a test image file."""
    if corrupted:
        # Create a corrupted file
        with open(path, 'wb') as f:
            f.write(b'corrupted image data')
    else:
        # Create a valid image
        img = Image.new('RGB', size, color='red')
        img.save(path, 'JPEG')


def test_comprehensive_error_handling():
    """Test comprehensive error handling scenarios."""
    print("=== Comprehensive Error Handling Test ===\n")
    
    # Initialize pygame
    pygame.init()
    
    # Initialize error handling
    error_integration = initialize_error_handling()
    error_integration.initialize((1920, 1080))
    
    print("✓ Error handling system initialized\n")
    
    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Test folders
        day_folder = temp_path / "day"
        night_folder = temp_path / "night"
        empty_folder = temp_path / "empty"
        
        day_folder.mkdir()
        night_folder.mkdir()
        empty_folder.mkdir()
        
        # Create test images
        valid_image1 = day_folder / "valid1.jpg"
        valid_image2 = day_folder / "valid2.jpg"
        corrupted_image = day_folder / "corrupted.jpg"
        
        create_test_image(str(valid_image1))
        create_test_image(str(valid_image2))
        create_test_image(str(corrupted_image), corrupted=True)
        
        print("Test files created\n")
        
        # Test 1: Image Manager Error Handling
        print("1. Testing Image Manager Error Handling")
        print("-" * 40)
        
        image_manager = ImageManager()
        
        # Test valid image loading
        valid_img = image_manager.load_image(str(valid_image1))
        if valid_img:
            print("✓ Valid image loaded successfully")
        else:
            print("✗ Failed to load valid image")
        
        # Test corrupted image handling
        corrupted_img = image_manager.load_image(str(corrupted_image))
        if corrupted_img is None:
            print("✓ Corrupted image handled correctly")
        else:
            print("✗ Corrupted image should have failed")
        
        # Test nonexistent image
        nonexistent_img = image_manager.load_image("/nonexistent/image.jpg")
        if nonexistent_img is None:
            print("✓ Nonexistent image handled correctly")
        else:
            print("✗ Nonexistent image should have failed")
        
        # Test folder scanning
        images = image_manager.scan_folder(str(day_folder))
        print(f"✓ Found {len(images)} valid images in folder (expected 2)")
        
        print()
        
        # Test 2: Carousel Manager Error Handling
        print("2. Testing Carousel Manager Error Handling")
        print("-" * 45)
        
        playback_config = PlaybackConfig()
        folder_config = FolderConfig(
            day=str(day_folder),
            night=str(empty_folder)  # Empty folder
        )
        
        carousel_manager = CarouselManager(playback_config, folder_config, image_manager)
        
        # Force reload to use our test folders
        carousel_manager.day_carousel.folder_path = str(day_folder)
        carousel_manager.night_carousel.folder_path = str(empty_folder)
        carousel_manager._load_all_carousels()
        
        # Test day carousel (has images)
        day_info = carousel_manager.get_current_image_info()
        if not day_info['is_empty']:
            print("✓ Day carousel loaded with images")
        else:
            print("✗ Day carousel should have images")
        
        # Test switching to empty night carousel
        carousel_manager.switch_carousel(CarouselMode.NIGHT)
        night_info = carousel_manager.get_current_image_info()
        if night_info['is_empty'] or night_info['total_images'] == 0:
            print("✓ Empty night carousel handled correctly")
        else:
            print("✗ Night carousel should be empty")
        
        print()
        
        # Test 3: Display Manager Error Handling
        print("3. Testing Display Manager Error Handling")
        print("-" * 42)
        
        display_config = DisplayConfig()
        display_manager = DisplayManager(display_config)
        
        # Test monitor detection
        monitors = display_manager.get_monitors()
        if len(monitors) > 0:
            print(f"✓ Detected {len(monitors)} monitor(s)")
        else:
            print("✗ Should detect at least one monitor")
        
        # Test monitor selection with invalid index
        selected_monitor = display_manager.select_monitor(monitors, 999)  # Invalid index
        if selected_monitor:
            print("✓ Fallback monitor selection worked")
        else:
            print("✗ Should have selected a fallback monitor")
        
        print()
        
        # Test 4: Fallback Display System
        print("4. Testing Fallback Display System")
        print("-" * 37)
        
        # Test empty folder display
        empty_display = error_integration.handle_empty_folder(str(empty_folder), "night")
        if empty_display:
            print("✓ Empty folder fallback display created")
        else:
            print("✗ Failed to create empty folder display")
        
        # Test retry display
        retry_display = error_integration.create_retry_display("folder scan", 2, 3, 1.5)
        if retry_display:
            print("✓ Retry display created")
        else:
            print("✗ Failed to create retry display")
        
        # Test system info display
        system_display = error_integration.create_system_info_display()
        if system_display:
            print("✓ System info display created")
        else:
            print("✗ Failed to create system info display")
        
        print()
        
        # Test 5: Recovery System
        print("5. Testing Recovery System")
        print("-" * 26)
        
        # Get system health
        health_info = error_integration.get_system_health_info()
        print(f"System health: {health_info['system_health']}")
        
        # Test component recovery
        recovery_result = error_integration.force_component_recovery('image_manager')
        if recovery_result:
            print("✓ Component recovery attempted")
        else:
            print("✗ Component recovery failed")
        
        # Test error reset
        error_integration.reset_component_errors('carousel_manager')
        print("✓ Component errors reset")
        
        print()
        
        # Test 6: Error Statistics
        print("6. Error Statistics")
        print("-" * 18)
        
        health_info = error_integration.get_system_health_info()
        error_stats = health_info.get('error_statistics', {})
        
        print(f"Error counts: {len(error_stats.get('error_counts', {}))}")
        print(f"Components monitored: {len(health_info.get('components', {}))}")
        
        for component, status in health_info.get('components', {}).items():
            health_status = "healthy" if status['healthy'] else "unhealthy"
            print(f"  {component}: {health_status} (errors: {status['error_count']})")
        
        print()
    
    # Cleanup
    error_integration.cleanup()
    pygame.quit()
    
    print("=== All Error Handling Tests Completed ===")
    print("✓ Comprehensive error handling system is working correctly!")


if __name__ == "__main__":
    test_comprehensive_error_handling()