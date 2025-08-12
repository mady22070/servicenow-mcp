
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
    c = _get_client(env); return build_pack.app_scaffold(c, spec, scope=scope, dry_run=dry_run)
@mcp.tool()
def create_table(table_label: str, table_name: str, extends: Optional[str] = None, scope: Optional[str] = "x_cloudorch_aiops", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return build_pack.create_table(c, table_label, table_name, extends=extends, scope=scope, dry_run=dry_run)
@mcp.tool()
def add_field(table_name: str, name: str, ftype: str, label: str, mandatory: bool = False, default: Optional[str] = None, choices: Optional[List[str]] = None, scope: Optional[str] = "x_cloudorch_aiops", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return build_pack.add_field(c, table_name, name, ftype, label, mandatory, default, choices, scope, dry_run)
@mcp.tool()
def add_choice(table_name: str, element: str, choices: List[str], dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return build_pack.add_choice(c, table_name, element, choices, dry_run)
@mcp.tool()
def create_catalog_item(name: str, category: str, description: str = "", active: bool = True, scope: Optional[str] = "x_cloudorch_aiops", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return build_pack.create_catalog_item(c, name, category, description, active, scope, dry_run)
@mcp.tool()
def add_catalog_variables(item_sys_id: str, variables_spec: List[Dict[str, Any]], dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return build_pack.add_catalog_variables(c, item_sys_id, variables_spec, dry_run)
@mcp.tool()
def add_catalog_client_script(item_sys_id: str, ui_type: str, script: str, dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return build_pack.add_catalog_client_script(c, item_sys_id, ui_type, script, dry_run)

# ---- scripts/dev ----
@mcp.tool()
def add_client_script(table: str, name: str, ui_type: str, script: str, scope: str = "x_cloudorch_aiops", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return scripts_pack.add_client_script(c, table, name, ui_type, script, scope, dry_run)
@mcp.tool()
def lint_client_script(script: str, ui_type: str) -> dict:
    return scripts_pack.lint_client_script(script, ui_type)
@mcp.tool()
def create_script_include(name: str, script: str, api_name: str = "", active: bool = True, scope: str = "x_cloudorch_aiops", table: str = "sys_script_include", dry_run: bool = False, env: str = "dev") -> dict:
    g = _guard_table(table, "write", override=dry_run); 
    if g: return g
    c = _get_client(env); return dev_pack.create_script_include(c, name, script, api_name or None, active, table, scope, dry_run)
@mcp.tool()
def create_business_rule(table_name: str, name: str, when: str, actions: dict, condition: str = "", script: str = "", active: bool = True, table: str = "sys_script", dry_run: bool = False, env: str = "dev") -> dict:
    g = _guard_table(table, "write", override=dry_run); 
    if g: return g
    c = _get_client(env); return dev_pack.create_business_rule(c, table_name, name, when, actions, condition, script, active, table, dry_run)
@mcp.tool()
def create_ui_policy(table_name: str, short_description: str, active: bool = True, condition: str = "", actions: list = None, policy_table: str = "ui_policy", action_table: str = "ui_policy_action", dry_run: bool = False, env: str = "dev") -> dict:
    for t in (policy_table, action_table):
        g = _guard_table(t, "write", override=dry_run)
        if g: return g
    c = _get_client(env); return dev_pack.create_ui_policy(c, table_name, short_description, active, condition, actions, policy_table, action_table, dry_run)

# ---- operate/troubleshoot ----
@mcp.tool()
def perf_top_transactions(since_minutes: int = 60, limit: int = 20, env: str = "dev") -> dict:
    c = _get_client(env); return operate_pack.perf_top_transactions(c, since_minutes, limit)
@mcp.tool()
def jobs_running(limit: int = 50, env: str = "dev") -> dict:
    c = _get_client(env); return operate_pack.jobs_running(c, limit)
@mcp.tool()
def ecc_queue_backlog(states: Optional[List[str]] = None, since_minutes: int = 120, limit: int = 100, env: str = "dev") -> dict:
    c = _get_client(env); return operate_pack.ecc_queue_backlog(c, states, since_minutes, limit)
@mcp.tool()
def events_backlog(limit: int = 100, env: str = "dev") -> dict:
    c = _get_client(env); return operate_pack.events_backlog(c, limit)
@mcp.tool()
def triggers_scheduled(limit: int = 100, env: str = "dev") -> dict:
    c = _get_client(env); return operate_pack.triggers_scheduled(c, limit)
@mcp.tool()
def logs_search(text: str, limit: int = 100, env: str = "dev") -> dict:
    c = _get_client(env); return operate_pack.logs_search(c, text, limit)
@mcp.tool()
def user_context(user_sys_id: str, env: str = "dev") -> dict:
    c = _get_client(env); return troubleshoot_pack.user_context(c, user_sys_id)
@mcp.tool()
def acl_summary(table: str, field: str = "", env: str = "dev") -> dict:
    c = _get_client(env); return troubleshoot_pack.acl_summary(c, table, field)
@mcp.tool()
def form_visibility(table: str, field: str = "", env: str = "dev") -> dict:
    c = _get_client(env); return troubleshoot_pack.form_visibility(c, table, field)
@mcp.tool()
def record_access_probe(table: str, sys_id: str, env: str = "dev") -> dict:
    c = _get_client(env); return troubleshoot_pack.record_access_probe(c, table, sys_id)

# ---- query ----
@mcp.tool()
def query_table(table: str, query: str = "", fields: Optional[List[str]] = None, limit: int = 100, display: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return query_pack.query_table(c, table, query, fields, limit, display)
@mcp.tool()
def stats(table: str, query: str = "", group_by: Optional[List[str]] = None, count: bool = True, sum: Optional[List[str]] = None, avg: Optional[List[str]] = None, minv: Optional[List[str]] = None, maxv: Optional[List[str]] = None, env: str = "dev") -> dict:
    c = _get_client(env); return query_pack.stats(c, table, query, group_by, count, sum, avg, minv, maxv)
@mcp.tool()
def ci_graph(root_sys_id: str, direction: str = "both", depth: int = 2, limit: int = 200, env: str = "dev") -> dict:
    c = _get_client(env); return query_pack.ci_graph(c, root_sys_id, direction, depth, limit)

# ---- data/event/discovery/integrations ----
@mcp.tool()
def create_data_source_jdbc(name: str, connection_url: str, username: str, password: str, target_table: str = "", jdbc_driver: str = "", table: str = "sys_data_source", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return data_pack.create_data_source_jdbc(c, name, connection_url, username, password, target_table or None, jdbc_driver or None, table, dry_run)
@mcp.tool()
def create_event_rule(name: str, filter_query: str, severity: str = "", table: str = "em_event_rule", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return event_pack.create_event_rule(c, name, filter_query, severity or None, table, dry_run)
@mcp.tool()
def create_alert_correlation_rule(name: str, group_by: list, match_query: str = "", table: str = "em_correlation_rule", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return event_pack.create_alert_correlation_rule(c, name, group_by, match_query or None, table, dry_run)
@mcp.tool()
def discovery_quick(name: str, ips: list, mid_server: str = "", schedule_table: str = "discovery_schedule", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return discovery_pack.quick_discovery(c, name, ips, mid_server or None, schedule_table, dry_run)
@mcp.tool()
def discovery_status(limit: int = 50, env: str = "dev") -> dict:
    c = _get_client(env); return discovery_pack.discovery_status(c, limit)
@mcp.tool()
def create_rest_message(name: str, endpoint: str, authentication_type: str = "none", table: str = "sys_rest_message", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return integrations_pack.create_rest_message(c, name, endpoint, authentication_type, table, dry_run)
@mcp.tool()
def add_rest_method(rest_message: str, function_name: str, http_method: str, relative_path: str = "", table: str = "sys_rest_message_fn", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return integrations_pack.add_rest_method(c, rest_message, function_name, http_method, relative_path, table, dry_run)

# ---- UI / Flow / ATF / Update set ----
@mcp.tool()
def ux_create_page(name: str, title: str, table_page: str = "sys_ux_page", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return ux_pack.create_ux_page(c, name, title, table_page, dry_run)
@mcp.tool()
def ux_add_component(page_sys_id: str, component_name: str, props: dict, table_component: str = "sys_ux_component", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return ux_pack.add_ux_component(c, page_sys_id, component_name, props, table_component, dry_run)
@mcp.tool()
def ux_create_experience(name: str, title: str, table_exp: str = "sys_ux_experience", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return ux_pack.create_ux_experience(c, name, title, table_exp, dry_run)
@mcp.tool()
def ux_add_route(experience_sys_id: str, path: str, page_sys_id: str, table_route: str = "sys_ux_route", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return ux_pack.add_ux_route(c, experience_sys_id, path, page_sys_id, table_route, dry_run)
@mcp.tool()
def flow_create(name: str, description: str = "", table: str = "sys_hub_flow", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return flow_pack.create_flow(c, name, description, table, dry_run)
@mcp.tool()
def flow_add_trigger_record_change(flow_sys_id: str, table_name: str, operation: str = "insert", table: str = "sys_hub_trigger", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return flow_pack.add_flow_trigger_record_change(c, flow_sys_id, table_name, operation, table, dry_run)
@mcp.tool()
def flow_activate(flow_sys_id: str, active: bool = True, table: str = "sys_hub_flow", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return flow_pack.activate_flow(c, flow_sys_id, active, table, dry_run)
@mcp.tool()
def atf_create_suite(name: str, description: str = "", env: str = "dev") -> dict:
    c = _get_client(env); return atf_pack.create_test_suite(c, name, description)
@mcp.tool()
def atf_create_ui_form_test(suite_sys_id: str, table_name: str, test_name: str, env: str = "dev") -> dict:
    c = _get_client(env); return atf_pack.create_ui_form_test(c, suite_sys_id, table_name, test_name)
@mcp.tool()
def create_update_set(name: str, description: str = "", application: str = "", state: str = "in progress", table: str = "sys_update_set", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return update_set_pack.create_update_set(c, name, description, application or None, state, table, dry_run)
@mcp.tool()
def close_update_set(sys_id: str, table: str = "sys_update_set", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return update_set_pack.close_update_set(c, sys_id, table, dry_run)

# ---- governance / cmdb / pipeline ----
@mcp.tool()
def capability_check(required_plugins: list = None, required_roles: list = None, probe_tables: list = None, env: str = "dev") -> dict:
    c = _get_client(env); return governance_pack.capability_check(c, required_plugins, required_roles, probe_tables)
@mcp.tool()
def export_update_set_meta(update_set_sys_id: str, env: str = "dev") -> dict:
    c = _get_client(env); return governance_pack.export_update_set_meta(c, update_set_sys_id)
@mcp.tool()
def cmdb_health_snapshot(classes: list = None, limit: int = 50, env: str = "dev") -> dict:
    c = _get_client(env); return cmdb_pack.cmdb_health_snapshot(c, classes, limit)
@mcp.tool()
def servicemap_seed(app_name: str, entry_point: str, table: str = "svc_map_seed", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return cmdb_pack.servicemap_seed(c, app_name, entry_point, table, dry_run)
@mcp.tool()
def impact_rule_add(service_sys_id: str, related_ci: str, relation_type: str = "Depends on::Used by", table: str = "svc_impact_rule", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return cmdb_pack.impact_rule_add(c, service_sys_id, related_ci, relation_type, table, dry_run)
@mcp.tool()
def deploy_plan(plan: list, update_set_sys_id: str = "", confirm: bool = False, continue_on_error: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return pipeline_pack.deploy_plan(c, plan, update_set_sys_id, confirm, continue_on_error)

# ---- impersonation ACL tester ----
@mcp.tool()
def deploy_impersonation_acl_api(api_name: str = "mcp_acl_test", base_path: str = "x_mcp/acltest", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return impersonation_pack.deploy_impersonation_acl_api(c, api_name, base_path, dry_run)
@mcp.tool()
def impersonation_acl_check(user_sys_id: str, table: str, sys_id: str = "", field: str = "", base_path: str = "x_mcp/acltest", env: str = "dev") -> dict:
    c = _get_client(env); return impersonation_pack.impersonation_acl_check(c, user_sys_id, table, sys_id, field, base_path)

# ---- change/problem/request ----
@mcp.tool()
def create_change_request(fields: dict, table: str = "change_request", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return change_pack.create_change_request(c, fields, table, dry_run)
@mcp.tool()
def update_change_request(sys_id: str, fields: dict, table: str = "change_request", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return change_pack.update_change_request(c, sys_id, fields, table, dry_run)
@mcp.tool()
def get_change_request(sys_id: str, table: str = "change_request", env: str = "dev") -> dict:
    c = _get_client(env); return change_pack.get_change_request(c, sys_id, table)
@mcp.tool()
def approve_change_request(sys_id: str, approver_sys_id: str = "", table: str = "change_request", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return change_pack.approve_change_request(c, sys_id, approver_sys_id or None, table, dry_run)
@mcp.tool()
def schedule_change_request(sys_id: str, start_date: str, end_date: str, table: str = "change_request", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return change_pack.schedule_change_request(c, sys_id, start_date, end_date, table, dry_run)
@mcp.tool()
def create_problem(fields: dict, table: str = "problem", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return problem_pack.create_problem(c, fields, table, dry_run)
@mcp.tool()
def update_problem(sys_id: str, fields: dict, table: str = "problem", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return problem_pack.update_problem(c, sys_id, fields, table, dry_run)
@mcp.tool()
def link_incident_to_problem(incident_sys_id: str, problem_sys_id: str, incident_table: str = "incident", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return problem_pack.link_incident_to_problem(c, incident_sys_id, problem_sys_id, incident_table, dry_run)
@mcp.tool()
def create_known_error(problem_sys_id: str, workaround: str, table: str = "known_error", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return problem_pack.create_known_error(c, problem_sys_id, workaround, table, dry_run)

# ---- requests ----
@mcp.tool()
def create_request(fields: dict, table: str = "sc_request", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return request_pack.create_request(c, fields, table, dry_run)
@mcp.tool()
def create_request_item(request_sys_id: str, catalog_item_sys_id: str, fields: dict = None, table: str = "sc_req_item", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return request_pack.create_request_item(c, request_sys_id, catalog_item_sys_id, fields, table, dry_run)
@mcp.tool()
def approve_request(sys_id: str, table: str = "sc_request", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return request_pack.approve_request(c, sys_id, table, dry_run)
@mcp.tool()
def fulfill_request_item(sys_id: str, table: str = "sc_req_item", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return request_pack.fulfill_request_item(c, sys_id, table, dry_run)

# ---- Users / Groups ----
@mcp.tool()
def create_user(fields: dict, table: str = "sys_user", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return user_pack.create_user(c, fields, table, dry_run)
@mcp.tool()
def update_user(sys_id: str, fields: dict, table: str = "sys_user", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return user_pack.update_user(c, sys_id, fields, table, dry_run)
@mcp.tool()
def get_user(sys_id: str, table: str = "sys_user", env: str = "dev") -> dict:
    c = _get_client(env); return user_pack.get_user(c, sys_id, table)
@mcp.tool()
def get_user_by_email(email: str, table: str = "sys_user", env: str = "dev") -> dict:
    c = _get_client(env); return user_pack.get_user_by_email(c, email, table)
@mcp.tool()
def create_group(fields: dict, table: str = "sys_user_group", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return user_pack.create_group(c, fields, table, dry_run)
@mcp.tool()
def add_user_to_group(user_sys_id: str, group_sys_id: str, table: str = "sys_user_grmember", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return user_pack.add_user_to_group(c, user_sys_id, group_sys_id, table, dry_run)
@mcp.tool()
def get_group_members(group_sys_id: str, table: str = "sys_user_grmember", env: str = "dev") -> dict:
    c = _get_client(env); return user_pack.get_group_members(c, group_sys_id, table)

# ---- Attachments ----
@mcp.tool()
def upload_attachment(table: str, sys_id: str, file_path: str, file_name: str = "", env: str = "dev") -> dict:
    c = _get_client(env); return attachment_pack.upload_attachment(c, table, sys_id, file_path, file_name)
@mcp.tool()
def list_attachments(table: str, sys_id: str, limit: int = 50, env: str = "dev") -> dict:
    c = _get_client(env); return attachment_pack.list_attachments(c, table, sys_id, limit)
@mcp.tool()
def download_attachment(attachment_sys_id: str, out_path: str, env: str = "dev") -> dict:
    c = _get_client(env); return attachment_pack.download_attachment(c, attachment_sys_id, out_path)
@mcp.tool()
def delete_attachment(attachment_sys_id: str, env: str = "dev") -> dict:
    c = _get_client(env); return attachment_pack.delete_attachment(c, attachment_sys_id)

# ---- Knowledge ----
@mcp.tool()
def create_knowledge_article(fields: dict, table: str = "kb_knowledge", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return knowledge_pack.create_knowledge_article(c, fields, table, dry_run)
@mcp.tool()
def publish_knowledge_article(sys_id: str, table: str = "kb_knowledge", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return knowledge_pack.publish_knowledge_article(c, sys_id, table, dry_run)
@mcp.tool()
def search_knowledge(query: str, limit: int = 20, table: str = "kb_knowledge", env: str = "dev") -> dict:
    c = _get_client(env); return knowledge_pack.search_knowledge(c, query, limit, table)
@mcp.tool()
def get_article_feedback(article_sys_id: str, table: str = "kb_feedback", limit: int = 50, env: str = "dev") -> dict:
    c = _get_client(env); return knowledge_pack.get_article_feedback(c, article_sys_id, table, limit)

# ---- Approvals & Notifications ----
@mcp.tool()
def get_pending_approvals(user_sys_id: str, table: str = "sysapproval_approver", limit: int = 100, env: str = "dev") -> dict:
    c = _get_client(env); return approvals_pack.get_pending_approvals(c, user_sys_id, table, limit)
@mcp.tool()
def approve_sysapproval(approval_sys_id: str, table: str = "sysapproval_approver", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return approvals_pack.approve_sysapproval(c, approval_sys_id, table, dry_run)
@mcp.tool()
def approve_record(table: str, sys_id: str, comments: str = "", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return approvals_pack.approve_record_generic(c, table, sys_id, comments, dry_run)
@mcp.tool()
def reject_record(table: str, sys_id: str, comments: str = "", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return approvals_pack.reject_record_generic(c, table, sys_id, comments, dry_run)
@mcp.tool()
def create_notification(fields: dict, table: str = "sysevent_email_action", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return notify_pack.create_notification(c, fields, table, dry_run)
@mcp.tool()
def get_user_notifications(user_sys_id: str, table: str = "sys_email", limit: int = 100, env: str = "dev") -> dict:
    c = _get_client(env); return notify_pack.get_user_notifications(c, user_sys_id, table, limit)

# ---- Table utilities ----
@mcp.tool()
def update_record(table: str, sys_id: str, fields: dict, dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return table_pack.update_record(c, table, sys_id, fields, dry_run)
@mcp.tool()
def delete_record(table: str, sys_id: str, dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return table_pack.delete_record(c, table, sys_id, dry_run)
@mcp.tool()
def get_record(table: str, sys_id: str, fields: list = None, env: str = "dev") -> dict:
    c = _get_client(env); return table_pack.get_record(c, table, sys_id, fields)
@mcp.tool()
def batch_insert_records(table: str, records: list, dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return table_pack.batch_insert_records(c, table, records, dry_run)
@mcp.tool()
def batch_update_records(table: str, updates: list, id_field: str = "sys_id", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return table_pack.batch_update_records(c, table, updates, id_field, dry_run)

# ---- Properties ----
@mcp.tool()
def property_get(name: str, table: str = "sys_properties", env: str = "dev") -> dict:
    c = _get_client(env); return props_pack.property_get(c, name, table)
@mcp.tool()
def property_set(name: str, value: str, table: str = "sys_properties", dry_run: bool = False, env: str = "dev") -> dict:
    c = _get_client(env); return props_pack.property_set(c, name, value, table, dry_run)

# ---- workspaces ----
@mcp.tool()
def ws_list() -> dict:
    return {"workspaces": _ws_list()}
@mcp.tool()
def ws_get(name: str = "default") -> dict:
    return {"name": name, "config": _ws_get(name)}
@mcp.tool()
def ws_set(name: str = "default", env: str = "", scope: str = "", confirm: bool = False) -> dict:
    updates = {}; 
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

@mcp.tool()
def investigate_data_quality(table: str, quality_checks: Optional[List[str]] = None, sample_size: int = 1000, env: str = "dev") -> dict:
    """Comprehensive data quality investigation"""
    c = _get_client(env)
    return senior_dev_pack.investigate_data_quality(c, table, quality_checks, sample_size)

@mcp.tool()
def generate_development_plan(story_analysis: Dict[str, Any], environment: str = "dev", env: str = "dev") -> dict:
    """Generate a comprehensive development plan from story analysis"""
    c = _get_client(env)
    return senior_dev_pack.generate_development_plan(c, story_analysis, environment)

@mcp.tool()
def root_cause_analysis(issue_description: str, related_table: Optional[str] = None, time_range_hours: int = 24, env: str = "dev") -> dict:
    """Perform root cause analysis for ServiceNow issues"""
    c = _get_client(env)
    return senior_dev_pack.root_cause_analysis(c, issue_description, related_table, time_range_hours)

# ---- Story-Driven Development ----
@mcp.tool()
def parse_user_story(story: str) -> dict:
    """Parse user story using standard format: As a [user], I want [goal] so that [benefit]"""
    return story_driven_pack.parse_user_story(story)

@mcp.tool()
def extract_technical_requirements(story_components: Dict[str, Any], env: str = "dev") -> dict:
    """Extract technical requirements from story components"""
    c = _get_client(env)
    return story_driven_pack.extract_technical_requirements(c, story_components)

@mcp.tool()
def generate_implementation_tasks(requirements: Dict[str, Any], story_context: Dict[str, Any], env: str = "dev") -> dict:
    """Generate specific implementation tasks from requirements"""
    c = _get_client(env)
    return {"tasks": story_driven_pack.generate_implementation_tasks(c, requirements, story_context)}

@mcp.tool()
def create_executable_plan(tasks: List[Dict[str, Any]], story_context: Dict[str, Any], env: str = "dev") -> dict:
    """Create an executable plan with specific ServiceNow operations"""
    c = _get_client(env)
    return story_driven_pack.create_executable_plan(c, tasks, story_context)

@mcp.tool()
def validate_story_completeness(story_analysis: Dict[str, Any]) -> dict:
    """Validate that a user story has sufficient detail for implementation"""
    return story_driven_pack.validate_story_completeness(story_analysis)

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

# ---- orchestrator ----
@mcp.tool()
def execute_plan(plan: list, confirm: bool = False, continue_on_error: bool = False, env: str = "dev") -> dict:
    def resolver(pack: str, func: str):
        c = _get_client(env)
        mod = None
        if pack == "build": from servicenow_mcp.packs import build_pack as mod
        elif pack == "scripts": from servicenow_mcp.packs import scripts_pack as mod
        elif pack == "operate": from servicenow_mcp.packs import operate_pack as mod
        elif pack == "query": from servicenow_mcp.packs import query_pack as mod
        elif pack == "data": from servicenow_mcp.packs import data_pack as mod
        elif pack == "event": from servicenow_mcp.packs import event_pack as mod
        elif pack == "discovery": from servicenow_mcp.packs import discovery_pack as mod
        elif pack == "integrations": from servicenow_mcp.packs import integrations_pack as mod
        elif pack == "itam": from servicenow_mcp.packs import itam_pack as mod
        elif pack == "irm": from servicenow_mcp.packs import irm_pack as mod
        elif pack == "ux": from servicenow_mcp.packs import ux_pack as mod
        elif pack == "flow": from servicenow_mcp.packs import flow_pack as mod
        elif pack == "atf": from servicenow_mcp.packs import atf_pack as mod
        elif pack == "update_set": from servicenow_mcp.packs import update_set_pack as mod
        elif pack == "change": from servicenow_mcp.packs import change_pack as mod
        elif pack == "problem": from servicenow_mcp.packs import problem_pack as mod
        elif pack == "request": from servicenow_mcp.packs import request_pack as mod
        elif pack == "user": from servicenow_mcp.packs import user_pack as mod
        elif pack == "knowledge": from servicenow_mcp.packs import knowledge_pack as mod
        elif pack == "attachment": from servicenow_mcp.packs import attachment_pack as mod
        elif pack == "approvals": from servicenow_mcp.packs import approvals_pack as mod
        elif pack == "notify": from servicenow_mcp.packs import notify_pack as mod
        elif pack == "table": from servicenow_mcp.packs import table_pack as mod
        elif pack == "props": from servicenow_mcp.packs import props_pack as mod
        elif pack == "senior_dev": from servicenow_mcp.packs import senior_dev_pack as mod
        elif pack == "story_driven": from servicenow_mcp.packs import story_driven_pack as mod
        else: raise ValueError(f"Unknown pack: {pack}")
        fn = getattr(mod, func)
        def call_with_client(**kwargs):
            return fn(c, **kwargs)
        return call_with_client
    return _execute_plan(resolver, plan, confirm=confirm, continue_on_error=continue_on_error)

if __name__ == "__main__":
    mcp.run()
