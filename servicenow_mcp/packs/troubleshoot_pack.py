
from typing import Dict, Any, List, Optional
from ..servicenow_client import ServiceNowClient
def user_context(client: ServiceNowClient, user_sys_id: str) -> Dict[str, Any]:
    roles = client.query_table('sys_user_has_role', query=f'user={user_sys_id}', fields=['role','role.name'], limit=2000)
    groups = client.query_table('sys_user_grmember', query=f'user={user_sys_id}', fields=['group','group.name'], limit=2000)
    return {"roles": roles, "groups": groups}
def acl_summary(client: ServiceNowClient, table: str, field: str = "") -> Dict[str, Any]:
    q = f"name={table}"; 
    if field: q += f"^field={field}"
    rules = client.query_table('sys_security_acl', query=q, fields=['operation','name','field','active','sys_id'], limit=500)
    role_map = {}
    for r in rules:
        aid = r.get("sys_id"); 
        if not aid: continue
        needed = client.query_table('sys_security_acl_role', query=f'acl={aid}', fields=['role','role.name'], limit=50)
        role_map[aid] = needed
    return {"rules": rules, "required_roles": role_map}
def form_visibility(client: ServiceNowClient, table: str, field: str = "") -> Dict[str, Any]:
    policies = client.query_table('ui_policy', query=f'table={table}^active=true', fields=['sys_id','short_description','condition'], limit=500)
    actions = client.query_table('ui_policy_action', query='', fields=['ui_policy','field','mandatory','visible','read_only'], limit=2000)
    pids = set(p.get('sys_id') for p in policies if p.get('sys_id'))
    actions = [a for a in actions if a.get('ui_policy') in pids and (not field or a.get('field') == field)]
    cs = client.query_table('sys_script_client', query=f'table={table}^active=true', fields=['sys_id','name','ui_type','script'], limit=500)
    script_flags = []
    for c in cs:
        s = (c.get('script') or '').lower()
        hits = [fn for fn in ('setdisplay','setvisible','setreadonly','setmandatory') if fn in s]
        if hits:
            script_flags.append({"sys_id": c.get('sys_id'), "name": c.get('name'), "hits": hits})
    return {"ui_policies": policies, "ui_policy_actions": actions, "client_script_flags": script_flags}
def record_access_probe(client: ServiceNowClient, table: str, sys_id: str) -> Dict[str, Any]:
    try:
        rec = client.get_record(table, sys_id, fields=['sys_id'])
        return {"read_ok": True, "record": rec}
    except Exception as e:
        return {"read_ok": False, "error": str(e)}
