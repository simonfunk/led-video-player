# Windows Deployment Setup Guide

This guide provides step-by-step instructions for deploying the Dual Carousel Slideshow on Windows systems, including Task Scheduler integration for automatic startup and day/night switching.

## Prerequisites

### System Requirements

- **Operating System**: Windows 10 or Windows 11
- **Python**: Python 3.8 or higher
- **Display**: At least one monitor (secondary monitor recommended)
- **User Account**: Standard user account (Administrator privileges NOT required)

### Python Installation

1. **Download Python**:
   - Visit [python.org](https://www.python.org/downloads/)
   - Download Python 3.8 or higher for Windows
   - **Important**: Check "Add Python to PATH" during installation

2. **Verify Installation**:
   ```cmd
   python --version
   pip --version
   ```

## Application Setup

### 1. Download and Extract

```cmd
# Create application directory
mkdir C:\DualCarouselSlideshow
cd C:\DualCarouselSlideshow

# Extract application files here
# (or clone from repository)
```

### 2. Install Dependencies

```cmd
# Navigate to application directory
cd C:\DualCarouselSlideshow

# Install required packages
pip install -r requirements.txt
```

### 3. Create Image Directories

```cmd
# Create image folders
mkdir images\day
mkdir images\night

# Copy your images to these folders
# Supported formats: .jpg, .jpeg, .png, .bmp
```

### 4. Configure Application

```cmd
# Copy example configuration
copy config.example.yaml config.yaml

# Edit configuration file (use Notepad or preferred editor)
notepad config.yaml
```

**Key settings for Windows**:
```yaml
display:
  monitor_index: 1              # Use secondary monitor (0=primary)
  always_on_top: true

folders:
  day: "C:\\DualCarouselSlideshow\\images\\day"
  night: "C:\\DualCarouselSlideshow\\images\\night"

logging:
  log_to_console: false         # Disable for scheduled tasks
  log_file_path: "C:\\DualCarouselSlideshow\\logs\\slideshow.log"
```

### 5. Test Installation

```cmd
# Test basic functionality
python main.py --log-level DEBUG

# Test with force modes (for scheduler)
python main.py --force-day
python main.py --force-night
```

## Task Scheduler Integration

### Method 1: Automatic Day/Night Switching (Recommended)

This method creates separate tasks for day and night modes that automatically switch the slideshow.

#### Create Day Mode Task

1. **Open Task Scheduler**:
   - Press `Win + R`, type `taskschd.msc`, press Enter
   - Or search "Task Scheduler" in Start menu

2. **Create Basic Task**:
   - Click "Create Basic Task..." in Actions panel
   - Name: `Slideshow Day Mode`
   - Description: `Switch slideshow to day mode`

3. **Set Trigger**:
   - When: `Daily`
   - Start date: Today
   - Start time: `6:00:00 AM` (or your preferred day start time)
   - Recur every: `1 days`

4. **Set Action**:
   - Action: `Start a program`
   - Program/script: `python`
   - Arguments: `main.py --force-day --config config.yaml`
   - Start in: `C:\DualCarouselSlideshow`

5. **Configure Settings**:
   - Check "Open the Properties dialog when I click Finish"
   - In Properties dialog:
     - General tab: Select "Run only when user is logged on"
     - Settings tab: 
       - Uncheck "Stop the task if it runs longer than"
       - Check "If the running task does not end when requested, force it to stop"

#### Create Night Mode Task

Repeat the above steps with these changes:
- Name: `Slideshow Night Mode`
- Description: `Switch slideshow to night mode`
- Start time: `6:00:00 PM` (or your preferred night start time)
- Arguments: `main.py --force-night --config config.yaml`

#### Create Startup Task (Optional)

For automatic startup when Windows boots:

1. **Create Basic Task**:
   - Name: `Slideshow Startup`
   - Description: `Start slideshow at login`

2. **Set Trigger**:
   - When: `When I log on`

3. **Set Action**:
   - Program/script: `python`
   - Arguments: `main.py --config config.yaml`
   - Start in: `C:\DualCarouselSlideshow`

### Method 2: Simple Startup Task

This method starts the slideshow once and lets it handle day/night switching internally.

1. **Create Basic Task**:
   - Name: `Dual Carousel Slideshow`
   - Trigger: `When I log on`
   - Action: 
     - Program: `python`
     - Arguments: `main.py --config config.yaml`
     - Start in: `C:\DualCarouselSlideshow`

2. **Configure for Reliability**:
   - General tab: "Run only when user is logged on"
   - Conditions tab: Uncheck "Start the task only if the computer is on AC power"
   - Settings tab: Check "Run task as soon as possible after a scheduled start is missed"

## Batch Scripts (Alternative Method)

Create batch scripts for easier Task Scheduler integration:

### start_slideshow_day.bat
```batch
@echo off
cd /d "C:\DualCarouselSlideshow"
python main.py --force-day --config config.yaml
```

### start_slideshow_night.bat
```batch
@echo off
cd /d "C:\DualCarouselSlideshow"
python main.py --force-night --config config.yaml
```

### start_slideshow.bat
```batch
@echo off
cd /d "C:\DualCarouselSlideshow"
python main.py --config config.yaml
```

Then use these batch files in Task Scheduler instead of direct Python commands.

## Troubleshooting

### Task Scheduler Issues

#### Task Fails to Start

**Check Task History**:
1. In Task Scheduler, select your task
2. Click "History" tab (enable if disabled)
3. Look for error codes and messages

**Common Solutions**:
```cmd
# Verify Python path
where python

# Test command manually
cd C:\DualCarouselSlideshow
python main.py --force-day --config config.yaml

# Check working directory
# Ensure "Start in" field is set to: C:\DualCarouselSlideshow
```

#### Task Runs But Application Doesn't Start

**Check User Context**:
- Ensure "Run only when user is logged on" is selected
- Don't use "Run with highest privileges" unless necessary
- Test with your current user account

**Check Dependencies**:
```cmd
# Verify all packages are installed
pip list | findstr pygame
pip list | findstr Pillow
pip list | findstr PyYAML
pip list | findstr astral
```

#### Multiple Instances Running

The application prevents multiple instances automatically, but if issues occur:

```cmd
# Check running processes
tasklist | findstr python

# Kill existing instances
taskkill /f /im python.exe
```

### Display Issues

#### Monitor Not Detected

```cmd
# Test monitor detection
python -c "import pygame; pygame.init(); print('Monitors:', pygame.display.list_modes())"

# Try different monitor index
python main.py --monitor-index 0  # Primary monitor
python main.py --monitor-index 1  # Secondary monitor
```

#### Window Positioning Problems

- Ensure monitors are properly configured in Windows Display Settings
- Try running once manually to verify monitor selection
- Check logs for display-related errors: `type logs\slideshow.log`

### Performance Issues

#### High CPU Usage

- Reduce image resolution (recommended: match monitor resolution)
- Increase transition duration in config: `transition_ms: 1000`
- Reduce image change frequency: `interval_seconds: 120`

#### Memory Issues

- Monitor memory usage in Task Manager
- Restart application periodically via additional scheduled task
- Reduce image cache size by limiting folder contents

### File and Folder Issues

#### Permission Errors

```cmd
# Ensure user has read/write access to application folder
icacls C:\DualCarouselSlideshow /grant %USERNAME%:(OI)(CI)F

# Create logs directory if missing
mkdir C:\DualCarouselSlideshow\logs
```

#### Images Not Loading

```cmd
# Check image formats (supported: .jpg, .jpeg, .png, .bmp)
dir images\day\*.jpg
dir images\night\*.png

# Verify folder paths in config.yaml
# Use full Windows paths: C:\DualCarouselSlideshow\images\day
```

## Security Considerations

### User Privileges

- **DO NOT** run with Administrator privileges
- Use standard user account for better security
- The application is designed to run without elevated permissions

### Firewall and Antivirus

- Add application folder to antivirus exclusions if needed
- No network access required - application runs locally only
- Python.exe may trigger security warnings initially

### File System Access

- Application only reads from image folders and writes to logs
- No system files are modified
- Desktop wallpaper is never changed (verified by isolation test)

## Maintenance

### Log Management

```cmd
# Check current log size
dir logs\slideshow.log

# Logs rotate automatically when they reach configured size
# Default: 10MB with 5 backup files

# Manual log cleanup if needed
del logs\slideshow.log.*
```

### Image Management

```cmd
# Add new images (application will detect automatically)
copy "C:\Users\%USERNAME%\Pictures\*.jpg" images\day\
copy "C:\Users\%USERNAME%\Pictures\*.jpg" images\night\

# Remove old images
del images\day\old_image.jpg
```

### Configuration Updates

```cmd
# Backup current config
copy config.yaml config.yaml.backup

# Edit configuration
notepad config.yaml

# Test changes
python main.py --config config.yaml --log-level DEBUG
```

## Uninstallation

### Remove Scheduled Tasks

1. Open Task Scheduler
2. Delete created tasks:
   - `Slideshow Day Mode`
   - `Slideshow Night Mode`
   - `Slideshow Startup` (if created)

### Remove Application

```cmd
# Stop any running instances
taskkill /f /im python.exe

# Remove application directory
rmdir /s C:\DualCarouselSlideshow

# Uninstall Python packages (optional)
pip uninstall pygame Pillow PyYAML astral
```

## Advanced Configuration

### Custom Scheduling

For complex scheduling needs, modify the Task Scheduler triggers:

- **Weekdays Only**: Set trigger to "Weekly" and select specific days
- **Multiple Times**: Create additional tasks with different times
- **Seasonal Adjustments**: Create separate tasks for different months

### Network Drives

To use images from network drives:

```yaml
folders:
  day: "\\\\server\\share\\images\\day"
  night: "\\\\server\\share\\images\\night"
```

Ensure network drive is mapped and accessible before slideshow starts.

### Multiple Monitor Setups

For systems with more than 2 monitors:

```cmd
# Test different monitor indices
python main.py --monitor-index 0  # Primary
python main.py --monitor-index 1  # Secondary  
python main.py --monitor-index 2  # Third monitor
```

Update `config.yaml` with the correct monitor index.

## Support

For additional help:

1. Check application logs: `type logs\slideshow.log`
2. Run with debug logging: `python main.py --log-level DEBUG`
3. Verify Task Scheduler task history
4. Test components individually using the troubleshooting commands above

## Example Complete Setup

Here's a complete example for a typical Windows deployment:

```cmd
# 1. Create directory
mkdir C:\DualCarouselSlideshow
cd C:\DualCarouselSlideshow

# 2. Install (after extracting application files)
pip install -r requirements.txt

# 3. Setup folders and images
mkdir images\day images\night
copy "C:\Users\%USERNAME%\Pictures\Day\*.jpg" images\day\
copy "C:\Users\%USERNAME%\Pictures\Night\*.jpg" images\night\

# 4. Configure
copy config.example.yaml config.yaml
# Edit config.yaml as needed

# 5. Test
python main.py --log-level DEBUG

# 6. Create scheduled tasks using Task Scheduler GUI
# - Day mode task: 6:00 AM daily
# - Night mode task: 6:00 PM daily
# - Startup task: At logon (optional)
```

This setup provides a robust, automated slideshow system that starts with Windows and switches between day and night modes automatically.