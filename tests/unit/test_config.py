"""
Unit tests for configuration management.
"""

import pytest
import os
from unittest.mock import patch

from tests import get_test_env_var, TEST_CONFIG


class TestConfiguration:
    """Test configuration utilities."""
    
    def test_get_test_env_var_with_value(self):
        """Test getting environment variable with value."""
        with patch.dict(os.environ, {"TEST_EXAMPLE": "test_value"}):
            result = get_test_env_var("EXAMPLE")
            assert result == "test_value"
    
    def test_get_test_env_var_with_default(self):
        """Test getting environment variable with default."""
        result = get_test_env_var("NONEXISTENT", "default_value")
        assert result == "default_value"
    
    def test_get_test_env_var_none(self):
        """Test getting nonexistent environment variable."""
        result = get_test_env_var("NONEXISTENT")
        assert result is None
    
    def test_test_config_structure(self):
        """Test that TEST_CONFIG has expected structure."""
        assert "default_env" in TEST_CONFIG
        assert "timeout" in TEST_CONFIG
        assert "retries" in TEST_CONFIG
        assert "dry_run" in TEST_CONFIG
        assert "log_level" in TEST_CONFIG
        
        # Verify types
        assert isinstance(TEST_CONFIG["default_env"], str)
        assert isinstance(TEST_CONFIG["timeout"], int)
        assert isinstance(TEST_CONFIG["retries"], int)
        assert isinstance(TEST_CONFIG["dry_run"], bool)
        assert isinstance(TEST_CONFIG["log_level"], str)