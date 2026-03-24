"""
ServiceNow Catalog Management Pack

This pack provides comprehensive catalog management capabilities including:
- Catalog item creation with best practices
- Category management
- Variable management
- Workflow integration
- Approval processes
- Fulfillment scripts
"""

from typing import Dict, Any, List, Optional
from ..servicenow_client import ServiceNowClient
from ..utils.audit_simple import log

def create_catalog_category(client: ServiceNowClient, title: str, description: str = "",
                          parent_category: Optional[str] = None, scope: Optional[str] = None,
                          dry_run: bool = False) -> Dict[str, Any]:
    """Create a catalog category"""
    
    payload = {
        'title': title,
        'description': description,
        'active': 'true'
    }
    
    if parent_category:
        payload['parent'] = parent_category
    
    if scope:
        payload['sys_scope'] = scope
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'sc_category',
            'record': payload
        }
    
    result = client.create_record('sc_category', payload)
    log("create_catalog_category", {
        "sys_id": result.get("sys_id"),
        "title": title
    })
    
    return result

def create_catalog_item_comprehensive(client: ServiceNowClient, name: str, short_description: str,
                                    category_sys_id: str, description: str = "",
                                    price: float = 0.0, workflow: Optional[str] = None,
                                    fulfillment_script: Optional[str] = None,
                                    scope: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
    """Create a comprehensive catalog item with all best practices"""
    
    payload = {
        'name': name,
        'short_description': short_description,
        'description': description,
        'category': category_sys_id,
        'price': str(price),
        'active': 'true',
        'available_for_order': 'true',
        'billable': 'false' if price == 0.0 else 'true'
    }
    
    if workflow:
        payload['workflow'] = workflow
    
    if fulfillment_script:
        payload['script'] = fulfillment_script
    
    if scope:
        payload['sys_scope'] = scope
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'sc_cat_item',
            'record': payload,
            'best_practices': {
                'has_workflow': workflow is not None,
                'has_fulfillment_script': fulfillment_script is not None,
                'is_free': price == 0.0
            }
        }
    
    result = client.create_record('sc_cat_item', payload)
    log("create_catalog_item_comprehensive", {
        "sys_id": result.get("sys_id"),
        "name": name,
        "category": category_sys_id
    })
    
    return result

def add_catalog_variable_with_validation(client: ServiceNowClient, item_sys_id: str, 
                                        variable_type: str, name: str, question: str,
                                        mandatory: bool = False, default_value: str = "",
                                        choices: Optional[List[str]] = None,
                                        validation_script: Optional[str] = None,
                                        dry_run: bool = False) -> Dict[str, Any]:
    """Add catalog variable with comprehensive validation"""
    
    # Validate variable type
    valid_types = ['string', 'integer', 'boolean', 'choice', 'multiple_choice', 
                   'date', 'date_time', 'reference', 'email', 'url']
    
    if variable_type not in valid_types:
        return {
            'error': f'Invalid variable type: {variable_type}',
            'valid_types': valid_types
        }
    
    payload = {
        'cat_item': item_sys_id,
        'name': name,
        'question_text': question,
        'type': variable_type,
        'mandatory': 'true' if mandatory else 'false',
        'active': 'true'
    }
    
    if default_value:
        payload['default_value'] = default_value
    
    if validation_script:
        payload['validation_script'] = validation_script
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'item_option_new',
            'record': payload,
            'choices_to_create': len(choices) if choices else 0
        }
    
    # Create the variable
    result = client.create_record('item_option_new', payload)
    variable_sys_id = result.get('sys_id')
    
    # Add choices if provided
    choice_results = []
    if choices and variable_type in ['choice', 'multiple_choice']:
        for choice in choices:
            choice_payload = {
                'item_option_new': variable_sys_id,
                'text': choice,
                'value': choice,
                'order': str(choices.index(choice) + 1)
            }
            choice_result = client.create_record('question_choice', choice_payload)
            choice_results.append(choice_result)
    
    log("add_catalog_variable_with_validation", {
        "variable_sys_id": variable_sys_id,
        "item_sys_id": item_sys_id,
        "name": name,
        "choices_created": len(choice_results)
    })
    
    return {
        'variable': result,
        'choices': choice_results
    }

def create_catalog_workflow(client: ServiceNowClient, name: str, table: str = "sc_req_item",
                          scope: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
    """Create a catalog workflow"""
    
    payload = {
        'name': name,
        'table': table,
        'active': 'true'
    }
    
    if scope:
        payload['sys_scope'] = scope
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'wf_workflow',
            'record': payload
        }
    
    result = client.create_record('wf_workflow', payload)
    log("create_catalog_workflow", {
        "sys_id": result.get("sys_id"),
        "name": name
    })
    
    return result

def add_approval_step(client: ServiceNowClient, workflow_sys_id: str, approver: str,
                     condition: str = "", order: int = 1, dry_run: bool = False) -> Dict[str, Any]:
    """Add approval step to workflow"""
    
    payload = {
        'workflow': workflow_sys_id,
        'approver': approver,
        'condition': condition,
        'order': str(order),
        'active': 'true'
    }
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'wf_activity',
            'record': payload
        }
    
    result = client.create_record('wf_activity', payload)
    log("add_approval_step", {
        "sys_id": result.get("sys_id"),
        "workflow": workflow_sys_id,
        "approver": approver
    })
    
    return result

