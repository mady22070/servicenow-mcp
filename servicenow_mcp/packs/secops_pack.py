"""
ServiceNow pack for Security Operations (SecOps)
"""
from typing import Dict, Any, Optional

from ..servicenow_client import ServiceNowClient

def create_security_incident(client: ServiceNowClient, short_description: str, description: Optional[str] = None, additional_fields: Optional[Dict[str, Any]] = None, table: str = "sn_si_incident", dry_run: bool = False) -> Dict[str, Any]:
    """
    Create a new security incident.
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

def get_security_incident(client: ServiceNowClient, sys_id: str, table: str = "sn_si_incident") -> Dict[str, Any]:
    """
    Get a security incident by its sys_id.
    """
    return client.get_record(table, sys_id)
