"""
ServiceNow MCP Adapter - Main entry point for the MCP server
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP

from .config import Config
from .servicenow_client import ServiceNowClient
from .packs import build_pack, operate_pack, query_pack
from .packs import scripts_pack, itam_pack, irm_pack
from .packs import data_pack, event_pack, discovery_pack, integrations_pack, planner_pack
from .packs import update_set_pack, atf_pack, ux_pack, flow_pack, dev_pack, scripted_rest_pack
from .packs import governance_pack, cmdb_pack, pipeline_pack, troubleshoot_pack, docs_pack, impersonation_pack
from .packs import change_pack, problem_pack, request_pack, user_pack, attachment_pack, knowledge_pack, approvals_pack, notify_pack, table_pack, props_pack
from .packs import senior_dev_pack, story_driven_pack
from .utils.plan import execute_plan as _execute_plan
from .utils.guard import is_allowed as _guard
from .utils.workspace import list_workspaces as _ws_list, get_workspace as _ws_get, set_workspace as _ws_set

mcp = FastMCP("servicenow-mcp")
_clients: Dict[str, ServiceNowClient] = {}

def _get_client(env: Optional[str]) -> ServiceNowClient:
    key = (env or "dev").lower()
    if key not in _clients:
        cfg = Config.for_env(key)
        _clients[key] = ServiceNowClient(cfg.instance_url, cfg.username, cfg.password)
    return _clients[key]

def _guard_table(table: str, op: str = "write", override: bool = False):
    ok, why = _guard(table, op, override)
    if not ok:
        return {"error": "guard_block", "message": why, "table": table}
    return None

# ---- basic incident helpers ----
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

# ---- scripts/dev ----
@mcp.tool()
def create_script_include(name: str, script: str, api_name: str = "", active: bool = True, scope: str = "x_cloudorch_aiops", table: str = "sys_script_include", dry_run: bool = False, env: str = "dev") -> dict:
    g = _guard_table(table, "write", override=dry_run)
    if g: return g
    c = _get_client(env)
    return dev_pack.create_script_include(c, name, script, api_name or None, active, table, scope, dry_run)

@mcp.tool()
def create_business_rule(table_name: str, name: str, when: str, actions: dict, condition: str = "", script: str = "", active: bool = True, table: str = "sys_script", dry_run: bool = False, env: str = "dev") -> dict:
    g = _guard_table(table, "write", override=dry_run)
    if g: return g
    c = _get_client(env)
    return dev_pack.create_business_rule(c, table_name, name, when, actions, condition, script, active, table, dry_run)

# ---- operate/troubleshoot ----
@mcp.tool()
def perf_top_transactions(since_minutes: int = 60, limit: int = 20, env: str = "dev") -> dict:
    c = _get_client(env)
    return operate_pack.perf_top_transactions(c, since_minutes, limit)

@mcp.tool()
def jobs_running(limit: int = 50, env: str = "dev") -> dict:
    c = _get_client(env)
    return operate_pack.jobs_running(c, limit)

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

# ---- Senior Developer Capabilities ----
@mcp.tool()
def analyze_user_story(story: str, context: Optional[Dict[str, Any]] = None, env: str = "dev") -> dict:
    """Analyze a user story and break it down into actionable development tasks"""
    c = _get_client(env)
    return senior_dev_pack.analyze_story(c, story, context)

@mcp.tool()
def troubleshoot_cmdb_duplicates(ci_class: str = "cmdb_ci", analysis_fields: Optional[List[str]] = None, limit: int = 100, env: str = "dev") -> dict:
    """Advanced CMDB duplicate analysis and troubleshooting"""
    c = _get_client(env)
    return senior_dev_pack.troubleshoot_cmdb_duplicates(c, ci_class, analysis_fields, limit)

# ---- Story-Driven Development ----
@mcp.tool()
def parse_user_story(story: str) -> dict:
    """Parse user story using standard format: As a [user], I want [goal] so that [benefit]"""
    return story_driven_pack.parse_user_story(story)

@mcp.tool()
def story_to_implementation(story: str, env: str = "dev") -> dict:
    """Complete story-to-implementation pipeline: parse story, analyze requirements, generate executable plan"""
    c = _get_client(env)
    
    # Step 1: Parse the story
    parsed_story = story_driven_pack.parse_user_story(story)
    
    # Step 2: Validate completeness
    validation = story_driven_pack.validate_story_completeness(parsed_story)
    
    if not validation["is_complete"]:
        return {
            "status": "incomplete_story",
            "validation": validation,
            "recommendations": validation["recommendations"]
        }
    
    # Step 3: Extract technical requirements
    requirements = story_driven_pack.extract_technical_requirements(c, parsed_story["components"])
    
    # Step 4: Generate implementation tasks
    tasks = story_driven_pack.generate_implementation_tasks(c, requirements, parsed_story)
    
    # Step 5: Create executable plan
    executable_plan = story_driven_pack.create_executable_plan(c, tasks, parsed_story)
    
    return {
        "status": "success",
        "parsed_story": parsed_story,
        "validation": validation,
        "requirements": requirements,
        "executable_plan": executable_plan
    }

if __name__ == "__main__":
    mcp.run()