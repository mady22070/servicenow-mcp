
from typing import Dict, Any, List, Optional
from ..servicenow_client import ServiceNowClient
def create_notification(client: ServiceNowClient, fields: Dict[str, Any], table: str = "sysevent_email_action", dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "table": table, "record": fields}
    return client.create_record(table, fields)
def get_user_notifications(client: ServiceNowClient, user_sys_id: str, table: str = "sys_email", limit: int = 100) -> Dict[str, Any]:
    q = f"recipientLIKE{user_sys_id}"
    return {"items": client.query_table(table, query=q, fields=["sys_id","subject","user_id","state","sys_created_on"], limit=limit)}
