
"""
Legacy Scripted REST Pack - Deprecated

This pack has been replaced by scripted_rest_api_pack.py which provides
comprehensive REST API development capabilities with scoped application support.

Please use the new pack for all REST API development.
"""

from typing import Dict, Any
from ..servicenow_client import ServiceNowClient
from ..utils.audit_simple import log

# Import the new comprehensive functions
from .scripted_rest_api_pack import (
    create_scoped_rest_api,
    add_rest_resource,
    validate_api_setup,
    generate_api_documentation
)

def create_scripted_rest_api(client: ServiceNowClient, name: str, base_path: str, active: bool = True,
                             table: str = "sys_ws_definition", dry_run: bool = False) -> Dict[str, Any]:
    """Legacy function - use create_scoped_rest_api instead"""
    log("legacy_api_usage", {"function": "create_scripted_rest_api", "recommendation": "use create_scoped_rest_api"})
    
    # Default scope for legacy calls
    scope = "x_legacy_api"
    
    return create_scoped_rest_api(
        client=client,
        name=name,
        scope=scope,
        base_path=base_path,
        dry_run=dry_run
    )

def add_scripted_rest_resource(client: ServiceNowClient, api_sys_id: str, verb: str, relative_path: str, script: str,
                               table: str = "sys_ws_operation", dry_run: bool = False) -> Dict[str, Any]:
    """Legacy function - use add_rest_resource instead"""
    log("legacy_api_usage", {"function": "add_scripted_rest_resource", "recommendation": "use add_rest_resource"})
    
    return add_rest_resource(
        client=client,
        api_sys_id=api_sys_id,
        http_method=verb,
        relative_path=relative_path,
        script=script,
        dry_run=dry_run
    )
