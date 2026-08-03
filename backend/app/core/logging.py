"""
Structured Logging Configuration.
"""

import logging
import sys
from pythonjsonlogger import jsonlogger
from datetime import datetime


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno


def setup_logging(env: str = "development"):
    """
    Setup structured logging.

    Args:
        env: Environment (development, production)
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

    if env == "production":
        # JSON format for production
        formatter = CustomJsonFormatter(
            fmt='%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Human-readable format for development
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