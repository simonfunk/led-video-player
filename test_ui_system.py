#!/usr/bin/env python3
"""
Test script for the UI system components.
"""
import sys
import os
import logging
import pygame

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config.config_manager import ConfigManager
from src.display.display_manager import DisplayManager
from src.carousel.carousel_manager import CarouselManager
from src.images.image_manager import ImageManager
from src.ui.ui_integration import create_ui_system


def setup_logging():
    """Set up logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_ui_components():
    """Test UI components initialization and basic functionality."""
    print("Testing UI system components...")
    
    # Initialize pygame
    pygame.init()
    
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Create managers
        display_manager = DisplayManager(config.display)
        image_manager = ImageManager()
        carousel_manager = CarouselManager(
            config.playback, config.folders, image_manager
        )
        
        # Test UI system creation
        ui_integration = create_ui_system(
            config, display_manager, carousel_manager, image_manager
        )
        
        print("✓ UI system created successfully")
        
        # Test status retrieval
        status = ui_integration.get_ui_status()
        print(f"✓ UI status retrieved: {status['is_running']}")
        
        # Test pause/resume
        ui_integration.pause_ui()
        status = ui_integration.get_ui_status()
        print(f"✓ Pause test: {status['is_paused']}")
        
        ui_integration.resume_ui()
        status = ui_integration.get_ui_status()
        print(f"✓ Resume test: {not status['is_paused']}")
        
        # Test hotkey info
        hotkeys = status.get('hotkey_bindings', {})
        print(f"✓ Hotkey bindings loaded: {len(hotkeys)} bindings")
        for key, action in hotkeys.items():
            print(f"  {key}: {action}")
        
        # Clean up
        ui_integration.cleanup_ui_system()
        print("✓ UI system cleaned up successfully")
        
        print("\nAll UI component tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        pygame.quit()


def test_event_handler():
    """Test event handler functionality."""
    print("\nTesting event handler...")
    
    try:
        from src.ui.event_handler import EventHandler, HotkeyAction
        
        # Create event handler
        event_handler = EventHandler()
        
        # Test callback registration
        callback_called = False
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        event_handler.register_callback(HotkeyAction.TOGGLE_PAUSE, test_callback)
        
        # Test hotkey info
        hotkey_info = event_handler.get_hotkey_info()
        print(f"✓ Hotkey info: {len(hotkey_info)} bindings")
        
        # Test statistics
        stats = event_handler.get_event_statistics()
        print(f"✓ Event statistics: {stats}")
        
        print("✓ Event handler tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Event handler test failed: {e}")
        return False


def test_renderer():
    """Test renderer components."""
    print("\nTesting renderer components...")
    
    try:
        from src.ui.renderer import ImageRenderer, TransitionEngine
        from src.config.models import PlaybackConfig
        
        # Initialize pygame for surface creation
        pygame.init()
        pygame.display.set_mode((800, 600))
        screen = pygame.display.get_surface()
        
        # Create renderer
        playback_config = PlaybackConfig()
        background_color = (0, 0, 0)
        
        renderer = ImageRenderer(screen, playback_config, background_color)
        transition_engine = TransitionEngine(screen, playback_config)
        
        # Test basic functionality
        screen_size = renderer.get_screen_size()
        print(f"✓ Renderer created, screen size: {screen_size}")
        
        # Test fallback message rendering
        renderer.render_fallback_message("Test Message")
        print("✓ Fallback message rendered")
        
        # Test instant transition
        transition_engine.instant_transition(None, background_color)
        print("✓ Instant transition completed")
        
        print("✓ Renderer tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Renderer test failed: {e}")
        return False
    finally:
        pygame.quit()


if __name__ == "__main__":
    setup_logging()
    
    print("Starting UI system tests...\n")
    
    success = True
    success &= test_event_handler()
    success &= test_renderer()
    success &= test_ui_components()
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)