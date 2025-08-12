"""
ServiceNow MCP Adapter - Main entry point for the MCP server

This module provides the core MCP server setup and client management.
Tool registration is handled by the ToolRegistry class to maintain separation of concerns.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP

from .config import Config
from .servicenow_client import ServiceNowClient
from .tool_registry import ToolRegistry
from .utils.plan import execute_plan as _execute_plan
from .utils.workspace import list_workspaces as _ws_list, get_workspace as _ws_get, set_workspace as _ws_set

# Import all the packs that are used in tool definitions
from .packs import (
    build_pack, operate_pack, query_pack, scripts_pack, itam_pack, irm_pack,
    data_pack, event_pack, discovery_pack, integrations_pack, planner_pack,
    update_set_pack, atf_pack, ux_pack, flow_pack, dev_pack, scripted_rest_pack,
    governance_pack, cmdb_pack, pipeline_pack, troubleshoot_pack, docs_pack, impersonation_pack,
    change_pack, problem_pack, request_pack, user_pack, attachment_pack, knowledge_pack, 
    approvals_pack, notify_pack, table_pack, props_pack, senior_dev_pack, story_driven_pack
)

# Initialize MCP server
mcp = FastMCP("servicenow-mcp")

# Client cache for connection reuse
_clients: Dict[str, ServiceNowClient] = {}

from .client_manager import client_manager

def _get_client(env: Optional[str]) -> ServiceNowClient:
    """Get ServiceNow client for environment - delegates to client manager"""
    return client_manager.get_client(env)

# Initialize tool registry and register all tools
tool_registry = ToolRegistry(mcp, _get_client)
tool_registry.register_all_tools()

# ---- Core Management Functions ----
@mcp.tool()
def client_health_check(env: Optional[str] = None) -> dict:
    """Check health status of ServiceNow client connections"""
    return client_manager.health_check(env)

@mcp.tool()
def clear_client_cache(env: str) -> dict:
    """Clear cached client for environment (useful for credential rotation)"""
    cleared = client_manager.clear_client(env)
    return {"cleared": cleared, "environment": env}

@mcp.tool()
def get_active_environments() -> dict:
    """Get list of environments with active client connections"""
    return {"environments": client_manager.get_active_environments()}

# ---- Basic Incident Helpers ----
@mcp.tool()
def create_incident(short_description: str, description: Optional[str] = None, additional_fields: Optional[Dict[str, Any]] = None, env: str = "dev") -> dict:
    c = _get_client(env)
    payload: Dict[str, Any] = {"short_description": short_description}
    if description: payload["description"] = description
    if additional_fields: payload.update(additional_fields)
    return c.create_record("incident", payload)

@mcp.tool()
def get_incident(sys_id: str, env: str = "dev") -> dict:
    c = _get_client(env)
    return c.get_record("incident", sys_id)

# ---- build & catalog ----
@mcp.tool()
def app_scaffold(spec: Dict[str, Any], scope: Optional[str] = "x_cloudorch_aiops", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env)
    return build_pack.app_scaffold(c, spec, scope=scope, dry_run=dry_run)

@mcp.tool()
def create_table(table_label: str, table_name: str, extends: Optional[str] = None, scope: Optional[str] = "x_cloudorch_aiops", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env)
    return build_pack.create_table(c, table_label, table_name, extends=extends, scope=scope, dry_run=dry_run)

@mcp.tool()
def add_field(table_name: str, name: str, ftype: str, label: str, mandatory: bool = False, default: Optional[str] = None, choices: Optional[List[str]] = None, scope: Optional[str] = "x_cloudorch_aiops", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env)
    return build_pack.add_field(c, table_name, name, ftype, label, mandatory, default, choices, scope, dry_run)

# ---- query ----
@mcp.tool()
def query_table(table: str, query: str = "", fields: Optional[List[str]] = None, limit: int = 100, display: bool = False, env: str = "dev") -> dict:
    c = _get_client(env)
    return query_pack.query_table(c, table, query, fields, limit, display)

@mcp.tool()
def stats(table: str, query: str = "", group_by: Optional[List[str]] = None, count: bool = True, sum: Optional[List[str]] = None, avg: Optional[List[str]] = None, minv: Optional[List[str]] = None, maxv: Optional[List[str]] = None, env: str = "dev") -> dict:
    c = _get_client(env)
    return query_pack.stats(c, table, query, group_by, count, sum, avg, minv, maxv)

@mcp.tool()
def ci_graph(root_sys_id: str, direction: str = "both", depth: int = 2, limit: int = 200, env: str = "dev") -> dict:
    c = _get_client(env)
    return query_pack.ci_graph(c, root_sys_id, direction, depth, limit)

# ---- orchestrator ----
@mcp.tool()
def execute_plan(plan: list, confirm: bool = False, continue_on_error: bool = False, env: str = "dev") -> dict:
    c = _get_client(env)
    return _execute_plan(c, plan, confirm, continue_on_error)

# ---- workspaces ----
@mcp.tool()
def ws_list() -> dict:
    return {"workspaces": _ws_list()}

@mcp.tool()
def ws_get(name: str = "default") -> dict:
    return {"name": name, "config": _ws_get(name)}

@mcp.tool()
def ws_set(name: str = "default", env: str = "", scope: str = "", confirm: bool = False) -> dict:
    updates = {}
    if env: updates["env"] = env
    if scope: updates["scope"] = scope
    updates["confirm"] = bool(confirm)
    return {"name": name, "config": _ws_set(name, updates)}

# Entry point for the MCP server
if __name__ == "__main__":
    mcp.run()