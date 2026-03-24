
from typing import Optional, Dict, Any
from ..servicenow_client import ServiceNowClient
from ..utils.audit_simple import log
def create_data_source_jdbc(client: ServiceNowClient, name: str, connection_url: str, username: str, password: str,
                            target_table: Optional[str] = None, jdbc_driver: Optional[str] = None,
                            table: str = "sys_data_source", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"name": name,"type": "JDBC","jdbc_connection_url": connection_url,"jdbc_user_name": username,"jdbc_password": password}
    if jdbc_driver: payload["jdbc_driver"] = jdbc_driver
    if target_table: payload["table_name"] = target_table
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload); log("create_data_source_jdbc", {"sys_id": res.get("sys_id"), "name": name}); return res
def create_import_set(client: ServiceNowClient, name: str, data_source: str, table: str = "sys_import_set", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"name": name, "data_source": data_source}
    if dry_run: return {"dry_run": True, "table": table, "record": payload}
    res = client.create_record(table, payload); log("create_import_set", {"sys_id": res.get("sys_id"), "name": name}); return res
