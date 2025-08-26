"""Version information for ServiceNow MCP server"""

__version__ = "0.8.0-full"
__version_info__ = (0, 8, 0, "full")

# Feature flags
FEATURES = {
    "multi_environment": True,
    "senior_developer_capabilities": True,
    "story_driven_development": True,
    "advanced_cmdb_analysis": True,
    "plan_execution": True,
    "workspace_management": True,
    "async_operations": True,
    "comprehensive_logging": True,
    "error_handling": True,
    "input_validation": True,
    "mcp_resources": True,
    "health_checks": True
}

# Build information
BUILD_INFO = {
    "name": "servicenow-mcp",
    "description": "ServiceNow MCP Server with comprehensive automation capabilities",
    "author": "ServiceNow MCP Team",
    "license": "MIT",
    "python_requires": ">=3.8",
    "mcp_version": ">=0.1.0"
}
