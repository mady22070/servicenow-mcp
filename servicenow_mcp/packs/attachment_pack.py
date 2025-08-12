
from typing import Dict, Any
from ..servicenow_client import ServiceNowClient
def upload_attachment(client: ServiceNowClient, table: str, sys_id: str, file_path: str, file_name: str = "") -> Dict[str, Any]:
    return client.upload_attachment(table, sys_id, file_path, file_name)
def list_attachments(client: ServiceNowClient, table: str, sys_id: str, limit: int = 50) -> Dict[str, Any]:
    return {"items": client.list_attachments(table, sys_id, limit)}
def download_attachment(client: ServiceNowClient, attachment_sys_id: str, out_path: str) -> Dict[str, Any]:
    return client.download_attachment(attachment_sys_id, out_path)
def delete_attachment(client: ServiceNowClient, attachment_sys_id: str, table: str = "sys_attachment") -> Dict[str, Any]:
    return client.delete_record(table, attachment_sys_id)
