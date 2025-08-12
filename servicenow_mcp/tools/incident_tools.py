"""
Incident Management Tools - Basic incident operations
"""

from typing import Optional, Dict, Any
from ..servicenow_client import ServiceNowClient


def create_incident(client: ServiceNowClient, short_description: str, 
                   description: Optional[str] = None, 
                   additional_fields: Optional[Dict[str, Any]] = None) -> dict:
    """Create a new incident record"""
    payload: Dict[str, Any] = {"short_description": short_description}
    
    if description:
        payload["description"] = description
    
    if additional_fields:
        payload.update(additional_fields)
    
    return client.create_record("incident", payload)


def get_incident(client: ServiceNowClient, sys_id: str) -> dict:
    """Retrieve an incident record by sys_id"""
    return client.get_record("incident", sys_id)


def update_incident(client: ServiceNowClient, sys_id: str, 
                   fields: Dict[str, Any]) -> dict:
    """Update an incident record"""
    return client.update_record("incident", sys_id, fields)


def close_incident(client: ServiceNowClient, sys_id: str, 
                  close_notes: str = "", resolution_code: str = "Solved (Permanently)") -> dict:
    """Close an incident with resolution details"""
    fields = {
        "state": "7",  # Closed
        "close_notes": close_notes,
        "resolution_code": resolution_code
    }
    return client.update_record("incident", sys_id, fields)