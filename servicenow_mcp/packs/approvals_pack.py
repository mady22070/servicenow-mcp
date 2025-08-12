
from typing import Dict, Any, Optional
from ..servicenow_client import ServiceNowClient
def get_pending_approvals(client: ServiceNowClient, user_sys_id: str, table: str = "sysapproval_approver", limit: int = 100) -> Dict[str, Any]:
    q = f"approver={user_sys_id}^state=requested"
    return {"items": client.query_table(table, query=q, fields=["sys_id","sysapproval","state","approver","source_table"], limit=limit)}
def approve_sysapproval(client: ServiceNowClient, approval_sys_id: str, table: str = "sysapproval_approver", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"state": "approved"}
    if dry_run: return {"dry_run": True, "table": table, "sys_id": approval_sys_id, "fields": payload}
    return client.update_record(table, approval_sys_id, payload)
def approve_record_generic(client: ServiceNowClient, table: str, sys_id: str, comments: str = "", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"approval": "approved"}
    if comments: payload["comments"] = comments
    if dry_run: return {"dry_run": True, "table": table, "sys_id": sys_id, "fields": payload}
    return client.update_record(table, sys_id, payload)
def reject_record_generic(client: ServiceNowClient, table: str, sys_id: str, comments: str = "", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"approval": "rejected"}
    if comments: payload["comments"] = comments
    if dry_run: return {"dry_run": True, "table": table, "sys_id": sys_id, "fields": payload}
    return client.update_record(table, sys_id, payload)
