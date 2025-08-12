
from typing import Dict, Any, List, Optional
from ..servicenow_client import ServiceNowClient
def update_record(client: ServiceNowClient, table: str, sys_id: str, fields: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "table": table, "sys_id": sys_id, "fields": fields}
    return client.update_record(table, sys_id, fields)
def delete_record(client: ServiceNowClient, table: str, sys_id: str, dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "table": table, "sys_id": sys_id}
    return client.delete_record(table, sys_id)
def get_record(client: ServiceNowClient, table: str, sys_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    return client.get_record(table, sys_id, fields)
def batch_insert_records(client: ServiceNowClient, table: str, records: List[Dict[str, Any]], dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "table": table, "count": len(records)}
    results = []
    for r in records:
        results.append(client.create_record(table, r))
    return {"results": results}
def batch_update_records(client: ServiceNowClient, table: str, updates: List[Dict[str, Any]], id_field: str = "sys_id", dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "table": table, "count": len(updates)}
    results = []
    for up in updates:
        sid = up.get(id_field); fields = {k:v for k,v in up.items() if k != id_field}
        if sid: results.append(client.update_record(table, sid, fields))
    return {"results": results}
