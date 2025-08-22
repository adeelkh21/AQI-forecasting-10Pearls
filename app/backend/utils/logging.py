import logging
import sys
from pathlib import Path
from typing import Optional

from .paths import ENV_CONFIG, REPORTS_DIR


def setup_logging(
    level: str = None,
    log_file: Optional[Path] = None,
    include_timestamp: bool = True
) -> logging.Logger:
    """
    Set up consistent logging configuration for the backend.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging
        include_timestamp: Whether to include timestamps in log format
        
    Returns:
        Configured logger instance
    """
    # Get log level from environment or use default
    log_level = level or ENV_CONFIG.get("LOG_LEVEL", "INFO")
    
    # Create formatter
    if include_timestamp:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            '%(name)s - %(levelname)s - %(message)s'
        )
    
    # Create logger
    logger = logging.getLogger('aqi_backend')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (will be prefixed with 'aqi_backend.')
        
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f'aqi_backend.{name}')
    return logging.getLogger('aqi_backend')


def log_job_progress(job_id: str, step: str, status: str, message: str = ""):
    """
    Log job progress with consistent formatting.
    
    Args:
        job_id: Unique job identifier
        step: Current step name
        status: Step status (pending, running, success, failed)
        message: Optional message about the step
    """
    logger = get_logger('jobs')
    log_msg = f"Job {job_id} - {step}: {status}"
    if message:
        log_msg += f" - {message}"
    
    if status == 'failed':
        logger.error(log_msg)
    elif status == 'success':
        logger.info(log_msg)
    elif status == 'running':
        logger.info(log_msg)
    else:
        logger.debug(log_msg)


# Create default logger
default_logger = setup_logging()
