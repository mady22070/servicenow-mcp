"""
Enhanced decorators for MCP tool registration with consistent patterns
"""

from functools import wraps
from typing import Any, Callable, Optional, Type
from .error_handler import handle_errors, validate_parameters
from .logging_config import get_logger, LogContext
from .client_factory import get_client_factory


def servicenow_tool(
    operation_name: Optional[str] = None,
    table: Optional[str] = None,
    validation_model: Optional[Type] = None,
    require_client: bool = True,
    async_operation: bool = False
):
    """
    Comprehensive decorator for ServiceNow MCP tools
    
    Args:
        operation_name: Name for logging and error handling
        table: ServiceNow table name for logging context
        validation_model: Pydantic model for parameter validation
        require_client: Whether to inject ServiceNow client
        async_operation: Whether to use async client
    """
    def decorator(func: Callable) -> Callable:
        # Apply validation if model provided
        if validation_model:
            func = validate_parameters(validation_model)(func)
        
        # Apply error handling
        op_name = operation_name or func.__name__
        func = handle_errors(op_name)(func)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract environment
            env = kwargs.get('env', 'dev')
            
            # Set up logging context
            log_context = {
                'operation': op_name,
                'env': env
            }
            if table:
                log_context['table'] = table
            if 'sys_id' in kwargs:
                log_context['sys_id'] = kwargs['sys_id']
            
            with LogContext(get_logger(), **log_context):
                # Inject client if required
                if require_client:
                    if async_operation:
                        # For async operations, we'd need to handle this differently
                        # This is a simplified version
                        client_factory = get_client_factory()
                        client = client_factory.get_sync_client(env)
                    else:
                        client_factory = get_client_factory()
                        client = client_factory.get_sync_client(env)
                    
                    # Add client as first argument if not already present
                    if not args or not hasattr(args[0], 'get_record'):
                        args = (client,) + args
                
                result = func(*args, **kwargs)
                
                # Log success
                logger = get_logger()
                logger.info(f"Operation {op_name} completed successfully")
                
                return result
        
        return wrapper
    return decorator


def incident_tool(operation_name: Optional[str] = None, validation_model: Optional[Type] = None):
    """Specialized decorator for incident operations"""
    return servicenow_tool(
        operation_name=operation_name,
        table="incident",
        validation_model=validation_model,
        require_client=True
    )


def query_tool(operation_name: Optional[str] = None, validation_model: Optional[Type] = None):
    """Specialized decorator for query operations"""
    return servicenow_tool(
        operation_name=operation_name,
        validation_model=validation_model,
        require_client=True
    )


def dev_tool(operation_name: Optional[str] = None, validation_model: Optional[Type] = None):
    """Specialized decorator for development operations"""
    return servicenow_tool(
        operation_name=operation_name,
        validation_model=validation_model,
        require_client=True
    )