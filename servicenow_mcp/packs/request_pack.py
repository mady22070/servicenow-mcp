
from typing import Dict, Any, Optional
from ..servicenow_client import ServiceNowClient
def create_request(client: ServiceNowClient, fields: Dict[str, Any], table: str = "sc_request", dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "table": table, "record": fields}
    return client.create_record(table, fields)
def create_request_item(client: ServiceNowClient, request_sys_id: str, catalog_item_sys_id: str, fields: Optional[Dict[str, Any]] = None, table: str = "sc_req_item", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"request": request_sys_id, "cat_item": catalog_item_sys_id}
    if fields: payload.update(fields)
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    return client.create_record(table, payload)
def approve_request(client: ServiceNowClient, sys_id: str, table: str = "sc_request", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"approval": "approved"}
    if dry_run: return {"dry_run": True, "table": table, "sys_id": sys_id, "fields": payload}
    return client.update_record(table, sys_id, payload)
def fulfill_request_item(client: ServiceNowClient, sys_id: str, table: str = "sc_req_item", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"state": "3"}  # Complete
    if dry_run: return {"dry_run": True, "table": table, "sys_id": sys_id, "fields": payload}
    return client.update_record(table, sys_id, payload)
