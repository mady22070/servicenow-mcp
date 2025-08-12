
from typing import Optional, Dict, Any
from ..servicenow_client import ServiceNowClient
from ..utils.audit import log
def create_rest_message(client: ServiceNowClient, name: str, endpoint: str, authentication_type: str = "none",
                        table: str = "sys_rest_message", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"name": name, "endpoint": endpoint, "authentication_type": authentication_type}
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload); log("create_rest_message", {"sys_id": res.get("sys_id"), "name": name}); return res
def add_rest_method(client: ServiceNowClient, rest_message: str, function_name: str, http_method: str, relative_path: str = "",
                    table: str = "sys_rest_message_fn", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"rest_message": rest_message, "function_name": function_name, "http_method": http_method, "relative_path": relative_path}
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload); log("add_rest_method", {"sys_id": res.get("sys_id"), "rest_message": rest_message, "function_name": function_name}); return res
