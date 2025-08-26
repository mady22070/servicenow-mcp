"""
ServiceNow MCP Adapter - Main entry point for the MCP server
"""

from __future__ import annotations

# Standard library imports
import asyncio
import atexit
import signal
from datetime import datetime
from typing import Any, Dict, List, Optional

# Third-party imports
from mcp.server.fastmcp import FastMCP

# Local imports
from .async_client import AsyncServiceNowClient
from .client_factory import get_client_factory
from .config import Config
from .constants import DefaultValues, ServiceNowTables
from .error_handler import MCPResponse, handle_errors, validate_parameters
from .logging_config import LogContext, get_logger, init_default_logger
from .models import (
    AddFieldParams,
    CreateBusinessRuleParams,
    CreateIncidentParams,
    CreateScriptIncludeParams,
    CreateTableParams,
    ExecutePlanParams,
    HealthCheck,
    QueryTableParams,
    ServerCapabilities,
    ServerInfo,
    StatsParams,
    WorkspaceParams,
)
from .resources import get_resource_provider
from .servicenow_client import ServiceNowClient
from .version import __version__

# Pack imports - organized by category
from .packs import (
    # Core operations
    build_pack, operate_pack, query_pack, data_pack,
    # Development
    dev_pack, scripts_pack, scripted_rest_pack, atf_pack,
    # ITSM
    change_pack, problem_pack, request_pack, irm_pack,
    # Infrastructure
    cmdb_pack, discovery_pack, itam_pack, pipeline_pack,
    # Workflow & Automation
    flow_pack, ux_pack, governance_pack, troubleshoot_pack,
    # Integration & Communication
    integrations_pack, planner_pack, docs_pack, impersonation_pack,
    # Additional packs
    update_set_pack, user_pack, attachment_pack, knowledge_pack,
    approvals_pack, notify_pack, table_pack, props_pack, event_pack,
    # Senior developer capabilities
    senior_dev_pack, story_driven_pack,
)

# Utility imports
from .utils.guard import is_allowed as _guard
from .utils.plan import execute_plan as _execute_plan
from .utils.workspace import (
    get_workspace as _ws_get,
    list_workspaces as _ws_list,
    set_workspace as _ws_set,
)

# Constants
SERVER_NAME = "servicenow-mcp"
DEFAULT_ENVIRONMENT = DefaultValues.ENVIRONMENT
DEFAULT_SCOPE = DefaultValues.SCOPE
DEFAULT_LIMIT = DefaultValues.DEFAULT_QUERY_LIMIT
DEFAULT_DEPTH = DefaultValues.DEFAULT_CI_GRAPH_DEPTH

# Initialize logging
logger = init_default_logger()

# Initialize MCP server with metadata
mcp = FastMCP(SERVER_NAME)

# Server info
SERVER_INFO = ServerInfo(
    name=SERVER_NAME,
    version=__version__,
    description="ServiceNow MCP Server with comprehensive automation capabilities",
    capabilities=ServerCapabilities(
        tools={
            "query_table": {"description": "Query ServiceNow tables with filters"},
            "create_incident": {"description": "Create ServiceNow incidents"},
            "stats": {"description": "Get table statistics and aggregations"},
            "execute_plan": {"description": "Execute multi-step automation plans"},
            "analyze_user_story": {"description": "Analyze user stories for development"},
            "troubleshoot_cmdb_duplicates": {"description": "Advanced CMDB duplicate analysis"}
        },
        resources={
            "tables": {"description": "ServiceNow table definitions"},
            "fields": {"description": "Table field definitions"},
            "records": {"description": "Table record data"},
            "scripts": {"description": "ServiceNow scripts and business rules"}
        }
    ),
    environments=[DEFAULT_ENVIRONMENT, "test", "prod"],
    features=[
        "multi-environment",
        "senior-developer-capabilities", 
        "story-driven-development",
        "advanced-cmdb-analysis",
        "plan-execution",
        "workspace-management",
        "async-operations",
        "comprehensive-logging",
        "error-handling",
        "input-validation"
    ]
)



