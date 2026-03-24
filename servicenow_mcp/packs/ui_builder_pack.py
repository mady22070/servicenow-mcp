"""
ServiceNow UI Builder Pack

This pack provides comprehensive UI Builder capabilities including:
- UI Builder page creation
- Component management
- Data binding
- Event handling
- Theme management
- Best practices validation
"""

from typing import Dict, Any, List, Optional
import json
from ..servicenow_client import ServiceNowClient
from ..utils.audit_simple import log

# UI Builder component types and their properties
UI_BUILDER_COMPONENTS = {
    'form': {
        'required_props': ['table', 'sys_id'],
        'optional_props': ['fields', 'view', 'readonly']
    },
    'list': {
        'required_props': ['table'],
        'optional_props': ['query', 'fields', 'limit', 'order_by']
    },
    'button': {
        'required_props': ['label'],
        'optional_props': ['variant', 'size', 'disabled', 'icon']
    },
    'text': {
        'required_props': ['value'],
        'optional_props': ['variant', 'size', 'color']
    },
    'container': {
        'required_props': [],
        'optional_props': ['direction', 'spacing', 'align', 'justify']
    },
    'card': {
        'required_props': [],
        'optional_props': ['title', 'subtitle', 'elevation', 'variant']
    }
}

def create_ui_builder_page(client: ServiceNowClient, name: str, title: str, 
                          description: str = "", scope: Optional[str] = None,
                          dry_run: bool = False) -> Dict[str, Any]:
    """Create a UI Builder page with best practices"""
    
    payload = {
        'name': name,
        'title': title,
        'description': description,
        'active': 'true',
        'type': 'page'
    }
    
    if scope:
        payload['sys_scope'] = scope
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'sys_ux_page',
            'record': payload,
            'best_practices': {
                'naming_convention': name.replace(' ', '_').lower() == name,
                'has_description': bool(description)
            }
        }
    
    result = client.create_record('sys_ux_page', payload)
    log("create_ui_builder_page", {
        "sys_id": result.get("sys_id"),
        "name": name,
        "title": title
    })
    
    return result

def add_ui_builder_component(client: ServiceNowClient, page_sys_id: str, 
                           component_type: str, component_id: str,
                           properties: Dict[str, Any], position: Dict[str, int] = None,
                           dry_run: bool = False) -> Dict[str, Any]:
    """Add component to UI Builder page with validation"""
    
    # Validate component type
    if component_type not in UI_BUILDER_COMPONENTS:
        return {
            'error': f'Invalid component type: {component_type}',
            'valid_types': list(UI_BUILDER_COMPONENTS.keys())
        }
    
    # Validate required properties
    component_config = UI_BUILDER_COMPONENTS[component_type]
    missing_props = []
    for prop in component_config['required_props']:
        if prop not in properties:
            missing_props.append(prop)
    
    if missing_props:
        return {
            'error': f'Missing required properties: {missing_props}',
            'required_props': component_config['required_props']
        }
    
    # Default position if not provided
    if position is None:
        position = {'x': 0, 'y': 0, 'width': 12, 'height': 4}
    
    payload = {
        'page': page_sys_id,
        'component_id': component_id,
        'component_type': component_type,
        'properties': json.dumps(properties),
        'position': json.dumps(position),
        'active': 'true'
    }
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'sys_ux_component',
            'record': payload,
            'validation': {
                'component_type': component_type,
                'required_props_met': len(missing_props) == 0,
                'properties_count': len(properties)
            }
        }
    
    result = client.create_record('sys_ux_component', payload)
    log("add_ui_builder_component", {
        "sys_id": result.get("sys_id"),
        "page_sys_id": page_sys_id,
        "component_type": component_type,
        "component_id": component_id
    })
    
    return result

def create_data_binding(client: ServiceNowClient, page_sys_id: str, binding_name: str,
                       data_source: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    """Create data binding for UI Builder page"""
    
    # Validate data source
    required_fields = ['type', 'table']
    missing_fields = [f for f in required_fields if f not in data_source]
    
    if missing_fields:
        return {
            'error': f'Missing required data source fields: {missing_fields}',
            'required_fields': required_fields
        }
    
    payload = {
        'page': page_sys_id,
        'name': binding_name,
        'data_source': json.dumps(data_source),
        'active': 'true'
    }
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'sys_ux_data_binding',
            'record': payload
        }
    
    result = client.create_record('sys_ux_data_binding', payload)
    log("create_data_binding", {
        "sys_id": result.get("sys_id"),
        "page_sys_id": page_sys_id,
        "binding_name": binding_name
    })
    
    return result

