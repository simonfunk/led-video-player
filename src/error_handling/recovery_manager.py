"""
Recovery manager for handling system-wide error recovery and graceful degradation.

This module provides:
- Coordinated error recovery across components
- System health monitoring
- Graceful degradation strategies
- Emergency fallback procedures
"""
import logging
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from threading import Lock, Thread, Event
from dataclasses import dataclass
from enum import Enum

from .error_handler import ErrorHandler, ErrorCategory, ErrorSeverity, ErrorInfo
from .fallback_display import FallbackDisplay


logger = logging.getLogger(__name__)


class SystemHealth(Enum):
    """System health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class ComponentStatus:
    """Status of a system component."""
    name: str
    healthy: bool
    last_error: Optional[datetime] = None
    error_count: int = 0
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3


class RecoveryManager:
    """
    Manages system-wide error recovery and graceful degradation.
    """
    
    def __init__(self, error_handler: ErrorHandler):
        """
        Initialize the recovery manager.
        
        Args:
            error_handler: The main error handler instance
        """
        self.error_handler = error_handler
        self.system_health = SystemHealth.HEALTHY
        self.components: Dict[str, ComponentStatus] = {}
        self.recovery_strategies: Dict[str, Callable] = {}
        self.fallback_display: Optional[FallbackDisplay] = None
        
        self._lock = Lock()
        self._monitoring_thread: Optional[Thread] = None
        self._monitoring_running = False
        self._monitoring_event = Event()
        
        # Recovery thresholds
        self.health_check_interval = 30  # seconds
        self.component_timeout = 300     # seconds before component considered failed
        self.emergency_threshold = 5     # critical errors before emergency mode
        
        # Initialize component tracking
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize tracking for system components."""
        component_names = [
            'image_manager',
            'carousel_manager', 
            'display_manager',
            'scheduler',
            'ui_controller'
        ]
        
        for name in component_names:
            self.components[name] = ComponentStatus(
                name=name,
                healthy=True,
                max_recovery_attempts=3 if name != 'display_manager' else 1
            )
    
    def register_recovery_strategy(self, component_name: str, recovery_function: Callable):
        """
        Register a recovery strategy for a component.
        
        Args:
            component_name: Name of the component
            recovery_function: Function to call for recovery
        """
        self.recovery_strategies[component_name] = recovery_function
        logger.info(f"Registered recovery strategy for {component_name}")
    
    def report_component_error(self, component_name: str, error_info: ErrorInfo) -> bool:
        """
        Report an error from a component and handle recovery.
        
        Args:
            component_name: Name of the component reporting the error
            error_info: Information about the error
            
        Returns:
            bool: True if component should continue, False if it should stop
        """
        with self._lock:
            if component_name not in self.components:
                logger.warning(f"Unknown component reported error: {component_name}")
                return True
            
            component = self.components[component_name]
            component.last_error = datetime.now()
            component.error_count += 1
            
            # Handle based on error severity
            if error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                component.healthy = False
                logger.warning(f"Component {component_name} marked as unhealthy due to {error_info.severity.value} error")
                
                # Attempt recovery
                if component.recovery_attempts < component.max_recovery_attempts:
                    return self._attempt_component_recovery(component_name)
                else:
                    logger.error(f"Component {component_name} exceeded recovery attempts")
                    return self._handle_component_failure(component_name)
            
            # Update system health
            self._update_system_health()
            
            return True
    
    def _attempt_component_recovery(self, component_name: str) -> bool:
        """
        Attempt to recover a failed component.
        
        Args:
            component_name: Name of the component to recover
            
        Returns:
            bool: True if recovery succeeded or component should continue
        """
        component = self.components[component_name]
        component.recovery_attempts += 1
        
        logger.info(f"Attempting recovery for {component_name} (attempt {component.recovery_attempts})")
        
        # Check if we have a recovery strategy
        if component_name in self.recovery_strategies:
            try:
                recovery_function = self.recovery_strategies[component_name]
                success = recovery_function()
                
                if success:
                    component.healthy = True
                    component.error_count = 0
                    logger.info(f"Successfully recovered component {component_name}")
                    self._update_system_health()
                    return True
                else:
                    logger.warning(f"Recovery failed for component {component_name}")
                    
            except Exception as e:
                logger.error(f"Recovery strategy failed for {component_name}: {e}")
        
        # Recovery failed or no strategy available
        return self._handle_component_failure(component_name)
    
    def _handle_component_failure(self, component_name: str) -> bool:
        """
        Handle permanent component failure.
        
        Args:
            component_name: Name of the failed component
            
        Returns:
            bool: True if system can continue without this component
        """
        logger.error(f"Component {component_name} has permanently failed")
        
        # Mark component as failed
        self.components[component_name].healthy = False
        
        # Determine if system can continue
        critical_components = ['display_manager']
        
        if component_name in critical_components:
            logger.critical(f"Critical component {component_name} failed, entering emergency mode")
            self._enter_emergency_mode()
            return False
        else:
            logger.warning(f"Non-critical component {component_name} failed, continuing with degraded functionality")
            self._update_system_health()
            return True
    
    def _update_system_health(self):
        """Update overall system health based on component status."""
        healthy_components = sum(1 for c in self.components.values() if c.healthy)
        total_components = len(self.components)
        
        if healthy_components == total_components:
            new_health = SystemHealth.HEALTHY
        elif healthy_components >= total_components * 0.8:
            new_health = SystemHealth.DEGRADED
        elif healthy_components >= total_components * 0.5:
            new_health = SystemHealth.CRITICAL
        else:
            new_health = SystemHealth.EMERGENCY
        
        if new_health != self.system_health:
            old_health = self.system_health
            self.system_health = new_health
            logger.warning(f"System health changed from {old_health.value} to {new_health.value}")
            
            # Take action based on health level
            if new_health == SystemHealth.EMERGENCY:
                self._enter_emergency_mode()
            elif new_health == SystemHealth.CRITICAL:
                self._enter_critical_mode()
    
    def _enter_critical_mode(self):
        """Enter critical mode with reduced functionality."""
        logger.warning("Entering critical mode - reduced functionality")
        
        # Disable non-essential features
        # This would be implemented based on specific application needs
        pass
    
    def _enter_emergency_mode(self):
        """Enter emergency mode with minimal functionality."""
        logger.critical("Entering emergency mode - minimal functionality only")
        
        # Stop all non-essential operations
        # Display emergency message
        # This would trigger application shutdown or safe mode
        pass
    
    def start_monitoring(self):
        """Start the health monitoring thread."""
        if self._monitoring_running:
            return
        
        self._monitoring_running = True
        self._monitoring_event.clear()
        self._monitoring_thread = Thread(target=self._monitoring_worker, daemon=True)
        self._monitoring_thread.start()
        
        logger.info("Started system health monitoring")
    
    def stop_monitoring(self):
        """Stop the health monitoring thread."""
        if not self._monitoring_running:
            return
        
        self._monitoring_running = False
        self._monitoring_event.set()
        
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5.0)
        
        logger.info("Stopped system health monitoring")
    
    def _monitoring_worker(self):
        """Background worker for system health monitoring."""
        while self._monitoring_running:
            try:
                # Wait for monitoring interval or stop event
                if self._monitoring_event.wait(timeout=self.health_check_interval):
                    break
                
                if not self._monitoring_running:
                    break
                
                # Perform health checks
                self._perform_health_checks()
                
            except Exception as e:
                logger.error(f"Error in monitoring worker: {e}")
    
    def _perform_health_checks(self):
        """Perform periodic health checks on components."""
        current_time = datetime.now()
        
        with self._lock:
            for component_name, component in self.components.items():
                # Check if component has been silent for too long
                if (component.last_error and 
                    current_time - component.last_error > timedelta(seconds=self.component_timeout)):
                    
                    if component.healthy:
                        logger.warning(f"Component {component_name} appears to be unresponsive")
                        # Could trigger a health check ping here
                
                # Reset error counts periodically for healthy components
                if (component.healthy and component.error_count > 0 and
                    (not component.last_error or 
                     current_time - component.last_error > timedelta(hours=1))):
                    component.error_count = 0
                    component.recovery_attempts = 0
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status information.
        
        Returns:
            Dictionary containing system status
        """
        with self._lock:
            component_status = {}
            for name, component in self.components.items():
                component_status[name] = {
                    'healthy': component.healthy,
                    'error_count': component.error_count,
                    'recovery_attempts': component.recovery_attempts,
                    'last_error': component.last_error.isoformat() if component.last_error else None
                }
            
            return {
                'system_health': self.system_health.value,
                'components': component_status,
                'monitoring_active': self._monitoring_running,
                'error_statistics': self.error_handler.get_error_statistics()
            }
    
    def force_recovery(self, component_name: str) -> bool:
        """
        Force recovery attempt for a specific component.
        
        Args:
            component_name: Name of the component to recover
            
        Returns:
            bool: True if recovery was attempted
        """
        if component_name not in self.components:
            logger.error(f"Cannot force recovery for unknown component: {component_name}")
            return False
        
        logger.info(f"Forcing recovery for component {component_name}")
        
        # Reset recovery attempts to allow retry
        with self._lock:
            self.components[component_name].recovery_attempts = 0
        
        return self._attempt_component_recovery(component_name)
    
    def reset_component_status(self, component_name: str):
        """
        Reset the status of a component to healthy.
        
        Args:
            component_name: Name of the component to reset
        """
        if component_name not in self.components:
            logger.error(f"Cannot reset unknown component: {component_name}")
            return
        
        with self._lock:
            component = self.components[component_name]
            component.healthy = True
            component.error_count = 0
            component.recovery_attempts = 0
            component.last_error = None
        
        self._update_system_health()
        logger.info(f"Reset status for component {component_name}")
    
    def cleanup(self):
        """Clean up recovery manager resources."""
        logger.info("Cleaning up recovery manager")
        self.stop_monitoring()
        
        with self._lock:
            self.components.clear()
            self.recovery_strategies.clear()
        
        logger.info("Recovery manager cleanup completed")


# Global recovery manager instance (will be initialized by application)
recovery_manager: Optional[RecoveryManager] = None


def initialize_recovery_manager(error_handler: ErrorHandler) -> RecoveryManager:
    """
    Initialize the global recovery manager.
    
    Args:
        error_handler: The main error handler instance
        
    Returns:
        RecoveryManager: The initialized recovery manager
    """
    global recovery_manager
    recovery_manager = RecoveryManager(error_handler)
    return recovery_manager


def get_recovery_manager() -> Optional[RecoveryManager]:
    """Get the global recovery manager instance."""
    return recovery_manager