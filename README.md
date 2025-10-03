# Dual Carousel Slideshow

A fullscreen slideshow application that displays images from separate day and night folders on a secondary monitor, with automatic switching based on configurable time schedules. The application runs as a borderless, always-on-top window without affecting your desktop wallpaper.

## Features

- 🖥️ **Multi-Monitor Support**: Automatically detects and displays on secondary monitors
- 🌅 **Day/Night Switching**: Automatic switching between image collections based on time or sunrise/sunset
- 🎛️ **Flexible Configuration**: YAML/JSON configuration with command-line overrides
- 🖼️ **Smart Image Handling**: Supports JPEG, PNG, BMP with automatic EXIF rotation
- ⌨️ **Hotkey Controls**: Keyboard shortcuts for navigation and mode switching
- 🔄 **Auto-Reload**: Automatically detects new images in folders
- 📊 **Robust Error Handling**: Graceful handling of corrupted files and system errors
- 📅 **Scheduler Integration**: Works with Windows Task Scheduler and macOS launchd
- 🎨 **Smooth Transitions**: Configurable crossfade transitions between images

## Quick Start

### 1. Installation

**Requirements**: Python 3.8 or higher

```bash
# Clone or download the project
git clone <repository-url>
cd dual-carousel-slideshow

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Image Folders

```bash
# Create image directories (if they don't exist)
mkdir -p images/day images/night

