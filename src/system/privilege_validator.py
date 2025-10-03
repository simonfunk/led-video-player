"""
Privilege validation utilities to ensure application runs without admin rights.
"""
import os
import sys
import logging
from typing import Dict, Any


class PrivilegeValidator:
    """Validates that the application is not running with elevated privileges."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_privileges(self) -> Dict[str, Any]:
        """
        Validate that the application is not running with elevated privileges.
        
        Returns:
            Dict containing validation results and recommendations
        """
        result = {
            'is_elevated': False,
            'platform': sys.platform,
            'warnings': [],
            'recommendations': []
        }
        
        try:
            if sys.platform == 'win32':
                result.update(self._check_windows_privileges())
            elif sys.platform == 'darwin':
                result.update(self._check_macos_privileges())
            elif sys.platform.startswith('linux'):
                result.update(self._check_linux_privileges())
            else:
                result['warnings'].append(f"Unknown platform: {sys.platform}")
                
        except Exception as e:
            self.logger.error(f"Error checking privileges: {e}")
            result['warnings'].append(f"Could not determine privilege level: {e}")
        
        return result
    
    def _check_windows_privileges(self) -> Dict[str, Any]:
        """Check Windows privilege level."""
        result = {'is_elevated': False, 'warnings': [], 'recommendations': []}
        
        try:
            import ctypes
            
            # Check if running as administrator
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            result['is_elevated'] = bool(is_admin)
            
            if is_admin:
                result['warnings'].append(
                    "Application is running with administrator privileges"
                )
                result['recommendations'].extend([
                    "Close the application and restart without 'Run as administrator'",
                    "For Task Scheduler: Ensure 'Run with highest privileges' is unchecked",
                    "The application is designed to run with standard user privileges"
                ])
            else:
                self.logger.info("Running with standard user privileges (recommended)")
                
        except ImportError:
            result['warnings'].append("Could not check Windows privileges (ctypes not available)")
        except Exception as e:
            result['warnings'].append(f"Error checking Windows privileges: {e}")
        
        return result
    
    def _check_macos_privileges(self) -> Dict[str, Any]:
        """Check macOS privilege level."""
        result = {'is_elevated': False, 'warnings': [], 'recommendations': []}
        
        try:
            # Check if running as root
            is_root = os.geteuid() == 0
            result['is_elevated'] = is_root
            
            if is_root:
                result['warnings'].append(
                    "Application is running as root (elevated privileges)"
                )
                result['recommendations'].extend([
                    "Close the application and restart as a regular user",
                    "For launchd: Use LaunchAgents (user-level) instead of LaunchDaemons (system-level)",
                    "The application is designed to run with standard user privileges"
                ])
            else:
                self.logger.info("Running with standard user privileges (recommended)")
                
        except Exception as e:
            result['warnings'].append(f"Error checking macOS privileges: {e}")
        
        return result
    
    def _check_linux_privileges(self) -> Dict[str, Any]:
        """Check Linux privilege level."""
        result = {'is_elevated': False, 'warnings': [], 'recommendations': []}
        
        try:
            # Check if running as root
            is_root = os.geteuid() == 0
            result['is_elevated'] = is_root
            
            if is_root:
                result['warnings'].append(
                    "Application is running as root (elevated privileges)"
                )
                result['recommendations'].extend([
                    "Close the application and restart as a regular user",
                    "For systemd: Use user services instead of system services",
                    "The application is designed to run with standard user privileges"
                ])
            else:
                self.logger.info("Running with standard user privileges (recommended)")
                
        except Exception as e:
            result['warnings'].append(f"Error checking Linux privileges: {e}")
        
        return result
    
    def log_privilege_status(self, validation_result: Dict[str, Any]) -> None:
        """Log privilege validation results."""
        if validation_result['is_elevated']:
            self.logger.warning("PRIVILEGE WARNING: Application is running with elevated privileges")
            for warning in validation_result['warnings']:
                self.logger.warning(f"  - {warning}")
            
            self.logger.info("Recommendations:")
            for recommendation in validation_result['recommendations']:
                self.logger.info(f"  - {recommendation}")
        else:
            self.logger.info("Privilege check passed: Running with appropriate user privileges")