
from typing import Dict, Any, Optional
from ..servicenow_client import ServiceNowClient
from ..utils.audit_simple import log
def create_update_set(client: ServiceNowClient, name: str, description: str = "", application: Optional[str] = None,
                      state: str = "in progress", table: str = "sys_update_set", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"name": name, "state": state, "description": description}
    if application: payload["application"] = application
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload); log("create_update_set", {"sys_id": res.get("sys_id"), "name": name}); return res
def close_update_set(client: ServiceNowClient, sys_id: str, table: str = "sys_update_set", dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "op": "close_update_set", "sys_id": sys_id}
    res = client.update_record(table, sys_id, {"state": "complete"}); log("close_update_set", {"sys_id": sys_id}); return res