def create_fulfillment_script_template(item_name: str, variables: List[str]) -> str:
    """Generate a fulfillment script template"""
    
    script_lines = [
        "// Fulfillment script for " + item_name,
        "// This script runs when the catalog item is ordered",
        "",
        "(function() {",
        "    // Get the current request item",
        "    var reqItem = current;",
        "    var request = reqItem.request.getRefRecord();",
        "",
        "    // Get variable values"
    ]
    
    for var in variables:
        script_lines.append(f"    var {var} = reqItem.variables.{var};")
    
    script_lines.extend([
        "",
        "    // Add your fulfillment logic here",
        "    // Example: Create a task, send notification, etc.",
        "",
        "    // Log the fulfillment",
        "    gs.info('Fulfilling catalog item: ' + reqItem.cat_item.name + ' for user: ' + request.requested_for.name);",
        "",
        "    // Set the request item to fulfilled",
        "    reqItem.state = 3; // Fulfilled",
        "    reqItem.update();",
        "",
        "})();"
    ])
    
    return "\n".join(script_lines)

def validate_catalog_item_setup(client: ServiceNowClient, item_sys_id: str) -> Dict[str, Any]:
    """Validate catalog item setup for best practices"""
    
    issues = []
    recommendations = []
    
    # Get catalog item details
    item = client.get_record('sc_cat_item', item_sys_id, 
                           fields=['name', 'short_description', 'description', 
                                  'category', 'workflow', 'script', 'price'])
    
    if not item:
        return {'error': 'Catalog item not found'}
    
    # Check basic fields
    if not item.get('short_description'):
        issues.append("Missing short description")
    
    if not item.get('description'):
        recommendations.append("Consider adding a detailed description")
    
    if not item.get('category'):
        issues.append("Catalog item must be assigned to a category")
    
    # Check variables
    variables = client.query_table('item_option_new',
                                 query=f"cat_item={item_sys_id}",
                                 fields=['name', 'question_text', 'type', 'mandatory'])
    
    if len(variables) == 0:
        recommendations.append("Consider adding variables to collect user input")
    
    # Check for mandatory variables without default values
    for var in variables:
        if var.get('mandatory') == 'true' and not var.get('default_value'):
            recommendations.append(f"Mandatory variable '{var.get('name')}' should have a default value")
    
    # Check workflow
    if not item.get('workflow'):
        recommendations.append("Consider adding a workflow for approval/fulfillment")
    
    # Check fulfillment script
    if not item.get('script'):
        recommendations.append("Consider adding a fulfillment script for automation")
    
    # Check pricing
    price = float(item.get('price', 0))
    if price > 0 and not item.get('workflow'):
        recommendations.append("Items with cost should have approval workflow")
    
    return {
        'item_name': item.get('name'),
        'variables_count': len(variables),
        'has_workflow': bool(item.get('workflow')),
        'has_fulfillment_script': bool(item.get('script')),
        'issues': issues,
        'recommendations': recommendations,
        'compliance_score': max(0, 100 - (len(issues) * 20) - (len(recommendations) * 5))
    }

def create_catalog_client_script_with_validation(client: ServiceNowClient, item_sys_id: str,
                                               ui_type: str, script: str, 
                                               dry_run: bool = False) -> Dict[str, Any]:
    """Create catalog client script with validation"""
    
    # Validate UI type
    valid_ui_types = ['onLoad', 'onChange', 'onSubmit', 'onCellEdit']
    if ui_type not in valid_ui_types:
        return {
            'error': f'Invalid UI type: {ui_type}',
            'valid_types': valid_ui_types
        }
    
    # Basic script validation
    issues = []
    if 'alert(' in script:
        issues.append("Avoid alert() - use g_form.addInfoMessage() instead")
    
    if ui_type == 'onSubmit' and 'return' not in script:
        issues.append("onSubmit scripts should return true/false")
    
    if 'g_form.setValue(' in script and ui_type == 'onLoad':
        issues.append("Setting values in onLoad may cause infinite loops")
    
    payload = {
        'cat_item': item_sys_id,
        'ui_type': ui_type,
        'script': script,
        'active': 'true'
    }
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'sc_cat_item_client_script',
            'record': payload,
            'validation_issues': issues
        }
    
    if issues:
        return {
            'warning': 'Script has validation issues',
            'issues': issues,
            'proceed_anyway': False
        }
    
    result = client.create_record('sc_cat_item_client_script', payload)
    log("create_catalog_client_script_with_validation", {
        "sys_id": result.get("sys_id"),
        "item_sys_id": item_sys_id,
        "ui_type": ui_type
    })
    
    return {
        'result': result,
        'validation_issues': issues
    }

def audit_catalog_best_practices(client: ServiceNowClient, scope: Optional[str] = None) -> Dict[str, Any]:
    """Audit catalog setup for best practices compliance"""
    
    query = f"sys_scope.scope={scope}" if scope else ""
    
    # Get all catalog items
    items = client.query_table('sc_cat_item', query=query,
                             fields=['sys_id', 'name', 'category', 'workflow', 'script'])
    
    issues = []
    recommendations = []
    item_scores = []
    
    for item in items:
        item_validation = validate_catalog_item_setup(client, item.get('sys_id'))
        issues.extend([f"Item '{item.get('name')}': {issue}" for issue in item_validation.get('issues', [])])
        recommendations.extend([f"Item '{item.get('name')}': {rec}" for rec in item_validation.get('recommendations', [])])
        item_scores.append(item_validation.get('compliance_score', 0))
    
    # Calculate overall score
    overall_score = sum(item_scores) / len(item_scores) if item_scores else 0
    
    return {
        'scope': scope,
        'summary': {
            'total_items': len(items),
            'items_with_workflow': len([i for i in items if i.get('workflow')]),
            'items_with_script': len([i for i in items if i.get('script')]),
            'total_issues': len(issues),
            'total_recommendations': len(recommendations)
        },
        'issues': issues,
        'recommendations': recommendations,
        'overall_compliance_score': round(overall_score, 2)
    }