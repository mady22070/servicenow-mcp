
from typing import Dict, Any
from ..servicenow_client import ServiceNowClient
from ..utils.audit import log
def create_scripted_rest_api(client: ServiceNowClient, name: str, base_path: str, active: bool = True,
                             table: str = "sys_ws_definition", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"name": name, "base_path": base_path, "active": "true" if active else "false"}
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload); log("create_scripted_rest_api", {"sys_id": res.get("sys_id"), "name": name}); return res
def add_scripted_rest_resource(client: ServiceNowClient, api_sys_id: str, verb: str, relative_path: str, script: str,
                               table: str = "sys_ws_operation", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"web_service_definition": api_sys_id, "http_method": verb, "relative_path": relative_path, "script": script}
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload); log("add_scripted_rest_resource", {"sys_id": res.get("sys_id"), "api": api_sys_id, "verb": verb, "path": relative_path}); return res
