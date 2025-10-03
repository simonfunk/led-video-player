#!/bin/bash
# Dual Carousel Slideshow - Force Night Mode Script for macOS
# 
# This script forces the slideshow into night mode, overriding any schedule.
# Use this script with Launch Agents to switch to night mode at specific times.
#
# Example Launch Agent configuration:
#   StartCalendarInterval: Hour=20, Minute=0 (8:00 PM daily)

# Configuration - EDIT THESE PATHS
SLIDESHOW_DIR="/Users/$(whoami)/slideshow"
PYTHON_EXE="/usr/local/bin/python3"
CONFIG_FILE="config.scheduler.example.yaml"
LOG_FILE="logs/scheduler.log"

# Change to slideshow directory
cd "$SLIDESHOW_DIR" || {
    echo "$(date) - ERROR: Could not change to slideshow directory: $SLIDESHOW_DIR" >> "$LOG_FILE"
    exit 1
}

# Log the force night mode attempt
echo "$(date) - Forcing night mode via Launch Agent" >> "$LOG_FILE"

# Force night mode
"$PYTHON_EXE" main.py --config "$CONFIG_FILE" --force-night
EXIT_CODE=$?

# Log exit status
if [ $EXIT_CODE -ne 0 ]; then
    echo "$(date) - Force night mode failed with error code $EXIT_CODE" >> "$LOG_FILE"
else
    echo "$(date) - Force night mode completed successfully" >> "$LOG_FILE"
fi

exit $EXIT_CODE