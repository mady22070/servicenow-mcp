"""
ServiceNow MCP Adapter - Main entry point for the MCP server

This module provides the core MCP server setup and client management.
All tool registration is handled by the ToolRegistry class to maintain separation of concerns.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP

from .config import Config
from .servicenow_client import ServiceNowClient
from .tool_registry import ToolRegistry
from .utils.plan import execute_plan as _execute_plan
from .utils.workspace import list_workspaces as _ws_list, get_workspace as _ws_get, set_workspace as _ws_set

# Lazy loading system for packs
from typing import TYPE_CHECKING
import importlib
from functools import lru_cache

# Type hints for development
if TYPE_CHECKING:
    from .packs import (
        build_pack, operate_pack, query_pack, scripts_pack, itam_pack, irm_pack,
        data_pack, event_pack, discovery_pack, integrations_pack, planner_pack,
        update_set_pack, atf_pack, ux_pack, flow_pack, dev_pack, scripted_rest_pack,
        governance_pack, cmdb_pack, pipeline_pack, troubleshoot_pack, docs_pack, impersonation_pack,
        change_pack, problem_pack, request_pack, user_pack, attachment_pack, knowledge_pack, 
        approvals_pack, notify_pack, table_pack, props_pack, senior_dev_pack, story_driven_pack
    )

@lru_cache(maxsize=None)
def _get_pack(pack_name: str):
    """Lazy load pack modules on demand with caching"""
    try:
        return importlib.import_module(f".packs.{pack_name}", package=__package__)
    except ImportError as e:
        raise ImportError(f"Failed to import pack '{pack_name}': {e}")

# Pack accessor functions for better organization
def get_build_pack(): return _get_pack("build_pack")
def get_query_pack(): return _get_pack("query_pack")
def get_senior_dev_pack(): return _get_pack("senior_dev_pack")
def get_story_driven_pack(): return _get_pack("story_driven_pack")
# Add other pack accessors as needed

# Initialize MCP server
mcp = FastMCP("servicenow-mcp")

# Client cache for connection reuse
_clients: Dict[str, ServiceNowClient] = {}

from .client_manager import client_manager
from .utils.guard import is_allowed as _guard

def _get_client(env: Optional[str]) -> ServiceNowClient:
    """Get ServiceNow client for environment - delegates to client manager"""
    return client_manager.get_client(env)

def _guard_table(table: str, op: str = "write", override: bool = False) -> Optional[Dict[str, Any]]:
    """Centralized table guard check with consistent error format"""
    ok, why = _guard(table, op, override)
    if not ok:
        return {
            "error": "guard_block", 
            "message": why, 
            "table": table,
            "_meta": {"guard_check": True, "operation": op}
        }
    return None

# Initialize tool registry with lazy loading support
tool_registry = ToolRegistry(mcp, _get_client, _get_pack)
tool_registry.register_all_tools()

# All tools are now registered through the ToolRegistry
# This provides better organization, lazy loading, and consistent error handling

# Entry point for the MCP server
if __name__ == "__main__":
    mcp.run()