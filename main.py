#!/usr/bin/env python3
"""
Main entry point for the Dual Carousel Slideshow application.
"""
import sys
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.config_manager import ConfigManager, create_cli_parser
from config.logging_setup import LoggingSetup
from error_handling.integration import initialize_error_handling
from system.privilege_validator import PrivilegeValidator
from system.dependency_validator import DependencyValidator
from system.single_instance import SingleInstanceEnforcer


def main():
    """Main application entry point with comprehensive error handling."""
    error_integration = None
    single_instance = None
    
    try:
        # Parse command line arguments
        parser = create_cli_parser()
        args = parser.parse_args()
        
        # Validate dependencies first (before logging setup)
        print("Checking dependencies...")
        dependency_validator = DependencyValidator()
        dep_result = dependency_validator.validate_dependencies()
        
        if not dep_result['all_critical_available']:
            print("\nCRITICAL ERROR: Required dependencies are missing!")
            print("=" * 60)
            for instruction in dep_result['installation_instructions']:
                if instruction.strip():
                    print(instruction)
            print("=" * 60)
            print("\nPlease install the missing dependencies and try again.")
            return 1
        
        # Check for single instance enforcement
        single_instance = SingleInstanceEnforcer()
        if not single_instance.acquire_lock():
            print("Another instance of the application is already running.")
            print("Only one instance can run at a time.")
            return 1
        
        # Convert args to dictionary for config manager
        cli_args = {
            'monitor_index': args.monitor_index,
            'day_folder': args.day_folder,
            'night_folder': args.night_folder,
            'interval': args.interval,
            'shuffle': args.shuffle,
            'no_shuffle': args.no_shuffle,
            'log_level': args.log_level,
            'force_day': args.force_day,
            'force_night': args.force_night,
        }
        
        # Load configuration with error handling
        try:
            config_manager = ConfigManager()
            config = config_manager.load_config(
                config_path=args.config,
                cli_args=cli_args
            )
        except Exception as e:
            print(f"Configuration error: {e}")
            print("Using default configuration...")
            config_manager = ConfigManager()
            config = config_manager.load_config()  # Load defaults
        
        # Set up logging with error handling
        try:
            LoggingSetup.setup_logging(config.logging)
            logger = LoggingSetup.get_logger(__name__)
        except Exception as e:
            print(f"Logging setup error: {e}")
            # Fallback to basic logging
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger(__name__)
        
        logger.info("Dual Carousel Slideshow starting...")
        
        # Log dependency status
        dependency_validator.log_dependency_status(dep_result)
        
        # Validate privileges (warn if running with elevated privileges)
        privilege_validator = PrivilegeValidator()
        privilege_result = privilege_validator.validate_privileges()
        privilege_validator.log_privilege_status(privilege_result)
        
        # Log single instance status
        lock_info = single_instance.get_lock_info()
        logger.info(f"Single instance lock acquired: {lock_info['lock_file_path']}")
        
        # Initialize error handling system
        try:
            error_integration = initialize_error_handling()
            logger.info("Error handling system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize error handling: {e}")
            # Continue without advanced error handling
        
        logger.info(f"Configuration loaded successfully")
        logger.info(f"Day folder: {config.folders.day}")
        logger.info(f"Night folder: {config.folders.night}")
        logger.info(f"Monitor index: {config.display.monitor_index}")
        logger.info(f"Schedule mode: {config.schedule.mode}")
        logger.info(f"Shuffle enabled: {config.playback.shuffle}")
        
        # Handle force mode flags for scheduler integration
        force_mode = None
        if args.force_day:
            force_mode = "day"
            logger.info("Force day mode enabled (scheduler integration)")
        elif args.force_night:
            force_mode = "night"
            logger.info("Force night mode enabled (scheduler integration)")
        
        if force_mode:
            logger.info(f"Application will override any manual mode selection and switch to {force_mode} mode")
        
        # Validate critical folders exist
        try:
            day_folder = Path(config.folders.day)
            night_folder = Path(config.folders.night)
            
            if not day_folder.exists():
                logger.warning(f"Day folder does not exist: {config.folders.day}")
                day_folder.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created day folder: {config.folders.day}")
            
            if not night_folder.exists():
                logger.warning(f"Night folder does not exist: {config.folders.night}")
                night_folder.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created night folder: {config.folders.night}")
                
        except Exception as e:
            logger.error(f"Failed to validate/create folders: {e}")
            # Continue anyway - error handling will manage empty folders
        
        # Initialize application components
        logger.info("Initializing application components...")
        
        # Import required components
        from src.display.display_manager import DisplayManager
        from src.carousel.carousel_manager import CarouselManager
        from src.images.image_manager import ImageManager
        from src.ui.ui_integration import create_ui_system
        from src.scheduler.schedule_manager import ScheduleManager
        
        # Initialize core components
        display_manager = DisplayManager(config.display)
        image_manager = ImageManager(cache_size=50)  # Use default cache size
        carousel_manager = CarouselManager(config.playback, config.folders, image_manager)
        
        logger.info("Core components initialized")
        
        # Initialize scheduler
        scheduler = ScheduleManager(config.schedule)
        logger.info("Scheduler initialized")
        
        # Create and initialize UI system
        ui_system = create_ui_system(config, display_manager, carousel_manager, image_manager)
        
        # Set up scheduler integration
        # Set up the callback for when scheduler changes mode
        scheduler.mode_change_callback = ui_system.handle_scheduler_mode_change
        logger.info("Scheduler integration enabled")
        
        # Handle force mode from command line
        if force_mode:
            from config.models import CarouselMode
            mode = CarouselMode.DAY if force_mode == "day" else CarouselMode.NIGHT
            ui_system.force_ui_mode(mode)
            logger.info(f"Applied force mode: {force_mode}")
        
        # Check system health before starting
        if error_integration:
            health_info = error_integration.get_system_health_info()
            logger.info(f"System health: {health_info['system_health']}")
        
        logger.info("Starting slideshow...")
        
        # Start the main UI loop (this will block until exit)
        ui_system.start_ui_loop()
        
        logger.info("Slideshow stopped")
        
        # Clean up
        logger.info("Scheduler stopped")
        
        ui_system.cleanup_ui_system()
        logger.info("UI system cleaned up")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 1
    except Exception as e:
        if 'logger' in locals():
            logger.critical(f"Unhandled application error: {e}", exc_info=True)
        else:
            print(f"Critical application error: {e}")
        return 1
    finally:
        # Clean up resources
        if single_instance:
            try:
                single_instance.release_lock()
            except Exception as e:
                if 'logger' in locals():
                    logger.error(f"Error releasing single instance lock: {e}")
        
        if error_integration:
            try:
                error_integration.cleanup()
            except Exception as e:
                if 'logger' in locals():
                    logger.error(f"Error during cleanup: {e}")


if __name__ == "__main__":
    sys.exit(main())