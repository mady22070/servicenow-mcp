"""
ServiceNow MCP Adapter - Production-ready version with all best practices
"""

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from .config import Config
from .servicenow_client import ServiceNowClient
from .models import *
from .constants import DefaultValues
from .error_handler import handle_errors, MCPResponse, validate_parameters
from .logging_config import init_default_logger, get_logger, LogContext
from .version import __version__

from .packs import build_pack, operate_pack, query_pack
# Import pack registry for organized pack management
from .pack_registry import get_pack_registry, PackCategory

# Core Development Packs
from .packs import (
    senior_dev_pack,
    story_driven_pack,
    dev_pack,
    scripts_pack,
    background_script_pack,
)

# Data and Configuration Packs
from .packs import (
    table_pack,
    data_pack,
    update_set_pack,
    attachment_pack,
    props_pack,
)

# ITSM and Service Management Packs
from .packs import (
    change_pack,
    problem_pack,
    request_pack,
    irm_pack,
    approvals_pack,
    notify_pack,
    csm_pack,  # NEW: Complete Customer Service Management
)

# CMDB and Discovery Packs
from .packs import (
    cmdb_pack,
    advanced_cmdb_pack,
    csdm_pack,
    discovery_pack,
    itam_pack,
    itom_pack,  # NEW: Complete ITOM functionality
    sam_ham_pack,  # NEW: Complete SAM & HAM functionality
)

# Workflow and Automation Packs
from .packs import (
    flow_pack,
    pipeline_pack,
    planner_pack,
    operate_pack,
)

# Integration and API Packs
from .packs import (
    scripted_rest_api_pack,
    scripted_rest_pack,
    integrations_pack,
)

# User Interface and Experience Packs
from .packs import (
    ui_builder_pack,
    catalog_pack,
    ux_pack,
    user_pack,
)

# Application Development Packs
from .packs import (
    scoped_app_pack,
    scoped_development_pack,
    best_practices_pack,
    naming_conventions_pack,
    catalog_management_pack,
    ui_management_pack,
)

# Testing and Quality Packs
from .packs import (
    atf_pack,
    troubleshoot_pack,
)

# Documentation and Knowledge Packs
from .packs import (
    servicenow_docs_pack,
    docs_pack,
    knowledge_pack,
)
try:
    from .packs import rag_knowledge_pack
    _RAG_PACK_AVAILABLE = True
except Exception:
    rag_knowledge_pack = None
    _RAG_PACK_AVAILABLE = False

# Security and Governance Packs
from .packs import (
    governance_pack,
    impersonation_pack,
    event_pack,
)

# Multi-Modal Content Processing Pack
try:
    from .packs.multimodal_pack import MultiModalPack
    _MULTIMODAL_AVAILABLE = True
except Exception:
    MultiModalPack = None
    _MULTIMODAL_AVAILABLE = False
from .utils.plan import execute_plan as _execute_plan
from .utils.guard import is_allowed as _guard
from .utils.workspace import list_workspaces as _ws_list, get_workspace as _ws_get, set_workspace as _ws_set

# Enhanced MCP Protocol Support
from .streaming import streaming_manager, create_table_query_stream
from .batch_operations import batch_manager, BatchSafetyControls
from .protocol_negotiation import protocol_negotiator, initialize_client_session
from .connection_pool import connection_pool_manager, get_pooled_client

# Initialize logging - disable console output for MCP protocol compatibility
import os
logger = init_default_logger(
    enable_console=os.getenv("MCP_LOG_CONSOLE", "false").lower() == "true",
    log_file=os.getenv("MCP_LOG_FILE", "/tmp/servicenow-mcp.log")
)

def _validate_pack_imports():
    """Validate that all imported packs are registered in the pack registry"""
    registry = get_pack_registry()
    registered_packs = set(registry.get_pack_names())
    
    # List of all imported pack modules (extract from import statements above)
    imported_packs = {
        # Core Development Packs
        'senior_dev_pack', 'story_driven_pack', 'dev_pack', 'scripts_pack',
        'background_script_pack',
        # Data and Configuration Packs
        'table_pack', 'data_pack', 'update_set_pack',
        'attachment_pack', 'props_pack',
        # ITSM and Service Management Packs
        'change_pack', 'problem_pack', 'request_pack', 'irm_pack',
        'approvals_pack', 'notify_pack', 'csm_pack',
        # CMDB and Discovery Packs
        'cmdb_pack', 'advanced_cmdb_pack', 'csdm_pack', 'discovery_pack', 'itam_pack', 'itom_pack', 'sam_ham_pack',
        # Workflow and Automation Packs
        'flow_pack', 'pipeline_pack', 'planner_pack', 'operate_pack',
        # Integration and API Packs
        'scripted_rest_api_pack', 'scripted_rest_pack', 'integrations_pack',
        # User Interface and Experience Packs
        'ui_builder_pack', 'catalog_pack', 'ux_pack', 'user_pack',
        # Application Development Packs
        'scoped_app_pack', 'scoped_development_pack', 'best_practices_pack',
        # Testing and Quality Packs
        'atf_pack', 'troubleshoot_pack',
        # Documentation and Knowledge Packs
        'servicenow_docs_pack', 'docs_pack', 'knowledge_pack',
        # Security and Governance Packs
        'governance_pack', 'impersonation_pack', 'event_pack',
        # Multi-Modal Content Processing Pack
        'multimodal_pack',
        # Additional packs
        'build_pack', 'query_pack'
    }
    
    # Check for unregistered imports
    unregistered = imported_packs - registered_packs
    if unregistered:
        logger.warning(f"Imported packs not registered in pack registry: {unregistered}")
    
    # Check for registered but not imported
    not_imported = registered_packs - imported_packs
    if not_imported:
        logger.info(f"Registered packs not imported: {not_imported}")
    
    logger.info(f"Pack validation complete: {len(imported_packs)} imported, {len(registered_packs)} registered")

# Validate pack imports on startup
_validate_pack_imports()

# Initialize MCP server with metadata
mcp = FastMCP(
    "servicenow-mcp",
    host=os.getenv("MCP_HOST", "0.0.0.0"),
    port=int(os.getenv("MCP_PORT", "8000")),
)

# Wire up real-time activity tracking on every tool call.
# We wrap ToolManager.call_tool so every tool — regardless of which pack
# it lives in — is recorded automatically with no changes to individual tools.
from .activity_tracker import tracker as _activity_tracker

_orig_call_tool = mcp._tool_manager.call_tool

async def _tracked_call_tool(name, arguments, context=None, convert_result=False):
    session_id = "unknown"
    try:
        if context is not None:
            req = getattr(getattr(context, "request_context", None), "request", None)
            if req is not None:
                session_id = req.headers.get("mcp-session-id", "unknown")
    except Exception:
        pass
    event_id = _activity_tracker.record_start(session_id, name)
    try:
        result = await _orig_call_tool(name, arguments, context, convert_result)
        _activity_tracker.record_end(event_id)
        return result
    except Exception as exc:
        _activity_tracker.record_end(event_id, error=str(exc))
        raise

mcp._tool_manager.call_tool = _tracked_call_tool

