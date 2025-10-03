# Scheduler Integration Examples

This directory contains example scripts and configurations for integrating the Dual Carousel Slideshow with system schedulers.

## Quick Start

1. **Choose your platform:**
   - Windows: Use the `windows_scheduler_scripts/` folder
   - macOS: Use the `macos_launchd_scripts/` folder

2. **Edit the configuration paths:**
   - Open the script files and update the paths to match your installation
   - Ensure Python and the slideshow application paths are correct

3. **Test manually first:**
   - Run the scripts manually to ensure they work before scheduling
   - Check the log files for any errors

4. **Set up scheduling:**
   - Follow the platform-specific instructions in `docs/scheduling.md`
   - Use the provided example configurations as starting points

## File Overview

### Windows Scripts (`windows_scheduler_scripts/`)

- `start_slideshow.bat` - General startup script for Task Scheduler
- `force_day_mode.bat` - Forces day mode (use for morning schedule)
- `force_night_mode.bat` - Forces night mode (use for evening schedule)

### macOS Scripts (`macos_launchd_scripts/`)

- `start_slideshow.sh` - General startup script for Launch Agents
- `force_day_mode.sh` - Forces day mode (use for morning schedule)  
- `force_night_mode.sh` - Forces night mode (use for evening schedule)

## Configuration Files

- `config.scheduler.example.yaml` - Example configuration optimized for scheduler use
  - File logging enabled
  - Console logging disabled
  - Appropriate timeouts and intervals

## Important Notes

### Security
- **Never run with administrator/root privileges**
- Use standard user accounts for all scheduled tasks
- The application will warn if running with elevated privileges

### Single Instance
- The application automatically prevents multiple instances
- If scheduling fails, check if another instance is already running
- Lock files are created in the system temp directory

### Logging
- All scripts include logging for troubleshooting
- Check both application logs and scheduler logs
- Log files are created in the `logs/` directory

### Dependencies
- The application validates all dependencies on startup
- Missing dependencies will prevent startup with helpful error messages
- Ensure all required Python packages are installed

## Troubleshooting

### Common Issues

1. **Script doesn't start:**
   - Check file paths in the script
   - Verify Python is installed and accessible
   - Test the script manually first

2. **Application starts but no display:**
   - Check monitor configuration
   - Verify image folders exist and contain images
   - Check application logs for errors

3. **Scheduler task fails:**
   - Ensure "Run only when user is logged on" (Windows)
   - Use LaunchAgents not LaunchDaemons (macOS)
   - Check scheduler logs for error details

4. **Permission errors:**
   - Don't use "Run with highest privileges" (Windows)
   - Don't run as root (macOS/Linux)
   - Use standard user permissions

### Getting Help

1. Check the application logs in `logs/slideshow.log`
2. Check the scheduler logs (created by the scripts)
3. Run the application manually with `--log-level DEBUG` for detailed output
4. Refer to the full documentation in `docs/scheduling.md`

## Example Scheduler Configurations

### Windows Task Scheduler - Daily Startup
```
Name: Dual Carousel Slideshow
Trigger: At log on (delay 30 seconds)
Action: start_slideshow.bat
Security: Run only when user is logged on
```

### Windows Task Scheduler - Day/Night Switching
```
Day Task:
  Name: Slideshow Day Mode
  Trigger: Daily at 6:00 AM
  Action: force_day_mode.bat

Night Task:
  Name: Slideshow Night Mode  
  Trigger: Daily at 8:00 PM
  Action: force_night_mode.bat
```

### macOS Launch Agent - Daily Startup
```xml
<!-- ~/Library/LaunchAgents/com.user.slideshow.plist -->
<key>RunAtLoad</key>
<true/>
<key>ProgramArguments</key>
<array>
    <string>/path/to/start_slideshow.sh</string>
</array>
```

### macOS Launch Agent - Scheduled Switching
```xml
<!-- Day mode at 6:00 AM -->
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>6</integer>
    <key>Minute</key>
    <integer>0</integer>
</dict>
<key>ProgramArguments</key>
<array>
    <string>/path/to/force_day_mode.sh</string>
</array>
```

For complete setup instructions, see `docs/scheduling.md`.