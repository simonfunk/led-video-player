"""
Comprehensive error handling and recovery system.

This module provides:
- Error classification and handling strategies
- Retry logic for recoverable errors
- Graceful degradation for system errors
- Fallback mechanisms for critical failures
"""
import logging
import time
from typing import Dict, Any, Optional, Callable, List, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"           # Minor issues, continue operation
    MEDIUM = "medium"     # Significant issues, attempt recovery
    HIGH = "high"         # Critical issues, graceful degradation
    CRITICAL = "critical" # System failure, emergency shutdown


class ErrorCategory(Enum):
    """Error categories for different handling strategies."""
    IMAGE_LOADING = "image_loading"
    FOLDER_ACCESS = "folder_access"
    DISPLAY_ERROR = "display_error"
    SYSTEM_ERROR = "system_error"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    PERMISSION = "permission"


@dataclass
class ErrorInfo:
    """Information about an error occurrence."""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    exception: Optional[Exception] = None
    timestamp: datetime = None
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.context is None:
            self.context = {}


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_backoff: bool = True
    jitter: bool = True


class ErrorHandler:
    """
    Comprehensive error handler with retry logic and graceful degradation.
    """
    
    def __init__(self):
        """Initialize the error handler."""
        self.error_counts: Dict[str, int] = {}
        self.last_errors: Dict[str, datetime] = {}
        self.retry_configs: Dict[ErrorCategory, RetryConfig] = {
            ErrorCategory.IMAGE_LOADING: RetryConfig(max_attempts=2, base_delay=0.5),
            ErrorCategory.FOLDER_ACCESS: RetryConfig(max_attempts=3, base_delay=1.0),
            ErrorCategory.DISPLAY_ERROR: RetryConfig(max_attempts=2, base_delay=2.0),
            ErrorCategory.SYSTEM_ERROR: RetryConfig(max_attempts=1, base_delay=5.0),
            ErrorCategory.CONFIGURATION: RetryConfig(max_attempts=1, base_delay=0.0),
            ErrorCategory.NETWORK: RetryConfig(max_attempts=3, base_delay=2.0),
            ErrorCategory.PERMISSION: RetryConfig(max_attempts=1, base_delay=0.0),
        }
        
        # Error thresholds for escalation
        self.error_thresholds = {
            ErrorCategory.IMAGE_LOADING: 10,  # Allow many image errors
            ErrorCategory.FOLDER_ACCESS: 5,   # Moderate folder errors
            ErrorCategory.DISPLAY_ERROR: 3,   # Few display errors
            ErrorCategory.SYSTEM_ERROR: 1,    # Immediate escalation
        }
    
    def handle_error(self, error_info: ErrorInfo) -> bool:
        """
        Handle an error with appropriate strategy.
        
        Args:
            error_info: Information about the error
            
        Returns:
            bool: True if operation should continue, False if it should stop
        """
        # Log the error
        self._log_error(error_info)
        
        # Update error tracking
        self._update_error_tracking(error_info)
        
        # Check if error threshold exceeded
        if self._is_error_threshold_exceeded(error_info.category):
            logger.critical(f"Error threshold exceeded for {error_info.category.value}")
            return False
        
        # Handle based on severity
        if error_info.severity == ErrorSeverity.CRITICAL:
            return False
        elif error_info.severity == ErrorSeverity.HIGH:
            return self._handle_high_severity_error(error_info)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            return self._handle_medium_severity_error(error_info)
        else:  # LOW severity
            return self._handle_low_severity_error(error_info)
    
    def retry_operation(self, operation: Callable, error_category: ErrorCategory, 
                       *args, **kwargs) -> Tuple[bool, Any]:
        """
        Retry an operation with exponential backoff.
        
        Args:
            operation: Function to retry
            error_category: Category of error for retry configuration
            *args, **kwargs: Arguments to pass to the operation
            
        Returns:
            Tuple of (success: bool, result: Any)
        """
        config = self.retry_configs.get(error_category, RetryConfig())
        
        for attempt in range(config.max_attempts):
            try:
                result = operation(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"Operation succeeded on attempt {attempt + 1}")
                return True, result
                
            except Exception as e:
                if attempt == config.max_attempts - 1:
                    # Last attempt failed
                    error_info = ErrorInfo(
                        category=error_category,
                        severity=ErrorSeverity.MEDIUM,
                        message=f"Operation failed after {config.max_attempts} attempts",
                        exception=e,
                        context={'attempts': config.max_attempts}
                    )
                    self.handle_error(error_info)
                    return False, None
                
                # Calculate delay for next attempt
                delay = self._calculate_retry_delay(config, attempt)
                logger.warning(f"Operation failed (attempt {attempt + 1}/{config.max_attempts}), "
                             f"retrying in {delay:.1f}s: {e}")
                time.sleep(delay)
        
        return False, None
    
    def _log_error(self, error_info: ErrorInfo):
        """Log an error with appropriate level."""
        log_message = f"[{error_info.category.value}] {error_info.message}"
        
        if error_info.exception:
            log_message += f" - {type(error_info.exception).__name__}: {error_info.exception}"
        
        if error_info.context:
            context_str = ", ".join(f"{k}={v}" for k, v in error_info.context.items())
            log_message += f" (Context: {context_str})"
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _update_error_tracking(self, error_info: ErrorInfo):
        """Update error tracking statistics."""
        key = f"{error_info.category.value}_{error_info.severity.value}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
        self.last_errors[key] = error_info.timestamp
    
    def _is_error_threshold_exceeded(self, category: ErrorCategory) -> bool:
        """Check if error threshold is exceeded for a category."""
        threshold = self.error_thresholds.get(category, 5)
        
        # Count errors in the last hour
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent_errors = 0
        
        for key, timestamp in self.last_errors.items():
            if key.startswith(category.value) and timestamp > cutoff_time:
                recent_errors += self.error_counts.get(key, 0)
        
        return recent_errors >= threshold
    
    def _handle_critical_error(self, error_info: ErrorInfo) -> bool:
        """Handle critical errors."""
        logger.critical(f"Critical error encountered: {error_info.message}")
        return False
    
    def _handle_high_severity_error(self, error_info: ErrorInfo) -> bool:
        """Handle high severity errors with graceful degradation."""
        logger.error(f"High severity error, attempting graceful degradation: {error_info.message}")
        
        if error_info.category == ErrorCategory.DISPLAY_ERROR:
            # Try to recover display
            return True  # Continue with degraded display
        elif error_info.category == ErrorCategory.SYSTEM_ERROR:
            # System errors are serious
            return False
        
        return True
    
    def _handle_medium_severity_error(self, error_info: ErrorInfo) -> bool:
        """Handle medium severity errors with recovery attempts."""
        logger.warning(f"Medium severity error, attempting recovery: {error_info.message}")
        return True  # Continue operation
    
    def _handle_low_severity_error(self, error_info: ErrorInfo) -> bool:
        """Handle low severity errors."""
        logger.info(f"Low severity error, continuing operation: {error_info.message}")
        return True
    
    def _calculate_retry_delay(self, config: RetryConfig, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        if config.exponential_backoff:
            delay = config.base_delay * (2 ** attempt)
        else:
            delay = config.base_delay
        
        # Apply maximum delay limit
        delay = min(delay, config.max_delay)
        
        # Add jitter to prevent thundering herd
        if config.jitter:
            import random
            jitter_factor = random.uniform(0.8, 1.2)
            delay *= jitter_factor
        
        return delay
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        return {
            'error_counts': self.error_counts.copy(),
            'last_errors': {k: v.isoformat() for k, v in self.last_errors.items()},
            'thresholds': self.error_thresholds.copy()
        }
    
    def reset_error_counts(self, category: Optional[ErrorCategory] = None):
        """Reset error counts for a category or all categories."""
        if category:
            keys_to_remove = [k for k in self.error_counts.keys() if k.startswith(category.value)]
            for key in keys_to_remove:
                del self.error_counts[key]
                if key in self.last_errors:
                    del self.last_errors[key]
        else:
            self.error_counts.clear()
            self.last_errors.clear()
        
        logger.info(f"Reset error counts for {category.value if category else 'all categories'}")


# Global error handler instance
error_handler = ErrorHandler()


def handle_image_error(image_path: str, exception: Exception) -> bool:
    """
    Handle image loading errors.
    
    Args:
        image_path: Path to the image that failed to load
        exception: The exception that occurred
        
    Returns:
        bool: True if operation should continue
    """
    error_info = ErrorInfo(
        category=ErrorCategory.IMAGE_LOADING,
        severity=ErrorSeverity.LOW,
        message=f"Failed to load image: {image_path}",
        exception=exception,
        context={'image_path': image_path}
    )
    return error_handler.handle_error(error_info)


def handle_folder_error(folder_path: str, exception: Exception) -> bool:
    """
    Handle folder access errors.
    
    Args:
        folder_path: Path to the folder that failed to access
        exception: The exception that occurred
        
    Returns:
        bool: True if operation should continue
    """
    error_info = ErrorInfo(
        category=ErrorCategory.FOLDER_ACCESS,
        severity=ErrorSeverity.MEDIUM,
        message=f"Failed to access folder: {folder_path}",
        exception=exception,
        context={'folder_path': folder_path}
    )
    return error_handler.handle_error(error_info)


def handle_display_error(exception: Exception, context: Dict[str, Any] = None) -> bool:
    """
    Handle display system errors.
    
    Args:
        exception: The exception that occurred
        context: Additional context information
        
    Returns:
        bool: True if operation should continue
    """
    error_info = ErrorInfo(
        category=ErrorCategory.DISPLAY_ERROR,
        severity=ErrorSeverity.HIGH,
        message="Display system error occurred",
        exception=exception,
        context=context or {}
    )
    return error_handler.handle_error(error_info)


def handle_system_error(message: str, exception: Exception, context: Dict[str, Any] = None) -> bool:
    """
    Handle general system errors.
    
    Args:
        message: Error message
        exception: The exception that occurred
        context: Additional context information
        
    Returns:
        bool: True if operation should continue
    """
    error_info = ErrorInfo(
        category=ErrorCategory.SYSTEM_ERROR,
        severity=ErrorSeverity.HIGH,
        message=message,
        exception=exception,
        context=context or {}
    )
    return error_handler.handle_error(error_info)