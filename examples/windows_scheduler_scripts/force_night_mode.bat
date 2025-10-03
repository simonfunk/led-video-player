@echo off
REM ============================================================================
REM Dual Carousel Slideshow - Force Night Mode Script for Task Scheduler
REM ============================================================================
REM 
REM This script forces the slideshow into night mode, overriding any schedule.
REM Use this script with Task Scheduler to automatically switch to night mode.
REM
REM Task Scheduler Configuration:
REM   Name: Slideshow Night Mode
REM   Trigger: Daily at 8:00 PM (or your preferred evening time)
REM   Action: Start this batch file
REM   Security: Run only when user is logged on (NOT as administrator)
REM   Settings: Stop existing task if running, Allow task to be run on demand
REM
REM This script will:
REM   1. Kill any existing slideshow instance
REM   2. Start slideshow in forced night mode
REM   3. Log all actions for troubleshooting
REM
REM ============================================================================

REM Configuration - EDIT THIS PATH TO MATCH YOUR INSTALLATION
set SLIDESHOW_DIR=C:\DualCarouselSlideshow

REM Application settings
set PYTHON_EXE=python
set CONFIG_FILE=config.yaml
set SCHEDULER_LOG=logs\scheduler.log

REM Ensure logs directory exists
if not exist "%SLIDESHOW_DIR%\logs" mkdir "%SLIDESHOW_DIR%\logs"

REM Change to slideshow directory
cd /d "%SLIDESHOW_DIR%" 2>nul
if errorlevel 1 (
    echo %date% %time% - ERROR: Could not change to directory: %SLIDESHOW_DIR% >> "%SCHEDULER_LOG%"
    exit /b 1
)

REM Log the force night mode attempt
echo %date% %time% - [NIGHT MODE] Starting night mode switch via scheduler >> "%SCHEDULER_LOG%"

REM Kill any existing slideshow instances (single instance enforcement should handle this, but be safe)
tasklist /fi "imagename eq python.exe" /fo csv | find /i "main.py" >nul 2>&1
if not errorlevel 1 (
    echo %date% %time% - [NIGHT MODE] Stopping existing slideshow instance >> "%SCHEDULER_LOG%"
    taskkill /f /im python.exe /fi "windowtitle eq *slideshow*" >nul 2>&1
    timeout /t 2 /nobreak >nul
)

REM Check if config file exists
if not exist "%CONFIG_FILE%" (
    echo %date% %time% - [NIGHT MODE] WARNING: Config file %CONFIG_FILE% not found, using defaults >> "%SCHEDULER_LOG%"
    set CONFIG_ARG=
) else (
    set CONFIG_ARG=--config "%CONFIG_FILE%"
)

REM Force night mode
echo %date% %time% - [NIGHT MODE] Executing: "%PYTHON_EXE%" main.py %CONFIG_ARG% --force-night >> "%SCHEDULER_LOG%"
"%PYTHON_EXE%" main.py %CONFIG_ARG% --force-night
set EXIT_CODE=%errorlevel%

REM Log exit status
if %EXIT_CODE% equ 0 (
    echo %date% %time% - [NIGHT MODE] Night mode switch completed successfully >> "%SCHEDULER_LOG%"
) else (
    echo %date% %time% - [NIGHT MODE] Night mode switch failed with error code %EXIT_CODE% >> "%SCHEDULER_LOG%"
)

exit /b %EXIT_CODE%