# Helper functions
def _get_client(env: Optional[str] = None) -> ServiceNowClient:
    """Get synchronous ServiceNow client for environment"""
    return get_client_factory().get_sync_client(env or DEFAULT_ENVIRONMENT)


async def _get_async_client(env: Optional[str] = None) -> AsyncServiceNowClient:
    """Get async ServiceNow client for environment"""
    return await get_client_factory().get_async_client(env or DEFAULT_ENVIRONMENT)


def _guard_table(table: str, op: str = "write", override: bool = False) -> Optional[Dict[str, Any]]:
    """
    Check table access permissions with enhanced error reporting
    
    Args:
        table: ServiceNow table name
        op: Operation type (read/write/delete)
        override: Whether to override guard restrictions
        
    Returns:
        None if allowed, error dict if blocked
    """
    ok, why = _guard(table, op, override)
    if not ok:
        logger.warning(f"Guard blocked {op} operation on table {table}: {why}")
        return {
            "error": "guard_block", 
            "message": why, 
            "table": table,
            "operation": op,
            "override_available": not override
        }
    return None


def _create_success_response(
    operation: str, 
    result: Any, 
    message: Optional[str] = None,
    **context
) -> Dict[str, Any]:
    """Create standardized success response with logging"""
    if message:
        logger.info(message, extra=context)
    return result if isinstance(result, dict) else {"result": result}

# Server metadata endpoints
@mcp.tool()
@handle_errors("server_info")
def get_server_info() -> dict:
    """Get MCP server information and capabilities"""
    return SERVER_INFO.dict()

@mcp.tool()
@handle_errors("health_check")
async def health_check(env: str = DEFAULT_ENVIRONMENT) -> dict:
    """Check ServiceNow instance connectivity and health"""
    try:
        client = await _get_async_client(env)
        async with client:
            health_result = await client.health_check()
        
        return HealthCheck(
            status="healthy" if health_result.get("status") == "healthy" else "unhealthy",
            timestamp=datetime.utcnow(),
            environment=env,
            connection_status={env: health_result.get("status") == "healthy"},
            response_time_ms=health_result.get("response_time_ms"),
            errors=[health_result.get("error")] if health_result.get("error") else []
        ).dict()
        
    except Exception as e:
        logger.error(f"Health check failed for {env}: {str(e)}")
        return HealthCheck(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            environment=env,
            connection_status={env: False},
            errors=[str(e)]
        ).dict()

# ---- Incident Management Tools ----
@mcp.tool()
@handle_errors("create_incident")
@validate_parameters(CreateIncidentParams)
def create_incident(
    short_description: str, 
    description: Optional[str] = None, 
    additional_fields: Optional[Dict[str, Any]] = None, 
    env: str = DEFAULT_ENVIRONMENT
) -> dict:
    """Create a new ServiceNow incident"""
    with LogContext(logger, operation="create_incident", env=env, table=ServiceNowTables.INCIDENT):
        client = _get_client(env)
        payload: Dict[str, Any] = {"short_description": short_description}
        
        if description: 
            payload["description"] = description
        if additional_fields: 
            payload.update(additional_fields)
        
        result = client.create_record(ServiceNowTables.INCIDENT, payload)
        return _create_success_response(
            "create_incident", 
            result,
            f"Created incident: {result.get('sys_id', 'unknown')}",
            env=env,
            table=ServiceNowTables.INCIDENT
        )


@mcp.tool()
@handle_errors("get_incident")
def get_incident(sys_id: str, env: str = DEFAULT_ENVIRONMENT) -> dict:
    """Get ServiceNow incident by sys_id"""
    with LogContext(logger, operation="get_incident", env=env, table=ServiceNowTables.INCIDENT, sys_id=sys_id):
        client = _get_client(env)
        result = client.get_record(ServiceNowTables.INCIDENT, sys_id)
        return _create_success_response(
            "get_incident",
            result,
            f"Retrieved incident: {sys_id}",
            env=env,
            sys_id=sys_id
        )

