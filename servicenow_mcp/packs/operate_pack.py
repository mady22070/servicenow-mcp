
from typing import Any, Dict, List, Optional
from ..servicenow_client import ServiceNowClient
def perf_top_transactions(client: ServiceNowClient, since_minutes: int = 60, limit: int = 20) -> Dict[str, Any]:
    rows = client.get_syslog_transactions(since_minutes=since_minutes, limit=limit*3)
    try:
        rows_sorted = sorted(rows, key=lambda r: float(r.get("response_time", 0)), reverse=True)
    except Exception:
        rows_sorted = rows
    return {"items": rows_sorted[:limit]}
def jobs_running(client: ServiceNowClient, limit: int = 50) -> Dict[str, Any]:
    return {"items": client.get_execution_trackers(limit=limit)}
def ecc_queue_backlog(client: ServiceNowClient, states: Optional[List[str]] = None, since_minutes: int = 120, limit: int = 100) -> Dict[str, Any]:
    return {"items": client.get_ecc_queue(states=states, since_minutes=since_minutes, limit=limit)}
def events_backlog(client: ServiceNowClient, limit: int = 100) -> Dict[str, Any]:
    return {"items": client.get_events(limit=limit)}
def triggers_scheduled(client: ServiceNowClient, limit: int = 100) -> Dict[str, Any]:
    fields = ["sys_id","name","state","next_action","job_context","sys_updated_on"]
    return {"items": client.query_table("sys_trigger", fields=fields, limit=limit)}
def logs_search(client: ServiceNowClient, text: str, limit: int = 100) -> Dict[str, Any]:
    q = f"messageLIKE{text}"; fields = ["sys_created_on","level","source","message"]
    return {"items": client.query_table("syslog", query=q, fields=fields, limit=limit)}
