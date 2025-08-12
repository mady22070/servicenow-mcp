"""
Decorators for ServiceNow MCP tools - Error handling, caching, and validation
"""

import functools
import time
from typing import Any, Callable, Dict, Optional
import logging

logger = logging.getLogger(__name__)


def servicenow_tool(cache_ttl: Optional[int] = None, 
                   validate_env: bool = True,
                   require_client: bool = True):
    """
    Decorator for ServiceNow MCP tools with common functionality
    
    Args:
        cache_ttl: Cache time-to-live in seconds (None = no caching)
        validate_env: Whether to validate environment parameter
        require_client: Whether this tool requires a ServiceNow client
    """
    def decorator(func: Callable) -> Callable:
        # Simple in-memory cache
        cache = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Environment validation
                if validate_env and 'env' in kwargs:
                    env = kwargs['env']
                    if env not in ['dev', 'test', 'prod']:
                        return {
                            "error": "invalid_environment",
                            "message": f"Environment '{env}' not supported. Use: dev, test, prod"
                        }
                
                # Cache check
                if cache_ttl:
                    cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
                    if cache_key in cache:
                        cached_result, cached_time = cache[cache_key]
                        if time.time() - cached_time < cache_ttl:
                            logger.debug(f"Cache hit for {func.__name__}")
                            return cached_result
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Cache result
                if cache_ttl and isinstance(result, dict) and 'error' not in result:
                    cache[cache_key] = (result, time.time())
                
                # Add execution metadata
                if isinstance(result, dict):
                    result['_meta'] = {
                        'execution_time_ms': round((time.time() - start_time) * 1000, 2),
                        'function': func.__name__,
                        'cached': False
                    }
                
                return result
                
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                return {
                    "error": "execution_error",
                    "message": str(e),
                    "function": func.__name__,
                    "_meta": {
                        "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                        "error": True
                    }
                }
        
        return wrapper
    return decorator


def guard_table(tables: list, operation: str = "write"):
    """
    Decorator to apply table guards to tool functions
    
    Args:
        tables: List of table names to guard
        operation: Operation type (read/write)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from .utils.guard import is_allowed
            
            dry_run = kwargs.get('dry_run', False)
            
            # Check guards for each table
            for table in tables:
                ok, why = is_allowed(table, operation, dry_run)
                if not ok:
                    return {
                        "error": "guard_block",
                        "message": why,
                        "table": table,
                        "operation": operation
                    }
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_required_params(*required_params):
    """
    Decorator to validate required parameters
    
    Args:
        required_params: Parameter names that are required
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            missing_params = []
            
            for param in required_params:
                if param not in kwargs or kwargs[param] is None:
                    missing_params.append(param)
            
            if missing_params:
                return {
                    "error": "missing_required_parameters",
                    "message": f"Missing required parameters: {', '.join(missing_params)}",
                    "required_parameters": required_params,
                    "missing_parameters": missing_params
                }
            
            return func(*args, **kwargs)
        return wrapper
    return decorator