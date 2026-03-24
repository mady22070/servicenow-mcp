
"""
Enhanced Table Pack with Comprehensive Field Type Support

This pack provides advanced table and field management capabilities with
support for all ServiceNow field types and best practices.
"""

from typing import Dict, Any, List, Optional, Union
import re
from ..servicenow_client import ServiceNowClient

# ServiceNow Field Types (comprehensive list)
SERVICENOW_FIELD_TYPES = {
    # Basic Data Types
    "string": {"max_length": 4000, "supports_default": True, "supports_choices": False},
    "integer": {"max_length": None, "supports_default": True, "supports_choices": False},
    "decimal": {"max_length": None, "supports_default": True, "supports_choices": False, "attributes": ["scale", "precision"]},
    "float": {"max_length": None, "supports_default": True, "supports_choices": False},
    "boolean": {"max_length": None, "supports_default": True, "supports_choices": False},
    
    # Date and Time Types
    "glide_date": {"max_length": None, "supports_default": True, "supports_choices": False},
    "glide_date_time": {"max_length": None, "supports_default": True, "supports_choices": False},
    "glide_time": {"max_length": None, "supports_default": True, "supports_choices": False},
    "glide_duration": {"max_length": None, "supports_default": True, "supports_choices": False},
    
    # Text Types
    "journal": {"max_length": None, "supports_default": False, "supports_choices": False},
    "journal_input": {"max_length": None, "supports_default": False, "supports_choices": False},
    "html": {"max_length": None, "supports_default": True, "supports_choices": False},
    "translated_html": {"max_length": None, "supports_default": True, "supports_choices": False},
    "translated_text": {"max_length": None, "supports_default": True, "supports_choices": False},
    
    # Reference Types
    "reference": {"max_length": 32, "supports_default": True, "supports_choices": False, "requires_reference": True},
    "glide_list": {"max_length": None, "supports_default": False, "supports_choices": False, "requires_reference": True},
    "document_id": {"max_length": 32, "supports_default": True, "supports_choices": False},
    
    # Choice Types
    "choice": {"max_length": 40, "supports_default": True, "supports_choices": True},
    
    # Validation Types
    "url": {"max_length": 1024, "supports_default": True, "supports_choices": False},
    "email": {"max_length": 100, "supports_default": True, "supports_choices": False},
    "phone_number": {"max_length": 40, "supports_default": True, "supports_choices": False},
    
    # Numeric Types
    "currency": {"max_length": None, "supports_default": True, "supports_choices": False, "attributes": ["currency_code"]},
    "percent_complete": {"max_length": None, "supports_default": True, "supports_choices": False},
    
    # Security Types
    "password": {"max_length": 40, "supports_default": False, "supports_choices": False},
    "password2": {"max_length": 40, "supports_default": False, "supports_choices": False},
    "encrypted_text": {"max_length": 4000, "supports_default": False, "supports_choices": False},
    
    # System Types
    "GUID": {"max_length": 32, "supports_default": False, "supports_choices": False},
    "conditions": {"max_length": None, "supports_default": False, "supports_choices": False},
    "script": {"max_length": None, "supports_default": True, "supports_choices": False},
    "script_plain": {"max_length": None, "supports_default": True, "supports_choices": False},
}

