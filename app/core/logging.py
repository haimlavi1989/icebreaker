import sys
import os
from loguru import logger
from app.core.config import settings

def setup_logging():
    """Configure the logger for the application."""
    # Remove default handlers
    logger.remove()
    
    # Add console handler with appropriate format
    logger.add(
        sys.stderr,
        format=settings.LOG_FORMAT,
        level=settings.LOG_LEVEL,
        colorize=True,
    )
    
    # Add file handler for persistent logs
    os.makedirs("logs", exist_ok=True)
    logger.add(
        "logs/icebreaker.log",
        rotation="10 MB",  # Rotate when the file reaches 10MB
        retention="1 week",  # Keep logs for 1 week
        compression="zip",  # Compress rotated logs
        level=settings.LOG_LEVEL,
        format="{time} | {level} | {name}:{function}:{line} - {message}",
    )
    
    # Add separate error log
    logger.add(
        "logs/errors.log",
        rotation="10 MB",
        retention="1 month",
        compression="zip",
        level="ERROR",
        format="{time} | {level} | {name}:{function}:{line} - {message}",
        backtrace=True,
        diagnose=True,
    )
    
    # Log startup message
    logger.info(f"Ice Breaker Generator starting up | Environment: {'TESTING' if settings.TESTING else 'DEVELOPMENT' if settings.DEBUG else 'PRODUCTION'}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    
    return logger