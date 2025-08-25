"""
ServiceNow pack for Customer Service Management (CSM)
"""
from typing import Dict, Any, Optional

from ..servicenow_client import ServiceNowClient

def create_case(client: ServiceNowClient, short_description: str, description: Optional[str] = None, contact: Optional[str] = None, account: Optional[str] = None, additional_fields: Optional[Dict[str, Any]] = None, table: str = "sn_customerservice_case", dry_run: bool = False) -> Dict[str, Any]:
    """
    Create a new customer service case.
    """
    payload = {
        "short_description": short_description,
    }
    if description:
        payload["description"] = description
    if contact:
        payload["contact"] = contact
    if account:
        payload["account"] = account
    if additional_fields:
        payload.update(additional_fields)

    if dry_run:
        return {"dry_run": True, "table": table, "record": payload}

    return client.create_record(table, payload)

def get_case(client: ServiceNowClient, sys_id: str, table: str = "sn_customerservice_case") -> Dict[str, Any]:
    """
    Get a customer service case by its sys_id.
    """
    return client.get_record(table, sys_id)
