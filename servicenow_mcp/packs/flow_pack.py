
from typing import Dict, Any
from ..servicenow_client import ServiceNowClient
from ..utils.audit import log
def create_flow(client: ServiceNowClient, name: str, description: str = "", table: str = "sys_hub_flow", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"name": name, "description": description, "active": "false"}
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload); log("flow_create", {"sys_id": res.get("sys_id"), "name": name}); return res
def add_flow_trigger_record_change(client: ServiceNowClient, flow_sys_id: str, table_name: str, operation: str = "insert", table: str = "sys_hub_trigger", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"flow": flow_sys_id, "type": "record_change", "table": table_name, "operation": operation}
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload); log("flow_trigger_record_change", {"sys_id": res.get("sys_id"), "flow": flow_sys_id}); return res
def activate_flow(client: ServiceNowClient, flow_sys_id: str, active: bool = True, table: str = "sys_hub_flow", dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "op": "activate_flow", "flow_sys_id": flow_sys_id, "active": active}
    res = client.update_record(table, flow_sys_id, {"active": "true" if active else "false"}); log("flow_activate", {"flow_sys_id": flow_sys_id, "active": active}); return res
