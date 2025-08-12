
from typing import Any, Dict, List, Optional
from ..servicenow_client import ServiceNowClient
DEFAULT_SCOPE = "x_cloudorch_aiops"
def app_scaffold(client: ServiceNowClient, spec: Dict[str, Any], scope: Optional[str] = DEFAULT_SCOPE, dry_run: bool = False) -> Dict[str, Any]:
    actions = []
    for tbl in spec.get("tables", []):
        actions.append({"op": "create_table", "table_label": tbl["table_label"], "table_name": tbl["table_name"], "extends": tbl.get("extends"), "scope": scope})
        for f in tbl.get("fields", []):
            actions.append({"op": "add_field", "table_name": tbl["table_name"], "name": f["name"], "type": f.get("type","string"),
                            "label": f.get("label", f["name"]), "mandatory": f.get("mandatory", False),
                            "default": f.get("default"), "choices": f.get("choices"), "scope": scope})
    if dry_run:
        return {"dry_run": True, "planned_actions": actions, "counts": {"tables": sum(1 for a in actions if a['op']=='create_table'), "fields": sum(1 for a in actions if a['op']=='add_field') }}
    results = []
    for a in actions:
        if a["op"] == "create_table":
            results.append(client.create_table(a["table_label"], a["table_name"], a.get("extends"), a.get("scope")))
        elif a["op"] == "add_field":
            results.append(client.add_field(a["table_name"], a["name"], a["type"], a["label"], a["mandatory"], a.get("default"), a.get("choices"), a.get("scope")))
    return {"dry_run": False, "results": results}
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
