"""
Single instance enforcement to prevent multiple application instances.
"""
import os
import sys
import logging
import tempfile
import atexit
from pathlib import Path
from typing import Optional


class SingleInstanceEnforcer:
    """Ensures only one instance of the application runs at a time."""
    
    def __init__(self, app_name: str = "dual_carousel_slideshow"):
        self.app_name = app_name
        self.logger = logging.getLogger(__name__)
        self.lock_file_path: Optional[Path] = None
        self.lock_file_handle: Optional[int] = None
    
    def acquire_lock(self) -> bool:
        """
        Acquire application lock to prevent duplicate instances.
        
        Returns:
            True if lock acquired successfully, False if another instance is running
        """
        try:
            # Create lock file path in temp directory
            temp_dir = Path(tempfile.gettempdir())
            self.lock_file_path = temp_dir / f"{self.app_name}.lock"
            
            # Platform-specific lock implementation
            if sys.platform == 'win32':
                return self._acquire_windows_lock()
            else:
                return self._acquire_unix_lock()
                
        except Exception as e:
            self.logger.error(f"Error acquiring application lock: {e}")
            return False
    
    def _acquire_windows_lock(self) -> bool:
        """Acquire lock on Windows using file locking."""
        try:
            import msvcrt
            
            # Try to create and lock the file
            self.lock_file_handle = os.open(
                str(self.lock_file_path), 
                os.O_CREAT | os.O_EXCL | os.O_RDWR
            )
            
            # Write PID to lock file
            os.write(self.lock_file_handle, str(os.getpid()).encode())
            
            # Register cleanup function
            atexit.register(self._release_lock)
            
            self.logger.info(f"Application lock acquired: {self.lock_file_path}")
            return True
            
        except FileExistsError:
            # Lock file exists, check if process is still running
            return self._handle_existing_lock_windows()
        except ImportError:
            self.logger.warning("msvcrt not available, using fallback lock method")
            return self._acquire_fallback_lock()
        except Exception as e:
            self.logger.error(f"Error acquiring Windows lock: {e}")
            return False
    
    def _acquire_unix_lock(self) -> bool:
        """Acquire lock on Unix-like systems using file locking."""
        try:
            import fcntl
            
            # Create lock file
            self.lock_file_handle = os.open(
                str(self.lock_file_path), 
                os.O_CREAT | os.O_WRONLY | os.O_TRUNC
            )
            
            # Try to acquire exclusive lock
            fcntl.flock(self.lock_file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Write PID to lock file
            os.write(self.lock_file_handle, str(os.getpid()).encode())
            
            # Register cleanup function
            atexit.register(self._release_lock)
            
            self.logger.info(f"Application lock acquired: {self.lock_file_path}")
            return True
            
        except BlockingIOError:
            # Another process has the lock
            self.logger.warning("Another instance of the application is already running")
            return False
        except ImportError:
            self.logger.warning("fcntl not available, using fallback lock method")
            return self._acquire_fallback_lock()
        except Exception as e:
            self.logger.error(f"Error acquiring Unix lock: {e}")
            return False
    
    def _acquire_fallback_lock(self) -> bool:
        """Fallback lock method using simple file existence."""
        try:
            if self.lock_file_path.exists():
                # Check if the PID in the file is still running
                return self._handle_existing_lock_fallback()
            
            # Create lock file with current PID
            with open(self.lock_file_path, 'w') as f:
                f.write(str(os.getpid()))
            
            # Register cleanup function
            atexit.register(self._release_lock)
            
            self.logger.info(f"Application lock acquired (fallback): {self.lock_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error acquiring fallback lock: {e}")
            return False
    
    def _handle_existing_lock_windows(self) -> bool:
        """Handle existing lock file on Windows."""
        try:
            # Try to read PID from lock file
            with open(self.lock_file_path, 'r') as f:
                pid_str = f.read().strip()
                if pid_str.isdigit():
                    pid = int(pid_str)
                    
                    # Check if process is still running
                    if self._is_process_running_windows(pid):
                        self.logger.warning(f"Another instance is running (PID: {pid})")
                        return False
                    else:
                        self.logger.info(f"Stale lock file found (PID: {pid}), removing")
                        self.lock_file_path.unlink(missing_ok=True)
                        return self._acquire_windows_lock()
            
            # If we can't read PID, assume stale lock
            self.logger.warning("Invalid lock file found, removing")
            self.lock_file_path.unlink(missing_ok=True)
            return self._acquire_windows_lock()
            
        except Exception as e:
            self.logger.error(f"Error handling existing Windows lock: {e}")
            return False
    
    def _handle_existing_lock_fallback(self) -> bool:
        """Handle existing lock file using fallback method."""
        try:
            # Try to read PID from lock file
            with open(self.lock_file_path, 'r') as f:
                pid_str = f.read().strip()
                if pid_str.isdigit():
                    pid = int(pid_str)
                    
                    # Check if process is still running
                    if self._is_process_running_fallback(pid):
                        self.logger.warning(f"Another instance is running (PID: {pid})")
                        return False
                    else:
                        self.logger.info(f"Stale lock file found (PID: {pid}), removing")
                        self.lock_file_path.unlink(missing_ok=True)
                        return self._acquire_fallback_lock()
            
            # If we can't read PID, assume stale lock
            self.logger.warning("Invalid lock file found, removing")
            self.lock_file_path.unlink(missing_ok=True)
            return self._acquire_fallback_lock()
            
        except Exception as e:
            self.logger.error(f"Error handling existing fallback lock: {e}")
            return False
    
    def _is_process_running_windows(self, pid: int) -> bool:
        """Check if a process is running on Windows."""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Open process handle
            handle = ctypes.windll.kernel32.OpenProcess(
                0x1000,  # PROCESS_QUERY_LIMITED_INFORMATION
                False,
                pid
            )
            
            if handle:
                # Get exit code
                exit_code = wintypes.DWORD()
                if ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                    ctypes.windll.kernel32.CloseHandle(handle)
                    return exit_code.value == 259  # STILL_ACTIVE
                
                ctypes.windll.kernel32.CloseHandle(handle)
            
            return False
            
        except Exception:
            # Fallback to tasklist command
            return self._is_process_running_fallback(pid)
    
    def _is_process_running_fallback(self, pid: int) -> bool:
        """Check if a process is running using cross-platform method."""
        try:
            # Send signal 0 to check if process exists (Unix)
            if hasattr(os, 'kill'):
                os.kill(pid, 0)
                return True
        except (OSError, ProcessLookupError):
            return False
        except Exception:
            pass
        
        # Fallback: assume process is not running
        return False
    
    def _release_lock(self) -> None:
        """Release the application lock."""
        try:
            if self.lock_file_handle is not None:
                try:
                    os.close(self.lock_file_handle)
                except Exception as e:
                    self.logger.warning(f"Error closing lock file handle: {e}")
                finally:
                    self.lock_file_handle = None
            
            if self.lock_file_path and self.lock_file_path.exists():
                try:
                    self.lock_file_path.unlink()
                    self.logger.debug(f"Application lock released: {self.lock_file_path}")
                except Exception as e:
                    self.logger.warning(f"Error removing lock file: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error releasing application lock: {e}")
    
    def release_lock(self) -> None:
        """Manually release the lock (also called automatically on exit)."""
        self._release_lock()
    
    def get_lock_info(self) -> dict:
        """Get information about the current lock."""
        return {
            'lock_file_path': str(self.lock_file_path) if self.lock_file_path else None,
            'has_lock': self.lock_file_handle is not None,
            'current_pid': os.getpid()
        }