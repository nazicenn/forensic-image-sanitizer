"""
Structured Logging Configuration.
"""

import logging
import sys
from datetime import datetime

# Try to import jsonlogger, fallback to standard logging
try:
    from pythonjsonlogger import jsonlogger
    HAS_JSON_LOGGER = True
except ImportError:
    HAS_JSON_LOGGER = False
    jsonlogger = None


class CustomJsonFormatter:
    """Custom JSON formatter with additional fields."""
    
    def __init__(self, fmt=None):
        self.fmt = fmt or '%(timestamp)s %(level)s %(name)s %(message)s'
    
    def format(self, record):
        log_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }
        return str(log_record)


def setup_logging(env: str = "development"):
    """
    Setup structured logging.
    """
    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set level
    log_level = logging.DEBUG if env == "development" else logging.INFO
    root_logger.setLevel(log_level)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)

    if env == "production" and HAS_JSON_LOGGER:
        # JSON format for production
        formatter = jsonlogger.JsonFormatter(
            fmt='%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Human-readable format for development or fallback
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set third-party log levels
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)