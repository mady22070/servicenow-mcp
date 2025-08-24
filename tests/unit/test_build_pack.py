"""
Unit tests for the build pack
"""

import pytest
from unittest.mock import Mock, call
from servicenow_mcp.packs import build_pack

class TestBuildPack:
    """Test cases for build pack functionality"""

    def test_app_scaffold_dry_run(self, mock_servicenow_client):
        """Test app_scaffold in dry run mode"""
        result = build_pack.app_scaffold(
            mock_servicenow_client,
            app_name="Test App",
            scope_name="x_mcp_test_app",
            description="A test application",
            dry_run=True
        )
        assert result["dry_run"] is True
        assert len(result["planned_actions"]) == 4
        assert result["planned_actions"][0]["op"] == "create_scope"

    def test_app_scaffold_execution(self, mock_servicenow_client):
        """Test the execution of the app_scaffold function"""
        # Mock the return value of the first create_record call (for sys_scope)
        mock_servicenow_client.create_record.side_effect = [
            {"success": True, "result": {"sys_id": "scope123"}}, # For sys_scope
            {"success": True, "result": {"sys_id": "menu123"}}, # For sys_app_application
            {"success": True, "result": {"sys_id": "module123"}}, # For sys_app_module
            {"success": True, "result": {"sys_id": "role123"}}, # For sys_user_role
        ]

        result = build_pack.app_scaffold(
            mock_servicenow_client,
            app_name="Test App",
            scope_name="x_mcp_test_app",
            description="A test application",
            dry_run=False
        )

        assert result["success"] is True
        assert mock_servicenow_client.create_record.call_count == 4

        # Check the calls made to the mock client
        calls = mock_servicenow_client.create_record.call_args_list

        # Call 1: sys_scope
        assert calls[0] == call("sys_scope", {
            "name": "Test App",
            "scope": "x_mcp_test_app",
            "short_description": "A test application",
            "source": "servicenow_mcp",
            "trackable": "true"
        })

        # Call 2: sys_app_application
        assert calls[1] == call("sys_app_application", {
            "title": "Test App",
            "hint": "A test application",
            "sys_scope": "scope123"
        })

        # Call 3: sys_app_module
        assert calls[2] == call("sys_app_module", {
            "title": "Test App Items",
            "application": "menu123",
            "sys_scope": "scope123"
        })

        # Call 4: sys_user_role
        assert calls[3] == call("sys_user_role", {
            "name": "x_mcp_test_app.user",
            "description": "Default user role for Test App",
            "sys_scope": "scope123"
        })
