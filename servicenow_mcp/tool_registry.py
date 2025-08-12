"""
Tool registry for organizing MCP tool registration by functional area
"""

from typing import Optional, Dict, Any, List, Callable
from mcp.server.fastmcp import FastMCP

from .servicenow_client import ServiceNowClient
from .tool_config import TOOL_CONFIGURATIONS, BASIC_TOOLS, WORKSPACE_TOOLS, PLAN_TOOLS
from .utils.guard import is_allowed as _guard


class ToolRegistry:
    """Centralized tool registration with consistent patterns and lazy loading"""
    
    def __init__(self, mcp_server: FastMCP, get_client_func, get_pack_func=None):
        self.mcp = mcp_server
        self._get_client = get_client_func
        self._get_pack = get_pack_func or self._default_get_pack
        self._registered_tools = set()  # Track registered tools
    
    def _default_get_pack(self, pack_name: str):
        """Default pack getter for backward compatibility"""
        from . import packs
        return getattr(packs, pack_name)
    
    def _guard_table(self, table: str, op: str = "write", override: bool = False):
        """Centralized guard check"""
        ok, why = _guard(table, op, override)
        if not ok:
            return {"error": "guard_block", "message": why, "table": table}
        return None
    
    def _register_pack_tools(self, pack_name: str, tool_configs: List[Dict[str, Any]]):
        """Register multiple tools from a pack with consistent pattern"""
        for config in tool_configs:
            self._register_tool(pack_name, **config)
    
    def _register_tool(self, pack_name: str, func_name: str, tool_name: str = None, 
                      description: str = "", guard_tables: List[str] = None,
                      client_required: bool = True):
        """Register a single tool with consistent error handling and lazy loading"""
        tool_name = tool_name or func_name
        
        # Avoid duplicate registration
        if tool_name in self._registered_tools:
            return
        
        def tool_wrapper(**kwargs):
            import time
            start_time = time.time()
            
            try:
                env = kwargs.get('env', 'dev')
                dry_run = kwargs.get('dry_run', False)
                
                # Apply guards if specified
                if guard_tables:
                    for table in guard_tables:
                        guard_result = self._guard_table(table, "write", override=dry_run)
                        if guard_result:
                            return guard_result
                
                # Lazy load the pack
                pack_module = self._get_pack(pack_name)
                
                # Get client if required
                if client_required:
                    client = self._get_client(env)
                    result = getattr(pack_module, func_name)(client, **kwargs)
                else:
                    result = getattr(pack_module, func_name)(**kwargs)
                
                # Add execution metadata
                if isinstance(result, dict) and "_meta" not in result:
                    result["_meta"] = {
                        "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                        "function": f"{pack_name}.{func_name}",
                        "environment": env
                    }
                
                return result
                
            except Exception as e:
                return {
                    "error": "execution_error",
                    "message": str(e),
                    "function": f"{pack_name}.{func_name}",
                    "_meta": {
                        "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                        "error": True
                    }
                }
        
        # Set docstring
        tool_wrapper.__doc__ = description or f"Tool: {pack_name}.{func_name}"
        tool_wrapper.__name__ = tool_name
        
        # Register with MCP
        self.mcp.tool()(tool_wrapper)
        
        # Track registration
        self._registered_tools.add(tool_name)
    
    def register_all_tools(self):
        """Register all tools using configuration-driven approach"""
        # Core management tools (handled separately)
        self.register_core_management_tools()
        
        # Register all pack-based tools from configuration
        for pack_name, pack_config in TOOL_CONFIGURATIONS.items():
            self._register_pack_tools(pack_name, pack_config["tools"])
        
        # Register basic tools
        for tool_config in BASIC_TOOLS:
            self._register_basic_tool(**tool_config)
        
        # Register workspace tools
        self.register_workspace_tools()
        
        # Register plan execution tools
        self.register_plan_tools()
        
        # Register composite tools
        self.register_composite_tools()
    
    def register_core_management_tools(self):
        """Register core management tools that don't belong to packs"""
        @self.mcp.tool()
        def client_health_check(env: Optional[str] = None) -> dict:
            """Check health status of ServiceNow client connections"""
            from ..client_manager import client_manager
            return client_manager.health_check(env)
        
        @self.mcp.tool()
        def clear_client_cache(env: str) -> dict:
            """Clear cached client for environment (useful for credential rotation)"""
            from ..client_manager import client_manager
            cleared = client_manager.clear_client(env)
            return {"cleared": cleared, "environment": env}
        
        @self.mcp.tool()
        def get_active_environments() -> dict:
            """Get list of environments with active client connections"""
            from ..client_manager import client_manager
            return {"environments": client_manager.get_active_environments()}
        
        # Track registrations
        self._registered_tools.update(["client_health_check", "clear_client_cache", "get_active_environments"])
    
    def register_query_tools(self):
        """Register query and statistics tools"""
        query_tools = [
            {
                "func_name": "query_table",
                "description": "Query records from a ServiceNow table"
            },
            {
                "func_name": "stats", 
                "description": "Generate statistics for table data"
            },
            {
                "func_name": "ci_graph",
                "description": "Generate configuration item relationship graph"
            }
        ]
        self._register_pack_tools("query_pack", query_tools)
    
    def register_dev_tools(self):
        """Register development tools"""
        dev_tools = [
            {
                "func_name": "create_script_include",
                "description": "Create a new script include",
                "guard_tables": ["sys_script_include"]
            },
            {
                "func_name": "create_business_rule",
                "description": "Create a new business rule",
                "guard_tables": ["sys_script"]
            },
            {
                "func_name": "create_ui_policy",
                "description": "Create a new UI policy",
                "guard_tables": ["ui_policy", "ui_policy_action"]
            }
        ]
        self._register_pack_tools("dev_pack", dev_tools)
    
    def register_operate_tools(self):
        """Register operational and troubleshooting tools"""
        operate_tools = [
            {
                "func_name": "perf_top_transactions",
                "description": "Get top performing transactions"
            },
            {
                "func_name": "jobs_running",
                "description": "Get currently running scheduled jobs"
            },
            {
                "func_name": "ecc_queue_backlog",
                "description": "Check ECC queue backlog"
            }
        ]
        self._register_pack_tools("operate_pack", operate_tools)
    
    def register_itsm_tools(self):
        """Register ITSM tools (incidents, problems, changes, requests)"""
        # Incident tools
        incident_tools = [
            {
                "func_name": "create_incident",
                "description": "Create a new incident record"
            },
            {
                "func_name": "get_incident", 
                "description": "Retrieve an incident record by sys_id"
            }
        ]
        
        # Since incidents are basic operations, register them directly
        for tool_config in incident_tools:
            self._register_basic_tool(**tool_config)
    
    def register_user_tools(self):
        """Register user and group management tools"""
        user_tools = [
            {
                "func_name": "create_user",
                "description": "Create a new user account",
                "guard_tables": ["sys_user"]
            },
            {
                "func_name": "get_user_by_email",
                "description": "Find user by email address"
            },
            {
                "func_name": "create_group",
                "description": "Create a new user group",
                "guard_tables": ["sys_user_group"]
            }
        ]
        self._register_pack_tools("user_pack", user_tools)
    
    def _register_basic_tool(self, func_name: str, description: str = "", guard_tables: List[str] = None):
        """Register basic tools that don't belong to a specific pack"""
        def tool_wrapper(**kwargs):
            import time
            start_time = time.time()
            
            try:
                env = kwargs.get('env', 'dev')
                dry_run = kwargs.get('dry_run', False)
                
                # Apply guards if specified
                if guard_tables:
                    for table in guard_tables:
                        guard_result = self._guard_table(table, "write", override=dry_run)
                        if guard_result:
                            return guard_result
                
                client = self._get_client(env)
                
                # Handle specific basic operations
                if func_name == "create_incident":
                    short_description = kwargs.get('short_description')
                    description_text = kwargs.get('description')
                    additional_fields = kwargs.get('additional_fields', {})
                    
                    payload = {"short_description": short_description}
                    if description_text:
                        payload["description"] = description_text
                    if additional_fields:
                        payload.update(additional_fields)
                    
                    result = client.create_record("incident", payload)
                
                elif func_name == "get_incident":
                    sys_id = kwargs.get('sys_id')
                    result = client.get_record("incident", sys_id)
                
                else:
                    raise ValueError(f"Unknown basic tool function: {func_name}")
                
                # Add execution metadata
                if isinstance(result, dict) and "_meta" not in result:
                    result["_meta"] = {
                        "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                        "function": func_name,
                        "environment": env
                    }
                
                return result
                
            except Exception as e:
                return {
                    "error": "execution_error",
                    "message": str(e),
                    "function": func_name,
                    "_meta": {
                        "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                        "error": True
                    }
                }
        
        tool_wrapper.__doc__ = description
        tool_wrapper.__name__ = func_name
        self.mcp.tool()(tool_wrapper)
        self._registered_tools.add(func_name)
    
    def register_workspace_tools(self):
        """Register workspace management tools"""
        for tool_config in WORKSPACE_TOOLS:
            self._register_workspace_tool(**tool_config)
    
    def register_plan_tools(self):
        """Register plan execution tools"""
        @self.mcp.tool()
        def execute_plan(plan: List[Dict[str, Any]], confirm: bool = False, 
                        continue_on_error: bool = False, env: str = "dev") -> dict:
            """Execute a multi-step plan"""
            from ..utils.plan import execute_plan as _execute_plan
            c = self._get_client(env)
            return _execute_plan(c, plan, confirm, continue_on_error)
        
        self._registered_tools.add("execute_plan")
    
    def register_composite_tools(self):
        """Register composite tools that combine multiple operations"""
        @self.mcp.tool()
        def story_to_implementation(story: str, env: str = "dev") -> dict:
            """Complete story-to-implementation pipeline"""
            import time
            start_time = time.time()
            
            try:
                c = self._get_client(env)
                story_pack = self._get_pack("story_driven_pack")
                
                # Use the complete pipeline function from the pack
                result = story_pack.story_to_implementation(c, story)
                
                # Add execution metadata if not present
                if isinstance(result, dict) and "_meta" not in result:
                    result["_meta"] = {
                        "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                        "function": "story_to_implementation",
                        "environment": env
                    }
                
                return result
                
            except Exception as e:
                return {
                    "error": "execution_error",
                    "message": str(e),
                    "function": "story_to_implementation",
                    "_meta": {
                        "execution_time_ms": round((time.time() - start_time) * 1000, 2),
                        "error": True
                    }
                }
        
        self._registered_tools.add("story_to_implementation")
    
    def _register_workspace_tool(self, func_name: str, description: str = "", client_required: bool = False):
        """Register workspace management tools"""
        def tool_wrapper(**kwargs):
            if func_name == "ws_list":
                from ..utils.workspace import list_workspaces as _ws_list
                return {"workspaces": _ws_list()}
            elif func_name == "ws_get":
                from ..utils.workspace import get_workspace as _ws_get
                name = kwargs.get('name', 'default')
                return {"name": name, "config": _ws_get(name)}
            elif func_name == "ws_set":
                from ..utils.workspace import set_workspace as _ws_set
                name = kwargs.get('name', 'default')
                env = kwargs.get('env', '')
                scope = kwargs.get('scope', '')
                confirm = kwargs.get('confirm', False)
                
                updates = {}
                if env: updates["env"] = env
                if scope: updates["scope"] = scope
                updates["confirm"] = bool(confirm)
                
                return {"name": name, "config": _ws_set(name, updates)}
            else:
                raise ValueError(f"Unknown workspace tool: {func_name}")
        
        tool_wrapper.__doc__ = description
        tool_wrapper.__name__ = func_name
        self.mcp.tool()(tool_wrapper)
        self._registered_tools.add(func_name)