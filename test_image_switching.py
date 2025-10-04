#!/usr/bin/env python3
"""
Simple test to check if image switching logic works.
"""
import sys
import time
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.config_manager import ConfigManager
from carousel.carousel_manager import CarouselManager
from images.image_manager import ImageManager

def test_image_switching():
    """Test basic image switching functionality."""
    print("Testing image switching logic...")
    
    # Load config
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    # Set short interval for testing
    config.playback.interval_seconds = 2
    
    print(f"Day folder: {config.folders.day}")
    print(f"Night folder: {config.folders.night}")
    print(f"Interval: {config.playback.interval_seconds} seconds")
    
    # Initialize components
    image_manager = ImageManager(cache_size=10)
    carousel_manager = CarouselManager(config.playback, config.folders, image_manager)
    
    # Get initial image info
    info = carousel_manager.get_current_image_info()
    print(f"Current mode: {info['mode']}")
    print(f"Total images: {info['total_images']}")
    print(f"Current index: {info['current_index']}")
    print(f"Current image: {info['current_image_path']}")
    
    if info['total_images'] == 0:
        print("ERROR: No images found!")
        return
    
    print("\nTesting image advancement...")
    for i in range(5):
        print(f"\nStep {i+1}:")
        
        # Advance to next image
        next_image = carousel_manager.advance_image()
        print(f"Advanced to: {next_image}")
        
        # Get updated info
        info = carousel_manager.get_current_image_info()
        print(f"New index: {info['current_index']}")
        
        time.sleep(1)
    
    print("\nImage switching test completed!")

if __name__ == "__main__":
    test_image_switching()