# Common field templates for quick creation
FIELD_TEMPLATES = {
    "name": {
        "field_type": "string",
        "label": "Name",
        "mandatory": True,
        "max_length": 100
    },
    "description": {
        "field_type": "string",
        "label": "Description",
        "mandatory": False,
        "max_length": 4000
    },
    "active": {
        "field_type": "boolean",
        "label": "Active",
        "mandatory": False,
        "default_value": "true"
    },
    "priority": {
        "field_type": "choice",
        "label": "Priority",
        "mandatory": False,
        "choices": [
            {"value": "1", "label": "Critical"},
            {"value": "2", "label": "High"},
            {"value": "3", "label": "Medium"},
            {"value": "4", "label": "Low"}
        ]
    },
    "state": {
        "field_type": "choice",
        "label": "State",
        "mandatory": True,
        "choices": [
            {"value": "1", "label": "New"},
            {"value": "2", "label": "In Progress"},
            {"value": "3", "label": "Resolved"},
            {"value": "4", "label": "Closed"}
        ]
    },
    "assigned_to": {
        "field_type": "reference",
        "label": "Assigned to",
        "mandatory": False,
        "reference_table": "sys_user"
    },
    "assignment_group": {
        "field_type": "reference",
        "label": "Assignment group",
        "mandatory": False,
        "reference_table": "sys_user_group"
    },
    "due_date": {
        "field_type": "glide_date",
        "label": "Due date",
        "mandatory": False
    },
    "created_on": {
        "field_type": "glide_date_time",
        "label": "Created",
        "mandatory": False
    },
    "email": {
        "field_type": "email",
        "label": "Email",
        "mandatory": False,
        "max_length": 100
    },
    "phone": {
        "field_type": "phone_number",
        "label": "Phone",
        "mandatory": False,
        "max_length": 40
    },
    "url": {
        "field_type": "url",
        "label": "URL",
        "mandatory": False,
        "max_length": 1024
    },
    "cost": {
        "field_type": "currency",
        "label": "Cost",
        "mandatory": False,
        "currency_code": "USD"
    },
    "percentage": {
        "field_type": "percent_complete",
        "label": "Percentage Complete",
        "mandatory": False
    },
    "comments": {
        "field_type": "journal",
        "label": "Comments",
        "mandatory": False
    },
    "work_notes": {
        "field_type": "journal_input",
        "label": "Work notes",
        "mandatory": False
    }
}


