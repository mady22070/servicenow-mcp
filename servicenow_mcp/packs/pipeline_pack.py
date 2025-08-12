
from typing import Dict, Any, List
from ..servicenow_client import ServiceNowClient
from . import atf_pack, update_set_pack, governance_pack
def deploy_plan(client: ServiceNowClient, plan: List[Dict[str, Any]], update_set_sys_id: str, confirm: bool = False, continue_on_error: bool = False) -> Dict[str, Any]:
    results = {"atf_runs": [], "update_set": None}
    suites = []
    for step in plan or []:
        args = step.get("args", {}); sid = args.get("suite_sys_id")
        if sid: suites.append(sid)
    for sid in suites:
        r = {"dry_run": True, "suite": sid} if not confirm else client.create_record("sys_atf_test_suite_run", {"test_suite": sid})
        results["atf_runs"].append(r)
    if update_set_sys_id:
        results["update_set"] = {"dry_run": True, "op": "close_update_set", "sys_id": update_set_sys_id} if not confirm else update_set_pack.close_update_set(client, update_set_sys_id)
    meta = governance_pack.export_update_set_meta(client, update_set_sys_id) if update_set_sys_id else {}
    results["export_meta"] = meta
    return results
