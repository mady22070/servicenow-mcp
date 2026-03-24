
from typing import Dict, Any
from ..servicenow_client import ServiceNowClient
from ..utils.audit_simple import log
def create_test_suite(client: ServiceNowClient, name: str, description: str = "", table: str = "sys_atf_test_suite", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"name": name, "description": description}
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload); log("atf_create_suite", {"sys_id": res.get("sys_id"), "name": name}); return res
def create_ui_form_test(client: ServiceNowClient, suite_sys_id: str, table_name: str, test_name: str, table: str = "sys_atf_test", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"name": test_name, "test_suite": suite_sys_id, "ui16_table": table_name}
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload); log("atf_create_ui_test", {"sys_id": res.get("sys_id"), "suite": suite_sys_id, "table": table_name}); return res
