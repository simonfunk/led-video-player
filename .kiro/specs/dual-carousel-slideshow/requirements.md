# Requirements Document

## Introduction

This document outlines the requirements for a dual-carousel fullscreen slideshow application designed to run on Windows systems. The application displays images from two different folders (Day and Night) on a secondary monitor, automatically switching between carousels based on configurable time schedules. The slideshow operates as a borderless, always-on-top window without affecting the Windows wallpaper.

## Requirements

### Requirement 1

**User Story:** As a user, I want the slideshow to display only on my secondary monitor in fullscreen mode, so that my primary monitor remains available for other work.

#### Acceptance Criteria

1. WHEN the application starts THEN the system SHALL detect all available monitors and identify the secondary monitor
2. WHEN the monitor index is configured THEN the system SHALL validate the index and use the specified monitor
3. IF the configured monitor index is invalid THEN the system SHALL select the largest non-primary display as fallback
4. WHEN displaying on the target monitor THEN the system SHALL create a borderless, always-on-top fullscreen window
5. WHEN the window is active THEN the system SHALL hide the mouse cursor after the configured inactivity period

### Requirement 2

**User Story:** As a user, I want separate image collections for day and night periods, so that appropriate imagery is displayed at different times of day.

#### Acceptance Criteria

1. WHEN the system is in day mode THEN the system SHALL display images only from the configured day folder
2. WHEN the system is in night mode THEN the system SHALL display images only from the configured night folder
3. WHEN switching between day and night modes THEN the system SHALL immediately change to the appropriate carousel
4. WHEN a folder is configured THEN the system SHALL support including images from subfolders if enabled
5. WHEN scanning folders THEN the system SHALL support .jpg, .jpeg, .png, and .bmp file formats
6. WHEN loading images THEN the system SHALL honor EXIF rotation data

### Requirement 3

**User Story:** As a user, I want automatic switching between day and night carousels based on time schedules, so that the appropriate imagery displays without manual intervention.

#### Acceptance Criteria

1. WHEN using fixed schedule mode THEN the system SHALL switch carousels at configured day_start and night_start times
2. WHEN using sun schedule mode THEN the system SHALL calculate sunrise and sunset times based on configured latitude and longitude
3. WHEN using sun schedule mode THEN the system SHALL recalculate sun times daily after midnight
4. WHEN schedule switching occurs THEN the system SHALL override any manual mode selection
5. WHEN day/night offset is configured THEN the system SHALL apply the offset minutes to sunrise/sunset times

### Requirement 4

**User Story:** As a user, I want images to display properly scaled and positioned on my monitor, so that they look good regardless of aspect ratio differences.

#### Acceptance Criteria

1. WHEN displaying images in cover mode THEN the system SHALL scale images to fill the screen while preserving aspect ratio
2. WHEN displaying images in fit mode THEN the system SHALL scale images to fit entirely within the screen with black bars if needed
3. WHEN transitioning between images THEN the system SHALL support crossfade transitions with configurable duration
4. WHEN an image cannot be loaded THEN the system SHALL skip the image, log the error, and continue to the next image
5. WHEN the background is visible THEN the system SHALL display the configured background color

### Requirement 5

**User Story:** As a user, I want to control the slideshow playback through keyboard shortcuts, so that I can interact with the slideshow when needed.

#### Acceptance Criteria

1. WHEN the Escape key is pressed THEN the system SHALL exit the application cleanly
2. WHEN the Space key is pressed THEN the system SHALL toggle between pause and resume states
3. WHEN the Right Arrow key is pressed THEN the system SHALL advance to the next image
4. WHEN the Left Arrow key is pressed THEN the system SHALL go back to the previous image
5. WHEN the D key is pressed THEN the system SHALL force day mode until the next scheduled change
6. WHEN the N key is pressed THEN the system SHALL force night mode until the next scheduled change

### Requirement 6

**User Story:** As a user, I want configurable slideshow behavior and timing, so that I can customize the experience to my preferences.

#### Acceptance Criteria

1. WHEN the interval is configured THEN the system SHALL advance images at the specified interval in seconds
2. WHEN shuffle mode is enabled THEN the system SHALL randomize the image order within each carousel
3. WHEN sequential mode is enabled THEN the system SHALL display images in alphabetical filename order
4. WHEN resume index is enabled THEN the system SHALL remember the last displayed image position between application runs
5. WHEN auto-reload is configured THEN the system SHALL rescan image folders at the specified interval to detect new files

### Requirement 7

**User Story:** As a user, I want robust error handling and logging, so that the application continues running even when encountering issues.

#### Acceptance Criteria

1. WHEN an image folder is empty THEN the system SHALL display a fallback message and retry scanning after a configured interval
2. WHEN an image file is corrupted or unreadable THEN the system SHALL log the error and skip to the next image
3. WHEN errors occur THEN the system SHALL write detailed logs to both console and rotating log files
4. WHEN log files reach the maximum size THEN the system SHALL rotate logs and maintain the configured number of backup files
5. WHEN the application encounters any error THEN the system SHALL continue operation without crashing

### Requirement 8

**User Story:** As a user, I want flexible configuration options, so that I can customize the application behavior without modifying code.

#### Acceptance Criteria

1. WHEN the application starts THEN the system SHALL load configuration from a YAML or JSON file with sensible defaults
2. WHEN command-line arguments are provided THEN the system SHALL override corresponding configuration file values
3. WHEN configuration is invalid THEN the system SHALL log validation errors and use default values where possible
4. WHEN monitor settings are configured THEN the system SHALL validate and apply the monitor selection preferences
5. WHEN folder paths are configured THEN the system SHALL validate that the paths exist and are accessible

### Requirement 9

**User Story:** As a user, I want the application to integrate with Windows Task Scheduler, so that it can start automatically at login or at specific times.

#### Acceptance Criteria

1. WHEN launched via Task Scheduler THEN the system SHALL start without requiring administrator privileges
2. WHEN multiple instances are attempted THEN the system SHALL prevent duplicate instances from running simultaneously
3. WHEN force day/night flags are provided THEN the system SHALL override manual mode selections and switch immediately
4. WHEN the system starts THEN the system SHALL validate all dependencies and display helpful error messages if any are missing
5. WHEN running as a scheduled task THEN the system SHALL operate reliably without user interaction

### Requirement 10

**User Story:** As a user, I want the slideshow to never interfere with my Windows wallpaper, so that my desktop appearance remains unchanged.

#### Acceptance Criteria

1. WHEN the application runs THEN the system SHALL NOT modify the Windows desktop wallpaper
2. WHEN the application exits THEN the system SHALL NOT leave any changes to the desktop wallpaper
3. WHEN displaying images THEN the system SHALL render only within its own application window
4. WHEN the window loses focus THEN the system SHALL maintain its always-on-top behavior on the target monitor
5. WHEN other applications are used THEN the system SHALL NOT interfere with their normal operation on other monitors