def add_event_handler(client: ServiceNowClient, component_sys_id: str, event_type: str,
                     handler_script: str, dry_run: bool = False) -> Dict[str, Any]:
    """Add event handler to UI Builder component"""
    
    # Validate event type
    valid_events = ['click', 'change', 'load', 'submit', 'focus', 'blur']
    if event_type not in valid_events:
        return {
            'error': f'Invalid event type: {event_type}',
            'valid_events': valid_events
        }
    
    # Basic script validation
    script_issues = []
    if 'alert(' in handler_script:
        script_issues.append("Avoid alert() in UI Builder - use notifications instead")
    
    if 'document.' in handler_script:
        script_issues.append("Avoid direct DOM manipulation - use UI Builder APIs")
    
    payload = {
        'component': component_sys_id,
        'event_type': event_type,
        'handler_script': handler_script,
        'active': 'true'
    }
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'sys_ux_event_handler',
            'record': payload,
            'script_issues': script_issues
        }
    
    if script_issues:
        return {
            'warning': 'Script has validation issues',
            'issues': script_issues,
            'proceed_anyway': False
        }
    
    result = client.create_record('sys_ux_event_handler', payload)
    log("add_event_handler", {
        "sys_id": result.get("sys_id"),
        "component_sys_id": component_sys_id,
        "event_type": event_type
    })
    
    return result

def create_ui_builder_theme(client: ServiceNowClient, name: str, colors: Dict[str, str],
                          typography: Dict[str, Any] = None, scope: Optional[str] = None,
                          dry_run: bool = False) -> Dict[str, Any]:
    """Create custom theme for UI Builder"""
    
    # Default typography if not provided
    if typography is None:
        typography = {
            'font_family': 'Source Sans Pro, sans-serif',
            'font_sizes': {
                'small': '12px',
                'medium': '14px',
                'large': '16px',
                'xlarge': '20px'
            }
        }
    
    theme_config = {
        'colors': colors,
        'typography': typography
    }
    
    payload = {
        'name': name,
        'theme_config': json.dumps(theme_config),
        'active': 'true'
    }
    
    if scope:
        payload['sys_scope'] = scope
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'sys_ux_theme',
            'record': payload,
            'theme_preview': theme_config
        }
    
    result = client.create_record('sys_ux_theme', payload)
    log("create_ui_builder_theme", {
        "sys_id": result.get("sys_id"),
        "name": name
    })
    
    return result

def validate_ui_builder_page(client: ServiceNowClient, page_sys_id: str) -> Dict[str, Any]:
    """Validate UI Builder page for best practices"""
    
    issues = []
    recommendations = []
    
    # Get page details
    page = client.get_record('sys_ux_page', page_sys_id,
                           fields=['name', 'title', 'description', 'active'])
    
    if not page:
        return {'error': 'Page not found'}
    
    # Check basic page properties
    if not page.get('description'):
        recommendations.append("Add a description to explain the page purpose")
    
    if page.get('active') != 'true':
        issues.append("Page is not active")
    
    # Get components
    components = client.query_table('sys_ux_component',
                                  query=f"page={page_sys_id}",
                                  fields=['component_type', 'component_id', 'properties'])
    
    if len(components) == 0:
        issues.append("Page has no components")
    
    # Validate components
    component_ids = []
    for comp in components:
        comp_id = comp.get('component_id')
        if comp_id in component_ids:
            issues.append(f"Duplicate component ID: {comp_id}")
        component_ids.append(comp_id)
        
        # Check component properties
        try:
            props = json.loads(comp.get('properties', '{}'))
            comp_type = comp.get('component_type')
            
            if comp_type in UI_BUILDER_COMPONENTS:
                required_props = UI_BUILDER_COMPONENTS[comp_type]['required_props']
                missing_props = [p for p in required_props if p not in props]
                if missing_props:
                    issues.append(f"Component {comp_id} missing required properties: {missing_props}")
        except json.JSONDecodeError:
            issues.append(f"Component {comp_id} has invalid properties JSON")
    
    # Get data bindings
    bindings = client.query_table('sys_ux_data_binding',
                                query=f"page={page_sys_id}",
                                fields=['name', 'data_source'])
    
    # Check for unused data bindings
    if len(bindings) > len(components):
        recommendations.append("Consider removing unused data bindings")
    
    # Get event handlers
    handlers = client.query_table('sys_ux_event_handler',
                                query=f"component.page={page_sys_id}",
                                fields=['event_type', 'handler_script'])
    
    # Validate event handlers
    for handler in handlers:
        script = handler.get('handler_script', '')
        if 'alert(' in script:
            issues.append("Event handler uses alert() - use notifications instead")
        if 'document.' in script:
            issues.append("Event handler uses direct DOM manipulation")
    
    return {
        'page_name': page.get('name'),
        'components_count': len(components),
        'bindings_count': len(bindings),
        'handlers_count': len(handlers),
        'issues': issues,
        'recommendations': recommendations,
        'compliance_score': max(0, 100 - (len(issues) * 15) - (len(recommendations) * 5))
    }

