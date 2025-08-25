"""
ServiceNow pack for Field Service Management (FSM)
"""
from typing import Dict, Any, Optional

from ..servicenow_client import ServiceNowClient

def create_work_order(client: ServiceNowClient, short_description: str, description: Optional[str] = None, additional_fields: Optional[Dict[str, Any]] = None, table: str = "wm_order", dry_run: bool = False) -> Dict[str, Any]:
    """
    Create a new field service work order.
    """
    payload = {
        "short_description": short_description,
    }
    if description:
        payload["description"] = description
    if additional_fields:
        payload.update(additional_fields)

    if dry_run:
        return {"dry_run": True, "table": table, "record": payload}

    return client.create_record(table, payload)

def get_work_order(client: ServiceNowClient, sys_id: str, table: str = "wm_order") -> Dict[str, Any]:
    """
    Get a field service work order by its sys_id.
    """
    return client.get_record(table, sys_id)
