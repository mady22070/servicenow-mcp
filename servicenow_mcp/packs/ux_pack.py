
from typing import Dict, Any
from ..servicenow_client import ServiceNowClient
from ..utils.audit import log
import json
def _json(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
def create_ux_page(client: ServiceNowClient, name: str, title: str, table_page: str = "sys_ux_page", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"name": name, "title": title, "active": "true"}
    if dry_run: return {"dry_run": True, "table": table_page, "record": payload}
    res = client.create_record(table_page, payload); log("ux_create_page", {"sys_id": res.get("sys_id"), "name": name}); return res
def add_ux_component(client: ServiceNowClient, page_sys_id: str, component_name: str, props: Dict[str, Any], table_component: str = "sys_ux_component", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"page": page_sys_id, "component_name": component_name, "props_json": _json(props)}
    if dry_run: return {"dry_run": True, "table": table_component, "record": payload}
    res = client.create_record(table_component, payload); log("ux_add_component", {"sys_id": res.get("sys_id"), "page": page_sys_id, "component": component_name}); return res
def create_ux_experience(client: ServiceNowClient, name: str, title: str, table_exp: str = "sys_ux_experience", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"name": name, "title": title, "active": "true"}
    if dry_run: return {"dry_run": True, "table": table_exp, "record": payload}
    res = client.create_record(table_exp, payload); log("ux_create_experience", {"sys_id": res.get("sys_id"), "name": name}); return res
def add_ux_route(client: ServiceNowClient, experience_sys_id: str, path: str, page_sys_id: str, table_route: str = "sys_ux_route", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"experience": experience_sys_id, "path": path, "page": page_sys_id}
    if dry_run: return {"dry_run": True, "table": table_route, "record": payload}
    res = client.create_record(table_route, payload); log("ux_add_route", {"sys_id": res.get("sys_id"), "experience": experience_sys_id, "path": path}); return res
