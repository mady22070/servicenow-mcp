
from typing import Dict, Any
from ..servicenow_client import ServiceNowClient
def property_get(client: ServiceNowClient, name: str, table: str = "sys_properties") -> Dict[str, Any]:
    rows = client.query_table(table, query=f"name={name}", fields=["sys_id","name","value","description"], limit=1)
    return {"items": rows}
def property_set(client: ServiceNowClient, name: str, value: str, table: str = "sys_properties", dry_run: bool = False) -> Dict[str, Any]:
    rows = client.query_table(table, query=f"name={name}", fields=["sys_id"], limit=1)
    if not rows:
        if dry_run: return {"dry_run": True, "op": "create_property", "name": name, "value": value}
        return client.create_record(table, {"name": name, "value": value})
    sys_id = rows[0]["sys_id"]
    if dry_run: return {"dry_run": True, "op": "update_property", "sys_id": sys_id, "value": value}
    return client.update_record(table, sys_id, {"value": value})
