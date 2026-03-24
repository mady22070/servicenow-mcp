
from typing import Dict, Any, Optional
from ..servicenow_client import ServiceNowClient
from ..utils.audit_simple import log
def asset_receive(client: ServiceNowClient, model: str, asset_tag: str, location: Optional[str] = None,
                  stockroom: Optional[str] = None, cost: Optional[float] = None, table: str = "alm_asset",
                  dry_run: bool = False) -> Dict[str, Any]:
    payload = {"model": model, "asset_tag": asset_tag}
    if location: payload["location"] = location
    if stockroom: payload["stockroom"] = stockroom
    if cost is not None: payload["cost"] = cost
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload); log("asset_receive", {"table": table, "sys_id": res.get("sys_id"), "asset_tag": asset_tag})
    return res
def asset_transfer(client: ServiceNowClient, asset_sys_id: str, stockroom_to: str, table: str = "alm_asset", dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "table": table, "sys_id": asset_sys_id, "to": stockroom_to}
    res = client.update_record(table, asset_sys_id, {"stockroom": stockroom_to}); log("asset_transfer", {"table": table, "sys_id": asset_sys_id, "to": stockroom_to}); return res
def asset_retire(client: ServiceNowClient, asset_sys_id: str, table: str = "alm_asset", dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "table": table, "sys_id": asset_sys_id, "state": "retired"}
    res = client.update_record(table, asset_sys_id, {"install_status": "7"}); log("asset_retire", {"table": table, "sys_id": asset_sys_id}); return res
