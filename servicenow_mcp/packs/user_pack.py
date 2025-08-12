
from typing import Dict, Any, Optional
from ..servicenow_client import ServiceNowClient
def create_user(client: ServiceNowClient, fields: Dict[str, Any], table: str = "sys_user", dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "table": table, "record": fields}
    return client.create_record(table, fields)
def update_user(client: ServiceNowClient, sys_id: str, fields: Dict[str, Any], table: str = "sys_user", dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "table": table, "sys_id": sys_id, "fields": fields}
    return client.update_record(table, sys_id, fields)
def get_user(client: ServiceNowClient, sys_id: str, table: str = "sys_user") -> Dict[str, Any]:
    return client.get_record(table, sys_id)
def get_user_by_email(client: ServiceNowClient, email: str, table: str = "sys_user") -> Dict[str, Any]:
    rows = client.query_table(table, query=f"email={email}", fields=["sys_id","name","email","user_name"], limit=1)
    return {"items": rows}
def create_group(client: ServiceNowClient, fields: Dict[str, Any], table: str = "sys_user_group", dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "table": table, "record": fields}
    return client.create_record(table, fields)
def add_user_to_group(client: ServiceNowClient, user_sys_id: str, group_sys_id: str, table: str = "sys_user_grmember", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"user": user_sys_id, "group": group_sys_id}
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    return client.create_record(table, payload)
def get_group_members(client: ServiceNowClient, group_sys_id: str, table: str = "sys_user_grmember") -> Dict[str, Any]:
    return {"items": client.query_table(table, query=f"group={group_sys_id}", fields=["user","user.name"], limit=500)}