def generate_ui_builder_template(page_type: str, table_name: Optional[str] = None) -> Dict[str, Any]:
    """Generate UI Builder page template based on common patterns"""
    
    templates = {
        'form_page': {
            'components': [
                {
                    'type': 'container',
                    'id': 'main_container',
                    'properties': {'direction': 'column', 'spacing': 'medium'},
                    'position': {'x': 0, 'y': 0, 'width': 12, 'height': 8}
                },
                {
                    'type': 'form',
                    'id': 'record_form',
                    'properties': {'table': table_name or 'incident', 'view': 'default'},
                    'position': {'x': 0, 'y': 1, 'width': 12, 'height': 6}
                },
                {
                    'type': 'button',
                    'id': 'save_button',
                    'properties': {'label': 'Save', 'variant': 'primary'},
                    'position': {'x': 0, 'y': 7, 'width': 2, 'height': 1}
                }
            ],
            'data_bindings': [
                {
                    'name': 'record_data',
                    'data_source': {
                        'type': 'record',
                        'table': table_name or 'incident'
                    }
                }
            ]
        },
        'list_page': {
            'components': [
                {
                    'type': 'container',
                    'id': 'main_container',
                    'properties': {'direction': 'column', 'spacing': 'medium'},
                    'position': {'x': 0, 'y': 0, 'width': 12, 'height': 8}
                },
                {
                    'type': 'list',
                    'id': 'records_list',
                    'properties': {'table': table_name or 'incident', 'limit': 50},
                    'position': {'x': 0, 'y': 1, 'width': 12, 'height': 7}
                }
            ],
            'data_bindings': [
                {
                    'name': 'list_data',
                    'data_source': {
                        'type': 'table',
                        'table': table_name or 'incident'
                    }
                }
            ]
        },
        'dashboard': {
            'components': [
                {
                    'type': 'container',
                    'id': 'dashboard_container',
                    'properties': {'direction': 'row', 'spacing': 'medium'},
                    'position': {'x': 0, 'y': 0, 'width': 12, 'height': 8}
                },
                {
                    'type': 'card',
                    'id': 'metrics_card',
                    'properties': {'title': 'Key Metrics', 'elevation': 2},
                    'position': {'x': 0, 'y': 1, 'width': 6, 'height': 3}
                },
                {
                    'type': 'card',
                    'id': 'recent_items_card',
                    'properties': {'title': 'Recent Items', 'elevation': 2},
                    'position': {'x': 6, 'y': 1, 'width': 6, 'height': 3}
                }
            ],
            'data_bindings': [
                {
                    'name': 'metrics_data',
                    'data_source': {
                        'type': 'aggregate',
                        'table': table_name or 'incident'
                    }
                }
            ]
        }
    }
    
    if page_type not in templates:
        return {
            'error': f'Invalid page type: {page_type}',
            'available_types': list(templates.keys())
        }
    
    return {
        'page_type': page_type,
        'template': templates[page_type],
        'table_name': table_name
    }

def audit_ui_builder_best_practices(client: ServiceNowClient, scope: Optional[str] = None) -> Dict[str, Any]:
    """Audit UI Builder implementation for best practices"""
    
    query = f"sys_scope.scope={scope}" if scope else ""
    
    # Get all UI Builder pages
    pages = client.query_table('sys_ux_page', query=query,
                             fields=['sys_id', 'name', 'title', 'active'])
    
    issues = []
    recommendations = []
    page_scores = []
    
    for page in pages:
        page_validation = validate_ui_builder_page(client, page.get('sys_id'))
        issues.extend([f"Page '{page.get('name')}': {issue}" for issue in page_validation.get('issues', [])])
        recommendations.extend([f"Page '{page.get('name')}': {rec}" for rec in page_validation.get('recommendations', [])])
        page_scores.append(page_validation.get('compliance_score', 0))
    
    # Calculate overall score
    overall_score = sum(page_scores) / len(page_scores) if page_scores else 0
    
    return {
        'scope': scope,
        'summary': {
            'total_pages': len(pages),
            'active_pages': len([p for p in pages if p.get('active') == 'true']),
            'total_issues': len(issues),
            'total_recommendations': len(recommendations)
        },
        'issues': issues,
        'recommendations': recommendations,
        'overall_compliance_score': round(overall_score, 2)
    }