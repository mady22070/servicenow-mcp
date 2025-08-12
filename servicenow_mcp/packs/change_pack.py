
from typing import Dict, Any, Optional
from ..servicenow_client import ServiceNowClient
TABLE = "change_request"
def create_change_request(client: ServiceNowClient, fields: Dict[str, Any], table: str = TABLE, dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "table": table, "record": fields}
    return client.create_record(table, fields)
def update_change_request(client: ServiceNowClient, sys_id: str, fields: Dict[str, Any], table: str = TABLE, dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "table": table, "sys_id": sys_id, "fields": fields}
    return client.update_record(table, sys_id, fields)
def get_change_request(client: ServiceNowClient, sys_id: str, table: str = TABLE) -> Dict[str, Any]:
    return client.get_record(table, sys_id)
def approve_change_request(client: ServiceNowClient, sys_id: str, approver_sys_id: Optional[str] = None, table: str = TABLE, dry_run: bool = False) -> Dict[str, Any]:
    payload = {"approval": "approved"}; 
    if approver_sys_id: payload["assigned_to"] = approver_sys_id
    if dry_run: return {"dry_run": True, "table": table, "sys_id": sys_id, "fields": payload}
    return client.update_record(table, sys_id, payload)
def schedule_change_request(client: ServiceNowClient, sys_id: str, start_date: str, end_date: str, table: str = TABLE, dry_run: bool = False) -> Dict[str, Any]:
    payload = {"start_date": start_date, "end_date": end_date}
    if dry_run: return {"dry_run": True, "table": table, "sys_id": sys_id, "fields": payload}
    return client.update_record(table, sys_id, payload)
