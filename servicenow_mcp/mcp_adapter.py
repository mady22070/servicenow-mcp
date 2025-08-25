"""
ServiceNow MCP Adapter - Main entry point for the MCP server
"""

from __future__ import annotations
from typing import Optional, Dict
from mcp.server.fastmcp import FastMCP

from .config import Config
from .servicenow_client import ServiceNowClient
from .tool_registry import ToolRegistry

# Initialize the MCP server
mcp = FastMCP("servicenow-mcp")

# In-memory cache for ServiceNowClient instances
_clients: Dict[str, ServiceNowClient] = {}

def _get_client(env: Optional[str]) -> ServiceNowClient:
    """
    Get a ServiceNowClient for the specified environment.
    Creates a new client if one doesn't exist for the environment.
    """
    key = (env or "dev").lower()
    if key not in _clients:
        cfg = Config.for_env(key)
        _clients[key] = ServiceNowClient(cfg.instance_url, cfg.username, cfg.password)
    return _clients[key]

if __name__ == "__main__":
    # Initialize the tool registry
    registry = ToolRegistry(mcp, _get_client)
    
    # Register all tools defined in the configuration
    registry.register_all_tools()
    
    # Start the MCP server
    mcp.run()