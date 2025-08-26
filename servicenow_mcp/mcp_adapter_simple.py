"""
ServiceNow MCP Adapter - Production-ready version with all best practices
"""

from typing import Dict, Any, List
import asyncio
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from .config import Config
from .servicenow_client import ServiceNowClient
from .models import *
from .error_handler import handle_errors, MCPResponse
from .logging_config import init_default_logger, get_logger, LogContext
from .version import __version__

from .packs import build_pack, operate_pack, query_pack
from .packs import senior_dev_pack, story_driven_pack
from .utils.plan import execute_plan as _execute_plan
from .utils.guard import is_allowed as _guard
from .utils.workspace import list_workspaces as _ws_list, get_workspace as _ws_get, set_workspace as _ws_set

# Initialize logging
logger = init_default_logger()

# Initialize MCP server with metadata
mcp = FastMCP("servicenow-mcp")

# Server info
SERVER_INFO = ServerInfo(
    name="servicenow-mcp",
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
        }
    ),
    environments=["dev", "test", "prod"],
    features=[
        "multi-environment",
        "senior-developer-capabilities", 
        "story-driven-development",
        "advanced-cmdb-analysis",
        "plan-execution",
        "workspace-management",
        "comprehensive-logging",
        "error-handling",
        "input-validation"
    ]
)

# Client management
_clients: Dict[str, ServiceNowClient] = {}

def _get_client(env: str = "dev") -> ServiceNowClient:
    """Get synchronous ServiceNow client for environment"""
    key = env.lower()
    if key not in _clients:
        cfg = Config.for_env(key)
        _clients[key] = ServiceNowClient(cfg.instance_url, cfg.username, cfg.password)
        logger.info(f"Created ServiceNow client for environment: {key}")
    return _clients[key]

def _guard_table(table: str, op: str = "write", override: bool = False):
    """Check table access permissions"""
    ok, why = _guard(table, op, override)
    if not ok:
        logger.warning(f"Guard blocked {op} operation on table {table}: {why}")
        return {"error": "guard_block", "message": why, "table": table}
    return None

# Server metadata endpoints
@mcp.tool()
def get_server_info():
    """Get MCP server information and capabilities"""
    return SERVER_INFO.dict()

