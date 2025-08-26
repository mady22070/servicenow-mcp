"""
Logging configuration for ServiceNow MCP server
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional
import json


class MCPFormatter(logging.Formatter):
    """Custom formatter for MCP server logs"""
    
    def __init__(self):
        super().__init__()
        
    def format(self, record):
        # Create structured log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'env'):
            log_entry['environment'] = record.env
        if hasattr(record, 'table'):
            log_entry['table'] = record.table
        if hasattr(record, 'operation'):
            log_entry['operation'] = record.operation
        if hasattr(record, 'sys_id'):
            log_entry['sys_id'] = record.sys_id
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        if hasattr(record, 'user'):
            log_entry['user'] = record.user
            
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry, default=str)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_console: bool = True
) -> logging.Logger:
    """
    Setup logging configuration for the MCP server
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        enable_console: Whether to enable console logging
        
    Returns:
        Configured logger instance
    """
    
    # Get log level from environment or parameter
    log_level = os.getenv("MCP_LOG_LEVEL", level).upper()
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    # Create root logger
    logger = logging.getLogger("servicenow_mcp")
    logger.setLevel(numeric_level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = MCPFormatter()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    # Log startup message
    logger.info("ServiceNow MCP logging initialized", extra={
        "level": log_level,
        "console_enabled": enable_console,
        "file_logging": log_file is not None,
        "log_file": log_file
    })
    
    return logger


def get_logger(name: str = "servicenow_mcp") -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding structured logging context"""
    
    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self.old_factory = None
        
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
            
        logging.setLogRecordFactory(record_factory)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


# Performance logging decorator
def log_performance(operation: str):
    """Decorator to log operation performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger()
            start_time = datetime.utcnow()
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                logger.info(f"Operation completed: {operation}", extra={
                    "operation": operation,
                    "duration_ms": round(duration, 2),
                    "success": True
                })
                
                return result
                
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                logger.error(f"Operation failed: {operation}", extra={
                    "operation": operation,
                    "duration_ms": round(duration, 2),
                    "success": False,
                    "error": str(e)
                })
                
                raise
                
        return wrapper
    return decorator


# Initialize default logger
_default_logger = None

def init_default_logger():
    """Initialize the default logger with environment-based configuration"""
    global _default_logger
    if _default_logger is None:
        log_level = os.getenv("MCP_LOG_LEVEL", "INFO")
        log_file = os.getenv("MCP_LOG_FILE")
        enable_console = os.getenv("MCP_LOG_CONSOLE", "true").lower() == "true"
        
        _default_logger = setup_logging(
            level=log_level,
            log_file=log_file,
            enable_console=enable_console
        )
    
    return _default_logger