
from typing import Any, Dict, List, Optional
from ..servicenow_client import ServiceNowClient
DEFAULT_SCOPE = "x_cloudorch_aiops"
def app_scaffold(client: ServiceNowClient, app_name: str, scope_name: str, description: str = "", dry_run: bool = False) -> Dict[str, Any]:
    """
    Scaffolds a new scoped application in ServiceNow.

    This creates:
    1. The application scope record (sys_scope).
    2. An application menu (sys_app_application).
    3. A default module (sys_app_module).
    4. A default user role (sys_user_role).
    """
    if dry_run:
        return {
            "dry_run": True,
            "planned_actions": [
                {"op": "create_scope", "name": app_name, "scope": scope_name},
                {"op": "create_app_menu", "name": app_name},
                {"op": "create_module", "name": f"{app_name} Items"},
                {"op": "create_role", "name": f"{scope_name}.user"},
            ]
        }

    results = {}

    # 1. Create the application scope
    scope_payload = {
        "name": app_name,
        "scope": scope_name,
        "short_description": description,
        "source": "servicenow_mcp",
        "trackable": "true"
    }
    scope_result = client.create_record("sys_scope", scope_payload)
    results["scope"] = scope_result
    if not scope_result.get("success"):
        return {"error": "Failed to create scope", "details": scope_result}

    app_sys_id = scope_result.get("result", {}).get("sys_id")

    # 2. Create the application menu
    menu_payload = {
        "title": app_name,
        "hint": description,
        "sys_scope": app_sys_id
    }
    menu_result = client.create_record("sys_app_application", menu_payload)
    results["menu"] = menu_result
    if not menu_result.get("success"):
        # Log error but continue
        results["menu_error"] = "Failed to create application menu"

    menu_sys_id = menu_result.get("result", {}).get("sys_id")

    # 3. Create a default module
    if menu_sys_id:
        module_payload = {
            "title": f"{app_name} Items",
            "application": menu_sys_id,
            "sys_scope": app_sys_id
        }
        module_result = client.create_record("sys_app_module", module_payload)
        results["module"] = module_result

    # 4. Create a default user role
    role_payload = {
        "name": f"{scope_name}.user",
        "description": f"Default user role for {app_name}",
        "sys_scope": app_sys_id
    }
    role_result = client.create_record("sys_user_role", role_payload)
    results["role"] = role_result

    return {"success": True, "results": results}
def create_table(client: ServiceNowClient, table_label: str, table_name: str, extends: Optional[str] = None, scope: Optional[str] = DEFAULT_SCOPE, dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "op": "create_table", "table_label": table_label, "table_name": table_name, "extends": extends, "scope": scope}
    return client.create_table(table_label, table_name, extends, scope)
def add_field(client: ServiceNowClient, table_name: str, name: str, ftype: str, label: str, mandatory: bool = False, default: Optional[str] = None, choices: Optional[List[str]] = None, scope: Optional[str] = DEFAULT_SCOPE, dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "op": "add_field", "table_name": table_name, "name": name, "type": ftype, "label": label, "mandatory": mandatory, "default": default, "choices": choices, "scope": scope}
    return client.add_field(table_name, name, ftype, label, mandatory, default, choices, scope)
def add_choice(client: ServiceNowClient, table_name: str, element: str, choices: List[str], dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "op": "add_choice", "table_name": table_name, "element": element, "choices": choices}
    return client.add_choice(table_name, element, choices)
def create_catalog_item(client: ServiceNowClient, name: str, category: str, description: str = "", active: bool = True, scope: Optional[str] = DEFAULT_SCOPE, dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "op": "create_catalog_item", "name": name, "category": category, "description": description, "active": active, "scope": scope}
    return client.create_record("sc_cat_item", {"name":name,"short_description":description,"active":"true" if active else "false","category":category})
def add_catalog_variables(client: ServiceNowClient, item_sys_id: str, variables_spec: List[Dict[str, Any]], dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "op": "add_catalog_variables", "item_sys_id": item_sys_id, "variables_count": len(variables_spec)}
    created = []
    for v in variables_spec:
        created.append(client.add_catalog_variable(item_sys_id, v.get("type","string"), v["name"], v.get("question", v["name"]), v.get("choices")))
    return {"created": created}
def add_catalog_client_script(client: ServiceNowClient, item_sys_id: str, ui_type: str, script: str, dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "op": "add_catalog_client_script", "item_sys_id": item_sys_id, "ui_type": ui_type, "lines": len(script.splitlines())}
    return client.add_catalog_client_script(item_sys_id, ui_type, script)
