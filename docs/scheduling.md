# Scheduling Integration Guide

This guide explains how to integrate the Dual Carousel Slideshow with system schedulers for automatic startup and day/night switching.

## Overview

The application supports integration with system schedulers through command-line flags that force specific modes:

- `--force-day`: Forces day mode immediately upon startup
- `--force-night`: Forces night mode immediately upon startup

These flags override any manual mode selections and switch the carousel immediately, making them perfect for scheduled tasks.

## Windows Task Scheduler Integration

### Prerequisites

- Windows 10 or later
- Python 3.8+ installed and accessible from PATH
- Application installed and tested manually first

### Basic Setup

1. **Open Task Scheduler**
   - Press `Win + R`, type `taskschd.msc`, press Enter
   - Or search for "Task Scheduler" in Start menu

2. **Create Basic Task**
   - Click "Create Basic Task..." in the Actions panel
   - Name: "Dual Carousel Slideshow - Startup"
   - Description: "Start slideshow application at login"

3. **Configure Trigger**
   - Select "When I log on"
   - Check "Delay task for: 30 seconds" (allows desktop to fully load)

4. **Configure Action**
   - Select "Start a program"
   - Program/script: `python` (or full path like `C:\Python39\python.exe`)
   - Add arguments: `"C:\path\to\your\slideshow\main.py" --config "C:\path\to\config.yaml"`
   - Start in: `C:\path\to\your\slideshow`

### Advanced Configuration for Day/Night Switching

#### Method 1: Separate Tasks for Day/Night

**Day Mode Task:**
```
Name: Dual Carousel - Force Day Mode
Trigger: Daily at 6:00 AM
Action: 
  Program: python
  Arguments: "C:\path\to\slideshow\main.py" --force-day --config "C:\path\to\config.yaml"
  Start in: C:\path\to\slideshow
```

**Night Mode Task:**
```
Name: Dual Carousel - Force Night Mode  
Trigger: Daily at 8:00 PM
Action:
  Program: python
  Arguments: "C:\path\to\slideshow\main.py" --force-night --config "C:\path\to\config.yaml"
  Start in: C:\path\to\slideshow
```

#### Method 2: Batch Script Wrapper

Create `start_slideshow.bat`:
```batch
@echo off
cd /d "C:\path\to\your\slideshow"
python main.py --config config.yaml
if errorlevel 1 (
    echo Slideshow exited with error
    pause
)
```

Create `force_day.bat`:
```batch
@echo off
cd /d "C:\path\to\your\slideshow"
python main.py --force-day --config config.yaml
```

Create `force_night.bat`:
```batch
@echo off
cd /d "C:\path\to\your\slideshow"
python main.py --force-night --config config.yaml
```

### Important Task Scheduler Settings