# ---- Query and Statistics Tools ----
@mcp.tool()
@handle_errors("query_table")
@validate_parameters(QueryTableParams)
def query_table(
    table: str, 
    query: str = "", 
    fields: Optional[List[str]] = None, 
    limit: int = DEFAULT_LIMIT, 
    display: bool = False, 
    env: str = DEFAULT_ENVIRONMENT
) -> dict:
    """Query ServiceNow table with filters and field selection"""
    with LogContext(logger, operation="query_table", env=env, table=table):
        client = _get_client(env)
        result = query_pack.query_table(client, table, query, fields, limit, display)
        record_count = len(result.get("result", [])) if isinstance(result.get("result"), list) else 0
        return _create_success_response(
            "query_table",
            result,
            f"Queried table {table}: {record_count} records returned",
            env=env,
            table=table,
            record_count=record_count
        )


@mcp.tool()
@handle_errors("stats")
@validate_parameters(StatsParams)
def stats(
    table: str, 
    query: str = "", 
    group_by: Optional[List[str]] = None, 
    count: bool = True, 
    sum: Optional[List[str]] = None, 
    avg: Optional[List[str]] = None, 
    minv: Optional[List[str]] = None, 
    maxv: Optional[List[str]] = None, 
    env: str = DEFAULT_ENVIRONMENT
) -> dict:
    """Get statistics and aggregations from ServiceNow table"""
    with LogContext(logger, operation="stats", env=env, table=table):
        c = _get_client(env)
        result = query_pack.stats(c, table, query, group_by, count, sum, avg, minv, maxv)
        logger.info(f"Generated stats for table {table}")
        return result

@mcp.tool()
@handle_errors("ci_graph")
def ci_graph(root_sys_id: str, direction: str = "both", depth: int = 2, limit: int = 200, env: str = "dev") -> dict:
    """Build CI relationship graph from ServiceNow CMDB"""
    with LogContext(logger, operation="ci_graph", env=env, sys_id=root_sys_id):
        c = _get_client(env)
        result = query_pack.ci_graph(c, root_sys_id, direction, depth, limit)
        logger.info(f"Built CI graph for {root_sys_id}: depth={depth}, direction={direction}")
        return result

# ---- build & catalog ----
@mcp.tool()
@handle_errors("app_scaffold")
def app_scaffold(spec, scope: str = "x_cloudorch_aiops", dry_run: bool = False, env: str = "dev"):
    """Scaffold a ServiceNow application from specification"""
    with LogContext(logger, operation="app_scaffold", env=env, scope=scope, dry_run=dry_run):
        c = _get_client(env)
        result = build_pack.app_scaffold(c, spec, scope=scope, dry_run=dry_run)
        logger.info(f"App scaffold {'simulated' if dry_run else 'created'} in scope {scope}")
        return result

@mcp.tool()
@handle_errors("create_table")
@validate_parameters(CreateTableParams)
def create_table(table_label: str, table_name: str, extends: str = None, scope: str = "x_cloudorch_aiops", dry_run: bool = False, env: str = "dev"):
    """Create a new ServiceNow table"""
    with LogContext(logger, operation="create_table", env=env, table=table_name, scope=scope, dry_run=dry_run):
        c = _get_client(env)
        result = build_pack.create_table(c, table_label, table_name, extends=extends, scope=scope, dry_run=dry_run)
        logger.info(f"Table {table_name} {'simulated' if dry_run else 'created'}")
        return result

@mcp.tool()
@handle_errors("add_field")
@validate_parameters(AddFieldParams)
def add_field(table_name: str, name: str, ftype: str, label: str, mandatory: bool = False, default: str = None, choices = None, scope: str = "x_cloudorch_aiops", dry_run: bool = False, env: str = "dev"):
    """Add a field to a ServiceNow table"""
    with LogContext(logger, operation="add_field", env=env, table=table_name, scope=scope, dry_run=dry_run):
        c = _get_client(env)
        result = build_pack.add_field(c, table_name, name, ftype, label, mandatory, default, choices, scope, dry_run)
        logger.info(f"Field {name} {'simulated' if dry_run else 'added'} to table {table_name}")
        return result

