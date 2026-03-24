
from typing import Optional, Dict, Any, List
from ..servicenow_client import ServiceNowClient
from ..utils.audit_simple import log
def create_event_rule(client: ServiceNowClient, name: str, filter_query: str, severity: Optional[str] = None,
                      table: str = "em_event_rule", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"name": name, "active": "true", "match_condition": filter_query}
    if severity: payload["severity"] = severity
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload); log("create_event_rule", {"sys_id": res.get("sys_id"), "name": name}); return res
def create_alert_correlation_rule(client: ServiceNowClient, name: str, group_by: List[str],
                                  match_query: Optional[str] = None, table: str = "em_correlation_rule",
                                  dry_run: bool = False) -> Dict[str, Any]:
    payload = {"name": name, "active": "true", "group_by": ",".join(group_by)}
    if match_query: payload["match_condition"] = match_query
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload); log("create_alert_correlation_rule", {"sys_id": res.get("sys_id"), "name": name}); return res
