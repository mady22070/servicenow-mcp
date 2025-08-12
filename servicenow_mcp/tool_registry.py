"""
Tool registry for organizing MCP tool registration by functional area
"""

from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP

from .servicenow_client import ServiceNowClient
from .packs import (
    build_pack, operate_pack, query_pack, scripts_pack, dev_pack,
    senior_dev_pack, story_driven_pack, advanced_cmdb_pack
)
from .utils.guard import is_allowed as _guard


class ToolRegistry:
    """Centralized tool registration with consistent patterns"""
    
    def __init__(self, mcp_server: FastMCP, get_client_func):
        self.mcp = mcp_server
        self._get_client = get_client_func
    
    def _guard_table(self, table: str, op: str = "write", override: bool = False):
        """Centralized guard check"""
        ok, why = _guard(table, op, override)
        if not ok:
            return {"error": "guard_block", "message": why, "table": table}
        return None
    
    def _register_pack_tools(self, pack_module, tool_configs: List[Dict[str, Any]]):
        """Register multiple tools from a pack with consistent pattern"""
        for config in tool_configs:
            self._register_tool(pack_module, **config)
    
    def _register_tool(self, pack_module, func_name: str, tool_name: str = None, 
                      description: str = "", guard_tables: List[str] = None,
                      client_required: bool = True):
        """Register a single tool with consistent error handling"""
        tool_name = tool_name or func_name
        
        def tool_wrapper(**kwargs):
            env = kwargs.get('env', 'dev')
            dry_run = kwargs.get('dry_run', False)
            
            # Apply guards if specified
            if guard_tables:
                for table in guard_tables:
                    guard_result = self._guard_table(table, "write", override=dry_run)
                    if guard_result:
                        return guard_result
            
            # Get client if required
            if client_required:
                client = self._get_client(env)
                return getattr(pack_module, func_name)(client, **kwargs)
            else:
                return getattr(pack_module, func_name)(**kwargs)
        
        # Set docstring
        tool_wrapper.__doc__ = description or getattr(pack_module, func_name).__doc__
        
        # Register with MCP
        self.mcp.tool()(tool_wrapper)
        
        # Store reference with proper name
        globals()[tool_name] = tool_wrapper
    
    def register_all_tools(self):
        """Register all tools organized by functional area"""
        self.register_story_driven_tools()
        self.register_senior_dev_tools()
        self.register_advanced_cmdb_tools()
        self.register_build_tools()
        # Add other tool categories...
    
    def register_story_driven_tools(self):
        """Register story-driven development tools"""
        story_tools = [
            {
                "func_name": "parse_user_story",
                "description": "Parse user story using standard format: As a [user], I want [goal] so that [benefit]",
                "client_required": False
            },
            {
                "func_name": "extract_technical_requirements", 
                "description": "Extract technical requirements from story components"
            },
            {
                "func_name": "generate_implementation_tasks",
                "description": "Generate specific implementation tasks from requirements"
            },
            {
                "func_name": "create_executable_plan",
                "description": "Create an executable plan with specific ServiceNow operations"
            },
            {
                "func_name": "validate_story_completeness",
                "description": "Validate that a user story has sufficient detail for implementation",
                "client_required": False
            }
        ]
        
        self._register_pack_tools(story_driven_pack, story_tools)
        
        # Register the composite function separately
        @self.mcp.tool()
        def story_to_implementation(story: str, env: str = "dev") -> dict:
            """Complete story-to-implementation pipeline"""
            c = self._get_client(env)
            
            parsed_story = story_driven_pack.parse_user_story(story)
            validation = story_driven_pack.validate_story_completeness(parsed_story)
            
            if not validation["is_complete"]:
                return {
                    "status": "incomplete_story",
                    "validation": validation,
                    "recommendations": validation["recommendations"]
                }
            
            requirements = story_driven_pack.extract_technical_requirements(c, parsed_story["components"])
            tasks = story_driven_pack.generate_implementation_tasks(c, requirements, parsed_story)
            executable_plan = story_driven_pack.create_executable_plan(c, tasks, parsed_story)
            
            return {
                "status": "success",
                "parsed_story": parsed_story,
                "validation": validation,
                "requirements": requirements,
                "executable_plan": executable_plan
            }
    
    def register_senior_dev_tools(self):
        """Register senior developer tools"""
        senior_tools = [
            {
                "func_name": "analyze_story",
                "tool_name": "analyze_user_story",
                "description": "Analyze a user story and break it down into actionable development tasks"
            },
            {
                "func_name": "troubleshoot_cmdb_duplicates",
                "description": "Advanced CMDB duplicate analysis and troubleshooting"
            },
            {
                "func_name": "investigate_data_quality",
                "description": "Comprehensive data quality investigation"
            },
            {
                "func_name": "generate_development_plan",
                "description": "Generate a comprehensive development plan from story analysis"
            },
            {
                "func_name": "root_cause_analysis",
                "description": "Perform root cause analysis for ServiceNow issues"
            }
        ]
        
        self._register_pack_tools(senior_dev_pack, senior_tools)
    
    def register_advanced_cmdb_tools(self):
        """Register advanced CMDB analysis and troubleshooting tools"""
        advanced_cmdb_tools = [
            {
                "func_name": "analyze_ci_lifecycle",
                "description": "Comprehensive CI lifecycle analysis including audit history and relationships"
            },
            {
                "func_name": "detect_duplicate_patterns",
                "description": "Advanced duplicate detection with pattern analysis and confidence scoring"
            },
            {
                "func_name": "investigate_ci_relationships",
                "description": "Deep investigation of CI relationships and dependencies with issue detection"
            }
        ]
        
        self._register_pack_tools(advanced_cmdb_pack, advanced_cmdb_tools)
    
    def register_build_tools(self):
        """Register build and catalog tools"""
        build_tools = [
            {
                "func_name": "app_scaffold",
                "description": "Scaffold a new ServiceNow application"
            },
            {
                "func_name": "create_table",
                "description": "Create a new table in ServiceNow",
                "guard_tables": ["sys_db_object"]
            },
            {
                "func_name": "add_field",
                "description": "Add a field to an existing table",
                "guard_tables": ["sys_dictionary"]
            }
        ]
        
        self._register_pack_tools(build_pack, build_tools)