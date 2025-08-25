"""
Comprehensive tool configuration for ServiceNow MCP server.
This file defines all tools in a structured, maintainable way.
"""

from typing import Dict, List, Any

# Tool configuration structure:
# {
#     "pack_name": {
#         "tools": [
#             {
#                 "func_name": "function_name_in_pack",
#                 "tool_name": "optional_different_tool_name", 
#                 "description": "Tool description",
#                 "guard_tables": ["table1", "table2"],  # Optional
#                 "client_required": True,  # Default: True
#                 "parameters": {...}  # Optional parameter definitions
#             }
#         ]
#     }
# }

TOOL_CONFIGURATIONS: Dict[str, Dict[str, Any]] = {
    
    # Story-Driven Development Tools
    "story_driven_pack": {
        "tools": [
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
    },
    
    # Senior Developer Tools
    "senior_dev_pack": {
        "tools": [
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
    },
    
    # Query and Statistics Tools
    "query_pack": {
        "tools": [
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
    },
    
    # Development Tools
    "dev_pack": {
        "tools": [
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
    },
    
    # Build and Application Tools
    "build_pack": {
        "tools": [
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
            },
            {
                "func_name": "add_choice",
                "description": "Add choice options to a field"
            },
            {
                "func_name": "create_catalog_item",
                "description": "Create a new service catalog item"
            },
            {
                "func_name": "add_catalog_variables",
                "description": "Add variables to a catalog item"
            },
            {
                "func_name": "add_catalog_client_script",
                "description": "Add client script to a catalog item"
            }
        ]
    },
    
    # Scripts and Client-side Tools
    "scripts_pack": {
        "tools": [
            {
                "func_name": "add_client_script",
                "description": "Add a client script to a table"
            },
            {
                "func_name": "lint_client_script",
                "description": "Lint and validate client script code",
                "client_required": False
            }
        ]
    },
    
    # Operational Tools
    "operate_pack": {
        "tools": [
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
            },
            {
                "func_name": "events_backlog",
                "description": "Check events backlog"
            },
            {
                "func_name": "triggers_scheduled",
                "description": "Get scheduled triggers"
            },
            {
                "func_name": "logs_search",
                "description": "Search system logs"
            }
        ]
    },
    
    # Troubleshooting Tools
    "troubleshoot_pack": {
        "tools": [
            {
                "func_name": "user_context",
                "description": "Get user context and permissions"
            },
            {
                "func_name": "acl_summary",
                "description": "Get ACL summary for table/field"
            },
            {
                "func_name": "form_visibility",
                "description": "Check form visibility rules"
            },
            {
                "func_name": "record_access_probe",
                "description": "Test record access permissions"
            }
        ]
    },

    # Customer Service Management (CSM) Tools
    "csm_pack": {
        "tools": [
            {
                "func_name": "create_case",
                "description": "Create a new customer service case",
                "guard_tables": ["sn_customerservice_case"]
            },
            {
                "func_name": "get_case",
                "description": "Get a customer service case by its sys_id"
            }
        ]
    },

    # Field Service Management (FSM) Tools
    "fsm_pack": {
        "tools": [
            {
                "func_name": "create_work_order",
                "description": "Create a new field service work order",
                "guard_tables": ["wm_order"]
            },
            {
                "func_name": "get_work_order",
                "description": "Get a field service work order by its sys_id"
            }
        ]
    },

    # Security Operations (SecOps) Tools
    "secops_pack": {
        "tools": [
            {
                "func_name": "create_security_incident",
                "description": "Create a new security incident",
                "guard_tables": ["sn_si_incident"]
            },
            {
                "func_name": "get_security_incident",
                "description": "Get a security incident by its sys_id"
            }
        ]
    },
    
    # Table Operations
    "table_pack": {
        "tools": [
            {
                "func_name": "update_record",
                "description": "Update an existing record"
            },
            {
                "func_name": "delete_record",
                "description": "Delete a record"
            },
            {
                "func_name": "get_record",
                "description": "Retrieve a single record"
            },
            {
                "func_name": "batch_insert_records",
                "description": "Insert multiple records in batch"
            },
            {
                "func_name": "batch_update_records",
                "description": "Update multiple records in batch"
            }
        ]
    },
    
    # User Management Tools
    "user_pack": {
        "tools": [
            {
                "func_name": "create_user",
                "description": "Create a new user account",
                "guard_tables": ["sys_user"]
            },
            {
                "func_name": "update_user",
                "description": "Update user information",
                "guard_tables": ["sys_user"]
            },
            {
                "func_name": "get_user",
                "description": "Get user by sys_id"
            },
            {
                "func_name": "get_user_by_email",
                "description": "Find user by email address"
            },
            {
                "func_name": "create_group",
                "description": "Create a new user group",
                "guard_tables": ["sys_user_group"]
            },
            {
                "func_name": "add_user_to_group",
                "description": "Add user to a group",
                "guard_tables": ["sys_user_grmember"]
            },
            {
                "func_name": "get_group_members",
                "description": "Get members of a group"
            }
        ]
    },
    
    # ITSM Tools
    "change_pack": {
        "tools": [
            {
                "func_name": "create_change_request",
                "description": "Create a new change request"
            },
            {
                "func_name": "update_change_request",
                "description": "Update change request"
            },
            {
                "func_name": "get_change_request",
                "description": "Get change request details"
            },
            {
                "func_name": "approve_change_request",
                "description": "Approve a change request"
            },
            {
                "func_name": "schedule_change_request",
                "description": "Schedule a change request"
            }
        ]
    },
    
    "problem_pack": {
        "tools": [
            {
                "func_name": "create_problem",
                "description": "Create a new problem record"
            },
            {
                "func_name": "update_problem",
                "description": "Update problem record"
            },
            {
                "func_name": "link_incident_to_problem",
                "description": "Link incident to problem"
            },
            {
                "func_name": "create_known_error",
                "description": "Create known error from problem"
            }
        ]
    },
    
    "request_pack": {
        "tools": [
            {
                "func_name": "create_request",
                "description": "Create a new service request"
            },
            {
                "func_name": "create_request_item",
                "description": "Create request item"
            },
            {
                "func_name": "approve_request",
                "description": "Approve a request"
            },
            {
                "func_name": "fulfill_request_item",
                "description": "Fulfill request item"
            }
        ]
    },
    
    # Flow and Workflow Tools
    "flow_pack": {
        "tools": [
            {
                "func_name": "create_flow",
                "tool_name": "flow_create",
                "description": "Create a new flow"
            },
            {
                "func_name": "add_flow_trigger_record_change",
                "tool_name": "flow_add_trigger_record_change",
                "description": "Add record change trigger to flow"
            },
            {
                "func_name": "activate_flow",
                "tool_name": "flow_activate",
                "description": "Activate or deactivate a flow"
            }
        ]
    },
    
    # Testing Tools
    "atf_pack": {
        "tools": [
            {
                "func_name": "create_test_suite",
                "tool_name": "atf_create_suite",
                "description": "Create ATF test suite"
            },
            {
                "func_name": "create_ui_form_test",
                "tool_name": "atf_create_ui_form_test",
                "description": "Create UI form test"
            }
        ]
    },
    
    # Update Set Management
    "update_set_pack": {
        "tools": [
            {
                "func_name": "create_update_set",
                "description": "Create a new update set"
            },
            {
                "func_name": "close_update_set",
                "description": "Close an update set"
            }
        ]
    },
    
    # Properties Management
    "props_pack": {
        "tools": [
            {
                "func_name": "property_get",
                "description": "Get system property value"
            },
            {
                "func_name": "property_set",
                "description": "Set system property value"
            }
        ]
    }
}

# Basic tools that don't belong to packs
BASIC_TOOLS = [
    {
        "func_name": "create_incident",
        "description": "Create a new incident record"
    },
    {
        "func_name": "get_incident",
        "description": "Retrieve an incident record by sys_id"
    }
]

# Workspace tools (handled separately)
WORKSPACE_TOOLS = [
    {
        "func_name": "ws_list",
        "description": "List available workspaces",
        "client_required": False
    },
    {
        "func_name": "ws_get", 
        "description": "Get workspace configuration",
        "client_required": False
    },
    {
        "func_name": "ws_set",
        "description": "Set workspace configuration", 
        "client_required": False
    }
]

# Plan execution tools
PLAN_TOOLS = [
    {
        "func_name": "execute_plan",
        "description": "Execute a multi-step plan"
    }
]