from typing import Dict, Any, Optional
from ..servicenow_client import ServiceNowClient
from ..utils.audit_simple import log

def create_policy(client: ServiceNowClient, name: str, owner_user: str, state: str = "draft",
                  table: str = "sn_grc_policy_statement", number_prefix: str = "POL",
                  dry_run: bool = False) -> Dict[str, Any]:
    payload = {"name": name, "owner": owner_user, "state": state, "number": number_prefix}
    if dry_run:
        return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload)
    log("irm_create_policy", {"table": table, "sys_id": res.get("sys_id")})
    return res

def create_risk(client: ServiceNowClient, name: str, risk_statement: str, scoring_method: str = "qualitative",
                table: str = "sn_risk_risk", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"name": name, "risk_statement": risk_statement, "risk_scoring_method": scoring_method}
    if dry_run:
        return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload)
    log("irm_create_risk", {"table": table, "sys_id": res.get("sys_id")})
    return res

def create_control(client: ServiceNowClient, name: str, framework: Optional[str] = None,
                   table: str = "sn_grc_control", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"name": name}
    if framework:
        payload["framework"] = framework
    if dry_run:
        return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload)
    log("irm_create_control", {"table": table, "sys_id": res.get("sys_id")})
    return res

def schedule_assessment(client: ServiceNowClient, template: str, assignment_group: str, due_in_days: int,
                        population_query: str, table: str = "asmt_assessment_instance",
                        dry_run: bool = False) -> Dict[str, Any]:
    payload = {
        "metric_type": template,
        "assignment_group": assignment_group,
        "due_date": f"javascript:gs.daysAgoStart({-int(due_in_days)})",
        "source_table": "cmdb_ci",
        "source_id_query": population_query
    }
    if dry_run:
        return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload)
    log("irm_schedule_assessment", {"table": table, "sys_id": res.get("sys_id")})
    return res
