# Implementation Plan

- [x] 1. Set up project structure and core configuration system
  - Create directory structure for the slideshow application
  - Implement configuration loading with YAML support and CLI argument parsing
  - Create data models using dataclasses for type safety
  - Set up logging system with file rotation
  - _Requirements: 8.1, 8.2, 8.3, 7.3, 7.4_

- [ ]* 1.1 Write unit tests for configuration system
  - Create tests for YAML parsing, CLI overrides, and validation
  - Test default value application and error handling
  - _Requirements: 8.1, 8.2, 8.3_

- [x] 2. Implement display and monitor management
  - Create monitor detection and enumeration functionality
  - Implement monitor selection logic with fallback behavior
  - Build fullscreen window creation using pygame
  - Add window positioning and always-on-top functionality
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2.1 Implement cursor management
  - Add cursor hiding after inactivity period
  - Handle cursor show/hide state transitions
  - _Requirements: 1.5_

- [ ]* 2.2 Write unit tests for display management
  - Test monitor detection and selection logic
  - Test window creation and positioning
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 3. Create image processing and management system
  - Implement image file discovery and filtering by supported formats
  - Create EXIF orientation processing using Pillow
  - Build image scaling functionality for cover and fit modes
  - Implement image caching system with preloading
  - _Requirements: 2.5, 2.6, 4.1, 4.2, 4.4_

- [ ]* 3.1 Write unit tests for image processing
  - Test EXIF orientation handling
  - Test scaling algorithms for different aspect ratios
  - Test file format support and error handling
  - _Requirements: 2.6, 4.1, 4.2_

- [x] 4. Implement carousel management system
  - Create carousel state management for day and night collections
  - Implement shuffle and sequential ordering logic
  - Build navigation functionality (next, previous, jump to index)
  - Add resume state persistence between application runs
  - _Requirements: 2.1, 2.2, 6.2, 6.3, 6.4_

- [x] 4.1 Implement auto-reload functionality
  - Add periodic folder scanning for new images
  - Handle dynamic image list updates during playback
  - _Requirements: 6.5_

- [ ]* 4.2 Write unit tests for carousel logic
  - Test shuffle algorithm consistency
  - Test index wrapping and navigation
  - Test resume state persistence
  - _Requirements: 6.2, 6.3, 6.4_

- [x] 5. Create scheduling system for day/night switching
  - Implement fixed schedule time calculations
  - Create astronomical sunrise/sunset calculations using Astral
  - Build manual override functionality with hotkey support
  - Add daily sun time recalculation logic
  - _Requirements: 3.1, 3.2, 3.3, 3.5, 5.5, 5.6_

- [x] 5.1 Handle schedule edge cases
  - Implement midnight boundary crossing logic
  - Add offset support for sunrise/sunset times
  - _Requirements: 3.4, 3.5_

- [ ]* 5.2 Write unit tests for scheduling
  - Test fixed schedule calculations across midnight
  - Test sunrise/sunset calculations for various locations
  - Test manual override behavior
  - _Requirements: 3.1, 3.2, 5.5, 5.6_

- [x] 6. Implement user interface and event handling
  - Create main event loop with pygame event processing
  - Implement hotkey handling for all required shortcuts (Esc, Space, arrows, D/N)
  - Build image transition system with crossfade support
  - Add pause/resume functionality
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 4.3_

- [x] 6.1 Implement rendering system
  - Create image rendering with proper scaling and positioning
  - Add background color support
  - Implement smooth transition animations
  - _Requirements: 4.1, 4.2, 4.3, 4.5_

- [ ]* 6.2 Write unit tests for UI components
  - Test hotkey event processing
  - Test transition timing and calculations
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 7. Add comprehensive error handling and recovery
  - Implement error handling for corrupted or unreadable images
  - Create empty folder detection with fallback messaging
  - Add graceful degradation for display and system errors
  - Implement retry logic for recoverable errors
  - _Requirements: 4.4, 7.1, 7.2, 7.5_

- [ ]* 7.1 Write unit tests for error handling
  - Test error recovery mechanisms
  - Test fallback behavior for various error conditions
  - _Requirements: 7.1, 7.2, 7.5_

- [-] 8. Create application controller and main entry point
  - Build central application controller coordinating all components
  - Implement component lifecycle management
  - Create main.py entry point with argument parsing
  - Add single instance enforcement to prevent duplicates
  - _Requirements: 9.2, 8.2_

- [ ] 8.1 Implement graceful shutdown
  - Add cleanup procedures for resources and state
  - Handle exit signals and cleanup on application termination
  - _Requirements: 5.1, 9.4_

- [ ]* 8.2 Write integration tests for application controller
  - Test component coordination and lifecycle
  - Test shutdown procedures and cleanup
  - _Requirements: 5.1, 9.2_

- [x] 9. Add cross-platform scheduling integration support
  - Create force day/night command line flags for scheduled switching
  - Implement privilege validation to ensure no admin rights required
  - Add helpful error messages for missing dependencies
  - Create example scheduling configuration documentation for:
    - Windows Task Scheduler
    - macOS launchd (Launch Agents/Daemons)
  - _Requirements: 9.1, 9.3, 9.4_

- [ ]* 9.1 Write tests for Task Scheduler integration
  - Test force mode command line arguments
  - Test single instance enforcement
  - _Requirements: 9.1, 9.2, 9.3_

- [x] 10. Create project packaging and documentation
  - Create requirements.txt with pinned dependency versions
  - Write example configuration files with comprehensive documentation
  - Create setup instructions for Windows deployment
  - Add README with usage examples and troubleshooting guide
  - _Requirements: 8.1, 8.4, 9.4_

- [x] 10.1 Validate desktop wallpaper isolation
  - Ensure application never modifies Windows wallpaper
  - Test window behavior to confirm no desktop interference
  - Verify proper window focus and always-on-top behavior
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_