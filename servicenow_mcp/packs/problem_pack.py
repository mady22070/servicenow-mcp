
from typing import Dict, Any
from ..servicenow_client import ServiceNowClient
def create_problem(client: ServiceNowClient, fields: Dict[str, Any], table: str = "problem", dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "table": table, "record": fields}
    return client.create_record(table, fields)
def update_problem(client: ServiceNowClient, sys_id: str, fields: Dict[str, Any], table: str = "problem", dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "table": table, "sys_id": sys_id, "fields": fields}
    return client.update_record(table, sys_id, fields)
def link_incident_to_problem(client: ServiceNowClient, incident_sys_id: str, problem_sys_id: str, incident_table: str = "incident", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"problem_id": problem_sys_id}
    if dry_run: return {"dry_run": True, "table": incident_table, "sys_id": incident_sys_id, "fields": payload}
    return client.update_record(incident_table, incident_sys_id, payload)
def create_known_error(client: ServiceNowClient, problem_sys_id: str, workaround: str, table: str = "known_error", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"problem": problem_sys_id, "workaround": workaround}
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    return client.create_record(table, payload)
