"""
Observability Module for Consulting Intelligence Platform

Provides structured logging, Cloud Logging integration, and error tracking
for production deployments on Google Cloud Run.

Author: Manoj Gundeti
"""

import logging
import json
import os
import sys
import traceback
from datetime import datetime
from typing import Optional, Any, Dict
from functools import wraps
import time


class CloudLoggingFormatter(logging.Formatter):
    """
    Formatter that outputs JSON structured logs for Google Cloud Logging.
    
    Cloud Logging automatically parses JSON logs and extracts severity,
    message, and custom fields for querying.
    """
    
    SEVERITY_MAP = {
        logging.DEBUG: 'DEBUG',
        logging.INFO: 'INFO',
        logging.WARNING: 'WARNING',
        logging.ERROR: 'ERROR',
        logging.CRITICAL: 'CRITICAL',
    }
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'severity': self.SEVERITY_MAP.get(record.levelno, 'DEFAULT'),
            'message': record.getMessage(),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info) if record.exc_info[0] else None
            }
        
        # Add custom fields from extra
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, default=str)


class LocalFormatter(logging.Formatter):
    """Human-readable formatter for local development."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format: [TIME] LEVEL module:function:line - message
        timestamp = datetime.now().strftime('%H:%M:%S')
        base_msg = f"[{timestamp}] {color}{record.levelname:8}{reset} {record.module}:{record.funcName}:{record.lineno} - {record.getMessage()}"
        
        if record.exc_info:
            base_msg += '\n' + ''.join(traceback.format_exception(*record.exc_info))
        
        return base_msg


def setup_logging(
    level: int = logging.INFO,
    cloud_logging: bool = None,
    app_name: str = "cip"
) -> logging.Logger:
    """
    Configure logging for the application.
    
    Args:
        level: Logging level (default INFO)
        cloud_logging: Force cloud logging format (auto-detected if None)
        app_name: Application name for the root logger
        
    Returns:
        Configured root logger
    """
    # Auto-detect Cloud Run environment
    if cloud_logging is None:
        cloud_logging = os.getenv('K_SERVICE') is not None  # K_SERVICE is set by Cloud Run
    
    # Get root logger
    logger = logging.getLogger(app_name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Set appropriate formatter
    if cloud_logging:
        handler.setFormatter(CloudLoggingFormatter())
    else:
        handler.setFormatter(LocalFormatter())
    
    logger.addHandler(handler)
    
    # Also configure the root logger for third-party libraries
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)  # Suppress noisy libraries
    
    return logger


def log_with_context(logger: logging.Logger, level: int, message: str, **context):
    """
    Log a message with additional context fields.
    
    Args:
        logger: Logger instance
        level: Log level
        message: Log message
        **context: Additional fields to include in structured log
    """
    record = logger.makeRecord(
        logger.name, level, '', 0, message, args=(), exc_info=None
    )
    record.extra_fields = context
    logger.handle(record)


def request_timer(logger: Optional[logging.Logger] = None):
    """
    Decorator to log function execution time.
    
    Args:
        logger: Logger to use (creates one if None)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                log_with_context(
                    logger, logging.DEBUG, 
                    f"{func.__name__} completed",
                    function=func.__name__,
                    duration_ms=round(elapsed * 1000, 2),
                    status="success"
                )
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                log_with_context(
                    logger, logging.ERROR,
                    f"{func.__name__} failed: {str(e)}",
                    function=func.__name__,
                    duration_ms=round(elapsed * 1000, 2),
                    status="error",
                    error_type=type(e).__name__
                )
                raise
        return wrapper
    return decorator


class HealthCheck:
    """
    Simple health check for Cloud Run.
    
    Tracks application health status for the health check endpoint.
    """
    
    def __init__(self):
        self.healthy = True
        self.last_check = datetime.utcnow()
        self.details: Dict[str, Any] = {}
    
    def set_healthy(self, component: str = "app"):
        """Mark a component as healthy."""
        self.healthy = True
        self.details[component] = {"status": "healthy", "checked_at": datetime.utcnow().isoformat()}
        self.last_check = datetime.utcnow()
    
    def set_unhealthy(self, component: str = "app", reason: str = "Unknown"):
        """Mark a component as unhealthy."""
        self.healthy = False
        self.details[component] = {
            "status": "unhealthy", 
            "reason": reason, 
            "checked_at": datetime.utcnow().isoformat()
        }
        self.last_check = datetime.utcnow()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return {
            "status": "healthy" if self.healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": self.details
        }


# Global health check instance
health = HealthCheck()


# Initialize logging on module import
def get_logger(name: str = "cip") -> logging.Logger:
    """Get a configured logger for the given name."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        setup_logging(app_name=name)
    return logger


# Environment validation
def validate_environment() -> Dict[str, bool]:
    """
    Validate required environment variables.
    
    Returns:
        Dict mapping variable names to whether they're set
    """
    required_vars = [
        'GOOGLE_API_KEY',
    ]
    
    optional_vars = [
        'DATABASE_TYPE',
        'DB_HOST',
        'DB_PORT', 
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD',
        'SMTP_SERVER',
        'SENDER_EMAIL',
        'SENDER_PASSWORD',
    ]
    
    results = {}
    
    for var in required_vars:
        value = os.getenv(var)
        results[var] = bool(value and value.strip())
    
    for var in optional_vars:
        value = os.getenv(var)
        results[var] = bool(value and value.strip()) if value else None
    
    return results


if __name__ == "__main__":
    # Test the logging configuration
    logger = setup_logging(level=logging.DEBUG)
    
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Test with context
    log_with_context(logger, logging.INFO, "User logged in", user_id=123, action="login")
    
    # Test environment validation
    env_status = validate_environment()
    print("\nEnvironment Status:")
    for var, status in env_status.items():
        status_str = "✅ Set" if status else ("⚠️ Optional" if status is None else "❌ Missing")
        print(f"  {var}: {status_str}")
