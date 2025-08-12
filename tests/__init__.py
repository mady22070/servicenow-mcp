"""
Test suite for ServiceNow MCP Server

This module provides test configuration, utilities, and fixtures for the
ServiceNow MCP server test suite. It includes setup for both unit and
integration tests with proper environment isolation.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Test configuration constants
TEST_ENV_PREFIX = "TEST_"
DEFAULT_TEST_TIMEOUT = 30
DEFAULT_TEST_RETRIES = 3

# Test data directories
TEST_DATA_DIR = Path(__file__).parent / "data"
FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Ensure test data directories exist
TEST_DATA_DIR.mkdir(exist_ok=True)
FIXTURES_DIR.mkdir(exist_ok=True)

# Test environment configuration
TEST_CONFIG = {
    "default_env": "dev",
    "timeout": DEFAULT_TEST_TIMEOUT,
    "retries": DEFAULT_TEST_RETRIES,
    "dry_run": True,  # Always use dry run in tests by default
    "log_level": "DEBUG",
}

def get_test_env_var(name: str, default: str = None) -> str:
    """
    Get test environment variable with TEST_ prefix.
    
    Args:
        name: Variable name (without TEST_ prefix)
        default: Default value if not found
        
    Returns:
        Environment variable value or default
    """
    return os.getenv(f"{TEST_ENV_PREFIX}{name}", default)

def is_integration_test_enabled() -> bool:
    """
    Check if integration tests should run.
    
    Returns:
        True if integration tests are enabled
    """
    return get_test_env_var("INTEGRATION_ENABLED", "false").lower() == "true"

def get_test_servicenow_config() -> dict:
    """
    Get ServiceNow configuration for testing.
    
    Returns:
        Dictionary with test ServiceNow configuration
    """
    return {
        "instance_url": get_test_env_var("SERVICENOW_INSTANCE_URL"),
        "username": get_test_env_var("SERVICENOW_USERNAME"),
        "password": get_test_env_var("SERVICENOW_PASSWORD"),
    }

# Version information for tests
try:
    from servicenow_mcp.version import __version__
    TEST_VERSION = __version__
except ImportError:
    TEST_VERSION = "unknown"

__all__ = [
    "TEST_CONFIG",
    "TEST_DATA_DIR", 
    "FIXTURES_DIR",
    "get_test_env_var",
    "is_integration_test_enabled",
    "get_test_servicenow_config",
    "TEST_VERSION",
]