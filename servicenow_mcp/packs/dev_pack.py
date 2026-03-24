
from typing import Dict, Any, Optional, List
from ..servicenow_client import ServiceNowClient
from ..utils.audit_simple import log
def create_script_include(client: ServiceNowClient, name: str, script: str, api_name: Optional[str] = None, active: bool = True,
                          table: str = "sys_script_include", scope: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
    payload = {"name": name, "active": "true" if active else "false", "script": script}
    if api_name: payload["api_name"] = api_name
    if scope: payload["sys_scope.name"] = scope
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload); log("create_script_include", {"sys_id": res.get("sys_id"), "name": name}); return res
def create_business_rule(client: ServiceNowClient, table_name: str, name: str, when: str, actions: Dict[str, bool],
                         condition: str = "", script: str = "", active: bool = True, table: str = "sys_script", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"name": name, "table": table_name, "when": when,
               "insert": "true" if actions.get("insert") else "false",
               "update": "true" if actions.get("update") else "false",
               "delete": "true" if actions.get("delete") else "false",
               "query": "true" if actions.get("query") else "false",
               "active": "true" if active else "false", "condition": condition, "script": script}
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload); log("create_business_rule", {"sys_id": res.get("sys_id"), "name": name}); return res
def create_ui_policy(client: ServiceNowClient, table_name: str, short_description: str, active: bool = True,
                     condition: str = "", actions: Optional[List[Dict[str, Any]]] = None,
                     policy_table: str = "ui_policy", action_table: str = "ui_policy_action",
                     dry_run: bool = False) -> Dict[str, Any]:
    policy = {"table": table_name, "short_description": short_description, "active": "true" if active else "false", "condition": condition}
    if dry_run: return {"dry_run": True, "policy": policy, "actions": actions or []}
    p = client.create_record(policy_table, policy); created = []
    for a in actions or []:
        payload = {"ui_policy": p.get("sys_id"), "field": a["field"]}
        for k in ("mandatory","visible","read_only"):
            if k in a: payload[k] = "true" if a[k] else "false"
        created.append(client.create_record(action_table, payload))
    log("create_ui_policy", {"policy_sys_id": p.get("sys_id"), "actions": len(created)})
    return {"policy": p, "actions": created}