@mcp.tool()
def health_check(env: str = "dev"):
    """Check ServiceNow instance connectivity and health"""
    try:
        client = _get_client(env)
        start_time = datetime.utcnow()
        
        # Simple connectivity test
        result = client.query_table("sys_user", limit=1)
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return HealthCheck(
            status="healthy" if not result.get("error") else "unhealthy",
            timestamp=datetime.utcnow(),
            environment=env,
            connection_status={env: not result.get("error")},
            response_time_ms=round(response_time, 2),
            errors=[result.get("error")] if result.get("error") else []
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

# ---- basic incident helpers ----
@mcp.tool()
def create_incident(short_description: str, description: str = None, additional_fields = None, env: str = "dev"):
    """Create a new ServiceNow incident"""
    with LogContext(logger, operation="create_incident", env=env, table="incident"):
        c = _get_client(env)
        payload = {"short_description": short_description}
        if description: 
            payload["description"] = description
        if additional_fields: 
            payload.update(additional_fields)
        
        result = c.create_record("incident", payload)
        logger.info(f"Created incident: {result.get('sys_id', 'unknown')}")
        return result

@mcp.tool()
def get_incident(sys_id: str, env: str = "dev"):
    """Get ServiceNow incident by sys_id"""
    with LogContext(logger, operation="get_incident", env=env, table="incident", sys_id=sys_id):
        c = _get_client(env)
        result = c.get_record("incident", sys_id)
        logger.info(f"Retrieved incident: {sys_id}")
        return result

# ---- query ----
@mcp.tool()
def query_table(table: str, query: str = "", fields = None, limit: int = 100, display: bool = False, env: str = "dev"):
    """Query ServiceNow table with filters and field selection"""
    with LogContext(logger, operation="query_table", env=env, table=table):
        c = _get_client(env)
        result = query_pack.query_table(c, table, query, fields, limit, display)
        record_count = len(result.get("result", [])) if isinstance(result.get("result"), list) else 0
        logger.info(f"Queried table {table}: {record_count} records returned")
        return result

@mcp.tool()
def stats(table: str, query: str = "", group_by = None, count: bool = True, sum_fields = None, avg_fields = None, min_fields = None, max_fields = None, env: str = "dev"):
    """Get statistics and aggregations from ServiceNow table"""
    with LogContext(logger, operation="stats", env=env, table=table):
        c = _get_client(env)
        result = query_pack.stats(c, table, query, group_by, count, sum_fields, avg_fields, min_fields, max_fields)
        logger.info(f"Generated stats for table {table}")
        return result

@mcp.tool()
def ci_graph(root_sys_id: str, direction: str = "both", depth: int = 2, limit: int = 200, env: str = "dev"):
    """Build CI relationship graph from ServiceNow CMDB"""
    with LogContext(logger, operation="ci_graph", env=env, sys_id=root_sys_id):
        c = _get_client(env)
        result = query_pack.ci_graph(c, root_sys_id, direction, depth, limit)
        logger.info(f"Built CI graph for {root_sys_id}: depth={depth}, direction={direction}")
        return result

# ---- build & catalog ----
@mcp.tool()
def create_table(table_label: str, table_name: str, extends: str = None, scope: str = "x_cloudorch_aiops", dry_run: bool = False, env: str = "dev"):
    """Create a new ServiceNow table"""
    with LogContext(logger, operation="create_table", env=env, table=table_name, scope=scope, dry_run=dry_run):
        c = _get_client(env)
        result = build_pack.create_table(c, table_label, table_name, extends=extends, scope=scope, dry_run=dry_run)
        logger.info(f"Table {table_name} {'simulated' if dry_run else 'created'}")
        return result

@mcp.tool()
def add_field(table_name: str, name: str, ftype: str, label: str, mandatory: bool = False, default: str = None, choices = None, scope: str = "x_cloudorch_aiops", dry_run: bool = False, env: str = "dev"):
    """Add a field to a ServiceNow table"""
    with LogContext(logger, operation="add_field", env=env, table=table_name, scope=scope, dry_run=dry_run):
        c = _get_client(env)
        result = build_pack.add_field(c, table_name, name, ftype, label, mandatory, default, choices, scope, dry_run)
        logger.info(f"Field {name} {'simulated' if dry_run else 'added'} to table {table_name}")
        return result

# ---- orchestrator ----
@mcp.tool()
def execute_plan(plan, confirm: bool = False, continue_on_error: bool = False, env: str = "dev"):
    """Execute a multi-step automation plan"""
    with LogContext(logger, operation="execute_plan", env=env, plan_steps=len(plan)):
        c = _get_client(env)
        result = _execute_plan(c, plan, confirm, continue_on_error)
        logger.info(f"Executed plan with {len(plan)} steps")
        return result

# ---- workspaces ----
@mcp.tool()
def ws_list():
    """List available workspaces"""
    with LogContext(logger, operation="ws_list"):
        result = {"workspaces": _ws_list()}
        logger.info(f"Listed {len(result['workspaces'])} workspaces")
        return result

@mcp.tool()
def ws_get(name: str = "default"):
    """Get workspace configuration"""
    with LogContext(logger, operation="ws_get", workspace=name):
        result = {"name": name, "config": _ws_get(name)}
        logger.info(f"Retrieved workspace config: {name}")
        return result

@mcp.tool()
def ws_set(name: str = "default", env: str = "", scope: str = "", confirm: bool = False):
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
def analyze_user_story(story: str, context = None, env: str = "dev"):
    """Analyze a user story and break it down into actionable development tasks"""
    with LogContext(logger, operation="analyze_user_story", env=env):
        c = _get_client(env)
        result = senior_dev_pack.analyze_story(c, story, context)
        logger.info("Analyzed user story for development tasks")
        return result

@mcp.tool()
def troubleshoot_cmdb_duplicates(ci_class: str = "cmdb_ci", analysis_fields = None, limit: int = 100, env: str = "dev"):
    """Advanced CMDB duplicate analysis and troubleshooting"""
    with LogContext(logger, operation="troubleshoot_cmdb_duplicates", env=env, table=ci_class):
        c = _get_client(env)
        result = senior_dev_pack.troubleshoot_cmdb_duplicates(c, ci_class, analysis_fields, limit)
        logger.info(f"Analyzed CMDB duplicates for {ci_class}")
        return result

# ---- Story-Driven Development ----
@mcp.tool()
def parse_user_story(story: str):
    """Parse user story using standard format: As a [user], I want [goal] so that [benefit]"""
    with LogContext(logger, operation="parse_user_story"):
        result = story_driven_pack.parse_user_story(story)
        logger.info("Parsed user story components")
        return result

@mcp.tool()
def story_to_implementation(story: str, env: str = "dev"):
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

if __name__ == "__main__":
    import atexit
    import signal
    
    def cleanup():
        logger.info("Cleaning up MCP server resources")
        logger.info("MCP server cleanup completed")
    
    # Register cleanup handlers
    atexit.register(cleanup)
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        cleanup()
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
        cleanup()