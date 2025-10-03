#!/bin/bash
# Dual Carousel Slideshow - Force Day Mode Script for macOS
# 
# This script forces the slideshow into day mode, overriding any schedule.
# Use this script with Launch Agents to switch to day mode at specific times.
#
# Example Launch Agent configuration:
#   StartCalendarInterval: Hour=6, Minute=0 (6:00 AM daily)

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

# Log the force day mode attempt
echo "$(date) - Forcing day mode via Launch Agent" >> "$LOG_FILE"

# Force day mode
"$PYTHON_EXE" main.py --config "$CONFIG_FILE" --force-day
EXIT_CODE=$?

# Log exit status
if [ $EXIT_CODE -ne 0 ]; then
    echo "$(date) - Force day mode failed with error code $EXIT_CODE" >> "$LOG_FILE"
else
    echo "$(date) - Force day mode completed successfully" >> "$LOG_FILE"
fi

exit $EXIT_CODE