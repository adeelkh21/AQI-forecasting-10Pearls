"""
Structured logging utilities for the AQI Forecasting System
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from .paths import LOG_LEVEL, LOG_FORMAT

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if they exist
        if hasattr(record, 'job_id'):
            log_entry['job_id'] = record.job_id
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

class ConsoleFormatter(logging.Formatter):
    """Human-readable console formatter"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record for console output"""
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Color coding for different levels
        level_colors = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m'  # Magenta
        }
        
        color = level_colors.get(record.levelname, '')
        reset = '\033[0m'
        
        # Format the message
        formatted = f"{color}[{timestamp}] {record.levelname:8s}{reset} {record.name}: {record.getMessage()}"
        
        # Add job_id if present
        if hasattr(record, 'job_id'):
            formatted += f" (Job: {record.job_id})"
        
        return formatted

def setup_logging(
    level: str = None,
    format_type: str = None,
    log_file: Optional[Path] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Setup logging configuration
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Log format ('json' or 'console')
        log_file: Optional log file path
        console_output: Whether to output to console
    
    Returns:
        Configured logger
    """
    # Use defaults from paths if not specified
    if level is None:
        level = LOG_LEVEL
    
    if format_type is None:
        format_type = LOG_FORMAT
    
    # Create logger
    logger = logging.getLogger('aqi_forecasting')
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        if format_type.lower() == 'json':
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_handler.setFormatter(ConsoleFormatter())
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance"""
    if name:
        return logging.getLogger(f'aqi_forecasting.{name}')
    return logging.getLogger('aqi_forecasting')

def log_with_context(logger: logging.Logger, level: str, message: str, **context):
    """Log message with additional context"""
    extra = {'extra': context}
    
    if level.upper() == 'DEBUG':
        logger.debug(message, extra=extra)
    elif level.upper() == 'INFO':
        logger.info(message, extra=extra)
    elif level.upper() == 'WARNING':
        logger.warning(message, extra=extra)
    elif level.upper() == 'ERROR':
        logger.error(message, extra=extra)
    elif level.upper() == 'CRITICAL':
        logger.critical(message, extra=extra)

# Convenience functions
def log_job_start(logger: logging.Logger, job_id: str, job_type: str, **kwargs):
    """Log job start with context"""
    log_with_context(
        logger, 'INFO',
        f"Job {job_id} started: {job_type}",
        job_id=job_id,
        job_type=job_type,
        **kwargs
    )

def log_job_complete(logger: logging.Logger, job_id: str, job_type: str, success: bool, **kwargs):
    """Log job completion with context"""
    status = "completed successfully" if success else "failed"
    log_with_context(
        logger, 'INFO' if success else 'ERROR',
        f"Job {job_id} {status}: {job_type}",
        job_id=job_id,
        job_type=job_type,
        success=success,
        **kwargs
    )

def log_data_operation(logger: logging.Logger, operation: str, file_path: str, **kwargs):
    """Log data operation with context"""
    log_with_context(
        logger, 'INFO',
        f"Data operation: {operation} on {file_path}",
        operation=operation,
        file_path=file_path,
        **kwargs
    )

if __name__ == "__main__":
    # Test logging setup
    print("🔍 Testing logging configuration...")
    
    # Test console logging
    logger = setup_logging(level='INFO', format_type='console')
    logger.info("✅ Console logging test successful")
    logger.warning("⚠️ Warning message test")
    logger.error("❌ Error message test")
    
    # Test JSON logging
    json_logger = setup_logging(level='INFO', format_type='json')
    json_logger.info("✅ JSON logging test successful")
    
    # Test context logging
    log_with_context(logger, 'INFO', 'Test message with context', user_id='test_user', operation='test')
    
    print("✅ Logging tests completed!")
