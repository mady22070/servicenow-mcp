
from typing import List, Optional, Dict, Any
from ..servicenow_client import ServiceNowClient
from ..utils.audit import log
def quick_discovery(client: ServiceNowClient, name: str, ips: List[str], mid_server: Optional[str] = None,
                    schedule_table: str = "discovery_schedule", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"name": name,"active": "true","type": "Quick","ip_range": ",".join(ips),"discover_now_ip_list": ",".join(ips)}
    if mid_server: payload["mid_server"] = mid_server
    if dry_run: return {"dry_run": True, "table": schedule_table, "record": payload}
    res = client.create_record(schedule_table, payload); log("discovery_quick", {"sys_id": res.get("sys_id"), "ips": ips}); return res
def discovery_status(client: ServiceNowClient, limit: int = 50) -> Dict[str, Any]:
    rows = client.query_table("discovery_status", fields=["sys_id","name","state","result","created","source","start_time","end_time"], limit=limit)
    return {"items": rows}
