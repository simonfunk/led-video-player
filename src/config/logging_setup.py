"""
Logging setup with file rotation support.
"""
import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

from .models import LoggingConfig


class LoggingSetup:
    """Sets up application logging with file rotation."""
    
    @staticmethod
    def setup_logging(config: LoggingConfig) -> None:
        """
        Set up logging based on configuration.
        
        Args:
            config: Logging configuration
        """
        # Create root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, config.level.upper()))
        
        # Clear any existing handlers
        root_logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Set up console logging
        if config.log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, config.level.upper()))
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # Set up file logging with rotation
        if config.log_to_file:
            try:
                # Ensure log directory exists
                log_path = Path(config.log_file_path)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Create rotating file handler
                file_handler = logging.handlers.RotatingFileHandler(
                    filename=config.log_file_path,
                    maxBytes=config.max_file_size_mb * 1024 * 1024,  # Convert MB to bytes
                    backupCount=config.backup_count,
                    encoding='utf-8'
                )
                file_handler.setLevel(getattr(logging, config.level.upper()))
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
                
                logging.info(f"File logging enabled: {config.log_file_path}")
                
            except Exception as e:
                # If file logging fails, log to console
                logging.error(f"Failed to set up file logging: {e}")
                if not config.log_to_console:
                    # Ensure we have at least console logging
                    console_handler = logging.StreamHandler()
                    console_handler.setLevel(getattr(logging, config.level.upper()))
                    console_handler.setFormatter(formatter)
                    root_logger.addHandler(console_handler)
        
        # Log initial setup message
        logging.info("Logging system initialized")
        logging.info(f"Log level: {config.level}")
        logging.info(f"Console logging: {config.log_to_console}")
        logging.info(f"File logging: {config.log_to_file}")
        
        if config.log_to_file:
            logging.info(f"Log file: {config.log_file_path}")
            logging.info(f"Max file size: {config.max_file_size_mb}MB")
            logging.info(f"Backup count: {config.backup_count}")
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Get a logger instance.
        
        Args:
            name: Logger name (typically __name__)
            
        Returns:
            logging.Logger: Logger instance
        """
        return logging.getLogger(name)