# Server info
SERVER_INFO = ServerInfo(
    name="servicenow-mcp",
    version=__version__,
    description="ServiceNow MCP Server with comprehensive automation capabilities",
    capabilities=ServerCapabilities(
        tools={
            "query_table": {"description": "Query ServiceNow tables with filters"},
            "create_record": {"description": "Create records in any ServiceNow table"},
            "get_record": {"description": "Get records from any ServiceNow table"},
            "update_record": {"description": "Update records in any ServiceNow table"},
            "delete_record": {"description": "Delete records from any ServiceNow table"},
            "create_incident": {"description": "Create ServiceNow incidents"},
            "stats": {"description": "Get table statistics and aggregations"},
            "execute_plan": {"description": "Execute multi-step automation plans"},
            "analyze_user_story": {"description": "Analyze user stories for development"},
            "troubleshoot_cmdb_duplicates": {"description": "Advanced CMDB duplicate analysis"},
            "discover_csdm_topology": {"description": "Discover CSDM 5.0 service topology"},
            "analyze_csdm_health": {"description": "Analyze CSDM health and compliance"},
            "validate_csdm_structure": {"description": "Validate CSDM structure for services"},
            "create_scoped_application": {"description": "Create scoped application with best practices"},
            "validate_naming_conventions": {"description": "Validate ServiceNow naming conventions"},
            "create_table_with_best_practices": {"description": "Create table following best practices"},
            "validate_script_best_practices": {"description": "Validate scripts for security and performance"},
            "create_catalog_item_comprehensive": {"description": "Create comprehensive catalog item"},
            "create_ui_builder_page": {"description": "Create UI Builder page with validation"},
            "audit_application_best_practices": {"description": "Audit application for best practices compliance"},
            "discover_cloud_resources": {"description": "Discover cloud resources in CSDM"},
            "create_scoped_rest_api": {"description": "Create scoped REST API with best practices"},
            "search_servicenow_documentation": {"description": "Search ServiceNow documentation and best practices"},
            "get_code_examples": {"description": "Get ServiceNow API code examples"},
            "get_troubleshooting_guide": {"description": "Get troubleshooting guides for common issues"},
            "enforce_scoped_development": {"description": "Enforce scoped development best practices"},
            "validate_scoped_table_creation": {"description": "Validate table creation for scoped development"},
            "audit_scoped_application": {"description": "Audit scoped application compliance"},
            "execute_background_script": {"description": "Execute ServiceNow background scripts with safety validation"},
            "validate_script_safety": {"description": "Validate script safety before execution"},
            "get_script_templates": {"description": "Get common background script templates"},
            "analyze_script_performance": {"description": "Analyze script for performance issues"},
            "create_client_script_comprehensive": {"description": "Create client scripts with full validation"},
            "create_business_rule_comprehensive": {"description": "Create business rules with proper scope handling"},
            "create_import_set_table": {"description": "Create import set staging table"},
            "create_transform_map": {"description": "Create transform map for data import"},
            "create_robust_transform_map": {"description": "Create complete transform map with field mappings"},
            "validate_import_set_configuration": {"description": "Validate import set and transform map setup"},
            "create_table_with_navigation": {"description": "Create table with automatic navigation modules"},
            "create_application_navigation_module": {"description": "Create custom navigation module for application"},
            "create_table_with_navigation_enhanced": {"description": "Create table with enhanced navigation and duplicate prevention"},
            # Scripts Pack
            "add_client_script": {"description": "Add client script with validation"},
            # Table Pack
            "batch_insert_records": {"description": "Batch insert multiple records"},
            "batch_update_records": {"description": "Batch update multiple records"},
            # Change Management Pack
            "create_change_request": {"description": "Create change request"},
            "update_change_request": {"description": "Update change request"},
            "get_change_request": {"description": "Get change request details"},
            "approve_change_request": {"description": "Approve change request"},
            "schedule_change_request": {"description": "Schedule change request"},
            # Problem Management Pack
            "create_problem": {"description": "Create problem record"},
            "update_problem": {"description": "Update problem record"},
            "link_incident_to_problem": {"description": "Link incident to problem"},
            "create_known_error": {"description": "Create known error record"},
            # Enhanced MCP Protocol Features
            "execute_batch_operations": {"description": "Execute multiple ServiceNow operations in a batch"},
            "stream_table_query": {"description": "Stream large table query results in chunks"},
            "negotiate_client_capabilities": {"description": "Negotiate MCP protocol capabilities with client"},
            "get_connection_pool_stats": {"description": "Get connection pool statistics"},
            # User Management Pack
            "create_user": {"description": "Create user account"},
            "update_user": {"description": "Update user information"},
            "get_user": {"description": "Get user details"},
            "get_user_by_email": {"description": "Find user by email address"},
            "create_group": {"description": "Create user group"},
            "add_user_to_group": {"description": "Add user to group"},
            "get_group_members": {"description": "Get group members"},
            # Flow Designer Pack
            "create_flow": {"description": "Create Flow Designer flow"},
            "add_flow_trigger_record_change": {"description": "Add record change trigger to flow"},
            "activate_flow": {"description": "Activate or deactivate flow"},
            # Update Set Pack
            "create_update_set": {"description": "Create update set"},
            "close_update_set": {"description": "Close update set"},
            # Attachment Pack
            "upload_attachment": {"description": "Upload file attachment"},
            "list_attachments": {"description": "List record attachments"},
            "download_attachment": {"description": "Download attachment"},
            "delete_attachment": {"description": "Delete attachment"},
            # CMDB Pack
            "cmdb_health_snapshot": {"description": "Get CMDB health snapshot"},
            "servicemap_seed": {"description": "Create service map seed"},
            "impact_rule_add": {"description": "Add impact rule"},
            # Data Pack
            "create_data_source_jdbc": {"description": "Create JDBC data source"},
            "create_import_set": {"description": "Create import set"},
            # Discovery Pack
            "quick_discovery": {"description": "Run quick discovery"},
            "discovery_status": {"description": "Get discovery status"},
            # ITAM Pack
            "asset_receive": {"description": "Receive asset into inventory"},
            "asset_transfer": {"description": "Transfer asset between locations"},
            "asset_retire": {"description": "Retire asset"},
            # ATF Pack
            "create_test_suite": {"description": "Create ATF test suite"},
            "create_ui_form_test": {"description": "Create UI form test"},
            # Scoped App Pack
            "add_application_dependency": {"description": "Add application dependency"},
            "create_application_property": {"description": "Create application property"},
            "create_application_file": {"description": "Create application file"},
            "validate_application_structure": {"description": "Validate application structure"},
            "package_application": {"description": "Package application for distribution"},
            "audit_scoped_applications": {"description": "Audit all scoped applications"},
            "create_application_file": {"description": "Create application file"},
            # Best Practices Pack
            "validate_mandatory_fields": {"description": "Validate mandatory fields"},
            "validate_security_best_practices": {"description": "Validate security best practices"},
            "validate_performance_best_practices": {"description": "Validate performance best practices"},
            "create_field_with_validation": {"description": "Create field with validation"},
            "create_business_rule_with_validation": {"description": "Create business rule with validation"},
            # Scripted REST Pack
            "create_scripted_rest_api": {"description": "Create scripted REST API"},
            "add_scripted_rest_resource": {"description": "Add scripted REST resource"},
            # Missing tools that are already defined
            "create_table": {"description": "Create ServiceNow table"},
            "add_field": {"description": "Add field to ServiceNow table"},
            "ci_graph": {"description": "Build CI relationship graph"},
            "create_catalog_category": {"description": "Create catalog category"},
            "add_catalog_variable_with_validation": {"description": "Add catalog variable with validation"},
            "add_ui_builder_component": {"description": "Add UI Builder component"},
            "add_rest_resource": {"description": "Add REST API resource"},
            "story_to_implementation": {"description": "Complete story-to-implementation pipeline"},
            # ITOM Pack Tools (NEW: Complete IT Operations Management)
            "create_discovery_schedule": {"description": "Create discovery schedule for infrastructure discovery"},
            "update_discovery_schedule": {"description": "Update existing discovery schedule (most common operation)"},
            "modify_discovery_pattern": {"description": "Modify discovery patterns for better CI identification"},
            "manage_discovery_credentials": {"description": "Comprehensive credential management (create/update/test/rotate)"},
            "create_service_mapping": {"description": "Create service mapping for business service discovery"},
            "update_service_mapping": {"description": "Update existing service mapping configurations"},
            "validate_service_mapping": {"description": "Validate service mapping and test discovery"},
            "configure_event_correlation_rule": {"description": "Configure intelligent event correlation rules"},
            "manage_event_policies": {"description": "Manage event policies (create/update/activate/deactivate)"},
            "itom_p1_infrastructure_war_room": {"description": "P1: Create infrastructure war room for critical incidents"},
            "itom_p1_service_dependency_analysis": {"description": "P1: Deep service dependency impact analysis"},
            # CSM Pack Tools (NEW: Complete Customer Service Management)
            "create_customer_case": {"description": "Create customer service case with routing"},
            "update_customer_case": {"description": "Update existing customer case (most common operation)"},
            "route_customer_case": {"description": "Route customer case to appropriate team/agent"},
            "escalate_customer_case": {"description": "Escalate customer case with tracking"},
            "create_knowledge_article": {"description": "Create knowledge article with categorization"},
            "update_knowledge_article": {"description": "Update existing knowledge article"},
            "search_knowledge_articles": {"description": "Search knowledge articles with analytics"},
            "analyze_knowledge_usage": {"description": "Analyze knowledge article usage patterns"},
            "optimize_customer_portal": {"description": "Optimize customer portal experience"},
            "analyze_customer_sentiment": {"description": "Analyze customer sentiment across touchpoints"},
            "csm_p1_customer_crisis_response": {"description": "P1: Activate customer crisis response"},
            "csm_p1_vip_customer_escalation": {"description": "P1: Emergency VIP customer escalation"},
            # SAM & HAM Pack Tools
            "create_software_asset": {"description": "Create software asset with license management"},
            "update_license_usage": {"description": "Update software license usage and compliance"},
            "optimize_software_licenses": {"description": "Analyze and optimize software license allocation"},
            "create_hardware_asset": {"description": "Create hardware asset with lifecycle tracking"},
            "update_hardware_asset": {"description": "Update hardware asset information and status"},
            "plan_hardware_refresh": {"description": "Plan hardware refresh based on age and budget"},
            # RAG Knowledge Pack Tools
            "semantic_knowledge_search": {"description": "Semantic search across ServiceNow knowledge base using RAG"},
            "generate_knowledge_article_from_ticket": {"description": "Generate knowledge article from resolved ticket using RAG"},
            "intelligent_troubleshooting_assistant": {"description": "Provide intelligent troubleshooting assistance using RAG"},
            "knowledge_gap_analysis": {"description": "Analyze knowledge gaps and suggest new articles using RAG"},
            # Pack Management Tools
            "get_pack_registry_info": {"description": "Get information about available packs organized by category"},
            "get_pack_loading_status": {"description": "Get status of pack loading and any issues"},
            "validate_pack_health": {"description": "Validate health of loaded packs"},
            # Multi-Modal Content Processing Tools
            "analyze_screenshot": {"description": "Analyze ServiceNow UI screenshots to extract elements and suggest operations"},
            "generate_workflow_diagram": {"description": "Generate workflow diagrams from ServiceNow Flow Designer or Workflow data"},
            "generate_relationship_diagram": {"description": "Generate relationship diagrams for CMDB entities or other ServiceNow objects"},
            "generate_architecture_diagram": {"description": "Generate architecture diagrams for ServiceNow configurations"},
            "generate_code_example": {"description": "Generate ServiceNow code examples with context-aware customization"},
            "create_visual_guide": {"description": "Create step-by-step visual guides for ServiceNow processes"},
            "generate_interactive_tutorial": {"description": "Generate comprehensive interactive tutorials with code examples and guides"},
            "extract_ui_automation_script": {"description": "Extract automation scripts from UI analysis for testing or RPA"}
        }
    ),
    environments=["dev", "test", "prod"],
    features=[
        "multi-environment",
        "senior-developer-capabilities", 
        "story-driven-development",
        "advanced-cmdb-analysis",
        "csdm-5.0-support",
        "cloud-resource-discovery",
        "service-topology-mapping",
        "plan-execution",
        "workspace-management",
        "comprehensive-logging",
        "error-handling",
        "input-validation",
        "multi-modal-processing",
        "screenshot-analysis",
        "diagram-generation",
        "code-example-generation",
        "visual-guides",
        "interactive-tutorials"
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
def get_pack_registry_info():
    """Get information about available packs organized by category"""
    registry = get_pack_registry()
    
    result = {
        "total_packs": len(registry.get_all_packs()),
        "categories": {},
        "pack_summary": registry.get_category_summary(),
        "validation_status": {}
    }
    
    # Get packs by category
    for category in registry.get_categories():
        packs = registry.get_packs_by_category(category)
        result["categories"][category.value] = [
            {
                "name": pack.name,
                "description": pack.description,
                "dependencies": pack.dependencies,
                "experimental": pack.experimental,
                "deprecated": pack.deprecated
            }
            for pack in packs
        ]
    
    # Validate dependencies
    missing_deps = registry.validate_dependencies()
    if missing_deps:
        result["validation_status"]["missing_dependencies"] = missing_deps
    else:
        result["validation_status"]["dependencies"] = "all_satisfied"
    
    return result

@mcp.tool()
def get_pack_loading_status():
    """Get status of pack loading and any issues"""
    from .pack_loader import get_pack_loader
    
    loader = get_pack_loader()
    return loader.get_loading_summary()

@mcp.tool()
def validate_pack_health():
    """Validate health of loaded packs"""
    from .pack_loader import get_pack_loader
    
    loader = get_pack_loader()
    return loader.validate_pack_health()

@mcp.tool()
def health_check(env: str = "dev"):
    """Check ServiceNow instance connectivity and health"""
    try:
        client = _get_client(env)
        start_time = datetime.utcnow()
        
        # Simple connectivity test - query_table returns a list on success or dict with error
        result = client.query_table("sys_user", limit=1)
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Check if result is a list (success) or dict with error
        is_healthy = isinstance(result, list)
        error_msg = None
        
        if not is_healthy and isinstance(result, dict):
            error_msg = result.get("error", "Unknown error")
        
        return HealthCheck(
            status="healthy" if is_healthy else "unhealthy",
            timestamp=datetime.utcnow(),
            environment=env,
            connection_status={env: is_healthy},
            response_time_ms=round(response_time, 2),
            errors=[error_msg] if error_msg else []
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

# ---- record operations ----
@mcp.tool()
def update_record(table: str, sys_id: str, fields: Dict[str, Any], env: str = "dev"):
    """Update a ServiceNow record with specified fields
    
    Args:
        table: ServiceNow table name (e.g., 'incident', 'change_request', 'sys_user')
        sys_id: System ID of the record to update
        fields: Dictionary of field names and values to update
        env: Environment to use (dev, test, prod)
    
    Returns:
        Updated record data
    
    Examples:
        # Update incident priority and state
        update_record('incident', 'abc123', {'priority': '1', 'state': '2'})
        
        # Update user information
        update_record('sys_user', 'user123', {'email': 'new@email.com', 'phone': '555-1234'})
        
        # Update change request
        update_record('change_request', 'chg123', {'state': 'approved', 'comments': 'Approved by manager'})
    """
    with LogContext(logger, operation="update_record", env=env, table=table, sys_id=sys_id):
        c = _get_client(env)
        result = c.update_record(table, sys_id, fields)
        logger.info(f"Updated {table} record {sys_id} with {len(fields)} fields")
        return result

@mcp.tool()
def get_record(table: str, sys_id: str, fields: Optional[List[str]] = None, env: str = "dev"):
    """Get a ServiceNow record by sys_id
    
    Args:
        table: ServiceNow table name (e.g., 'incident', 'change_request', 'sys_user')
        sys_id: System ID of the record to retrieve
        fields: Optional list of specific fields to retrieve
        env: Environment to use (dev, test, prod)
    
    Returns:
        Record data
    
    Examples:
        # Get full incident record
        get_record('incident', 'abc123')
        
        # Get specific fields only
        get_record('sys_user', 'user123', ['name', 'email', 'department'])
    """
    with LogContext(logger, operation="get_record", env=env, table=table, sys_id=sys_id):
        c = _get_client(env)
        result = c.get_record(table, sys_id, fields)
        logger.info(f"Retrieved {table} record {sys_id}")
        return result

@mcp.tool()
def create_record(table: str, fields: Dict[str, Any], env: str = "dev"):
    """Create a new ServiceNow record
    
    Args:
        table: ServiceNow table name (e.g., 'incident', 'change_request', 'sys_user')
        fields: Dictionary of field names and values for the new record
        env: Environment to use (dev, test, prod)
    
    Returns:
        Created record data including sys_id
    
    Examples:
        # Create new incident
        create_record('incident', {
            'short_description': 'Server down',
            'description': 'Web server is not responding',
            'priority': '1',
            'category': 'hardware'
        })
        
        # Create new user
        create_record('sys_user', {
            'user_name': 'john.doe',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@company.com'
        })
    """
    with LogContext(logger, operation="create_record", env=env, table=table):
        c = _get_client(env)
        result = c.create_record(table, fields)
        logger.info(f"Created {table} record: {result.get('sys_id', 'unknown')}")
        return result

@mcp.tool()
def delete_record(table: str, sys_id: str, env: str = "dev"):
    """Delete a ServiceNow record
    
    Args:
        table: ServiceNow table name (e.g., 'incident', 'change_request')
        sys_id: System ID of the record to delete
        env: Environment to use (dev, test, prod)
    
    Returns:
        Deletion result
    
    Examples:
        # Delete incident
        delete_record('incident', 'abc123')
        
        # Delete change request
        delete_record('change_request', 'chg123')
    """
    with LogContext(logger, operation="delete_record", env=env, table=table, sys_id=sys_id):
        c = _get_client(env)
        result = c.delete_record(table, sys_id)
        logger.info(f"Deleted {table} record {sys_id}")
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
@handle_errors("create_table")
@validate_parameters(CreateTableParams)
def create_table(
    table_label: str, 
    table_name: str, 
    extends: Optional[str] = None, 
    scope: str = DefaultValues.SCOPE, 
    dry_run: bool = False, 
    env: str = DefaultValues.ENVIRONMENT
) -> Dict[str, Any]:
    """
    Create a new ServiceNow table with navigation and duplicate prevention
    
    This is a simplified version of create_table_with_navigation_enhanced with navigation enabled by default.
    
    Args:
        table_label: Display label for the table
        table_name: Technical table name (must be alphanumeric with underscores)
        extends: Parent table to extend (optional)
        scope: Application scope
        dry_run: Preview changes without executing
        env: Environment (dev/test/prod)
        
    Returns:
        Dictionary containing creation results and metadata
    """
    # Delegate to the enhanced version with navigation enabled
    return create_table_with_navigation_enhanced(
        table_label=table_label,
        table_name=table_name,
        extends=extends,
        scope=scope,
        create_navigation=True,  # Always create navigation for this simplified version
        dry_run=dry_run,
        env=env
    )

@mcp.tool()
def add_field(table_name: str, name: str, ftype: str, label: str, mandatory: bool = False, default: str = None, choices = None, scope: str = "x_cloudorch_aiops", dry_run: bool = False, env: str = "dev"):
    """Add a field to a ServiceNow table (legacy function - use add_field_enhanced for full feature support)"""
    with LogContext(logger, operation="add_field", env=env, table=table_name, scope=scope, dry_run=dry_run):
        c = _get_client(env)
        result = build_pack.add_field(c, table_name, name, ftype, label, mandatory, default, choices, scope, dry_run)
        logger.info(f"Field {name} {'simulated' if dry_run else 'added'} to table {table_name}")
        return result

@mcp.tool()
def add_field_enhanced(
    table_name: str, 
    field_name: str, 
    field_type: str, 
    label: str, 
    mandatory: bool = False, 
    default_value: str = None, 
    choices = None, 
    reference_table: str = None, 
    reference_qual: str = None, 
    max_length: int = None, 
    scope: str = None, 
    dry_run: bool = False, 
    env: str = "dev",
    **additional_attributes
):
    """
    Enhanced field creation with comprehensive ServiceNow field type support
    
    Supports all ServiceNow field types including:
    - Basic types: string, integer, decimal, float, boolean
    - Date/time: glide_date, glide_date_time, glide_time, glide_duration
    - Text: journal, journal_input, html, translated_html, translated_text
    - Reference: reference, glide_list, document_id
    - Choice: choice (with proper choice options)
    - Validation: url, email, phone_number
    - Numeric: currency, percent_complete
    - Security: password, password2, encrypted_text
    - System: GUID, conditions, script, script_plain
    
    Args:
        table_name: Name of the table to add field to
        field_name: Technical name of the field (should start with u_ for custom fields)
        field_type: ServiceNow field type (see supported types above)
        label: Display label for the field
        mandatory: Whether field is required
        default_value: Default value for the field
        choices: List of choice options for choice fields (format: [{"value": "1", "label": "High"}, ...])
        reference_table: Referenced table name for reference fields (e.g., "sys_user")
        reference_qual: Reference qualifier for reference fields
        max_length: Maximum field length (overrides default)
        scope: Application scope
        dry_run: Preview without creating
        env: Environment (dev/test/prod)
        **additional_attributes: Field-specific attributes (e.g., currency_code, scale, precision)
    
    Returns:
        Dictionary with field creation results, validation info, and field type details
    """
    with LogContext(logger, operation="add_field_enhanced", env=env, table=table_name, field_type=field_type, dry_run=dry_run):
        c = _get_client(env)
        
        # Convert choices to proper format if provided
        formatted_choices = None
        if choices:
            if isinstance(choices, list):
                formatted_choices = []
                for choice in choices:
                    if isinstance(choice, dict):
                        formatted_choices.append(choice)
                    elif isinstance(choice, str):
                        formatted_choices.append({"value": choice, "label": choice})
                    else:
                        formatted_choices.append({"value": str(choice), "label": str(choice)})
        
        result = table_pack.add_field_enhanced(
            client=c,
            table_name=table_name,
            field_name=field_name,
            field_type=field_type,
            label=label,
            mandatory=mandatory,
            default_value=default_value,
            choices=formatted_choices,
            reference_table=reference_table,
            reference_qual=reference_qual,
            max_length=max_length,
            scope=scope,
            dry_run=dry_run,
            **additional_attributes
        )
        
        logger.info(f"Enhanced field {field_name} ({'simulated' if dry_run else 'created'}) on table {table_name} with type {field_type}")
        return result

@mcp.tool()
def create_table_with_fields(
    table_name: str,
    table_label: str,
    fields: List[Dict[str, Any]],
    extends: str = None,
    scope: str = None,
    dry_run: bool = False,
    env: str = "dev"
):
    """
    Create a table with multiple fields in one operation
    
    Args:
        table_name: Technical table name (should start with u_ for custom tables)
        table_label: Display label for table
        fields: List of field definitions with comprehensive field type support
        extends: Parent table to extend (optional)
        scope: Application scope
        dry_run: Preview without creating
        env: Environment (dev/test/prod)
    
    Field definition format:
    {
        "field_name": "u_priority",
        "field_type": "choice",
        "label": "Priority",
        "mandatory": false,
        "choices": [
            {"value": "1", "label": "Critical"},
            {"value": "2", "label": "High"},
            {"value": "3", "label": "Medium"}
        ]
    }
    
    Supported field types: string, integer, decimal, float, boolean, glide_date, 
    glide_date_time, glide_time, glide_duration, journal, journal_input, html, 
    reference, glide_list, choice, url, email, phone_number, currency, 
    percent_complete, password, encrypted_text, and more.
    
    Returns:
        Dictionary with table and field creation results
    """
    with LogContext(logger, operation="create_table_with_fields", env=env, table=table_name, field_count=len(fields), dry_run=dry_run):
        c = _get_client(env)
        
        result = table_pack.create_table_with_fields(
            client=c,
            table_name=table_name,
            table_label=table_label,
            fields=fields,
            extends=extends,
            scope=scope,
            dry_run=dry_run
        )
        
        logger.info(f"Table {table_name} with {len(fields)} fields {'simulated' if dry_run else 'created'}")
        return result

@mcp.tool()
def add_field_from_template(
    table_name: str,
    template_name: str,
    field_name: str = None,
    label: str = None,
    scope: str = None,
    dry_run: bool = False,
    env: str = "dev",
    **overrides
):
    """
    Create a field from a predefined template
    
    Available templates:
    - name: String field for names (mandatory, 100 chars)
    - description: String field for descriptions (4000 chars)
    - active: Boolean field with default true
    - priority: Choice field with Critical/High/Medium/Low options
    - state: Choice field with New/In Progress/Resolved/Closed options
    - assigned_to: Reference to sys_user table
    - assignment_group: Reference to sys_user_group table
    - due_date: Date field
    - created_on: Date/time field
    - email: Email field with validation
    - phone: Phone number field
    - url: URL field with validation
    - cost: Currency field (USD)
    - percentage: Percent complete field
    - comments: Journal field
    - work_notes: Journal input field
    
    Args:
        table_name: Name of the table
        template_name: Name of the field template (see available templates above)
        field_name: Override field name (defaults to u_{template_name})
        label: Override field label
        scope: Application scope
        dry_run: Preview without creating
        env: Environment (dev/test/prod)
        **overrides: Override any template attributes
    
    Returns:
        Dictionary with field creation results
    """
    with LogContext(logger, operation="add_field_from_template", env=env, table=table_name, template=template_name, dry_run=dry_run):
        c = _get_client(env)
        
        result = table_pack.add_field_from_template(
            client=c,
            table_name=table_name,
            template_name=template_name,
            field_name=field_name,
            label=label,
            scope=scope,
            dry_run=dry_run,
            **overrides
        )
        
        logger.info(f"Field from template {template_name} {'simulated' if dry_run else 'created'} on table {table_name}")
        return result

@mcp.tool()
def get_field_type_documentation():
    """
    Get comprehensive documentation for all supported ServiceNow field types
    
    Returns detailed information about:
    - All supported field types with descriptions
    - Field type capabilities (supports_default, supports_choices, etc.)
    - Available field templates
    - Usage examples for different field types
    
    Use this to understand what field types are available and how to use them.
    """
    with LogContext(logger, operation="get_field_type_documentation"):
        result = table_pack.get_field_type_documentation()
        logger.info(f"Retrieved documentation for {len(result['supported_types'])} field types")
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

# ---- Enhanced MCP Protocol Features ----
@mcp.tool()
def execute_batch_operations(operations: List[Dict[str, Any]], batch_id: str = None, 
                           fail_fast: bool = True, parallel: bool = False, env: str = "dev"):
    """Execute multiple ServiceNow operations in a batch with safety controls"""
    with LogContext(logger, operation="execute_batch_operations", env=env, batch_size=len(operations)):
        try:
            # Validate batch request
            request = BatchRequest(
                operations=operations,
                batch_id=batch_id,
                fail_fast=fail_fast,
                parallel=parallel
            )
            
            # Safety validation
            validation_errors = BatchSafetyControls.validate_batch_request(request)
            if validation_errors:
                return {
                    "error": "batch_validation_failed",
                    "validation_errors": validation_errors
                }
            
            # Get client and execute batch
            client = _get_client(env)
            
            # Execute batch using asyncio
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(
                    batch_manager.execute_batch(request, client, env)
                )
                return response.dict()
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Batch execution failed: {str(e)}")
            return {
                "error": "batch_execution_failed",
                "message": str(e)
            }

@mcp.tool()
def negotiate_client_capabilities(streaming: bool = False, batch_operations: bool = False,
                                max_batch_size: int = None, protocol_version: str = "1.0"):
    """Negotiate MCP protocol capabilities with the client"""
    with LogContext(logger, operation="negotiate_capabilities"):
        try:
            from .models import ClientCapabilities
            
            client_capabilities = ClientCapabilities(
                streaming=streaming,
                batch_operations=batch_operations,
                max_batch_size=max_batch_size,
                protocol_version=protocol_version
            )
            
            # Use a default client ID for now
            client_id = "default_client"
            session_info = initialize_client_session(client_id, explicit_capabilities=client_capabilities)
            
            logger.info(f"Negotiated capabilities: streaming={streaming}, batch={batch_operations}")
            return session_info
            
        except Exception as e:
            logger.error(f"Capability negotiation failed: {str(e)}")
            return {
                "error": "negotiation_failed",
                "message": str(e)
            }

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

# ---- CSDM 5.0 Capabilities ----
@mcp.tool()
def discover_csdm_topology(root_ci_id: str, depth: int = 3, include_cloud: bool = True, env: str = "dev"):
    """Discover complete CSDM 5.0 topology from a root CI"""
    with LogContext(logger, operation="discover_csdm_topology", env=env, root_ci=root_ci_id):
        c = _get_client(env)
        result = csdm_pack.discover_csdm_topology(c, root_ci_id, depth, include_cloud)
        logger.info(f"Discovered CSDM topology for {root_ci_id}: depth={depth}")
        return result

@mcp.tool()
def analyze_csdm_health(ci_class: str = None, environment: str = None, env: str = "dev"):
    """Analyze CSDM health and compliance across the environment"""
    with LogContext(logger, operation="analyze_csdm_health", env=env, ci_class=ci_class):
        c = _get_client(env)
        result = csdm_pack.analyze_csdm_health(c, ci_class, environment)
        logger.info(f"Analyzed CSDM health: compliance_score={result.get('csdm_compliance_score', 0)}")
        return result

@mcp.tool()
def validate_csdm_structure(business_service_id: str, env: str = "dev"):
    """Validate CSDM structure for a business service"""
    with LogContext(logger, operation="validate_csdm_structure", env=env, service_id=business_service_id):
        c = _get_client(env)
        result = csdm_pack.validate_csdm_structure(c, business_service_id)
        logger.info(f"Validated CSDM structure: score={result.get('validation_score', 0)}")
        return result

@mcp.tool()
def discover_cloud_resources(cloud_provider: str = "aws", region: str = None, env: str = "dev"):
    """Discover and analyze cloud resources in CSDM"""
    with LogContext(logger, operation="discover_cloud_resources", env=env, provider=cloud_provider):
        c = _get_client(env)
        result = csdm_pack.discover_cloud_resources(c, cloud_provider, region)
        logger.info(f"Discovered {result.get('total_resources', 0)} cloud resources for {cloud_provider}")
        return result

# ---- ServiceNow Best Practices Tools ----
@mcp.tool()
def create_scoped_application(name: str, scope: str, version: str = "1.0.0", description: str = "", 
                            vendor: str = "", vendor_prefix: str = "", dry_run: bool = False, env: str = "dev"):
    """Create a new scoped application following ServiceNow best practices"""
    with LogContext(logger, operation="create_scoped_application", env=env, scope=scope, dry_run=dry_run):
        client = _get_client(env)
        result = best_practices_pack.create_scoped_application(client, name, scope, version, description, dry_run)
        return result

@mcp.tool()
def validate_naming_conventions(name: str, object_type: str):
    """Validate ServiceNow naming conventions for various object types"""
    with LogContext(logger, operation="validate_naming_conventions", object_type=object_type):
        result = best_practices_pack.validate_naming_conventions(name, object_type)
        return result

@mcp.tool()
def create_table_with_best_practices(table_label: str, table_name: str, scope: str, 
                                   extends: str = None, dry_run: bool = False, env: str = "dev"):
    """Create table following ServiceNow best practices"""
    with LogContext(logger, operation="create_table_with_best_practices", env=env, table=table_name, scope=scope, dry_run=dry_run):
        client = _get_client(env)
        result = best_practices_pack.create_table_with_best_practices(client, table_label, table_name, scope, extends, dry_run)
        return result

@mcp.tool()
def validate_script_best_practices(script: str, script_type: str = "server"):
    """Validate scripts for security and performance best practices"""
    with LogContext(logger, operation="validate_script_best_practices", script_type=script_type):
        result = best_practices_pack.validate_script_best_practices(script, script_type)
        return result

@mcp.tool()
def audit_application_best_practices(scope: str, env: str = "dev"):
    """Audit an entire application for best practices compliance"""
    with LogContext(logger, operation="audit_application_best_practices", env=env, scope=scope):
        client = _get_client(env)
        result = best_practices_pack.audit_application_best_practices(client, scope)
        return result

# ---- Catalog Management Tools ----
@mcp.tool()
def create_catalog_category(title: str, description: str = "", parent_category: str = None, 
                          scope: str = None, dry_run: bool = False, env: str = "dev"):
    """Create a catalog category"""
    with LogContext(logger, operation="create_catalog_category", env=env, dry_run=dry_run):
        client = _get_client(env)
        result = catalog_pack.create_catalog_category(client, title, description, parent_category, scope, dry_run)
        return result



@mcp.tool()
def add_catalog_variable_with_validation(item_sys_id: str, variable_type: str, name: str, question: str,
                                       mandatory: bool = False, default_value: str = "",
                                       choices: List[str] = None, validation_script: str = None,
                                       dry_run: bool = False, env: str = "dev"):
    """Add catalog variable with comprehensive validation"""
    with LogContext(logger, operation="add_catalog_variable_with_validation", env=env, dry_run=dry_run):
        client = _get_client(env)
        result = catalog_pack.add_catalog_variable_with_validation(
            client, item_sys_id, variable_type, name, question, mandatory, 
            default_value, choices, validation_script, dry_run
        )
        return result

@mcp.tool()
def validate_catalog_item_setup(item_sys_id: str, env: str = "dev"):
    """Validate catalog item setup for best practices"""
    with LogContext(logger, operation="validate_catalog_item_setup", env=env):
        client = _get_client(env)
        result = catalog_pack.validate_catalog_item_setup(client, item_sys_id)
        return result

# ---- UI Builder Tools ----
@mcp.tool()
def create_ui_builder_page(name: str, title: str, description: str = "", 
                         scope: str = None, dry_run: bool = False, env: str = "dev"):
    """Create a UI Builder page with best practices"""
    with LogContext(logger, operation="create_ui_builder_page", env=env, dry_run=dry_run):
        client = _get_client(env)
        result = ui_builder_pack.create_ui_builder_page(client, name, title, description, scope, dry_run)
        return result

@mcp.tool()
def add_ui_builder_component(page_sys_id: str, component_type: str, component_id: str,
                           properties: Dict[str, Any], position: Dict[str, int] = None,
                           dry_run: bool = False, env: str = "dev"):
    """Add component to UI Builder page with validation"""
    with LogContext(logger, operation="add_ui_builder_component", env=env, dry_run=dry_run):
        client = _get_client(env)
        result = ui_builder_pack.add_ui_builder_component(
            client, page_sys_id, component_type, component_id, properties, position, dry_run
        )
        return result

@mcp.tool()
def validate_ui_builder_page(page_sys_id: str, env: str = "dev"):
    """Validate UI Builder page for best practices"""
    with LogContext(logger, operation="validate_ui_builder_page", env=env):
        client = _get_client(env)
        result = ui_builder_pack.validate_ui_builder_page(client, page_sys_id)
        return result

@mcp.tool()
def generate_ui_builder_template(page_type: str, table_name: str = None):
    """Generate UI Builder page template based on common patterns"""
    with LogContext(logger, operation="generate_ui_builder_template", page_type=page_type):
        result = ui_builder_pack.generate_ui_builder_template(page_type, table_name)
        return result

# ---- Scoped Application Management Tools ----
@mcp.tool()
def add_application_dependency(app_sys_id: str, dependency_scope: str, min_version: str = "1.0.0",
                             dry_run: bool = False, env: str = "dev"):
    """Add dependency to scoped application"""
    with LogContext(logger, operation="add_application_dependency", env=env, dry_run=dry_run):
        client = _get_client(env)
        result = scoped_app_pack.add_application_dependency(client, app_sys_id, dependency_scope, min_version, dry_run)
        return result

@mcp.tool()
def create_application_property(app_sys_id: str, name: str, value: str, description: str = "",
                              property_type: str = "string", dry_run: bool = False, env: str = "dev"):
    """Create application-specific system property"""
    with LogContext(logger, operation="create_application_property", env=env, dry_run=dry_run):
        client = _get_client(env)
        result = scoped_app_pack.create_application_property(client, app_sys_id, name, value, description, property_type, dry_run)
        return result

@mcp.tool()
def validate_application_structure(app_sys_id: str, env: str = "dev"):
    """Validate scoped application structure and best practices"""
    with LogContext(logger, operation="validate_application_structure", env=env):
        client = _get_client(env)
        result = scoped_app_pack.validate_application_structure(client, app_sys_id)
        return result

@mcp.tool()
def package_application(app_sys_id: str, include_data: bool = False, env: str = "dev"):
    """Package application for distribution"""
    with LogContext(logger, operation="package_application", env=env):
        client = _get_client(env)
        result = scoped_app_pack.package_application(client, app_sys_id, include_data)
        return result

@mcp.tool()
def audit_scoped_applications(env: str = "dev"):
    """Audit all scoped applications for best practices"""
    with LogContext(logger, operation="audit_scoped_applications", env=env):
        client = _get_client(env)
        result = scoped_app_pack.audit_scoped_applications(client)
        return result

@mcp.tool()
def create_table_with_navigation(app_sys_id: str, table_name: str, table_label: str, 
                               extends: str = None, create_navigation: bool = True, 
                               dry_run: bool = False, env: str = "dev"):
    """Create a table and automatically add navigation modules for it"""
    with LogContext(logger, operation="create_table_with_navigation", env=env, table_name=table_name, dry_run=dry_run):
        client = _get_client(env)
        result = scoped_app_pack.create_table_with_navigation(
            client, app_sys_id, table_name, table_label, extends, create_navigation, dry_run
        )
        return result

@mcp.tool()
def create_application_navigation_module(app_sys_id: str, title: str, link_type: str, 
                                       target: str = "", roles: str = None, order: int = 500,
                                       dry_run: bool = False, env: str = "dev"):
    """Create a custom navigation module for an application"""
    with LogContext(logger, operation="create_application_navigation_module", env=env, title=title, dry_run=dry_run):
        client = _get_client(env)
        result = scoped_app_pack.create_application_navigation_module(
            client, app_sys_id, title, link_type, target, roles, order, dry_run
        )
        return result

@mcp.tool()
@handle_errors("create_table_with_navigation_enhanced")
@validate_parameters(CreateTableWithNavigationParams)
def create_table_with_navigation_enhanced(
    table_label: str, 
    table_name: str, 
    extends: Optional[str] = None, 
    scope: str = DefaultValues.SCOPE, 
    create_navigation: bool = True,
    dry_run: bool = False, 
    env: str = DefaultValues.ENVIRONMENT
) -> Dict[str, Any]:
    """
    Create a ServiceNow table with enhanced navigation and duplicate prevention
    
    Args:
        table_label: Display label for the table
        table_name: Technical table name (must be alphanumeric with underscores)
        extends: Parent table to extend (optional)
        scope: Application scope (must start with 'x_' for custom scopes)
        create_navigation: Whether to create navigation module for the table
        dry_run: Preview changes without executing
        env: Environment (dev/test/prod)
        
    Returns:
        Dictionary containing creation results and metadata
    """
    with LogContext(logger, 
                   operation="create_table_with_navigation_enhanced", 
                   env=env, 
                   table=table_name, 
                   scope=scope, 
                   dry_run=dry_run,
                   create_navigation=create_navigation):
        
        c = _get_client(env)
        result = build_pack.create_table_with_navigation_enhanced(
            c, 
            table_label, 
            table_name, 
            extends=extends, 
            scope=scope, 
            create_navigation=create_navigation, 
            dry_run=dry_run
        )
        
        # Enhanced logging with more context
        action = "simulated" if dry_run else "created"
        nav_status = "with navigation" if create_navigation else "without navigation"
        logger.info(f"Enhanced table '{table_name}' {action} {nav_status} in scope '{scope}'")
        
        return result

# ---- Enhanced Scripted REST API Tools ----
@mcp.tool()
def create_scoped_rest_api(name: str, scope: str, version: str = "v1", description: str = "",
                         authentication: str = "none", base_path: str = None,
                         dry_run: bool = False, env: str = "dev"):
    """Create a scoped REST API with comprehensive best practices"""
    with LogContext(logger, operation="create_scoped_rest_api", env=env, scope=scope, dry_run=dry_run):
        client = _get_client(env)
        result = scripted_rest_api_pack.create_scoped_rest_api(
            client, name, scope, version, description, authentication, base_path, dry_run
        )
        return result

@mcp.tool()
def add_rest_resource(api_sys_id: str, http_method: str, relative_path: str, script: str,
                     description: str = "", request_schema: Dict[str, Any] = None,
                     response_schema: Dict[str, Any] = None, dry_run: bool = False, env: str = "dev"):
    """Add REST resource with comprehensive validation"""
    with LogContext(logger, operation="add_rest_resource", env=env, dry_run=dry_run):
        client = _get_client(env)
        result = scripted_rest_api_pack.add_rest_resource(
            client, api_sys_id, http_method, relative_path, script, description,
            request_schema, response_schema, dry_run
        )
        return result

@mcp.tool()
def generate_rest_script_template(http_method: str, resource_type: str = "item", table_name: str = None):
    """Generate REST script template based on method and resource type"""
    with LogContext(logger, operation="generate_rest_script_template", method=http_method):
        result = scripted_rest_api_pack.generate_rest_script_template(http_method, resource_type, table_name)
        return {"template": result, "method": http_method, "resource_type": resource_type}

@mcp.tool()
def validate_rest_api_setup(api_sys_id: str, env: str = "dev"):
    """Validate complete REST API setup for best practices"""
    with LogContext(logger, operation="validate_rest_api_setup", env=env):
        client = _get_client(env)
        result = scripted_rest_api_pack.validate_api_setup(client, api_sys_id)
        return result

@mcp.tool()
def generate_api_documentation(api_sys_id: str, env: str = "dev"):
    """Generate comprehensive API documentation"""
    with LogContext(logger, operation="generate_api_documentation", env=env):
        client = _get_client(env)
        result = scripted_rest_api_pack.generate_api_documentation(client, api_sys_id)
        return result

# ---- ServiceNow Documentation Tools ----
@mcp.tool()
def search_servicenow_documentation(topic: str, category: str = None, version: str = "latest"):
    """Search ServiceNow documentation for specific topics"""
    with LogContext(logger, operation="search_servicenow_documentation", topic=topic, category=category):
        result = servicenow_docs_pack.search_documentation(topic, category, version)
        return result

@mcp.tool()
def get_code_examples(api_name: str, method: str = None):
    """Get code examples for ServiceNow APIs"""
    with LogContext(logger, operation="get_code_examples", api=api_name, method=method):
        result = servicenow_docs_pack.get_code_examples(api_name, method)
        return result

@mcp.tool()
def get_troubleshooting_guide(error_type: str, context: str = None):
    """Get troubleshooting guide for common ServiceNow issues"""
    with LogContext(logger, operation="get_troubleshooting_guide", error_type=error_type):
        result = servicenow_docs_pack.get_troubleshooting_guide(error_type, context)
        return result

@mcp.tool()
def get_version_specific_info(feature: str, version: str = "latest"):
    """Get version-specific information about ServiceNow features"""
    with LogContext(logger, operation="get_version_specific_info", feature=feature, version=version):
        result = servicenow_docs_pack.get_version_specific_info(feature, version)
        return result

@mcp.tool()
def search_community_solutions(problem: str, category: str = None):
    """Search for community solutions and discussions"""
    with LogContext(logger, operation="search_community_solutions", problem=problem, category=category):
        result = servicenow_docs_pack.search_community_solutions(problem, category)
        return result

@mcp.tool()
def generate_learning_path(topic: str, skill_level: str = "beginner"):
    """Generate a learning path for ServiceNow topics"""
    with LogContext(logger, operation="generate_learning_path", topic=topic, skill_level=skill_level):
        result = servicenow_docs_pack.generate_learning_path(topic, skill_level)
        return result

# ---- Scoped Development Enforcement Tools ----
@mcp.tool()
def enforce_scoped_development(scope: str, env: str = "dev"):
    """Initialize scoped development enforcement"""
    with LogContext(logger, operation="enforce_scoped_development", env=env, scope=scope):
        client = _get_client(env)
        result = scoped_development_pack.enforce_scoped_development(client, scope)
        return result

@mcp.tool()
def validate_scoped_table_creation(table_name: str, scope: str, env: str = "dev"):
    """Validate table creation for scoped development"""
    with LogContext(logger, operation="validate_scoped_table_creation", env=env, table=table_name, scope=scope):
        client = _get_client(env)
        result = scoped_development_pack.validate_scoped_table_creation(client, table_name, scope)
        return result

@mcp.tool()
def validate_scoped_field_creation(table_name: str, field_name: str, scope: str, env: str = "dev"):
    """Validate field creation for scoped development"""
    with LogContext(logger, operation="validate_scoped_field_creation", env=env, table=table_name, scope=scope):
        client = _get_client(env)
        result = scoped_development_pack.validate_scoped_field_creation(client, table_name, field_name, scope)
        return result

@mcp.tool()
def audit_scoped_application(scope: str, env: str = "dev"):
    """Audit scoped application for compliance"""
    with LogContext(logger, operation="audit_scoped_application", env=env, scope=scope):
        client = _get_client(env)
        result = scoped_development_pack.audit_scoped_application(client, scope)
        return result

@mcp.tool()
def get_application_dependencies(scope: str, env: str = "dev"):
    """Get application dependencies"""
    with LogContext(logger, operation="get_application_dependencies", env=env, scope=scope):
        client = _get_client(env)
        result = scoped_development_pack.get_application_dependencies(client, scope)
        return result

@mcp.tool()
def generate_scoped_naming_suggestions(base_name: str, scope: str, object_type: str):
    """Generate naming suggestions for scoped objects"""
    with LogContext(logger, operation="generate_scoped_naming_suggestions", scope=scope, object_type=object_type):
        result = scoped_development_pack.generate_scoped_naming_suggestions(base_name, scope, object_type)
        return result

# ---- Background Script Execution Tools ----
@mcp.tool()
def execute_background_script(script: str, description: str = "", validate_safety: bool = True,
                            allow_dangerous: bool = False, dry_run: bool = False, env: str = "dev"):
    """Execute ServiceNow background script with safety validation"""
    with LogContext(logger, operation="execute_background_script", env=env, dry_run=dry_run):
        client = _get_client(env)
        result = background_script_pack.execute_background_script(
            client, script, description, validate_safety, allow_dangerous, dry_run
        )
        return result

@mcp.tool()
def validate_script_safety(script: str, allow_dangerous: bool = False):
    """Validate script safety before execution"""
    with LogContext(logger, operation="validate_script_safety"):
        result = background_script_pack.validate_script_safety(script, allow_dangerous)
        return result

@mcp.tool()
def get_script_templates():
    """Get common background script templates"""
    with LogContext(logger, operation="get_script_templates"):
        result = background_script_pack.get_script_templates()
        return {"templates": result, "available_templates": list(result.keys())}

@mcp.tool()
def analyze_script_performance(script: str):
    """Analyze script for potential performance issues"""
    with LogContext(logger, operation="analyze_script_performance"):
        result = background_script_pack.analyze_script_performance(script)
        return result

@mcp.tool()
def validate_script_syntax(script: str):
    """Validate JavaScript syntax of the script"""
    with LogContext(logger, operation="validate_script_syntax"):
        result = background_script_pack.validate_script_syntax(script)
        return result

@mcp.tool()
def get_script_execution_history(limit: int = 10, env: str = "dev"):
    """Get recent script execution history"""
    with LogContext(logger, operation="get_script_execution_history", env=env):
        client = _get_client(env)
        result = background_script_pack.get_execution_history(client, limit)
        return result

# ---- Enhanced Scripts Development Tools ----
@mcp.tool()
def create_client_script_comprehensive(table: str, name: str, ui_type: str, script: str,
                                     description: str = "", condition: str = "", field: str = "",
                                     scope: str = None, active: bool = True, dry_run: bool = False, env: str = "dev"):
    """Create comprehensive client script with full validation and proper scope handling"""
    with LogContext(logger, operation="create_client_script_comprehensive", env=env, table=table, ui_type=ui_type, dry_run=dry_run):
        client = _get_client(env)
        result = scripts_pack.create_client_script_comprehensive(
            client, table, name, ui_type, script, description, condition, field, scope, active, dry_run
        )
        return result

@mcp.tool()
def create_business_rule_comprehensive(table: str, name: str, when: str, rule_type: str, script: str,
                                     condition: str = "", description: str = "", 
                                     actions: Dict[str, bool] = None, order: int = 100,
                                     scope: str = None, active: bool = True, dry_run: bool = False, env: str = "dev"):
    """Create comprehensive business rule with proper scope handling and validation"""
    with LogContext(logger, operation="create_business_rule_comprehensive", env=env, table=table, rule_type=rule_type, dry_run=dry_run):
        client = _get_client(env)
        result = scripts_pack.create_business_rule_comprehensive(
            client, table, name, when, rule_type, script, condition, description, actions, order, scope, active, dry_run
        )
        return result

@mcp.tool()
def create_import_set_table(table_name: str, label: str, staging_table_name: str = None,
                          scope: str = None, dry_run: bool = False, env: str = "dev"):
    """Create import set staging table extending sys_import_set_row"""
    with LogContext(logger, operation="create_import_set_table", env=env, table=table_name, dry_run=dry_run):
        client = _get_client(env)
        result = data_pack.create_import_set_table(
            client, table_name, label, staging_table_name, scope, dry_run
        )
        return result

@mcp.tool()
def create_transform_map(name: str, source_table: str, target_table: str, description: str = "",
                       run_business_rules: bool = True, scope: str = None, dry_run: bool = False, env: str = "dev"):
    """Create transform map for import set processing"""
    with LogContext(logger, operation="create_transform_map", env=env, source_table=source_table, target_table=target_table, dry_run=dry_run):
        client = _get_client(env)
        result = data_pack.create_transform_map(
            client, name, source_table, target_table, description, run_business_rules, scope, dry_run
        )
        return result

@mcp.tool()
def create_field_mapping(transform_map_sys_id: str, source_field: str, target_field: str,
                       mapping_type: str = "direct", transform_script: str = "", default_value: str = "",
                       coalesce: bool = False, dry_run: bool = False, env: str = "dev"):
    """Create field mapping for transform map"""
    with LogContext(logger, operation="create_field_mapping", env=env, mapping_type=mapping_type, dry_run=dry_run):
        client = _get_client(env)
        result = data_pack.create_field_mapping(
            client, transform_map_sys_id, source_field, target_field, mapping_type, 
            transform_script, default_value, coalesce, dry_run
        )
        return result

@mcp.tool()
def create_robust_transform_map(name: str, source_table: str, target_table: str, 
                              field_mappings: List[Dict[str, Any]], description: str = "",
                              run_business_rules: bool = True, scope: str = None, 
                              dry_run: bool = False, env: str = "dev"):
    """Create complete transform map with field mappings"""
    with LogContext(logger, operation="create_robust_transform_map", env=env, mappings_count=len(field_mappings), dry_run=dry_run):
        client = _get_client(env)
        result = data_pack.create_robust_transform_map(
            client, name, source_table, target_table, field_mappings, description, 
            run_business_rules, scope, dry_run
        )
        return result

@mcp.tool()
def validate_import_set_configuration(source_table: str, target_table: str, env: str = "dev"):
    """Validate import set and transform map configuration"""
    with LogContext(logger, operation="validate_import_set_configuration", env=env, source_table=source_table, target_table=target_table):
        client = _get_client(env)
        result = data_pack.validate_import_set_configuration(client, source_table, target_table)
        return result

@mcp.tool()
def get_enhanced_script_templates():
    """Get comprehensive script templates for client scripts, business rules, and transform scripts"""
    with LogContext(logger, operation="get_enhanced_script_templates"):
        result = scripts_pack.generate_script_templates()
        return {
            "templates": result,
            "categories": list(result.keys()),
            "total_templates": sum(len(category) for category in result.values())
        }

# ---- Scripts Pack Tools ----
@mcp.tool()
def add_client_script(table: str, name: str, ui_type: str, script: str, scope: Optional[str] = None, dry_run: bool = False, env: str = "dev"):
    """Add client script with validation"""
    with LogContext(logger, operation="add_client_script", env=env, table=table, dry_run=dry_run):
        c = _get_client(env)
        result = scripts_pack.add_client_script(c, table, name, ui_type, script, scope, dry_run)
        logger.info(f"Client script {name} {'simulated' if dry_run else 'added'} to table {table}")
        return result

# ---- Table Pack Tools ----
@mcp.tool()
def batch_insert_records(table: str, records: List[Dict[str, Any]], dry_run: bool = False, env: str = "dev"):
    """Batch insert multiple records"""
    with LogContext(logger, operation="batch_insert_records", env=env, table=table, dry_run=dry_run):
        c = _get_client(env)
        result = table_pack.batch_insert_records(c, table, records, dry_run)
        logger.info(f"Batch insert {'simulated' if dry_run else 'completed'}: {len(records)} records to {table}")
        return result

@mcp.tool()
def batch_update_records(table: str, updates: List[Dict[str, Any]], id_field: str = "sys_id", dry_run: bool = False, env: str = "dev"):
    """Batch update multiple records"""
    with LogContext(logger, operation="batch_update_records", env=env, table=table, dry_run=dry_run):
        c = _get_client(env)
        result = table_pack.batch_update_records(c, table, updates, id_field, dry_run)
        logger.info(f"Batch update {'simulated' if dry_run else 'completed'}: {len(updates)} records in {table}")
        return result

# ---- Change Management Pack Tools ----
@mcp.tool()
def create_change_request(fields: Dict[str, Any], table: str = "change_request", dry_run: bool = False, env: str = "dev"):
    """Create change request"""
    with LogContext(logger, operation="create_change_request", env=env, table=table, dry_run=dry_run):
        c = _get_client(env)
        result = change_pack.create_change_request(c, fields, table, dry_run)
        logger.info(f"Change request {'simulated' if dry_run else 'created'}")
        return result

@mcp.tool()
def update_change_request(sys_id: str, fields: Dict[str, Any], table: str = "change_request", dry_run: bool = False, env: str = "dev"):
    """Update change request"""
    with LogContext(logger, operation="update_change_request", env=env, table=table, sys_id=sys_id, dry_run=dry_run):
        c = _get_client(env)
        result = change_pack.update_change_request(c, sys_id, fields, table, dry_run)
        logger.info(f"Change request {sys_id} {'simulated' if dry_run else 'updated'}")
        return result

@mcp.tool()
def get_change_request(sys_id: str, table: str = "change_request", env: str = "dev"):
    """Get change request details"""
    with LogContext(logger, operation="get_change_request", env=env, table=table, sys_id=sys_id):
        c = _get_client(env)
        result = change_pack.get_change_request(c, sys_id, table)
        logger.info(f"Retrieved change request {sys_id}")
        return result

@mcp.tool()
def approve_change_request(sys_id: str, approver_sys_id: Optional[str] = None, table: str = "change_request", dry_run: bool = False, env: str = "dev"):
    """Approve change request"""
    with LogContext(logger, operation="approve_change_request", env=env, table=table, sys_id=sys_id, dry_run=dry_run):
        c = _get_client(env)
        result = change_pack.approve_change_request(c, sys_id, approver_sys_id, table, dry_run)
        logger.info(f"Change request {sys_id} {'approval simulated' if dry_run else 'approved'}")
        return result

@mcp.tool()
def schedule_change_request(sys_id: str, start_date: str, end_date: str, table: str = "change_request", dry_run: bool = False, env: str = "dev"):
    """Schedule change request"""
    with LogContext(logger, operation="schedule_change_request", env=env, table=table, sys_id=sys_id, dry_run=dry_run):
        c = _get_client(env)
        result = change_pack.schedule_change_request(c, sys_id, start_date, end_date, table, dry_run)
        logger.info(f"Change request {sys_id} {'scheduling simulated' if dry_run else 'scheduled'}")
        return result

# ---- Problem Management Pack Tools ----
@mcp.tool()
def create_problem(fields: Dict[str, Any], table: str = "problem", dry_run: bool = False, env: str = "dev"):
    """Create problem record"""
    with LogContext(logger, operation="create_problem", env=env, table=table, dry_run=dry_run):
        c = _get_client(env)
        result = problem_pack.create_problem(c, fields, table, dry_run)
        logger.info(f"Problem {'simulated' if dry_run else 'created'}")
        return result

@mcp.tool()
def update_problem(sys_id: str, fields: Dict[str, Any], table: str = "problem", dry_run: bool = False, env: str = "dev"):
    """Update problem record"""
    with LogContext(logger, operation="update_problem", env=env, table=table, sys_id=sys_id, dry_run=dry_run):
        c = _get_client(env)
        result = problem_pack.update_problem(c, sys_id, fields, table, dry_run)
        logger.info(f"Problem {sys_id} {'simulated' if dry_run else 'updated'}")
        return result

@mcp.tool()
def link_incident_to_problem(incident_sys_id: str, problem_sys_id: str, incident_table: str = "incident", dry_run: bool = False, env: str = "dev"):
    """Link incident to problem"""
    with LogContext(logger, operation="link_incident_to_problem", env=env, incident_id=incident_sys_id, problem_id=problem_sys_id, dry_run=dry_run):
        c = _get_client(env)
        result = problem_pack.link_incident_to_problem(c, incident_sys_id, problem_sys_id, incident_table, dry_run)
        logger.info(f"Incident {incident_sys_id} {'link simulated' if dry_run else 'linked'} to problem {problem_sys_id}")
        return result

@mcp.tool()
def create_known_error(problem_sys_id: str, workaround: str, table: str = "known_error", dry_run: bool = False, env: str = "dev"):
    """Create known error record"""
    with LogContext(logger, operation="create_known_error", env=env, table=table, problem_id=problem_sys_id, dry_run=dry_run):
        c = _get_client(env)
        result = problem_pack.create_known_error(c, problem_sys_id, workaround, table, dry_run)
        logger.info(f"Known error {'simulated' if dry_run else 'created'} for problem {problem_sys_id}")
        return result

# ---- User Management Pack Tools ----
@mcp.tool()
def create_user(fields: Dict[str, Any], table: str = "sys_user", dry_run: bool = False, env: str = "dev"):
    """Create user account"""
    with LogContext(logger, operation="create_user", env=env, table=table, dry_run=dry_run):
        c = _get_client(env)
        result = user_pack.create_user(c, fields, table, dry_run)
        logger.info(f"User {'simulated' if dry_run else 'created'}")
        return result

@mcp.tool()
def update_user(sys_id: str, fields: Dict[str, Any], table: str = "sys_user", dry_run: bool = False, env: str = "dev"):
    """Update user information"""
    with LogContext(logger, operation="update_user", env=env, table=table, sys_id=sys_id, dry_run=dry_run):
        c = _get_client(env)
        result = user_pack.update_user(c, sys_id, fields, table, dry_run)
        logger.info(f"User {sys_id} {'simulated' if dry_run else 'updated'}")
        return result

@mcp.tool()
def get_user(sys_id: str, table: str = "sys_user", env: str = "dev"):
    """Get user details"""
    with LogContext(logger, operation="get_user", env=env, table=table, sys_id=sys_id):
        c = _get_client(env)
        result = user_pack.get_user(c, sys_id, table)
        logger.info(f"Retrieved user {sys_id}")
        return result

@mcp.tool()
def get_user_by_email(email: str, table: str = "sys_user", env: str = "dev"):
    """Find user by email address"""
    with LogContext(logger, operation="get_user_by_email", env=env, table=table, email=email):
        c = _get_client(env)
        result = user_pack.get_user_by_email(c, email, table)
        logger.info(f"Searched for user by email: {email}")
        return result

@mcp.tool()
def create_group(fields: Dict[str, Any], table: str = "sys_user_group", dry_run: bool = False, env: str = "dev"):
    """Create user group"""
    with LogContext(logger, operation="create_group", env=env, table=table, dry_run=dry_run):
        c = _get_client(env)
        result = user_pack.create_group(c, fields, table, dry_run)
        logger.info(f"Group {'simulated' if dry_run else 'created'}")
        return result

@mcp.tool()
def add_user_to_group(user_sys_id: str, group_sys_id: str, table: str = "sys_user_grmember", dry_run: bool = False, env: str = "dev"):
    """Add user to group"""
    with LogContext(logger, operation="add_user_to_group", env=env, table=table, user_id=user_sys_id, group_id=group_sys_id, dry_run=dry_run):
        c = _get_client(env)
        result = user_pack.add_user_to_group(c, user_sys_id, group_sys_id, table, dry_run)
        logger.info(f"User {user_sys_id} {'addition simulated' if dry_run else 'added'} to group {group_sys_id}")
        return result

@mcp.tool()
def get_group_members(group_sys_id: str, table: str = "sys_user_grmember", env: str = "dev"):
    """Get group members"""
    with LogContext(logger, operation="get_group_members", env=env, table=table, group_id=group_sys_id):
        c = _get_client(env)
        result = user_pack.get_group_members(c, group_sys_id, table)
        logger.info(f"Retrieved members for group {group_sys_id}")
        return result

# ---- Flow Designer Pack Tools ----
@mcp.tool()
def create_flow(name: str, description: str = "", table: str = "sys_hub_flow", dry_run: bool = False, env: str = "dev"):
    """Create Flow Designer flow"""
    with LogContext(logger, operation="create_flow", env=env, table=table, flow_name=name, dry_run=dry_run):
        c = _get_client(env)
        result = flow_pack.create_flow(c, name, description, table, dry_run)
        logger.info(f"Flow {name} {'simulated' if dry_run else 'created'}")
        return result

@mcp.tool()
def add_flow_trigger_record_change(flow_sys_id: str, table_name: str, operation: str = "insert", table: str = "sys_hub_trigger", dry_run: bool = False, env: str = "dev"):
    """Add record change trigger to flow"""
    with LogContext(logger, operation="add_flow_trigger_record_change", env=env, table=table, flow_id=flow_sys_id, trigger_table=table_name, dry_run=dry_run):
        c = _get_client(env)
        result = flow_pack.add_flow_trigger_record_change(c, flow_sys_id, table_name, operation, table, dry_run)
        logger.info(f"Record change trigger {'simulated' if dry_run else 'added'} to flow {flow_sys_id}")
        return result

@mcp.tool()
def activate_flow(flow_sys_id: str, active: bool = True, table: str = "sys_hub_flow", dry_run: bool = False, env: str = "dev"):
    """Activate or deactivate flow"""
    with LogContext(logger, operation="activate_flow", env=env, table=table, flow_id=flow_sys_id, active=active, dry_run=dry_run):
        c = _get_client(env)
        result = flow_pack.activate_flow(c, flow_sys_id, active, table, dry_run)
        logger.info(f"Flow {flow_sys_id} {'activation simulated' if dry_run else ('activated' if active else 'deactivated')}")
        return result

# ---- Update Set Pack Tools ----
@mcp.tool()
def create_update_set(name: str, description: str = "", application: Optional[str] = None, state: str = "in progress", table: str = "sys_update_set", dry_run: bool = False, env: str = "dev"):
    """Create update set"""
    with LogContext(logger, operation="create_update_set", env=env, table=table, name=name, dry_run=dry_run):
        c = _get_client(env)
        result = update_set_pack.create_update_set(c, name, description, application, state, table, dry_run)
        logger.info(f"Update set {name} {'simulated' if dry_run else 'created'}")
        return result

@mcp.tool()
def close_update_set(sys_id: str, table: str = "sys_update_set", dry_run: bool = False, env: str = "dev"):
    """Close update set"""
    with LogContext(logger, operation="close_update_set", env=env, table=table, sys_id=sys_id, dry_run=dry_run):
        c = _get_client(env)
        result = update_set_pack.close_update_set(c, sys_id, table, dry_run)
        logger.info(f"Update set {sys_id} {'close simulated' if dry_run else 'closed'}")
        return result

# ---- Attachment Pack Tools ----
@mcp.tool()
def upload_attachment(table: str, sys_id: str, file_path: str, file_name: str = "", env: str = "dev"):
    """Upload file attachment"""
    with LogContext(logger, operation="upload_attachment", env=env, table=table, sys_id=sys_id, file_path=file_path):
        c = _get_client(env)
        result = attachment_pack.upload_attachment(c, table, sys_id, file_path, file_name)
        logger.info(f"Attachment uploaded to {table} record {sys_id}")
        return result

@mcp.tool()
def list_attachments(table: str, sys_id: str, limit: int = 50, env: str = "dev"):
    """List record attachments"""
    with LogContext(logger, operation="list_attachments", env=env, table=table, sys_id=sys_id):
        c = _get_client(env)
        result = attachment_pack.list_attachments(c, table, sys_id, limit)
        logger.info(f"Listed attachments for {table} record {sys_id}")
        return result

@mcp.tool()
def download_attachment(attachment_sys_id: str, out_path: str, env: str = "dev"):
    """Download attachment"""
    with LogContext(logger, operation="download_attachment", env=env, attachment_id=attachment_sys_id, out_path=out_path):
        c = _get_client(env)
        result = attachment_pack.download_attachment(c, attachment_sys_id, out_path)
        logger.info(f"Downloaded attachment {attachment_sys_id} to {out_path}")
        return result

@mcp.tool()
def delete_attachment(attachment_sys_id: str, table: str = "sys_attachment", env: str = "dev"):
    """Delete attachment"""
    with LogContext(logger, operation="delete_attachment", env=env, table=table, attachment_id=attachment_sys_id):
        c = _get_client(env)
        result = attachment_pack.delete_attachment(c, attachment_sys_id, table)
        logger.info(f"Deleted attachment {attachment_sys_id}")
        return result

# ---- CMDB Pack Tools ----
@mcp.tool()
def cmdb_health_snapshot(classes: Optional[List[str]] = None, limit: int = 50, env: str = "dev"):
    """Get CMDB health snapshot"""
    with LogContext(logger, operation="cmdb_health_snapshot", env=env, classes=classes):
        c = _get_client(env)
        result = cmdb_pack.cmdb_health_snapshot(c, classes, limit)
        logger.info(f"Generated CMDB health snapshot")
        return result

@mcp.tool()
def servicemap_seed(app_name: str, entry_point: str, table: str = "svc_map_seed", dry_run: bool = False, env: str = "dev"):
    """Create service map seed"""
    with LogContext(logger, operation="servicemap_seed", env=env, table=table, app_name=app_name, dry_run=dry_run):
        c = _get_client(env)
        result = cmdb_pack.servicemap_seed(c, app_name, entry_point, table, dry_run)
        logger.info(f"Service map seed {app_name} {'simulated' if dry_run else 'created'}")
        return result

@mcp.tool()
def impact_rule_add(service_sys_id: str, related_ci: str, relation_type: str = "Depends on::Used by", table: str = "svc_impact_rule", dry_run: bool = False, env: str = "dev"):
    """Add impact rule"""
    with LogContext(logger, operation="impact_rule_add", env=env, table=table, service_id=service_sys_id, ci=related_ci, dry_run=dry_run):
        c = _get_client(env)
        result = cmdb_pack.impact_rule_add(c, service_sys_id, related_ci, relation_type, table, dry_run)
        logger.info(f"Impact rule {'simulated' if dry_run else 'added'} for service {service_sys_id}")
        return result

# ---- Data Pack Tools ----
@mcp.tool()
def create_data_source_jdbc(name: str, connection_url: str, username: str, password: str, target_table: Optional[str] = None, jdbc_driver: Optional[str] = None, table: str = "sys_data_source", dry_run: bool = False, env: str = "dev"):
    """Create JDBC data source"""
    with LogContext(logger, operation="create_data_source_jdbc", env=env, table=table, name=name, dry_run=dry_run):
        c = _get_client(env)
        result = data_pack.create_data_source_jdbc(c, name, connection_url, username, password, target_table, jdbc_driver, table, dry_run)
        logger.info(f"JDBC data source {name} {'simulated' if dry_run else 'created'}")
        return result

@mcp.tool()
def create_import_set(name: str, data_source: str, table: str = "sys_import_set", dry_run: bool = False, env: str = "dev"):
    """Create import set"""
    with LogContext(logger, operation="create_import_set", env=env, table=table, name=name, dry_run=dry_run):
        c = _get_client(env)
        result = data_pack.create_import_set(c, name, data_source, table, dry_run)
        logger.info(f"Import set {name} {'simulated' if dry_run else 'created'}")
        return result

# ---- Discovery Pack Tools ----
@mcp.tool()
def quick_discovery(name: str, ips: List[str], mid_server: Optional[str] = None, schedule_table: str = "discovery_schedule", dry_run: bool = False, env: str = "dev"):
    """Run quick discovery"""
    with LogContext(logger, operation="quick_discovery", env=env, table=schedule_table, name=name, ips=ips, dry_run=dry_run):
        c = _get_client(env)
        result = discovery_pack.quick_discovery(c, name, ips, mid_server, schedule_table, dry_run)
        logger.info(f"Quick discovery {name} {'simulated' if dry_run else 'created'} for {len(ips)} IPs")
        return result

@mcp.tool()
def discovery_status(limit: int = 50, env: str = "dev"):
    """Get discovery status"""
    with LogContext(logger, operation="discovery_status", env=env):
        c = _get_client(env)
        result = discovery_pack.discovery_status(c, limit)
        logger.info(f"Retrieved discovery status")
        return result

# ---- ITAM Pack Tools ----
@mcp.tool()
def asset_receive(model: str, asset_tag: str, location: Optional[str] = None, stockroom: Optional[str] = None, cost: Optional[float] = None, table: str = "alm_asset", dry_run: bool = False, env: str = "dev"):
    """Receive asset into inventory"""
    with LogContext(logger, operation="asset_receive", env=env, table=table, asset_tag=asset_tag, dry_run=dry_run):
        c = _get_client(env)
        result = itam_pack.asset_receive(c, model, asset_tag, location, stockroom, cost, table, dry_run)
        logger.info(f"Asset {asset_tag} {'receipt simulated' if dry_run else 'received'}")
        return result

@mcp.tool()
def asset_transfer(asset_sys_id: str, stockroom_to: str, table: str = "alm_asset", dry_run: bool = False, env: str = "dev"):
    """Transfer asset between locations"""
    with LogContext(logger, operation="asset_transfer", env=env, table=table, asset_id=asset_sys_id, destination=stockroom_to, dry_run=dry_run):
        c = _get_client(env)
        result = itam_pack.asset_transfer(c, asset_sys_id, stockroom_to, table, dry_run)
        logger.info(f"Asset {asset_sys_id} {'transfer simulated' if dry_run else 'transferred'} to {stockroom_to}")
        return result

@mcp.tool()
def asset_retire(asset_sys_id: str, table: str = "alm_asset", dry_run: bool = False, env: str = "dev"):
    """Retire asset"""
    with LogContext(logger, operation="asset_retire", env=env, table=table, asset_id=asset_sys_id, dry_run=dry_run):
        c = _get_client(env)
        result = itam_pack.asset_retire(c, asset_sys_id, table, dry_run)
        logger.info(f"Asset {asset_sys_id} {'retirement simulated' if dry_run else 'retired'}")
        return result

# ---- ATF Pack Tools ----
@mcp.tool()
def create_test_suite(name: str, description: str = "", table: str = "sys_atf_test_suite", dry_run: bool = False, env: str = "dev"):
    """Create ATF test suite"""
    with LogContext(logger, operation="create_test_suite", env=env, table=table, name=name, dry_run=dry_run):
        c = _get_client(env)
        result = atf_pack.create_test_suite(c, name, description, table, dry_run)
        logger.info(f"Test suite {name} {'simulated' if dry_run else 'created'}")
        return result

@mcp.tool()
def create_ui_form_test(suite_sys_id: str, table_name: str, test_name: str, table: str = "sys_atf_test", dry_run: bool = False, env: str = "dev"):
    """Create UI form test"""
    with LogContext(logger, operation="create_ui_form_test", env=env, table=table, suite_id=suite_sys_id, test_name=test_name, dry_run=dry_run):
        c = _get_client(env)
        result = atf_pack.create_ui_form_test(c, suite_sys_id, table_name, test_name, table, dry_run)
        logger.info(f"UI form test {test_name} {'simulated' if dry_run else 'created'}")
        return result

# ---- Additional Scoped App Pack Tools ----
@mcp.tool()
def create_application_file(app_sys_id: str, name: str, content: str, file_type: str = "script_include", dry_run: bool = False, env: str = "dev"):
    """Create application file"""
    with LogContext(logger, operation="create_application_file", env=env, app_id=app_sys_id, file_name=name, file_type=file_type, dry_run=dry_run):
        c = _get_client(env)
        result = scoped_app_pack.create_application_file(c, app_sys_id, name, content, file_type, dry_run)
        logger.info(f"Application file {name} ({file_type}) {'simulated' if dry_run else 'created'} for app {app_sys_id}")
        return result

# ---- Additional Best Practices Pack Tools ----
@mcp.tool()
def validate_mandatory_fields(table_name: str, fields: List[Dict[str, Any]]):
    """Validate mandatory fields"""
    with LogContext(logger, operation="validate_mandatory_fields", table=table_name):
        result = best_practices_pack.validate_mandatory_fields(table_name, fields)
        logger.info(f"Validated mandatory fields for table {table_name}")
        return result

@mcp.tool()
def validate_security_best_practices(script: str, context: str = 'server'):
    """Validate security best practices"""
    with LogContext(logger, operation="validate_security_best_practices", context=context):
        result = best_practices_pack.validate_security_best_practices(script, context)
        logger.info(f"Validated security best practices for {context} script")
        return result

@mcp.tool()
def validate_performance_best_practices(script: str):
    """Validate performance best practices"""
    with LogContext(logger, operation="validate_performance_best_practices"):
        result = best_practices_pack.validate_performance_best_practices(script)
        logger.info(f"Validated performance best practices")
        return result

@mcp.tool()
def create_field_with_validation(table_name: str, field_name: str, field_type: str, label: str, mandatory: bool = False, scope: Optional[str] = None, dry_run: bool = False, env: str = "dev"):
    """Create field with validation"""
    with LogContext(logger, operation="create_field_with_validation", env=env, table=table_name, field_name=field_name, dry_run=dry_run):
        c = _get_client(env)
        result = best_practices_pack.create_field_with_validation(c, table_name, field_name, field_type, label, mandatory, scope, dry_run)
        logger.info(f"Field {field_name} {'simulated' if dry_run else 'created'} on table {table_name}")
        return result

@mcp.tool()
def create_business_rule_with_validation(table_name: str, name: str, when: str, script: str, condition: str = "", scope: Optional[str] = None, dry_run: bool = False, env: str = "dev"):
    """Create business rule with validation"""
    with LogContext(logger, operation="create_business_rule_with_validation", env=env, table=table_name, rule_name=name, dry_run=dry_run):
        c = _get_client(env)
        result = best_practices_pack.create_business_rule_with_validation(c, table_name, name, when, script, condition, scope, dry_run)
        logger.info(f"Business rule {name} {'simulated' if dry_run else 'created'} for table {table_name}")
        return result

# ---- Scripted REST Pack Tools ----
@mcp.tool()
def create_scripted_rest_api(name: str, base_path: str, active: bool = True, table: str = "sys_ws_definition", dry_run: bool = False, env: str = "dev"):
    """Create scripted REST API"""
    with LogContext(logger, operation="create_scripted_rest_api", env=env, table=table, name=name, dry_run=dry_run):
        c = _get_client(env)
        result = scripted_rest_pack.create_scripted_rest_api(c, name, base_path, active, table, dry_run)
        logger.info(f"Scripted REST API {name} {'simulated' if dry_run else 'created'}")
        return result

@mcp.tool()
def add_scripted_rest_resource(api_sys_id: str, verb: str, relative_path: str, script: str, table: str = "sys_ws_operation", dry_run: bool = False, env: str = "dev"):
    """Add scripted REST resource"""
    with LogContext(logger, operation="add_scripted_rest_resource", env=env, table=table, api_id=api_sys_id, verb=verb, dry_run=dry_run):
        c = _get_client(env)
        result = scripted_rest_pack.add_scripted_rest_resource(c, api_sys_id, verb, relative_path, script, table, dry_run)
        logger.info(f"REST resource {verb} {relative_path} {'simulated' if dry_run else 'added'} to API {api_sys_id}")
        return result

# ---- ITOM Pack Tools ---- (NEW: Complete IT Operations Management)
@mcp.tool()
def create_discovery_schedule(name: str, target_ranges: List[str], discovery_types: List[str] = None, schedule: str = "daily", active: bool = True, credentials: List[str] = None, env: str = "dev"):
    """Create new discovery schedule for infrastructure discovery"""
    with LogContext(logger, operation="create_discovery_schedule", env=env, name=name, targets=len(target_ranges)):
        c = _get_client(env)
        result = itom_pack.create_discovery_schedule(c, name, target_ranges, discovery_types, schedule, active, credentials, env)
        logger.info(f"Discovery schedule '{name}' created with {len(target_ranges)} target ranges")
        return result

@mcp.tool()
def update_discovery_schedule(schedule_sys_id: str, updates: Dict[str, Any], env: str = "dev"):
    """Update existing discovery schedule - most common real-world operation"""
    with LogContext(logger, operation="update_discovery_schedule", env=env, schedule_id=schedule_sys_id):
        c = _get_client(env)
        result = itom_pack.update_discovery_schedule(c, schedule_sys_id, updates, env)
        logger.info(f"Discovery schedule {schedule_sys_id} updated: {list(updates.keys())}")
        return result

@mcp.tool()
def modify_discovery_pattern(pattern_sys_id: str, pattern_updates: Dict[str, Any], env: str = "dev"):
    """Modify existing discovery pattern - critical for discovery accuracy"""
    with LogContext(logger, operation="modify_discovery_pattern", env=env, pattern_id=pattern_sys_id):
        c = _get_client(env)
        result = itom_pack.modify_discovery_pattern(c, pattern_sys_id, pattern_updates, env)
        logger.info(f"Discovery pattern {pattern_sys_id} modified: {list(pattern_updates.keys())}")
        return result

@mcp.tool()
def manage_discovery_credentials(action: str, credential_data: Dict[str, Any], credential_sys_id: str = None, env: str = "dev"):
    """Comprehensive discovery credentials management (create, update, test, rotate)"""
    with LogContext(logger, operation="manage_discovery_credentials", env=env, action=action, credential_id=credential_sys_id):
        c = _get_client(env)
        result = itom_pack.manage_discovery_credentials(c, action, credential_data, credential_sys_id, env)
        logger.info(f"Discovery credentials {action} operation completed")
        return result

@mcp.tool()
def create_service_mapping(service_name: str, entry_points: List[Dict[str, Any]], mapping_patterns: List[Dict[str, Any]] = None, auto_discovery: bool = True, env: str = "dev"):
    """Create new service mapping for business service discovery"""
    with LogContext(logger, operation="create_service_mapping", env=env, service=service_name, entry_points=len(entry_points)):
        c = _get_client(env)
        result = itom_pack.create_service_mapping(c, service_name, entry_points, mapping_patterns, auto_discovery, env)
        logger.info(f"Service mapping '{service_name}' created with {len(entry_points)} entry points")
        return result

@mcp.tool()
def update_service_mapping(mapping_sys_id: str, updates: Dict[str, Any], update_entry_points: bool = False, update_patterns: bool = False, env: str = "dev"):
    """Update existing service mapping - common maintenance task"""
    with LogContext(logger, operation="update_service_mapping", env=env, mapping_id=mapping_sys_id):
        c = _get_client(env)
        result = itom_pack.update_service_mapping(c, mapping_sys_id, updates, update_entry_points, update_patterns, env)
        logger.info(f"Service mapping {mapping_sys_id} updated")
        return result

@mcp.tool()
def validate_service_mapping(mapping_sys_id: str, run_discovery_test: bool = True, env: str = "dev"):
    """Validate service mapping configuration and test discovery"""
    with LogContext(logger, operation="validate_service_mapping", env=env, mapping_id=mapping_sys_id):
        c = _get_client(env)
        result = itom_pack.validate_service_mapping(c, mapping_sys_id, run_discovery_test, env)
        logger.info(f"Service mapping {mapping_sys_id} validation completed")
        return result

@mcp.tool()
def configure_event_correlation_rule(rule_name: str, correlation_logic: Dict[str, Any], action: str = "create", rule_sys_id: str = None, env: str = "dev"):
    """Configure event correlation rules for intelligent alerting"""
    with LogContext(logger, operation="configure_event_correlation_rule", env=env, rule_name=rule_name, action=action):
        c = _get_client(env)
        result = itom_pack.configure_event_correlation_rule(c, rule_name, correlation_logic, action, rule_sys_id, env)
        logger.info(f"Event correlation rule '{rule_name}' {action} operation completed")
        return result

@mcp.tool()
def manage_event_policies(policy_action: str, policy_data: Dict[str, Any], policy_sys_id: str = None, env: str = "dev"):
    """Comprehensive event policy management (create, update, activate, deactivate)"""
    with LogContext(logger, operation="manage_event_policies", env=env, action=policy_action, policy_id=policy_sys_id):
        c = _get_client(env)
        result = itom_pack.manage_event_policies(c, policy_action, policy_data, policy_sys_id, env)
        logger.info(f"Event policy {policy_action} operation completed")
        return result

@mcp.tool()
def itom_p1_infrastructure_war_room(incident_sys_id: str, affected_cis: List[str], create_bridge: bool = True, notify_stakeholders: bool = True, env: str = "dev"):
    """P1: Create infrastructure war room for critical incidents"""
    with LogContext(logger, operation="itom_p1_infrastructure_war_room", env=env, incident_id=incident_sys_id, affected_cis=len(affected_cis)):
        c = _get_client(env)
        result = itom_pack.itom_p1_infrastructure_war_room(c, incident_sys_id, affected_cis, create_bridge, notify_stakeholders, env)
        logger.info(f"P1 infrastructure war room activated for incident {incident_sys_id}")
        return result

@mcp.tool()
def itom_p1_service_dependency_analysis(affected_service_sys_id: str, analysis_depth: int = 3, include_business_impact: bool = True, env: str = "dev"):
    """P1: Deep service dependency analysis for infrastructure incidents"""
    with LogContext(logger, operation="itom_p1_service_dependency_analysis", env=env, service_id=affected_service_sys_id, depth=analysis_depth):
        c = _get_client(env)
        result = itom_pack.itom_p1_service_dependency_analysis(c, affected_service_sys_id, analysis_depth, include_business_impact, env)
        logger.info(f"P1 service dependency analysis completed for service {affected_service_sys_id}")
        return result

# ---- CSM Pack Tools ---- (NEW: Complete Customer Service Management)
@mcp.tool()
def create_customer_case(customer_account: str, contact_sys_id: str, subject: str, description: str, priority: str = "moderate", category: str = None, subcategory: str = None, product: str = None, additional_fields: Dict[str, Any] = None, env: str = "dev"):
    """Create customer service case with intelligent routing"""
    with LogContext(logger, operation="create_customer_case", env=env, customer=customer_account, priority=priority):
        c = _get_client(env)
        result = csm_pack.create_customer_case(c, customer_account, contact_sys_id, subject, description, priority, category, subcategory, product, additional_fields, env)
        logger.info(f"Customer case created: {result.get('case', {}).get('number', 'N/A')}")
        return result

@mcp.tool()
def update_customer_case(case_sys_id: str, updates: Dict[str, Any], add_work_notes: bool = True, notify_customer: bool = False, env: str = "dev"):
    """Update existing customer case - most common CSM operation"""
    with LogContext(logger, operation="update_customer_case", env=env, case_id=case_sys_id):
        c = _get_client(env)
        result = csm_pack.update_customer_case(c, case_sys_id, updates, add_work_notes, notify_customer, env)
        logger.info(f"Customer case updated: {list(updates.keys())}")
        return result

@mcp.tool()
def route_customer_case(case_sys_id: str, routing_criteria: Dict[str, Any], routing_reason: str = None, preserve_history: bool = True, env: str = "dev"):
    """Route customer case to appropriate team/agent based on criteria"""
    with LogContext(logger, operation="route_customer_case", env=env, case_id=case_sys_id):
        c = _get_client(env)
        result = csm_pack.route_customer_case(c, case_sys_id, routing_criteria, routing_reason, preserve_history, env)
        logger.info(f"Customer case routed: {result.get('routing_result', {}).get('assignment_group', 'N/A')}")
        return result

@mcp.tool()
def escalate_customer_case(case_sys_id: str, escalation_type: str, escalation_reason: str, target_group: str = None, target_manager: str = None, escalation_level: int = 1, env: str = "dev"):
    """Escalate customer case with proper tracking and notification"""
    with LogContext(logger, operation="escalate_customer_case", env=env, case_id=case_sys_id, escalation_type=escalation_type, level=escalation_level):
        c = _get_client(env)
        result = csm_pack.escalate_customer_case(c, case_sys_id, escalation_type, escalation_reason, target_group, target_manager, escalation_level, env)
        logger.info(f"Customer case escalated to level {escalation_level}")
        return result

@mcp.tool()
def create_knowledge_article(title: str, short_description: str, text: str, knowledge_base: str = "IT", category: str = None, workflow: str = "published", tags: List[str] = None, related_articles: List[str] = None, env: str = "dev"):
    """Create knowledge article with proper categorization"""
    with LogContext(logger, operation="create_knowledge_article", env=env, title=title, kb=knowledge_base):
        c = _get_client(env)
        result = csm_pack.create_knowledge_article(c, title, short_description, text, knowledge_base, category, workflow, tags, related_articles, env)
        logger.info(f"Knowledge article created: {title}")
        return result

@mcp.tool()
def update_knowledge_article(article_sys_id: str, updates: Dict[str, Any], update_version: bool = True, preserve_feedback: bool = True, env: str = "dev"):
    """Update existing knowledge article - common knowledge management task"""
    with LogContext(logger, operation="update_knowledge_article", env=env, article_id=article_sys_id):
        c = _get_client(env)
        result = csm_pack.update_knowledge_article(c, article_sys_id, updates, update_version, preserve_feedback, env)
        logger.info(f"Knowledge article updated: {list(updates.keys())}")
        return result

@mcp.tool()
def search_knowledge_articles(search_query: str, knowledge_base: str = None, category: str = None, tags: List[str] = None, max_results: int = 10, include_analytics: bool = False, env: str = "dev"):
    """Search knowledge articles with advanced filtering and analytics"""
    with LogContext(logger, operation="search_knowledge_articles", env=env, query=search_query, max_results=max_results):
        c = _get_client(env)
        result = csm_pack.search_knowledge_articles(c, search_query, knowledge_base, category, tags, max_results, include_analytics, env)
        logger.info(f"Knowledge search completed: {result.get('articles_found', 0)} articles found")
        return result

@mcp.tool()
def analyze_knowledge_usage(article_sys_id: str = None, knowledge_base: str = None, time_period_days: int = 30, include_feedback: bool = True, env: str = "dev"):
    """Analyze knowledge article usage patterns and effectiveness"""
    with LogContext(logger, operation="analyze_knowledge_usage", env=env, article_id=article_sys_id, kb=knowledge_base, period=time_period_days):
        c = _get_client(env)
        result = csm_pack.analyze_knowledge_usage(c, article_sys_id, knowledge_base, time_period_days, include_feedback, env)
        logger.info(f"Knowledge usage analysis completed for {time_period_days} day period")
        return result

@mcp.tool()
def optimize_customer_portal(portal_sys_id: str, optimization_areas: List[str], run_analysis: bool = True, apply_recommendations: bool = False, env: str = "dev"):
    """Optimize customer portal experience with analytics-driven recommendations"""
    with LogContext(logger, operation="optimize_customer_portal", env=env, portal_id=portal_sys_id, areas=len(optimization_areas)):
        c = _get_client(env)
        result = csm_pack.optimize_customer_portal(c, portal_sys_id, optimization_areas, run_analysis, apply_recommendations, env)
        logger.info(f"Portal optimization completed for {len(optimization_areas)} areas")
        return result

@mcp.tool()
def analyze_customer_sentiment(customer_sys_id: str = None, case_sys_id: str = None, time_period_days: int = 30, include_prediction: bool = True, sentiment_sources: List[str] = None, env: str = "dev"):
    """Analyze customer sentiment across multiple touchpoints"""
    with LogContext(logger, operation="analyze_customer_sentiment", env=env, customer_id=customer_sys_id, case_id=case_sys_id, period=time_period_days):
        c = _get_client(env)
        result = csm_pack.analyze_customer_sentiment(c, customer_sys_id, case_sys_id, time_period_days, include_prediction, sentiment_sources, env)
        logger.info(f"Customer sentiment analysis completed across {len(sentiment_sources or [])} sources")
        return result

@mcp.tool()
def csm_p1_customer_crisis_response(crisis_type: str, affected_customers: List[str], crisis_description: str, severity_level: int = 1, create_war_room: bool = True, auto_notify: bool = True, env: str = "dev"):
    """P1: Activate customer crisis response for major service disruptions"""
    with LogContext(logger, operation="csm_p1_customer_crisis_response", env=env, crisis_type=crisis_type, affected_count=len(affected_customers), severity=severity_level):
        c = _get_client(env)
        result = csm_pack.csm_p1_customer_crisis_response(c, crisis_type, affected_customers, crisis_description, severity_level, create_war_room, auto_notify, env)
        logger.info(f"P1 customer crisis response activated: {crisis_type} affecting {len(affected_customers)} customers")
        return result

@mcp.tool()
def csm_p1_vip_customer_escalation(customer_account_sys_id: str, escalation_reason: str, impact_assessment: Dict[str, Any], immediate_actions: List[str], notify_executives: bool = True, env: str = "dev"):
    """P1: Emergency escalation protocol for VIP customers"""
    with LogContext(logger, operation="csm_p1_vip_customer_escalation", env=env, customer_id=customer_account_sys_id, actions_count=len(immediate_actions)):
        c = _get_client(env)
        result = csm_pack.csm_p1_vip_customer_escalation(c, customer_account_sys_id, escalation_reason, impact_assessment, immediate_actions, notify_executives, env)
        logger.info(f"P1 VIP customer escalation activated for customer {customer_account_sys_id}")
        return result

# ---- SAM & HAM Pack Tools ----
@mcp.tool()
def create_software_asset(license_name: str, software_model: str, vendor: str, license_type: str, total_licenses: int, cost_per_license: float = None, purchase_date: str = None, expiration_date: str = None, entitlement_details: Dict[str, Any] = None, compliance_requirements: Dict[str, Any] = None, env: str = "dev"):
    """Create software asset with comprehensive license management and compliance tracking"""
    with LogContext(logger, operation="create_software_asset", env=env, software=software_model, vendor=vendor, licenses=total_licenses):
        c = _get_client(env)
        result = sam_ham_pack.create_software_asset(c, license_name, software_model, vendor, license_type, total_licenses, cost_per_license, purchase_date, expiration_date, entitlement_details, compliance_requirements, env)
        logger.info(f"Software asset created: {license_name} ({total_licenses} {license_type} licenses)")
        return result

@mcp.tool()
def update_license_usage(license_sys_id: str, allocated_count: int = None, consumed_count: int = None, compliance_notes: str = None, recalculate_compliance: bool = True, update_allocations: bool = False, env: str = "dev"):
    """Update software license usage and compliance status - Most common SAM operation"""
    with LogContext(logger, operation="update_license_usage", env=env, license_id=license_sys_id, allocated=allocated_count, consumed=consumed_count):
        c = _get_client(env)
        result = sam_ham_pack.update_license_usage(c, license_sys_id, allocated_count, consumed_count, compliance_notes, recalculate_compliance, update_allocations, env)
        logger.info(f"License usage updated: {result.get('license_usage', {}).get('compliance_state', 'unknown')} status")
        return result

@mcp.tool()
def optimize_software_licenses(software_model: str = None, publisher: str = None, target_utilization: float = 0.85, analysis_period_days: int = 90, apply_recommendations: bool = False, env: str = "dev"):
    """Analyze and optimize software license allocation for cost savings"""
    with LogContext(logger, operation="optimize_software_licenses", env=env, software=software_model, publisher=publisher, target_util=target_utilization):
        c = _get_client(env)
        result = sam_ham_pack.optimize_software_licenses(c, software_model, publisher, target_utilization, analysis_period_days, apply_recommendations, env)
        logger.info(f"License optimization completed: ${result.get('total_potential_savings', 0):.2f} potential savings")
        return result

@mcp.tool()
def create_hardware_asset(asset_tag: str, model: str, serial_number: str, location: str, assigned_to: str = None, cost: float = None, purchase_date: str = None, warranty_expiration: str = None, model_category: str = "computer", manufacturer: str = None, asset_state: str = "in_stock", maintenance_contract: Dict[str, Any] = None, env: str = "dev"):
    """Create hardware asset with complete lifecycle tracking"""
    with LogContext(logger, operation="create_hardware_asset", env=env, asset_tag=asset_tag, model=model, manufacturer=manufacturer):
        c = _get_client(env)
        result = sam_ham_pack.create_hardware_asset(c, asset_tag, model, serial_number, location, assigned_to, cost, purchase_date, warranty_expiration, model_category, manufacturer, asset_state, maintenance_contract, env)
        logger.info(f"Hardware asset created: {asset_tag} ({manufacturer or 'Unknown'} {model})")
        return result

@mcp.tool()
def update_hardware_asset(asset_sys_id: str, location: str = None, assigned_to: str = None, state: str = None, substatus: str = None, notes: str = None, track_lifecycle: bool = True, update_financial: bool = True, env: str = "dev"):
    """Update hardware asset information and status - Most common HAM operation"""
    with LogContext(logger, operation="update_hardware_asset", env=env, asset_id=asset_sys_id, location=location, assigned_to=assigned_to, state=state):
        c = _get_client(env)
        result = sam_ham_pack.update_hardware_asset(c, asset_sys_id, location, assigned_to, state, substatus, notes, track_lifecycle, update_financial, env)
        logger.info(f"Hardware asset updated: {result.get('changes_made', [])} changes applied")
        return result

@mcp.tool()
def plan_hardware_refresh(location: str = None, asset_category: str = None, age_threshold_years: int = 4, budget_limit: float = None, include_cost_analysis: bool = True, generate_recommendations: bool = True, env: str = "dev"):
    """Plan hardware refresh based on asset age, warranty, and budget constraints"""
    with LogContext(logger, operation="plan_hardware_refresh", env=env, location=location, category=asset_category, age_threshold=age_threshold_years):
        c = _get_client(env)
        result = sam_ham_pack.plan_hardware_refresh(c, location, asset_category, age_threshold_years, budget_limit, include_cost_analysis, generate_recommendations, env)
        logger.info(f"Hardware refresh planning completed: {result.get('total_refresh_cost', 0):.2f} estimated cost")
        return result

def cleanup():
    """Cleanup resources on shutdown"""
    logger.info("Cleaning up MCP server resources")
    logger.info("MCP server cleanup completed")


# ---- Enhanced Naming Conventions Pack ----
@mcp.tool()
def validate_table_name_enhanced(table_name: str, scope: str = None, env: str = "dev"):
    """
    Validate table name against ServiceNow naming conventions
    
    Args:
        table_name: Name of the table to validate
        scope: Application scope (optional)
        env: Environment (dev/test/prod)
    
    Returns:
        Validation result with issues and recommendations
    """
    with LogContext(logger, operation="validate_table_name_enhanced", env=env, table=table_name, scope=scope):
        c = _get_client(env)
        result = naming_conventions_pack.validate_table_name(table_name, scope)
        logger.info(f"Table name validation: {result['is_valid']}")
        return result


@mcp.tool()
def validate_field_name_enhanced(field_name: str, field_type: str = "string", 
                               table_name: str = "", scope: str = None, env: str = "dev"):
    """
    Validate field name against ServiceNow naming conventions
    
    Args:
        field_name: Name of the field to validate
        field_type: Type of the field
        table_name: Name of the parent table
        scope: Application scope (optional)
        env: Environment (dev/test/prod)
    
    Returns:
        Validation result with issues and recommendations
    """
    with LogContext(logger, operation="validate_field_name_enhanced", env=env, field_name=field_name, field_type=field_type):
        c = _get_client(env)
        result = naming_conventions_pack.validate_field_name(field_name, field_type, table_name, scope)
        logger.info(f"Field name validation: {result['is_valid']}")
        return result


@mcp.tool()
def suggest_compliant_names(description: str, object_type: str = "table", 
                          field_type: str = "string", scope: str = None, env: str = "dev"):
    """
    Suggest ServiceNow compliant names based on description
    
    Args:
        description: Description of the object
        object_type: 'table' or 'field'
        field_type: Type of field (if object_type is 'field')
        scope: Application scope (optional)
        env: Environment (dev/test/prod)
    
    Returns:
        Suggested names with validation results
    """
    with LogContext(logger, operation="suggest_compliant_names", env=env, object_type=object_type):
        c = _get_client(env)
        result = naming_conventions_pack.suggest_compliant_names(description, object_type, field_type, scope)
        logger.info(f"Suggested name: {result['suggested_name']}")
        return result


@mcp.tool()
def get_naming_best_practices(scope: str = None, env: str = "dev"):
    """
    Get ServiceNow naming best practices and guidelines
    
    Args:
        scope: Application scope (optional)
        env: Environment (dev/test/prod)
    
    Returns:
        Comprehensive naming guidelines
    """
    with LogContext(logger, operation="get_naming_best_practices", env=env, scope=scope):
        result = naming_conventions_pack.get_naming_best_practices(scope)
        logger.info("Retrieved naming best practices")
        return result


# ---- Comprehensive Catalog Management Pack ----
@mcp.tool()
def create_catalog_item_comprehensive(name: str, short_description: str, category: str,
                                    description: str = "", variables: List[Dict[str, Any]] = None,
                                    ui_policies: List[Dict[str, Any]] = None,
                                    client_scripts: List[Dict[str, Any]] = None,
                                    scope: str = None, dry_run: bool = False, env: str = "dev"):
    """
    Create a comprehensive catalog item with variables, UI policies, and client scripts
    
    Args:
        name: Name of the catalog item
        short_description: Short description
        category: Category sys_id or name
        description: Detailed description
        variables: List of variable definitions
        ui_policies: List of UI policy definitions
        client_scripts: List of client script definitions
        scope: Application scope
        dry_run: Preview without creating
        env: Environment (dev/test/prod)
    
    Returns:
        Dictionary with creation results
    """
    with LogContext(logger, operation="create_catalog_item_comprehensive", env=env, name=name, dry_run=dry_run):
        c = _get_client(env)
        result = catalog_management_pack.create_catalog_item_comprehensive(
            c, name, short_description, category, description, 
            variables or [], ui_policies or [], client_scripts or [], scope, dry_run
        )
        logger.info(f"Catalog item {'simulated' if dry_run else 'created'}: {name}")
        return result


@mcp.tool()
def create_variable_set(name: str, title: str, variables: List[Dict[str, Any]],
                       scope: str = None, dry_run: bool = False, env: str = "dev"):
    """
    Create a variable set with multiple variables
    
    Args:
        name: Internal name of the variable set
        title: Display title
        variables: List of variable definitions
        scope: Application scope
        dry_run: Preview without creating
        env: Environment (dev/test/prod)
    
    Returns:
        Dictionary with creation results
    """
    with LogContext(logger, operation="create_variable_set", env=env, name=name, dry_run=dry_run):
        c = _get_client(env)
        result = catalog_management_pack.create_variable_set(c, name, title, variables, scope, dry_run)
        logger.info(f"Variable set {'simulated' if dry_run else 'created'}: {name}")
        return result


@mcp.tool()
def create_catalog_ui_policy(catalog_item_sys_id: str, name: str, conditions: str,
                           actions: List[Dict[str, Any]], reverse_if_false: bool = True,
                           active: bool = True, scope: str = None, dry_run: bool = False, env: str = "dev"):
    """
    Create a catalog UI policy with actions
    
    Args:
        catalog_item_sys_id: Catalog item sys_id
        name: Name of the UI policy
        conditions: Policy conditions (JavaScript)
        actions: List of policy actions
        reverse_if_false: Reverse actions when conditions are false
        active: Whether the policy is active
        scope: Application scope
        dry_run: Preview without creating
        env: Environment (dev/test/prod)
    
    Returns:
        Dictionary with creation results
    """
    with LogContext(logger, operation="create_catalog_ui_policy", env=env, name=name, dry_run=dry_run):
        c = _get_client(env)
        result = catalog_management_pack.create_catalog_ui_policy(
            c, catalog_item_sys_id, name, conditions, actions, reverse_if_false, active, scope, dry_run
        )
        logger.info(f"Catalog UI policy {'simulated' if dry_run else 'created'}: {name}")
        return result


@mcp.tool()
def get_variable_type_documentation(env: str = "dev"):
    """
    Get comprehensive documentation for all catalog variable types
    
    Args:
        env: Environment (dev/test/prod)
    
    Returns:
        Dictionary with variable type information and examples
    """
    with LogContext(logger, operation="get_variable_type_documentation", env=env):
        result = catalog_management_pack.get_variable_type_documentation()
        logger.info("Retrieved variable type documentation")
        return result


# ---- Comprehensive UI Management Pack ----
@mcp.tool()
def create_ui_policy_comprehensive(table: str, name: str, conditions: str,
                                 actions: List[Dict[str, Any]], policy_type: str = "form",
                                 reverse_if_false: bool = True, run_scripts: bool = False,
                                 active: bool = True, scope: str = None, dry_run: bool = False, env: str = "dev"):
    """
    Create a comprehensive UI policy with actions
    
    Args:
        table: Target table name
        name: Name of the UI policy
        conditions: Policy conditions
        actions: List of policy actions
        policy_type: Type of UI policy ('form', 'catalog', 'list')
        reverse_if_false: Reverse actions when conditions are false
        run_scripts: Execute scripts when policy runs
        active: Whether the policy is active
        scope: Application scope
        dry_run: Preview without creating
        env: Environment (dev/test/prod)
    
    Returns:
        Dictionary with creation results
    """
    with LogContext(logger, operation="create_ui_policy_comprehensive", env=env, table=table, name=name, dry_run=dry_run):
        c = _get_client(env)
        result = ui_management_pack.create_ui_policy_comprehensive(
            c, table, name, conditions, actions, policy_type, reverse_if_false, run_scripts, active, scope, dry_run
        )
        logger.info(f"UI policy {'simulated' if dry_run else 'created'}: {name}")
        return result


@mcp.tool()
def create_ui_action_comprehensive(table: str, name: str, action_type: str, script: str = "",
                                 condition: str = "", form_style: str = "button", list_style: str = "button",
                                 active: bool = True, scope: str = None, dry_run: bool = False, env: str = "dev"):
    """
    Create a comprehensive UI action
    
    Args:
        table: Target table name
        name: Name of the UI action
        action_type: Type of UI action (form_button, list_choice, etc.)
        script: JavaScript code to execute
        condition: Condition for when action is available
        form_style: Style for form actions
        list_style: Style for list actions
        active: Whether the action is active
        scope: Application scope
        dry_run: Preview without creating
        env: Environment (dev/test/prod)
    
    Returns:
        Dictionary with creation results
    """
    with LogContext(logger, operation="create_ui_action_comprehensive", env=env, table=table, name=name, dry_run=dry_run):
        c = _get_client(env)
        result = ui_management_pack.create_ui_action_comprehensive(
            c, table, name, action_type, script, condition, form_style, list_style, active, scope, dry_run
        )
        logger.info(f"UI action {'simulated' if dry_run else 'created'}: {name}")
        return result


@mcp.tool()
def create_form_layout_comprehensive(table: str, sections: List[Dict[str, Any]] = None,
                                   related_lists: List[Dict[str, Any]] = None,
                                   ui_policies: List[Dict[str, Any]] = None,
                                   ui_actions: List[Dict[str, Any]] = None,
                                   scope: str = None, dry_run: bool = False, env: str = "dev"):
    """
    Create a comprehensive form layout with sections, related lists, policies, and actions
    
    Args:
        table: Target table name
        sections: List of form section definitions
        related_lists: List of related list definitions
        ui_policies: List of UI policy definitions
        ui_actions: List of UI action definitions
        scope: Application scope
        dry_run: Preview without creating
        env: Environment (dev/test/prod)
    
    Returns:
        Dictionary with creation results
    """
    with LogContext(logger, operation="create_form_layout_comprehensive", env=env, table=table, dry_run=dry_run):
        c = _get_client(env)
        result = ui_management_pack.create_form_layout_comprehensive(
            c, table, sections or [], related_lists or [], ui_policies or [], ui_actions or [], scope, dry_run
        )
        logger.info(f"Form layout {'simulated' if dry_run else 'created'} for table: {table}")
        return result


@mcp.tool()
def get_ui_management_documentation(env: str = "dev"):
    """
    Get comprehensive documentation for UI management components
    
    Args:
        env: Environment (dev/test/prod)
    
    Returns:
        Dictionary with UI component information and examples
    """
    with LogContext(logger, operation="get_ui_management_documentation", env=env):
        result = ui_management_pack.get_ui_management_documentation()
        logger.info("Retrieved UI management documentation")
        return result


# ---- Multi-Modal Content Processing Tools ----

# Initialize multimodal pack (optional — requires Pillow and related deps)
multimodal_pack = MultiModalPack() if _MULTIMODAL_AVAILABLE else None

@mcp.tool()
async def analyze_screenshot(image_data: str, analysis_options: Dict[str, Any] = None):
    """
    Analyze ServiceNow UI screenshots to extract elements and suggest operations.
    
    Args:
        image_data: Base64 encoded image data
        analysis_options: Options for analysis configuration
        
    Returns:
        Screenshot analysis results with UI elements and operation suggestions
    """
    with LogContext(logger, operation="analyze_screenshot"):
        result = await multimodal_pack.analyze_screenshot(image_data, analysis_options)
        logger.info("Completed screenshot analysis")
        return result

@mcp.tool()
async def generate_workflow_diagram(workflow_data: Dict[str, Any], format: str = "mermaid"):
    """
    Generate workflow diagrams from ServiceNow Flow Designer or Workflow data.
    
    Args:
        workflow_data: Workflow definition data
        format: Output format (mermaid, svg, interactive)
        
    Returns:
        Generated workflow diagram in specified format
    """
    with LogContext(logger, operation="generate_workflow_diagram"):
        result = await multimodal_pack.generate_workflow_diagram(workflow_data, format)
        logger.info(f"Generated workflow diagram in {format} format")
        return result

@mcp.tool()
async def generate_relationship_diagram(entity_data: Dict[str, Any], relationships: List[Dict[str, Any]], 
                                       layout: str = "force_directed"):
    """
    Generate relationship diagrams for CMDB entities or other ServiceNow objects.
    
    Args:
        entity_data: Entity information
        relationships: List of relationships between entities
        layout: Layout algorithm to use
        
    Returns:
        Generated relationship diagram with interactive capabilities
    """
    with LogContext(logger, operation="generate_relationship_diagram"):
        result = await multimodal_pack.generate_relationship_diagram(entity_data, relationships, layout)
        logger.info(f"Generated relationship diagram with {layout} layout")
        return result

@mcp.tool()
async def generate_architecture_diagram(architecture_data: Dict[str, Any], include_layers: bool = True):
    """
    Generate architecture diagrams for ServiceNow configurations.
    
    Args:
        architecture_data: Architecture configuration data
        include_layers: Include architectural layers in diagram
        
    Returns:
        Generated architecture diagram with component relationships
    """
    with LogContext(logger, operation="generate_architecture_diagram"):
        result = await multimodal_pack.generate_architecture_diagram(architecture_data, include_layers)
        logger.info("Generated architecture diagram")
        return result

@mcp.tool()
async def generate_code_example(example_type: str, context: Dict[str, Any], scenario: str = None):
    """
    Generate ServiceNow code examples with context-aware customization.
    
    Args:
        example_type: Type of code example (business_rule, script_include, client_script, flow_action)
        context: Context information for example generation
        scenario: Specific scenario or use case
        
    Returns:
        Generated code example with documentation and usage notes
    """
    with LogContext(logger, operation="generate_code_example"):
        result = await multimodal_pack.generate_code_example(example_type, context, scenario)
        logger.info(f"Generated {example_type} code example")
        return result

@mcp.tool()
async def create_visual_guide(process_type: str, context: Dict[str, Any], difficulty_level: str = "intermediate"):
    """
    Create step-by-step visual guides for ServiceNow processes.
    
    Args:
        process_type: Type of process (form_configuration, business_rule_creation, workflow_setup)
        context: Process context and requirements
        difficulty_level: Difficulty level (beginner, intermediate, advanced)
        
    Returns:
        Generated visual guide with step-by-step instructions
    """
    with LogContext(logger, operation="create_visual_guide"):
        result = await multimodal_pack.create_visual_guide(process_type, context, difficulty_level)
        logger.info(f"Created visual guide for {process_type}")
        return result

@mcp.tool()
async def generate_interactive_tutorial(tutorial_context: Dict[str, Any], include_assessment: bool = True,
                                       interactive_features: List[str] = None):
    """
    Generate comprehensive interactive tutorials with code examples and guides.
    
    Args:
        tutorial_context: Tutorial requirements and context
        include_assessment: Include assessment questions
        interactive_features: List of interactive features to include
        
    Returns:
        Complete interactive tutorial with examples and assessments
    """
    with LogContext(logger, operation="generate_interactive_tutorial"):
        result = await multimodal_pack.generate_interactive_tutorial(
            tutorial_context, include_assessment, interactive_features
        )
        logger.info("Generated interactive tutorial")
        return result

@mcp.tool()
async def extract_ui_automation_script(ui_analysis: Dict[str, Any], automation_type: str = "servicenow_api"):
    """
    Extract automation scripts from UI analysis for testing or RPA.
    
    Args:
        ui_analysis: UI analysis result from screenshot analysis
        automation_type: Type of automation script (selenium, playwright, servicenow_api)
        
    Returns:
        Generated automation script based on UI analysis
    """
    with LogContext(logger, operation="extract_ui_automation_script"):
        result = await multimodal_pack.extract_ui_automation_script(ui_analysis, automation_type)
        logger.info(f"Generated {automation_type} automation script")
        return result


if __name__ == "__main__":
    import atexit
    import signal
    
    # Register cleanup handlers
    atexit.register(cleanup)
    
    def signal_handler(signum, frame):
        cleanup()
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Log startup only to file, not console
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