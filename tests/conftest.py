"""
Pytest configuration and shared fixtures for ServiceNow MCP tests.

This module provides common fixtures, test configuration, and utilities
used across the test suite.
"""

import os
import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, Generator
import tempfile
import shutil
from pathlib import Path

# Import test utilities
from tests import (
    TEST_CONFIG,
    get_test_env_var,
    is_integration_test_enabled,
    get_test_servicenow_config,
)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle integration test skipping."""
    if not is_integration_test_enabled():
        skip_integration = pytest.mark.skip(
            reason="Integration tests disabled (set TEST_INTEGRATION_ENABLED=true)"
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


# Environment fixtures
@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Provide test configuration."""
    return TEST_CONFIG.copy()


@pytest.fixture(scope="session")
def servicenow_config() -> Dict[str, str]:
    """Provide ServiceNow configuration for tests."""
    return get_test_servicenow_config()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


# Mock fixtures
@pytest.fixture
def mock_servicenow_client():
    """Provide a mock ServiceNow client."""
    client = Mock()
    
    # Mock common methods
    client.query_table.return_value = {
        "result": [],
        "_meta": {"execution_time_ms": 100, "cached": False}
    }
    client.get_record.return_value = {
        "result": {"sys_id": "test123", "number": "INC0000001"},
        "_meta": {"execution_time_ms": 50, "cached": False}
    }
    client.create_record.return_value = {
        "result": {"sys_id": "new123"},
        "_meta": {"execution_time_ms": 200, "cached": False}
    }
    client.update_record.return_value = {
        "result": {"sys_id": "test123"},
        "_meta": {"execution_time_ms": 150, "cached": False}
    }
    client.delete_record.return_value = {
        "result": {"success": True},
        "_meta": {"execution_time_ms": 100, "cached": False}
    }
    
    return client


@pytest.fixture
def mock_client_manager():
    """Provide a mock client manager."""
    manager = Mock()
    manager.get_client.return_value = Mock()
    manager.health_check.return_value = {
        "dev": {"status": "healthy", "response_time": "0.1s"}
    }
    manager.get_active_environments.return_value = ["dev"]
    return manager


@pytest.fixture
def sample_incident_data():
    """Provide sample incident data for tests."""
    return {
        "short_description": "Test incident",
        "description": "This is a test incident for unit testing",
        "urgency": "3",
        "impact": "3",
        "category": "Software",
        "subcategory": "Application",
        "state": "1",
        "assigned_to": "test.user",
    }


@pytest.fixture
def sample_user_story():
    """Provide sample user story for testing."""
    return (
        "As a service desk agent, I want to automatically assign incidents "
        "based on category so that tickets are routed to the right team faster"
    )


@pytest.fixture
def sample_cmdb_data():
    """Provide sample CMDB data for tests."""
    return [
        {
            "sys_id": "ci001",
            "name": "Server001",
            "ip_address": "192.168.1.100",
            "serial_number": "SN001",
            "sys_class_name": "cmdb_ci_server",
        },
        {
            "sys_id": "ci002", 
            "name": "Server001",  # Potential duplicate
            "ip_address": "192.168.1.100",
            "serial_number": "SN002",
            "sys_class_name": "cmdb_ci_server",
        },
    ]


# Environment variable fixtures
@pytest.fixture
def clean_env():
    """Provide clean environment for tests."""
    original_env = os.environ.copy()
    # Clear ServiceNow environment variables
    for key in list(os.environ.keys()):
        if key.startswith("SERVICENOW_") or key.startswith("MCP_"):
            del os.environ[key]
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def test_env_vars():
    """Set up test environment variables."""
    test_vars = {
        "SERVICENOW_DEV_INSTANCE_URL": "https://test.service-now.com",
        "SERVICENOW_DEV_USERNAME": "test_user",
        "SERVICENOW_DEV_PASSWORD": "test_pass",
        "MCP_LOG_LEVEL": "DEBUG",
        "MCP_ALLOW_TABLES": "incident,problem,change_request",
    }
    
    original_values = {}
    for key, value in test_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield test_vars
    
    # Restore original values
    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


# Async fixtures for async tests
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Parametrized fixtures
@pytest.fixture(params=["dev", "test", "prod"])
def environment(request):
    """Parametrized fixture for different environments."""
    return request.param


@pytest.fixture(params=[True, False])
def dry_run_mode(request):
    """Parametrized fixture for dry run mode."""
    return request.param


# Integration test fixtures
@pytest.fixture(scope="session")
@pytest.mark.integration
def real_servicenow_client():
    """Provide real ServiceNow client for integration tests."""
    config = get_test_servicenow_config()
    if not all(config.values()):
        pytest.skip("ServiceNow configuration not available for integration tests")
    
    # Import here to avoid import errors if module not available
    try:
        from servicenow_mcp.servicenow_client import ServiceNowClient
        return ServiceNowClient(
            instance_url=config["instance_url"],
            username=config["username"],
            password=config["password"],
        )
    except ImportError:
        pytest.skip("ServiceNow client not available")


# Utility fixtures
@pytest.fixture
def capture_logs(caplog):
    """Capture and provide access to logs during tests."""
    import logging
    caplog.set_level(logging.DEBUG)
    return caplog


@pytest.fixture
def mock_time():
    """Mock time functions for consistent testing."""
    import time
    from unittest.mock import patch
    
    with patch('time.time', return_value=1640995200.0):  # 2022-01-01 00:00:00
        with patch('time.sleep'):
            yield


# Performance testing fixtures
@pytest.fixture
def performance_monitor():
    """Monitor performance during tests."""
    import time
    start_time = time.time()
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = start_time
            
        def elapsed(self):
            return time.time() - self.start_time
            
        def assert_max_time(self, max_seconds):
            elapsed = self.elapsed()
            assert elapsed <= max_seconds, f"Test took {elapsed}s, max allowed {max_seconds}s"
    
    yield PerformanceMonitor()