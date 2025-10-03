@echo off
REM ============================================================================
REM Dual Carousel Slideshow - Startup Script for Windows Task Scheduler
REM ============================================================================
REM 
REM This script starts the slideshow application with proper error handling
REM and logging for use with Windows Task Scheduler.
REM
REM Usage:
REM   1. Edit the SLIDESHOW_DIR path below to match your installation
REM   2. Create a Task Scheduler task that runs this batch file
REM   3. Configure the task to "Run only when user is logged on"
REM   4. Set the task's "Start in" directory to the slideshow folder
REM
REM Example Task Scheduler Configuration:
REM   Name: Dual Carousel Slideshow
REM   Trigger: At log on (with 30 second delay)
REM   Action: This batch file
REM   Security: Run only when user is logged on (NOT as administrator)
REM
REM ============================================================================

REM Configuration - EDIT THIS PATH TO MATCH YOUR INSTALLATION
set SLIDESHOW_DIR=C:\DualCarouselSlideshow

REM Application settings (usually don't need to change these)
set PYTHON_EXE=python
set CONFIG_FILE=config.yaml
set SCHEDULER_LOG=logs\scheduler.log

REM Ensure logs directory exists
if not exist "%SLIDESHOW_DIR%\logs" mkdir "%SLIDESHOW_DIR%\logs"

REM Change to slideshow directory
cd /d "%SLIDESHOW_DIR%" 2>nul
if errorlevel 1 (
    echo %date% %time% - ERROR: Could not change to directory: %SLIDESHOW_DIR% >> "%SCHEDULER_LOG%"
    echo ERROR: Slideshow directory not found: %SLIDESHOW_DIR%
    echo Please edit this batch file and set the correct SLIDESHOW_DIR path.
    pause
    exit /b 1
)

REM Log startup attempt
echo %date% %time% - Starting Dual Carousel Slideshow from %CD% >> "%SCHEDULER_LOG%"

REM Check if Python is available
"%PYTHON_EXE%" --version >nul 2>&1
if errorlevel 1 (
    echo %date% %time% - ERROR: Python not found. Please install Python and add it to PATH. >> "%SCHEDULER_LOG%"
    echo ERROR: Python not found. Please install Python and add it to PATH.
    pause
    exit /b 1
)

REM Check if main.py exists
if not exist "main.py" (
    echo %date% %time% - ERROR: main.py not found in %CD% >> "%SCHEDULER_LOG%"
    echo ERROR: main.py not found. Please check the slideshow directory path.
    pause
    exit /b 1
)

REM Check if config file exists
if not exist "%CONFIG_FILE%" (
    echo %date% %time% - WARNING: Config file %CONFIG_FILE% not found, using defaults >> "%SCHEDULER_LOG%"
    set CONFIG_ARG=
) else (
    set CONFIG_ARG=--config "%CONFIG_FILE%"
)

REM Start the slideshow application
echo %date% %time% - Executing: "%PYTHON_EXE%" main.py %CONFIG_ARG% >> "%SCHEDULER_LOG%"
"%PYTHON_EXE%" main.py %CONFIG_ARG%
set EXIT_CODE=%errorlevel%

REM Log exit status
if %EXIT_CODE% equ 0 (
    echo %date% %time% - Slideshow exited normally >> "%SCHEDULER_LOG%"
) else (
    echo %date% %time% - Slideshow exited with error code %EXIT_CODE% >> "%SCHEDULER_LOG%"
)

REM For debugging: uncomment the next line to pause and show any errors
REM pause

exit /b %EXIT_CODE%