**Security Options:**
- ✅ "Run only when user is logged on" (recommended)
- ❌ "Run with highest privileges" (NOT recommended - app doesn't need admin rights)
- User account: Your regular user account (not Administrator)

**Conditions:**
- ✅ "Start the task only if the computer is on AC power" (for laptops)
- ✅ "Wake the computer to run this task" (if needed)
- ❌ "Start only if the following network connection is available" (usually not needed)

**Settings:**
- ✅ "Allow task to be run on demand"
- ✅ "Run task as soon as possible after a scheduled start is missed"
- ❌ "Stop the task if it runs longer than" (slideshow runs continuously)
- "If the running task does not end when requested, force it to stop": ✅

### Troubleshooting Windows Tasks

**Task doesn't start:**
- Check that Python is in PATH: `python --version` in Command Prompt
- Use full paths for both Python and the script
- Check the task history in Task Scheduler for error details
- Test the command manually in Command Prompt first

**Task starts but slideshow doesn't appear:**
- Ensure "Run only when user is logged on" is selected
- Check that the monitor configuration is correct
- Verify the image folders exist and contain images
- Check the log files for error messages

## macOS launchd Integration

### Prerequisites

- macOS 10.14 or later
- Python 3.8+ installed (via Homebrew recommended)
- Application installed and tested manually first

### User-Level Launch Agent (Recommended)

Create `~/Library/LaunchAgents/com.user.dual-carousel-slideshow.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.dual-carousel-slideshow</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/yourusername/slideshow/main.py</string>
        <string>--config</string>
        <string>/Users/yourusername/slideshow/config.yaml</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Users/yourusername/slideshow</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <false/>
    
    <key>StandardOutPath</key>
    <string>/Users/yourusername/slideshow/logs/launchd.out</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/yourusername/slideshow/logs/launchd.err</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
```

### Day/Night Switching with launchd

**Day Mode Launch Agent** (`com.user.dual-carousel-day.plist`):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.dual-carousel-day</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/yourusername/slideshow/main.py</string>
        <string>--force-day</string>
        <string>--config</string>
        <string>/Users/yourusername/slideshow/config.yaml</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Users/yourusername/slideshow</string>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>/Users/yourusername/slideshow/logs/day-mode.out</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/yourusername/slideshow/logs/day-mode.err</string>
</dict>
</plist>
```

**Night Mode Launch Agent** (`com.user.dual-carousel-night.plist`):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.dual-carousel-night</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/yourusername/slideshow/main.py</string>
        <string>--force-night</string>
        <string>--config</string>
        <string>/Users/yourusername/slideshow/config.yaml</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Users/yourusername/slideshow</string>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>20</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>/Users/yourusername/slideshow/logs/night-mode.out</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/yourusername/slideshow/logs/night-mode.err</string>
</dict>
</plist>
```

### Managing Launch Agents

**Load/Enable:**
```bash
launchctl load ~/Library/LaunchAgents/com.user.dual-carousel-slideshow.plist
```

**Unload/Disable:**
```bash
launchctl unload ~/Library/LaunchAgents/com.user.dual-carousel-slideshow.plist
```

**Check Status:**
```bash
launchctl list | grep dual-carousel
```

**View Logs:**
```bash
tail -f ~/slideshow/logs/launchd.out
tail -f ~/slideshow/logs/launchd.err
```

### Troubleshooting macOS Launch Agents

**Agent doesn't start:**
- Check plist syntax: `plutil -lint ~/Library/LaunchAgents/com.user.dual-carousel-slideshow.plist`
- Verify Python path: `which python3`
- Check permissions: `ls -la ~/Library/LaunchAgents/`
- View system logs: `log show --predicate 'subsystem == "com.apple.launchd"' --last 1h`

**Agent starts but slideshow doesn't appear:**
- Ensure the slideshow is configured for the correct display
- Check that the user is logged in (Launch Agents only run when user is logged in)
- Verify image folders exist and are accessible
- Check the output logs for error messages

## General Best Practices

### Security Considerations

1. **Never run with elevated privileges**
   - The application is designed to run with standard user permissions
   - Elevated privileges are not required and may cause security issues

2. **Use user-level scheduling**
   - Windows: "Run only when user is logged on"
   - macOS: Use LaunchAgents, not LaunchDaemons
   - Linux: Use user systemd services, not system services

3. **Validate paths and permissions**
   - Ensure all paths in configuration are accessible to the user
   - Test manually before setting up scheduled tasks

### Monitoring and Maintenance

1. **Log Monitoring**
   - Regularly check application logs for errors
   - Set up log rotation to prevent disk space issues
   - Monitor system scheduler logs for task execution issues

2. **Health Checks**
   - Periodically verify the slideshow is running correctly
   - Check that image folders are accessible and contain current content
   - Verify display configuration after system updates

3. **Updates and Changes**
   - Test configuration changes manually before updating scheduled tasks
   - Keep backup copies of working configurations
   - Document any customizations for future reference

### Performance Optimization

1. **Resource Management**
   - Configure appropriate image cache sizes
   - Use SSD storage for image folders when possible
   - Monitor memory usage during extended operation

2. **Network Considerations**
   - If using network-mounted image folders, ensure reliable connectivity
   - Consider local caching for network-based images
   - Handle network interruptions gracefully

3. **Display Management**
   - Verify monitor configuration after system updates
   - Handle display disconnection/reconnection scenarios
   - Test multi-monitor setups thoroughly

## Example Configurations

### Home Office Setup
- Single secondary monitor
- Automatic day/night switching based on fixed schedule
- Startup at login, no manual intervention required

### Digital Signage Setup
- Multiple displays with different content
- Scheduled content updates via network folders
- Automatic restart on system reboot
- Remote monitoring and management

### Development/Testing Setup
- Manual mode switching for testing
- Detailed logging enabled
- Easy configuration switching for different scenarios
- Quick startup/shutdown for development cycles

For more detailed configuration examples, see the `config.example.yaml` file in the project root.