def update_record(client: ServiceNowClient, table: str, sys_id: str, fields: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    """Update a ServiceNow record with specified fields"""
    if dry_run: 
        return {"dry_run": True, "table": table, "sys_id": sys_id, "fields": fields}
    return client.update_record(table, sys_id, fields)


def delete_record(client: ServiceNowClient, table: str, sys_id: str, dry_run: bool = False) -> Dict[str, Any]:
    """Delete a ServiceNow record"""
    if dry_run: 
        return {"dry_run": True, "table": table, "sys_id": sys_id}
    return client.delete_record(table, sys_id)


def get_record(client: ServiceNowClient, table: str, sys_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get a ServiceNow record by sys_id"""
    return client.get_record(table, sys_id, fields)


def batch_insert_records(client: ServiceNowClient, table: str, records: List[Dict[str, Any]], dry_run: bool = False) -> Dict[str, Any]:
    """Batch insert multiple records"""
    if dry_run: 
        return {"dry_run": True, "table": table, "count": len(records)}
    results = []
    for r in records:
        results.append(client.create_record(table, r))
    return {"results": results}


def batch_update_records(client: ServiceNowClient, table: str, updates: List[Dict[str, Any]], id_field: str = "sys_id", dry_run: bool = False) -> Dict[str, Any]:
    """Batch update multiple records"""
    if dry_run: 
        return {"dry_run": True, "table": table, "count": len(updates)}
    results = []
    for up in updates:
        sid = up.get(id_field)
        fields = {k: v for k, v in up.items() if k != id_field}
        if sid: 
            results.append(client.update_record(table, sid, fields))
    return {"results": results}


def add_field_enhanced(
    client: ServiceNowClient,
    table_name: str,
    field_name: str,
    field_type: str,
    label: str,
    mandatory: bool = False,
    default_value: Optional[str] = None,
    choices: Optional[List[Dict[str, str]]] = None,
    reference_table: Optional[str] = None,
    reference_qual: Optional[str] = None,
    max_length: Optional[int] = None,
    scope: Optional[str] = None,
    dry_run: bool = False,
    **additional_attributes
) -> Dict[str, Any]:
    """
    Enhanced field creation with comprehensive ServiceNow field type support
    
    Args:
        client: ServiceNow client instance
        table_name: Name of the table to add field to
        field_name: Technical name of the field (must follow naming conventions)
        field_type: ServiceNow field type (see SERVICENOW_FIELD_TYPES)
        label: Display label for the field
        mandatory: Whether field is required
        default_value: Default value for the field
        choices: List of choice options for choice fields
        reference_table: Referenced table name for reference fields
        reference_qual: Reference qualifier for reference fields
        max_length: Maximum field length
        scope: Application scope
        dry_run: Preview without creating
        **additional_attributes: Additional field-specific attributes
    
    Returns:
        Dictionary containing field creation results
    """
    
    # Validate inputs
    validation_result = _validate_field_inputs(
        table_name, field_name, field_type, label, 
        default_value, choices, reference_table
    )
    
    if not validation_result["valid"]:
        return {
            "success": False,
            "error": "Validation failed",
            "validation_errors": validation_result["errors"],
            "recommendations": validation_result["recommendations"]
        }
    
    if dry_run:
        return {
            "dry_run": True,
            "table_name": table_name,
            "field_name": field_name,
            "field_type": field_type,
            "label": label,
            "mandatory": mandatory,
            "validation": validation_result,
            "field_info": _get_field_type_info(field_type)
        }
    
    try:
        # Create the field payload
        field_payload = _create_field_payload(
            table_name=table_name,
            field_name=field_name,
            field_type=field_type,
            label=label,
            mandatory=mandatory,
            default_value=default_value,
            reference_table=reference_table,
            reference_qual=reference_qual,
            max_length=max_length,
            **additional_attributes
        )
        
        # Add scope if provided
        if scope:
            field_payload["sys_scope"] = scope
        
        # Create the field in sys_dictionary
        field_result = client.create_record("sys_dictionary", field_payload)
        
        results = {
            "success": True,
            "field": field_result,
            "field_type": field_type,
            "table_name": table_name,
            "field_name": field_name
        }
        
        # Handle choices for choice fields
        if field_type == "choice" and choices:
            choice_results = _create_choice_options(client, table_name, field_name, choices)
            results["choices"] = choice_results
        
        # Add field type specific information
        results["field_info"] = _get_field_type_info(field_type)
        
        return results
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create field: {str(e)}",
            "field_type": field_type,
            "table_name": table_name,
            "field_name": field_name
        }


def create_table_with_fields(
    client: ServiceNowClient,
    table_name: str,
    table_label: str,
    fields: List[Dict[str, Any]],
    extends: Optional[str] = None,
    scope: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Create a table with multiple fields in one operation
    
    Args:
        client: ServiceNow client instance
        table_name: Technical table name
        table_label: Display label for table
        fields: List of field definitions
        extends: Parent table to extend
        scope: Application scope
        dry_run: Preview without creating
    
    Returns:
        Dictionary containing creation results
    """
    
    if dry_run:
        # Validate all fields and return preview
        validation_results = []
        for field_def in fields:
            validation = _validate_field_definition(field_def)
            validation_results.append(validation)
        
        return {
            "dry_run": True,
            "table_name": table_name,
            "table_label": table_label,
            "field_count": len(fields),
            "field_validations": validation_results,
            "extends": extends,
            "scope": scope,
            "supported_field_types": list(SERVICENOW_FIELD_TYPES.keys())
        }
    
    try:
        # Create the table first
        table_payload = {
            "name": table_name,
            "label": table_label,
            "is_extendable": "false",
            "access": "public"
        }
        
        if extends:
            table_payload["super_class"] = extends
        
        if scope:
            table_payload["sys_scope"] = scope
        
        table_result = client.create_record("sys_db_object", table_payload)
        
        # Create all fields
        field_results = []
        for field_def in fields:
            field_result = add_field_enhanced(
                client=client,
                table_name=table_name,
                scope=scope,
                **field_def
            )
            field_results.append(field_result)
        
        return {
            "success": True,
            "table": table_result,
            "fields": field_results,
            "field_count": len(field_results),
            "successful_fields": len([f for f in field_results if f.get("success")]),
            "failed_fields": len([f for f in field_results if not f.get("success")])
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create table with fields: {str(e)}",
            "table_name": table_name
        }


def add_field_from_template(
    client: ServiceNowClient,
    table_name: str,
    template_name: str,
    field_name: Optional[str] = None,
    label: Optional[str] = None,
    scope: Optional[str] = None,
    dry_run: bool = False,
    **overrides
) -> Dict[str, Any]:
    """
    Create a field from a predefined template
    
    Args:
        client: ServiceNow client instance
        table_name: Name of the table
        template_name: Name of the field template
        field_name: Override field name (defaults to template name)
        label: Override field label
        scope: Application scope
        dry_run: Preview without creating
        **overrides: Override any template attributes
    
    Returns:
        Dictionary containing field creation results
    """
    
    template = FIELD_TEMPLATES.get(template_name)
    if not template:
        return {
            "success": False,
            "error": f"Unknown template: {template_name}",
            "available_templates": list(FIELD_TEMPLATES.keys())
        }
    
    # Merge template with overrides
    field_config = template.copy()
    field_config.update(overrides)
    
    # Set field name and label
    field_config["field_name"] = field_name or f"u_{template_name}"
    if label:
        field_config["label"] = label
    
    return add_field_enhanced(
        client=client,
        table_name=table_name,
        scope=scope,
        dry_run=dry_run,
        **field_config
    )


def get_field_type_documentation() -> Dict[str, Any]:
    """Get comprehensive documentation for all supported field types"""
    
    documentation = {
        "supported_types": [],
        "field_templates": list(FIELD_TEMPLATES.keys()),
        "examples": {}
    }
    
    for field_type, config in SERVICENOW_FIELD_TYPES.items():
        type_info = {
            "name": field_type,
            "description": _get_field_type_description(field_type),
            "supports_default": config.get("supports_default", False),
            "supports_choices": config.get("supports_choices", False),
            "requires_reference": config.get("requires_reference", False),
            "max_length": config.get("max_length"),
            "additional_attributes": config.get("attributes", [])
        }
        documentation["supported_types"].append(type_info)
    
    # Add examples
    documentation["examples"] = {
        "string_field": {
            "field_type": "string",
            "label": "Description",
            "max_length": 255,
            "mandatory": False
        },
        "choice_field": {
            "field_type": "choice",
            "label": "Priority",
            "choices": [
                {"value": "1", "label": "High"},
                {"value": "2", "label": "Medium"},
                {"value": "3", "label": "Low"}
            ]
        },
        "reference_field": {
            "field_type": "reference",
            "label": "Assigned to",
            "reference_table": "sys_user"
        },
        "date_field": {
            "field_type": "glide_date",
            "label": "Due Date",
            "mandatory": False
        },
        "currency_field": {
            "field_type": "currency",
            "label": "Cost",
            "currency_code": "USD"
        },
        "email_field": {
            "field_type": "email",
            "label": "Contact Email",
            "max_length": 100
        }
    }
    
    return documentation


# Helper functions
def _validate_field_inputs(
    table_name: str,
    field_name: str,
    field_type: str,
    label: str,
    default_value: Optional[str],
    choices: Optional[List[Dict[str, str]]],
    reference_table: Optional[str]
) -> Dict[str, Any]:
    """Validate field creation inputs"""
    
    errors = []
    recommendations = []
    
    # Validate table name
    if not table_name or not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', table_name):
        errors.append("Table name must be alphanumeric with underscores, starting with a letter")
    
    # Validate field name
    if not field_name or not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', field_name):
        errors.append("Field name must be alphanumeric with underscores, starting with a letter")
    
    # Check field name length
    if len(field_name) > 80:
        errors.append("Field name cannot exceed 80 characters")
    
    # Validate field type
    if field_type not in SERVICENOW_FIELD_TYPES:
        errors.append(f"Unsupported field type: {field_type}")
        recommendations.append(f"Supported types: {', '.join(SERVICENOW_FIELD_TYPES.keys())}")
    
    # Validate label
    if not label or len(label.strip()) == 0:
        errors.append("Field label is required")
    
    if len(label) > 40:
        recommendations.append("Field labels longer than 40 characters may be truncated in some views")
    
    # Validate choices for choice fields
    if field_type == "choice":
        if not choices or len(choices) == 0:
            recommendations.append("Choice fields should have at least one choice option")
        else:
            # Validate choice structure
            for i, choice in enumerate(choices):
                if not isinstance(choice, dict) or "value" not in choice:
                    errors.append(f"Choice {i+1} must be a dictionary with 'value' key")
    
    # Validate reference table for reference fields
    field_config = SERVICENOW_FIELD_TYPES.get(field_type, {})
    if field_config.get("requires_reference"):
        if not reference_table:
            errors.append(f"Reference table is required for field type '{field_type}'")
        elif not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', reference_table):
            errors.append("Reference table name must be valid ServiceNow table name")
    
    # Field naming conventions
    if not field_name.startswith('u_') and not field_name.startswith('x_'):
        recommendations.append("Custom fields should start with 'u_' or application prefix (e.g., 'x_app_')")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "recommendations": recommendations
    }


def _validate_field_definition(field_def: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a field definition dictionary"""
    
    required_keys = ["field_name", "field_type", "label"]
    missing_keys = [key for key in required_keys if key not in field_def]
    
    if missing_keys:
        return {
            "valid": False,
            "field_name": field_def.get("field_name", "unknown"),
            "errors": [f"Missing required keys: {', '.join(missing_keys)}"]
        }
    
    return _validate_field_inputs(
        table_name="temp",  # Will be set by caller
        field_name=field_def["field_name"],
        field_type=field_def["field_type"],
        label=field_def["label"],
        default_value=field_def.get("default_value"),
        choices=field_def.get("choices"),
        reference_table=field_def.get("reference_table")
    )


def _create_field_payload(
    table_name: str,
    field_name: str,
    field_type: str,
    label: str,
    mandatory: bool = False,
    default_value: Optional[str] = None,
    reference_table: Optional[str] = None,
    reference_qual: Optional[str] = None,
    max_length: Optional[int] = None,
    **additional_attributes
) -> Dict[str, Any]:
    """Create a comprehensive field payload for ServiceNow sys_dictionary table"""
    
    field_config = SERVICENOW_FIELD_TYPES.get(field_type, {})
    
    # Base payload
    payload = {
        "name": table_name,
        "element": field_name,
        "internal_type": field_type,
        "column_label": label,
        "mandatory": "true" if mandatory else "false",
        "active": "true"
    }
    
    # Add default value if supported and provided
    if field_config.get("supports_default", False) and default_value is not None:
        payload["default_value"] = default_value
    
    # Add max length
    if max_length:
        payload["max_length"] = str(max_length)
    elif field_config.get("max_length"):
        payload["max_length"] = str(field_config["max_length"])
    
    # Handle reference fields
    if field_config.get("requires_reference", False):
        if reference_table:
            payload["reference"] = reference_table
        if reference_qual:
            payload["reference_qual"] = reference_qual
    
    # Handle decimal/currency precision
    if field_type in ["decimal", "currency"]:
        payload["scale"] = additional_attributes.get("scale", "2")
        payload["precision"] = additional_attributes.get("precision", "18")
    
    # Handle currency code
    if field_type == "currency":
        payload["currency_code"] = additional_attributes.get("currency_code", "USD")
    
    return payload


def _create_choice_options(
    client: ServiceNowClient,
    table_name: str,
    field_name: str,
    choices: List[Dict[str, str]]
) -> List[Dict[str, Any]]:
    """Create choice options for a choice field"""
    
    choice_results = []
    
    for i, choice in enumerate(choices):
        choice_payload = {
            "name": table_name,
            "element": field_name,
            "value": choice["value"],
            "label": choice.get("label", choice["value"]),
            "sequence": choice.get("order", i * 10),  # Default ordering
            "inactive": "false"
        }
        
        try:
            result = client.create_record("sys_choice", choice_payload)
            choice_results.append({
                "success": True,
                "choice": result,
                "value": choice_payload["value"],
                "label": choice_payload["label"]
            })
        except Exception as e:
            choice_results.append({
                "success": False,
                "error": str(e),
                "value": choice_payload["value"],
                "label": choice_payload["label"]
            })
    
    return choice_results


def _get_field_type_info(field_type: str) -> Dict[str, Any]:
    """Get information about a field type"""
    
    config = SERVICENOW_FIELD_TYPES.get(field_type, {})
    
    return {
        "type": field_type,
        "supports_default": config.get("supports_default", False),
        "supports_choices": config.get("supports_choices", False),
        "requires_reference": config.get("requires_reference", False),
        "max_length": config.get("max_length"),
        "additional_attributes": config.get("attributes", [])
    }


def _get_field_type_description(field_type: str) -> str:
    """Get human-readable description for field type"""
    
    descriptions = {
        "string": "Text field for short to medium text (up to 4000 characters)",
        "integer": "Whole numbers only",
        "decimal": "Decimal numbers with configurable precision",
        "float": "Floating point numbers",
        "boolean": "True/False checkbox",
        "glide_date": "Date only (YYYY-MM-DD format)",
        "glide_date_time": "Date and time",
        "glide_time": "Time only",
        "glide_duration": "Duration/elapsed time",
        "journal": "Work notes/comments with history",
        "journal_input": "Journal with input formatting",
        "html": "Rich text/HTML content",
        "reference": "Reference to another table record",
        "glide_list": "Multiple references (comma-separated)",
        "choice": "Dropdown with predefined values",
        "url": "URL field with validation",
        "email": "Email field with validation",
        "phone_number": "Phone number field",
        "currency": "Currency field with currency code",
        "percent_complete": "Percentage (0-100)",
        "password": "Encrypted password field",
        "password2": "Two-way encrypted password",
        "encrypted_text": "Encrypted text field"
    }
    
    return descriptions.get(field_type, f"ServiceNow field type: {field_type}")