# ---- scripts/dev ----
@mcp.tool()
@handle_errors("create_script_include")
@validate_parameters(CreateScriptIncludeParams)
def create_script_include(name: str, script: str, api_name: str = "", active: bool = True, scope: str = "x_cloudorch_aiops", table: str = "sys_script_include", dry_run: bool = False, env: str = "dev") -> dict:
    """Create a ServiceNow script include"""
    g = _guard_table(table, "write", override=dry_run)
    if g: return g
    
    with LogContext(logger, operation="create_script_include", env=env, table=table, scope=scope, dry_run=dry_run):
        c = _get_client(env)
        result = dev_pack.create_script_include(c, name, script, api_name or None, active, table, scope, dry_run)
        logger.info(f"Script include {name} {'simulated' if dry_run else 'created'}")
        return result

@mcp.tool()
@handle_errors("create_business_rule")
@validate_parameters(CreateBusinessRuleParams)
def create_business_rule(table_name: str, name: str, when: str, actions: dict, condition: str = "", script: str = "", active: bool = True, table: str = "sys_script", dry_run: bool = False, env: str = "dev") -> dict:
    """Create a ServiceNow business rule"""
    g = _guard_table(table, "write", override=dry_run)
    if g: return g
    
    with LogContext(logger, operation="create_business_rule", env=env, table=table, dry_run=dry_run):
        c = _get_client(env)
        result = dev_pack.create_business_rule(c, table_name, name, when, actions, condition, script, active, table, dry_run)
        logger.info(f"Business rule {name} {'simulated' if dry_run else 'created'} for table {table_name}")
        return result

# ---- operate/troubleshoot ----
@mcp.tool()
@handle_errors("perf_top_transactions")
def perf_top_transactions(since_minutes: int = 60, limit: int = 20, env: str = "dev") -> dict:
    """Get top performing transactions from ServiceNow"""
    with LogContext(logger, operation="perf_top_transactions", env=env):
        c = _get_client(env)
        result = operate_pack.perf_top_transactions(c, since_minutes, limit)
        logger.info(f"Retrieved top {limit} transactions from last {since_minutes} minutes")
        return result

@mcp.tool()
@handle_errors("jobs_running")
def jobs_running(limit: int = 50, env: str = "dev") -> dict:
    """Get currently running ServiceNow jobs"""
    with LogContext(logger, operation="jobs_running", env=env):
        c = _get_client(env)
        result = operate_pack.jobs_running(c, limit)
        logger.info(f"Retrieved {limit} running jobs")
        return result

# ---- orchestrator ----
@mcp.tool()
@handle_errors("execute_plan")
@validate_parameters(ExecutePlanParams)
def execute_plan(plan: list, confirm: bool = False, continue_on_error: bool = False, env: str = "dev") -> dict:
    """Execute a multi-step automation plan"""
    with LogContext(logger, operation="execute_plan", env=env, plan_steps=len(plan)):
        c = _get_client(env)
        result = _execute_plan(c, plan, confirm, continue_on_error)
        logger.info(f"Executed plan with {len(plan)} steps")
        return result

# ---- workspaces ----
@mcp.tool()
@handle_errors("ws_list")
def ws_list() -> dict:
    """List available workspaces"""
    with LogContext(logger, operation="ws_list"):
        result = {"workspaces": _ws_list()}
        logger.info(f"Listed {len(result['workspaces'])} workspaces")
        return result

@mcp.tool()
@handle_errors("ws_get")
def ws_get(name: str = "default") -> dict:
    """Get workspace configuration"""
    with LogContext(logger, operation="ws_get", workspace=name):
        result = {"name": name, "config": _ws_get(name)}
        logger.info(f"Retrieved workspace config: {name}")
        return result

