
from typing import Dict, Any, List, Optional
from ..servicenow_client import ServiceNowClient
def capability_check(client: ServiceNowClient, required_plugins: Optional[List[str]] = None, required_roles: Optional[List[str]] = None, probe_tables: Optional[List[str]] = None) -> Dict[str, Any]:
    required_plugins = required_plugins or []; required_roles = required_roles or []; probe_tables = probe_tables or []
    plugins = []
    if required_plugins:
        for pid in required_plugins:
            rows = client.query_table('sys_plugins', query=f"name={pid}^active=true", fields=['name','active','version'], limit=1)
            plugins.append({"id": pid, "active": bool(rows)})
    roles_ok = []
    if required_roles:
        me = client.get_any('/api/now/ui/user').get('result',{}); uid = me.get('userID') or me.get('sys_id')
        have = set(r.get('role.name') for r in client.query_table('sys_user_has_role', query=f"user={uid}", fields=['role.name'], limit=2000) if r.get('role.name'))
        for r in required_roles: roles_ok.append({"role": r, "has": r in have})
    table_probes = []
    for t in probe_tables:
        try:
            items = client.query_table(t, fields=['sys_id'], limit=1)
            table_probes.append({"table": t, "read_ok": True, "sample": items})
        except Exception as e:
            table_probes.append({"table": t, "read_ok": False, "error": str(e)})
    ok = all(p.get('active') for p in plugins) and all(r.get('has') for r in roles_ok) and all(tp['read_ok'] for tp in table_probes)
    return {"ok": ok, "plugins": plugins, "roles": roles_ok, "probes": table_probes}
def export_update_set_meta(client: ServiceNowClient, update_set_sys_id: str) -> Dict[str, Any]:
    us = client.get_record('sys_update_set', update_set_sys_id, fields=['name','state','application','sys_updated_on'])
    files = client.query_table('sys_attachment', query=f"table_sys_id={update_set_sys_id}^table_name=sys_update_set", fields=['sys_id','file_name','size_bytes'], limit=200)
    return {"update_set": us, "attachments": files}
