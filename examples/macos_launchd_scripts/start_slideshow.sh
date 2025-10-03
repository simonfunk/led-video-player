#!/bin/bash
# Dual Carousel Slideshow - Startup Script for macOS launchd
# 
# This script starts the slideshow application with proper error handling
# and logging for use with macOS Launch Agents.
#
# Usage:
#   1. Edit the paths below to match your installation
#   2. Make the script executable: chmod +x start_slideshow.sh
#   3. Create a Launch Agent plist that runs this script
#   4. Load the Launch Agent with launchctl

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

# Log startup attempt
echo "$(date) - Starting Dual Carousel Slideshow" >> "$LOG_FILE"

# Start the slideshow application
"$PYTHON_EXE" main.py --config "$CONFIG_FILE"
EXIT_CODE=$?

# Log exit status
if [ $EXIT_CODE -ne 0 ]; then
    echo "$(date) - Slideshow exited with error code $EXIT_CODE" >> "$LOG_FILE"
else
    echo "$(date) - Slideshow exited normally" >> "$LOG_FILE"
fi

exit $EXIT_CODE