@mcp.tool()
@handle_errors("ws_set")
@validate_parameters(WorkspaceParams)
def ws_set(name: str = "default", env: str = "", scope: str = "", confirm: bool = False) -> dict:
    """Set workspace configuration"""
    with LogContext(logger, operation="ws_set", workspace=name):
        updates = {}
        if env: updates["env"] = env
        if scope: updates["scope"] = scope
        updates["confirm"] = bool(confirm)
        result = {"name": name, "config": _ws_set(name, updates)}
        logger.info(f"Updated workspace config: {name}")
        return result

# ---- Senior Developer Capabilities ----
@mcp.tool()
@handle_errors("analyze_user_story")
def analyze_user_story(story: str, context = None, env: str = "dev"):
    """Analyze a user story and break it down into actionable development tasks"""
    with LogContext(logger, operation="analyze_user_story", env=env):
        c = _get_client(env)
        result = senior_dev_pack.analyze_story(c, story, context)
        logger.info("Analyzed user story for development tasks")
        return result

@mcp.tool()
@handle_errors("troubleshoot_cmdb_duplicates")
def troubleshoot_cmdb_duplicates(ci_class: str = "cmdb_ci", analysis_fields = None, limit: int = 100, env: str = "dev"):
    """Advanced CMDB duplicate analysis and troubleshooting"""
    with LogContext(logger, operation="troubleshoot_cmdb_duplicates", env=env, table=ci_class):
        c = _get_client(env)
        result = senior_dev_pack.troubleshoot_cmdb_duplicates(c, ci_class, analysis_fields, limit)
        logger.info(f"Analyzed CMDB duplicates for {ci_class}")
        return result

# ---- Story-Driven Development ----
@mcp.tool()
@handle_errors("parse_user_story")
def parse_user_story(story: str) -> dict:
    """Parse user story using standard format: As a [user], I want [goal] so that [benefit]"""
    with LogContext(logger, operation="parse_user_story"):
        result = story_driven_pack.parse_user_story(story)
        logger.info("Parsed user story components")
        return result

@mcp.tool()
@handle_errors("story_to_implementation")
def story_to_implementation(story: str, env: str = "dev") -> dict:
    """Complete story-to-implementation pipeline: parse story, analyze requirements, generate executable plan"""
    with LogContext(logger, operation="story_to_implementation", env=env):
        c = _get_client(env)
        
        # Step 1: Parse the story
        parsed_story = story_driven_pack.parse_user_story(story)
        
        # Step 2: Validate completeness
        validation = story_driven_pack.validate_story_completeness(parsed_story)
        
        if not validation["is_complete"]:
            logger.warning("User story is incomplete")
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
        
        logger.info("Generated complete implementation plan from user story")
        return {
            "status": "success",
            "parsed_story": parsed_story,
            "validation": validation,
            "requirements": requirements,
            "executable_plan": executable_plan
        }

# ---- MCP Resources ----
# Note: Resources are available but commented out due to FastMCP parameter matching issues
# They can be enabled once the parameter matching is resolved

# @mcp.resource("servicenow://tables/{env}")
# @handle_errors("list_tables_resource")
# async def list_tables_resource(env: str) -> List[dict]:
#     """List ServiceNow tables as MCP resources"""
#     provider = get_resource_provider()
#     tables = await provider.list_tables(env=env, limit=200)
#     return [table.dict() for table in tables]

# Cleanup function
async def cleanup():
    """Cleanup resources on shutdown"""
    logger.info("Cleaning up MCP server resources")
    
    # Close async clients through factory
    client_factory = get_client_factory()
    await client_factory.close_all_async_clients()
    
    # Close resource provider clients
    provider = get_resource_provider()
    await provider.close_all_clients()
    
    logger.info("MCP server cleanup completed")

if __name__ == "__main__":
    import atexit
    import signal
    
    # Register cleanup handlers
    atexit.register(lambda: asyncio.run(cleanup()))
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.run(cleanup())
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info(f"Starting ServiceNow MCP Server v{__version__}")
    logger.info(f"Server capabilities: {', '.join(SERVER_INFO.features)}")
    
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise
    finally:
        asyncio.run(cleanup())