
from typing import Dict, Any, Optional, List
from ..servicenow_client import ServiceNowClient
def cmdb_health_snapshot(client: ServiceNowClient, classes: Optional[List[str]] = None, limit: int = 50) -> Dict[str, Any]:
    out = {}
    for table in ('cmdb_health_metric_status', 'cmdb_health_score', 'cmdb_health_result'):
        try:
            q = ""
            if classes: q = '^'.join([f"class_name={c}" for c in classes])
            rows = client.query_table(table, query=q, fields=['class_name','kpi','metric','score','last_run'], limit=limit)
            if rows: out[table] = rows
        except Exception: continue
    return {"snapshot": out}
def servicemap_seed(client: ServiceNowClient, app_name: str, entry_point: str, table: str = "svc_map_seed", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"name": app_name, "entry_point": entry_point, "active": "true"}
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    return client.create_record(table, payload)
def impact_rule_add(client: ServiceNowClient, service_sys_id: str, related_ci: str, relation_type: str = "Depends on::Used by",
                    table: str = "svc_impact_rule", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"service": service_sys_id, "ci": related_ci, "relation_type": relation_type}
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    return client.create_record(table, payload)
