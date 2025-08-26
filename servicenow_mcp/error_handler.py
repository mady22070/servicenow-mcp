"""
Comprehensive error handling for ServiceNow MCP server
"""

from __future__ import annotations
from typing import Any, Dict, Optional, Type, Union
from functools import wraps
import traceback
import sys
from datetime import datetime

from .models import MCPError, MCPResponse
from .logging_config import get_logger


class MCPException(Exception):
    """Base exception for MCP operations"""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "mcp_error",
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.utcnow()


class ValidationError(MCPException):
    """Validation error for input parameters"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
            
        super().__init__(message, "validation_error", details)


class AuthenticationError(MCPException):
    """Authentication/authorization error"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "auth_error")


class ServiceNowError(MCPException):
    """ServiceNow API error"""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        details = {}
        if status_code:
            details["status_code"] = status_code
        if response_data:
            details["response_data"] = response_data
            
        super().__init__(message, "servicenow_error", details)


class ConfigurationError(MCPException):
    """Configuration error"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        details = {}
        if config_key:
            details["config_key"] = config_key
            
        super().__init__(message, "config_error", details)


class GuardError(MCPException):
    """Security guard error"""
    
    def __init__(self, message: str, table: Optional[str] = None, operation: Optional[str] = None):
        details = {}
        if table:
            details["table"] = table
        if operation:
            details["operation"] = operation
            
        super().__init__(message, "guard_error", details)


class TimeoutError(MCPException):
    """Operation timeout error"""
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None):
        details = {}
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
            
        super().__init__(message, "timeout_error", details)


class ResourceNotFoundError(MCPException):
    """Resource not found error"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
            
        super().__init__(message, "not_found_error", details)


def create_error_response(
    error: Union[Exception, MCPException, str],
    operation: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> MCPResponse:
    """
    Create a standardized error response
    
    Args:
        error: Exception or error message
        operation: Operation that failed
        context: Additional context information
        
    Returns:
        MCPResponse with error details
    """
    logger = get_logger()
    
    if isinstance(error, MCPException):
        mcp_error = MCPError(
            error=error.error_code,
            message=error.message,
            details=error.details
        )
        
        # Add context if provided
        if context:
            mcp_error.details.update(context)
            
        # Add operation if provided
        if operation:
            mcp_error.details["operation"] = operation
            
        # Log the error
        logger.error(f"MCP Error in {operation or 'unknown'}: {error.message}", extra={
            "operation": operation,
            "error_code": error.error_code,
            "details": error.details
        })
        
    elif isinstance(error, Exception):
        # Convert generic exception to MCP error
        error_details = {
            "exception_type": type(error).__name__,
            "traceback": traceback.format_exc()
        }
        
        if context:
            error_details.update(context)
            
        if operation:
            error_details["operation"] = operation
            
        mcp_error = MCPError(
            error="internal_error",
            message=str(error),
            details=error_details
        )
        
        # Log the error
        logger.error(f"Unexpected error in {operation or 'unknown'}: {str(error)}", extra={
            "operation": operation,
            "exception_type": type(error).__name__,
            "traceback": traceback.format_exc()
        })
        
    else:
        # String error message
        error_details = {}
        if context:
            error_details.update(context)
        if operation:
            error_details["operation"] = operation
            
        mcp_error = MCPError(
            error="general_error",
            message=str(error),
            details=error_details
        )
        
        # Log the error
        logger.error(f"Error in {operation or 'unknown'}: {str(error)}", extra={
            "operation": operation,
            "message": str(error)
        })
    
    return MCPResponse(
        success=False,
        error=mcp_error,
        metadata={
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "operation": operation
        }
    )


def handle_errors(operation: Optional[str] = None):
    """
    Decorator for comprehensive error handling
    
    Args:
        operation: Name of the operation for logging
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # If result is already an MCPResponse with error, return as-is
                if isinstance(result, dict) and result.get("error"):
                    return result
                    
                # Wrap successful result in MCPResponse if not already wrapped
                if not isinstance(result, dict) or "success" not in result:
                    return MCPResponse(
                        success=True,
                        data=result if isinstance(result, dict) else {"result": result},
                        metadata={
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "operation": operation or func.__name__
                        }
                    ).dict()
                
                return result
                
            except MCPException as e:
                return create_error_response(e, operation or func.__name__).dict()
                
            except Exception as e:
                return create_error_response(e, operation or func.__name__).dict()
                
        return wrapper
    return decorator


def validate_parameters(model_class: Type):
    """
    Decorator for parameter validation using Pydantic models
    
    Args:
        model_class: Pydantic model class for validation
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Validate parameters using the model
                validated_params = model_class(**kwargs)
                
                # Replace kwargs with validated parameters
                return func(*args, **validated_params.dict())
                
            except Exception as e:
                if "validation error" in str(e).lower():
                    raise ValidationError(f"Parameter validation failed: {str(e)}")
                raise
                
        return wrapper
    return decorator


def safe_execute(func, *args, **kwargs) -> Dict[str, Any]:
    """
    Safely execute a function with error handling
    
    Args:
        func: Function to execute
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Dictionary with success/error information
    """
    try:
        result = func(*args, **kwargs)
        return {
            "success": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger = get_logger()
        logger.error(f"Safe execution failed: {str(e)}", extra={
            "function": func.__name__ if hasattr(func, '__name__') else str(func),
            "args": str(args)[:200],  # Truncate long args
            "kwargs": str(kwargs)[:200]  # Truncate long kwargs
        })
        
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


def log_and_raise(
    exception_class: Type[MCPException],
    message: str,
    operation: Optional[str] = None,
    **kwargs
):
    """
    Log an error and raise an exception
    
    Args:
        exception_class: Exception class to raise
        message: Error message
        operation: Operation name for logging
        **kwargs: Additional arguments for the exception
    """
    logger = get_logger()
    
    logger.error(f"Raising {exception_class.__name__}: {message}", extra={
        "operation": operation,
        "exception_class": exception_class.__name__,
        "message": message
    })
    
    raise exception_class(message, **kwargs)