# Add your images
cp /path/to/your/day/images/* images/day/
cp /path/to/your/night/images/* images/night/
```

### 3. Configure

```bash
# Copy example configuration
cp config.example.yaml config.yaml

# Edit configuration (optional)
nano config.yaml
```

### 4. Run

```bash
# Start the slideshow
python3 main.py
```

## Configuration

### Basic Configuration

The application uses YAML configuration files. Here's a minimal example:

```yaml
display:
  monitor_index: 1              # Use secondary monitor
  background_color: "#000000"   # Black background

schedule:
  mode: "fixed"                 # Use fixed time schedule
  fixed_schedule:
    day_start: "06:00"          # Switch to day mode at 6 AM
    night_start: "18:00"        # Switch to night mode at 6 PM

folders:
  day: "./images/day"           # Day images folder
  night: "./images/night"       # Night images folder

playback:
  interval_seconds: 60          # Change images every minute
  shuffle: true                 # Randomize order
```

### Advanced Configuration

For detailed configuration options, see `config.example.yaml` which includes:

- **Display Settings**: Monitor selection, cursor behavior, window properties
- **Schedule Modes**: Fixed times or astronomical sunrise/sunset calculations
- **Playback Options**: Intervals, transitions, image scaling modes
- **Logging Configuration**: File logging, rotation, debug levels

### Astronomical Scheduling

Use sunrise/sunset times for natural day/night switching:

```yaml
schedule:
  mode: "sun"
  sun_schedule:
    latitude: 40.7128           # Your location (NYC example)
    longitude: -74.0060
    day_offset_minutes: 30      # Start day mode 30 min after sunrise
    night_offset_minutes: -30   # Start night mode 30 min before sunset
```

## Usage Examples

### Basic Usage

```bash
# Run with default settings
python3 main.py

# Use specific config file
python3 main.py --config my-config.yaml

# Override monitor selection
python3 main.py --monitor-index 0

# Change image interval
python3 main.py --interval 30
```

### Scheduler Integration

For automated startup with Windows Task Scheduler or macOS launchd:

```bash
# Force day mode (for morning task)
python3 main.py --force-day --config config.scheduler.example.yaml

# Force night mode (for evening task)
python3 main.py --force-night --config config.scheduler.example.yaml
```

### Hotkey Controls

While the slideshow is running:

- **Esc**: Exit application
- **Space**: Pause/resume slideshow
- **Right Arrow**: Next image
- **Left Arrow**: Previous image
- **D**: Force day mode
- **N**: Force night mode

## Windows Task Scheduler Setup

### Method 1: Automatic Switching

Create two scheduled tasks for automatic day/night switching:

1. **Day Mode Task**:
   - Trigger: Daily at 6:00 AM
   - Action: `python3 main.py --force-day --config config.scheduler.example.yaml`
   - Settings: "Run only when user is logged on"

2. **Night Mode Task**:
   - Trigger: Daily at 6:00 PM  
   - Action: `python3 main.py --force-night --config config.scheduler.example.yaml`
   - Settings: "Run only when user is logged on"

### Method 2: Login Startup

Create a single task that starts with Windows:

- Trigger: "At log on"
- Action: `python3 main.py --config config.yaml`
- Settings: "Run only when user is logged on"

See `examples/README_SCHEDULER_INTEGRATION.md` for detailed setup instructions.

## Troubleshooting

### Common Issues

#### Application Won't Start

**Problem**: "No monitors detected" or display errors
```bash
# Check available monitors
python3 -c "import pygame; pygame.init(); print(pygame.display.list_modes())"

# Try primary monitor
python3 main.py --monitor-index 0
```

**Problem**: "Dependencies missing"
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check specific packages
python3 -c "import pygame, PIL, yaml, astral; print('All dependencies OK')"
```

#### Images Not Displaying

**Problem**: Empty folders or unsupported formats
```bash
# Check folder contents
ls -la images/day/ images/night/

# Supported formats: .jpg, .jpeg, .png, .bmp
# Convert unsupported formats:
# mogrify -format jpg *.webp  # Convert WebP to JPEG
```

**Problem**: Images appear corrupted or rotated incorrectly
- Check EXIF data: The app automatically handles EXIF rotation
- Verify image integrity: Try opening images in another application
- Check logs: `tail -f logs/slideshow.log`

#### Scheduling Issues

**Problem**: Task Scheduler tasks fail to start
```bash
# Test manually first
python3 main.py --force-day --config config.scheduler.example.yaml

# Check working directory in Task Scheduler
# Ensure full paths are used for Python and script
```

**Problem**: Multiple instances running
```bash
# Check for existing instances
ps aux | grep main.py  # Linux/macOS
tasklist | findstr python  # Windows

# Kill existing instances if needed
pkill -f main.py  # Linux/macOS
```

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
# Run with debug logging
python3 main.py --log-level DEBUG

# Check log file
tail -f logs/slideshow.log
```

### Performance Issues

**Problem**: High CPU usage or slow transitions
- Reduce image resolution (recommended: 1920x1080 or monitor resolution)
- Increase transition duration: `transition_ms: 1000`
- Disable shuffle mode temporarily: `shuffle: false`
- Check available RAM: Large images are cached in memory

**Problem**: Memory usage grows over time
- Reduce `reload_images_every_seconds` value
- Restart application periodically via scheduler
- Monitor logs for memory-related warnings

### System-Specific Issues

#### Windows

**Problem**: Window doesn't stay on top
- The application uses pygame which has limited always-on-top support
- Consider using third-party tools like "Always On Top" utilities

**Problem**: Antivirus blocking execution
- Add application folder to antivirus exclusions
- Use `--log-level DEBUG` to identify blocked operations

#### macOS

**Problem**: Permission denied errors
```bash
# Grant accessibility permissions in System Preferences
# Security & Privacy > Privacy > Accessibility
```

**Problem**: Python not found in scheduled tasks
```bash
# Use full Python path in launchd plist
which python3  # Find full path
# Use result in launchd configuration
```

#### Linux

**Problem**: Display server compatibility
```bash
# For Wayland, may need X11 compatibility
export GDK_BACKEND=x11
python3 main.py
```

## Project Structure

```
dual-carousel-slideshow/
├── main.py                     # Main application entry point
├── requirements.txt            # Python dependencies (pinned versions)
├── config.example.yaml         # Comprehensive configuration example
├── config.scheduler.example.yaml  # Scheduler-optimized configuration
├── test_wallpaper_isolation.py    # Desktop wallpaper isolation test
├── src/                        # Source code modules
│   ├── config/                 # Configuration management
│   ├── display/                # Display and monitor management  
│   ├── images/                 # Image processing and management
│   ├── carousel/               # Carousel state management
│   ├── scheduler/              # Day/night scheduling
│   ├── ui/                     # User interface and event handling
│   ├── error_handling/         # Error handling and recovery
│   └── system/                 # System integration utilities
├── images/                     # Default image directories
│   ├── day/                    # Day mode images
│   └── night/                  # Night mode images
├── logs/                       # Application logs
├── examples/                   # Integration examples
│   ├── README_SCHEDULER_INTEGRATION.md
│   ├── macos_launchd_scripts/
│   └── windows_scheduler_scripts/
└── docs/                       # Additional documentation
    └── scheduling.md
```

## Development

This project follows a spec-driven development approach with comprehensive error handling and testing. See the `.kiro/specs/dual-carousel-slideshow/` directory for detailed requirements, design documentation, and implementation tasks.

### Running Tests

```bash
# Test wallpaper isolation
python3 test_wallpaper_isolation.py

# Test error handling
python3 test_comprehensive_error_handling.py

# Visual carousel test
python3 test_carousel_visual.py
```

## License

This project is provided as-is for educational and personal use. See individual dependency licenses for third-party components.

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review log files in `logs/slideshow.log`
3. Run with `--log-level DEBUG` for detailed diagnostics
4. Verify configuration with example files

## Contributing

Contributions are welcome! Please:

1. Follow the existing code structure and patterns
2. Add appropriate error handling and logging
3. Update documentation for new features
4. Test on multiple monitor configurations when possible