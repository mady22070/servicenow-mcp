
from typing import Optional, Dict, Any, List
import re
from ..servicenow_client import ServiceNowClient
from ..utils.audit_simple import log
def lint_client_script(script: str, ui_type: str) -> Dict[str, Any]:
    issues = []
    if "g_form." in script and "function onSubmit" in script and "return" not in script:
        issues.append("onSubmit script should return true/false.")
    if re.search(r"var\s+\w+\s*=\s*;", script):
        issues.append("Variable declared but assigned empty; check logic.")
    if "alert(" in script:
        issues.append("Avoid alert() in client scripts; use g_form.addInfoMessage/warn.")
    return {"issues": issues, "ok": len(issues) == 0}
def add_client_script(client: ServiceNowClient, table: str, name: str, ui_type: str, script: str, scope: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
    lint = lint_client_script(script, ui_type)
    payload = {"name": name, "table": table, "ui_type": ui_type, "script": script}
    if scope: payload["sys_scope.name"] = scope
    if dry_run: return {"dry_run": True, "lint": lint, "record": payload}
    res = client.create_record("sys_script_client", payload)
    log("add_client_script", {"table": table, "name": name, "ui_type": ui_type, "sys_id": res.get("sys_id")})
    return {"result": res, "lint": lint}
