
from typing import Dict, Any
from ..servicenow_client import ServiceNowClient
from ..utils.audit_simple import log
API_NAME = "mcp_acl_test"; API_BASE = "x_mcp/acltest"
SCRIPT = r"""(function process(request, response) {
  var body = request.body.data || {};
  var userSysId = body.user_sys_id + '';
  var table = body.table + '';
  var sysId = (body.sys_id || '') + '';
  var field = (body.field || '') + '';
  var result = { user: userSysId, table: table, sys_id: sysId, field: field, checks: {} };
  try {
    var imp = new GlideImpersonate(); imp.impersonate(userSysId);
    var gr = new GlideRecordSecure(table);
    if (sysId) { if (gr.get(sysId)) { result.checks.read_record = gr.isValidRecord(); } else { result.checks.read_record = false; result.error = 'record_not_found'; } }
    else { result.checks.table_exists = gr.isValid(); }
    if (field) { var sec = GlideSecurityManager.get().propertySetCanRead(gr, field); result.checks.field_read = !!sec; }
    var req = []; var acl = new GlideRecord('sys_security_acl');
    acl.addQuery('name', table); if (field) acl.addQuery('field', field); acl.query();
    while (acl.next()) { var map = new GlideRecord('sys_security_acl_role'); map.addQuery('acl', acl.getUniqueValue()); map.query();
      var roles = []; while (map.next()) roles.push('' + map.role.name);
      if (roles.length) req.push({acl: ''+acl.getUniqueValue(), op: ''+acl.operation, roles: roles}); }
    result.required_roles = req; imp.impersonate(gs.getUserID()); response.setBody(result);
  } catch (e) { result.error = '' + e; response.setBody(result); }
})(request, response);
"""
def deploy_impersonation_acl_api(client: ServiceNowClient, api_name: str = API_NAME, base_path: str = API_BASE, dry_run: bool = False) -> Dict[str, Any]:
    existing = client.query_table('sys_ws_definition', query=f'name={api_name}', fields=['sys_id','name','base_path'], limit=1)
    if existing and isinstance(existing, list) and len(existing) > 0: api = existing[0]
    else:
        if dry_run: return {"dry_run": True, "op": "create_api", "name": api_name, "base_path": base_path}
        api = client.create_record('sys_ws_definition', {"name": api_name, "base_path": base_path, "active": "true"})
    op_q = client.query_table('sys_ws_operation', query=f'web_service_definition={api.get("sys_id")}^relative_path=check', fields=['sys_id'], limit=1)
    if op_q and isinstance(op_q, list) and len(op_q) > 0: op = op_q[0]
    else:
        if dry_run: return {"dry_run": True, "op": "create_operation", "api": api.get("sys_id"), "path": "check"}
        op = client.create_record('sys_ws_operation', {"web_service_definition": api.get("sys_id"), "http_method": "POST", "relative_path": "check", "active": "true", "script": SCRIPT})
    log("deploy_impersonation_acl_api", {"api": api.get("sys_id"), "op": op.get("sys_id")}); return {"api": api, "operation": op}
def impersonation_acl_check(client: ServiceNowClient, user_sys_id: str, table: str, sys_id: str = "", field: str = "", base_path: str = API_BASE) -> Dict[str, Any]:
    payload = {"user_sys_id": user_sys_id, "table": table, "sys_id": sys_id, "field": field}
    return client.post_any(f"/api/{base_path}/check", payload)
