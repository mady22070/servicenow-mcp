"""
ServiceNow Scoped Application Management Pack

This pack provides comprehensive scoped application management including:
- Application creation and configuration
- Dependency management
- Application file management
- Version control
- Publishing and distribution
- Best practices validation
"""

from typing import Dict, Any, List, Optional
import re
from ..servicenow_client import ServiceNowClient
from ..utils.audit_simple import log

def create_scoped_application(client: ServiceNowClient, name: str, scope: str, 
                            version: str = "1.0.0", description: str = "",
                            vendor: str = "", vendor_prefix: str = "",
                            dry_run: bool = False) -> Dict[str, Any]:
    """Create a new scoped application with comprehensive setup"""
    
    # Validate scope naming convention
    if not re.match(r'^x_[a-z0-9_]+$', scope):
        return {
            'error': 'Invalid scope format. Must start with x_ and contain only lowercase letters, numbers, and underscores',
            'example': 'x_my_app'
        }
    
    # Validate version format
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        return {
            'error': 'Invalid version format. Must be in format X.Y.Z (e.g., 1.0.0)',
            'example': '1.0.0'
        }
    
    payload = {
        'name': name,
        'scope': scope,
        'version': version,
        'short_description': description,
        'vendor': vendor,
        'vendor_prefix': vendor_prefix,
        'active': 'true',
        'can_edit_in_studio': 'true',
        'enforce_license': 'false',
        'private': 'true'
    }
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'sys_app',
            'record': payload,
            'validation': {
                'scope_valid': True,
                'version_valid': True,
                'recommended_setup': [
                    'Create application tables',
                    'Set up application roles',
                    'Configure application properties',
                    'Add application documentation'
                ]
            }
        }
    
    # Check if application already exists
    existing_app = client.query_table('sys_app', 
                                     query=f'scope={scope}',
                                     fields=['sys_id', 'name', 'version'])
    
    if existing_app:
        return {
            'warning': 'Application already exists',
            'existing_application': existing_app[0],
            'skipped': True,
            'message': f'Application with scope {scope} already exists: "{existing_app[0].get("name")}" v{existing_app[0].get("version")}'
        }
    
    result = client.create_record('sys_app', payload)
    app_sys_id = result.get('sys_id')
    
    # Check and create default application role
    existing_user_role = client.query_table('sys_user_role',
                                           query=f'name={scope}_user',
                                           fields=['sys_id', 'name'])
    
    if existing_user_role:
        role_result = {'sys_id': existing_user_role[0]['sys_id'], 'existing': True}
    else:
        role_result = client.create_record('sys_user_role', {
            'name': f'{scope}_user',
            'description': f'Default user role for {name}',
            'sys_scope': app_sys_id
        })
    
    # Check and create admin role for the application
    existing_admin_role = client.query_table('sys_user_role',
                                            query=f'name={scope}_admin',
                                            fields=['sys_id', 'name'])
    
    if existing_admin_role:
        admin_role_result = {'sys_id': existing_admin_role[0]['sys_id'], 'existing': True}
    else:
        admin_role_result = client.create_record('sys_user_role', {
            'name': f'{scope}_admin',
            'description': f'Admin role for {name}',
            'sys_scope': app_sys_id
        })
    
    # Create application properties category
    prop_category_result = client.create_record('sys_properties_category', {
        'name': scope,
        'title': f'{name} Properties',
        'sys_scope': app_sys_id
    })
    
    # Check and create main application menu
    existing_app_menu = client.query_table('sys_app_module',
                                          query=f'application={app_sys_id}^title={name}^link_type=SEPARATOR',
                                          fields=['sys_id', 'title'])
    
    if existing_app_menu:
        app_menu_result = {'sys_id': existing_app_menu[0]['sys_id'], 'existing': True}
    else:
        app_menu_result = client.create_record('sys_app_module', {
            'title': name,
            'hint': description or f'Access {name} application',
            'order': '100',
            'roles': f'{scope}_user',
            'active': 'true',
            'sys_scope': app_sys_id,
            'application': app_sys_id,
            'name': '',  # Empty name makes it a menu header
            'link_type': 'SEPARATOR'
        })
    
    # Check and create "Home" module under the application menu
    existing_home_module = client.query_table('sys_app_module',
                                             query=f'application={app_sys_id}^name={scope}_home',
                                             fields=['sys_id', 'title'])
    
    if existing_home_module:
        home_module_result = {'sys_id': existing_home_module[0]['sys_id'], 'existing': True}
    else:
        home_module_result = client.create_record('sys_app_module', {
            'title': f'{name} Home',
            'hint': f'Home page for {name}',
            'order': '110',
            'roles': f'{scope}_user',
            'active': 'true',
            'sys_scope': app_sys_id,
            'application': app_sys_id,
            'name': f'{scope}_home',
            'link_type': 'HOMEPAGE'
        })
    
    # Create "All" module for main table (if we can determine it)
    # This will be enhanced when tables are created
    
    log("create_scoped_application", {
        "app_sys_id": app_sys_id,
        "name": name,
        "scope": scope,
        "role_created": role_result.get('sys_id'),
        "admin_role_created": admin_role_result.get('sys_id'),
        "prop_category_created": prop_category_result.get('sys_id'),
        "app_menu_created": app_menu_result.get('sys_id'),
        "home_module_created": home_module_result.get('sys_id')
    })
    
    return {
        'application': result,
        'default_role': role_result,
        'admin_role': admin_role_result,
        'properties_category': prop_category_result,
        'application_menu': app_menu_result,
        'home_module': home_module_result,
        'navigation_created': True,
        'next_steps': [
            'Application menu created and should appear in ServiceNow navigation',
            'Create tables using create_table_with_navigation() to add table modules',
            'Assign users the appropriate roles to access the application'
        ]
    }

def add_application_dependency(client: ServiceNowClient, app_sys_id: str, 
                             dependency_scope: str, min_version: str = "1.0.0",
                             dry_run: bool = False) -> Dict[str, Any]:
    """Add dependency to scoped application"""
    
    # Check if dependency application exists
    dep_apps = client.query_table('sys_app', 
                                query=f'scope={dependency_scope}',
                                fields=['sys_id', 'name', 'version'])
    
    if not dep_apps:
        return {
            'error': f'Dependency application with scope {dependency_scope} not found'
        }
    
    dep_app = dep_apps[0]
    
    payload = {
        'source': app_sys_id,
        'target': dep_app.get('sys_id'),
        'min_version': min_version,
        'type': 'depends_on'
    }
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'sys_app_dependency',
            'record': payload,
            'dependency_info': {
                'name': dep_app.get('name'),
                'current_version': dep_app.get('version')
            }
        }
    
    result = client.create_record('sys_app_dependency', payload)
    log("add_application_dependency", {
        "sys_id": result.get("sys_id"),
        "app_sys_id": app_sys_id,
        "dependency_scope": dependency_scope
    })
    
    return result

def create_application_property(client: ServiceNowClient, app_sys_id: str, name: str,
                              value: str, description: str = "", 
                              property_type: str = "string", dry_run: bool = False) -> Dict[str, Any]:
    """Create application-specific system property"""
    
    # Get application scope
    app = client.get_record('sys_app', app_sys_id, fields=['scope'])
    if not app:
        return {'error': 'Application not found'}
    
    scope = app.get('scope')
    property_name = f"{scope}.{name}"
    
    payload = {
        'name': property_name,
        'value': value,
        'description': description,
        'type': property_type,
        'sys_scope': app_sys_id
    }
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'sys_properties',
            'record': payload,
            'full_property_name': property_name
        }
    
    result = client.create_record('sys_properties', payload)
    log("create_application_property", {
        "sys_id": result.get("sys_id"),
        "property_name": property_name,
        "app_sys_id": app_sys_id
    })
    
    return result

def create_application_file(client: ServiceNowClient, app_sys_id: str, name: str,
                          content: str, file_type: str = "script_include",
                          dry_run: bool = False) -> Dict[str, Any]:
    """Create application file (script include, business rule, etc.)"""
    
    # Map file types to tables
    file_type_mapping = {
        'script_include': 'sys_script_include',
        'business_rule': 'sys_script',
        'client_script': 'sys_script_client',
        'ui_policy': 'ui_policy',
        'ui_action': 'sys_ui_action'
    }
    
    if file_type not in file_type_mapping:
        return {
            'error': f'Invalid file type: {file_type}',
            'valid_types': list(file_type_mapping.keys())
        }
    
    table = file_type_mapping[file_type]
    
    payload = {
        'name': name,
        'sys_scope': app_sys_id,
        'active': 'true'
    }
    
    # Add type-specific fields
    if file_type == 'script_include':
        payload['script'] = content
        payload['api_name'] = name
    elif file_type == 'business_rule':
        payload['script'] = content
        payload['table'] = 'incident'  # Default table
        payload['when'] = 'before'
    elif file_type == 'client_script':
        payload['script'] = content
        payload['table'] = 'incident'  # Default table
        payload['ui_type'] = 'onLoad'
    
    if dry_run:
        return {
            'dry_run': True,
            'table': table,
            'record': payload,
            'file_type': file_type
        }
    
    result = client.create_record(table, payload)
    log("create_application_file", {
        "sys_id": result.get("sys_id"),
        "name": name,
        "file_type": file_type,
        "app_sys_id": app_sys_id
    })
    
    return result

def validate_application_structure(client: ServiceNowClient, app_sys_id: str) -> Dict[str, Any]:
    """Validate scoped application structure and best practices"""
    
    issues = []
    recommendations = []
    
    # Get application details
    app = client.get_record('sys_app', app_sys_id,
                          fields=['name', 'scope', 'version', 'short_description', 'vendor'])
    
    if not app:
        return {'error': 'Application not found'}
    
    scope = app.get('scope')
    
    # Check basic application properties
    if not app.get('short_description'):
        issues.append("Application missing description")
    
    if not app.get('vendor'):
        recommendations.append("Consider adding vendor information")
    
    # Check application tables
    tables = client.query_table('sys_db_object',
                              query=f'sys_scope.scope={scope}',
                              fields=['name', 'label'])
    
    if len(tables) == 0:
        recommendations.append("Consider creating application-specific tables")
    
    # Validate table naming
    for table in tables:
        table_name = table.get('name', '')
        if not table_name.startswith(f'x_{scope.replace("x_", "")}_'):
            issues.append(f"Table '{table_name}' doesn't follow naming convention")
    
    # Check application roles
    roles = client.query_table('sys_user_role',
                             query=f'sys_scope.scope={scope}',
                             fields=['name'])
    
    if len(roles) == 0:
        recommendations.append("Consider creating application-specific roles")
    
    # Check application properties
    properties = client.query_table('sys_properties',
                                  query=f'sys_scope.scope={scope}',
                                  fields=['name', 'value'])
    
    if len(properties) == 0:
        recommendations.append("Consider adding application properties for configuration")
    
    # Check script includes
    script_includes = client.query_table('sys_script_include',
                                       query=f'sys_scope.scope={scope}',
                                       fields=['name', 'api_name'])
    
    # Check business rules
    business_rules = client.query_table('sys_script',
                                      query=f'sys_scope.scope={scope}',
                                      fields=['name', 'table'])
    
    # Check client scripts
    client_scripts = client.query_table('sys_script_client',
                                      query=f'sys_scope.scope={scope}',
                                      fields=['name', 'table'])
    
    # Check dependencies
    dependencies = client.query_table('sys_app_dependency',
                                    query=f'source={app_sys_id}',
                                    fields=['target.name', 'min_version'])
    
    return {
        'application_name': app.get('name'),
        'scope': scope,
        'summary': {
            'tables': len(tables),
            'roles': len(roles),
            'properties': len(properties),
            'script_includes': len(script_includes),
            'business_rules': len(business_rules),
            'client_scripts': len(client_scripts),
            'dependencies': len(dependencies)
        },
        'issues': issues,
        'recommendations': recommendations,
        'compliance_score': max(0, 100 - (len(issues) * 15) - (len(recommendations) * 5))
    }

def package_application(client: ServiceNowClient, app_sys_id: str, 
                       include_data: bool = False) -> Dict[str, Any]:
    """Package application for distribution"""
    
    app = client.get_record('sys_app', app_sys_id,
                          fields=['name', 'scope', 'version'])
    
    if not app:
        return {'error': 'Application not found'}
    
    scope = app.get('scope')
    
    # Get all application components
    components = {}
    
    # Tables
    components['tables'] = client.query_table('sys_db_object',
                                            query=f'sys_scope.scope={scope}',
                                            fields=['name', 'label', 'super_class'])
    
    # Fields
    components['fields'] = client.query_table('sys_dictionary',
                                            query=f'sys_scope.scope={scope}',
                                            fields=['name', 'element', 'column_label', 'internal_type'])
    
    # Script Includes
    components['script_includes'] = client.query_table('sys_script_include',
                                                     query=f'sys_scope.scope={scope}',
                                                     fields=['name', 'api_name', 'script'])
    
    # Business Rules
    components['business_rules'] = client.query_table('sys_script',
                                                    query=f'sys_scope.scope={scope}',
                                                    fields=['name', 'table', 'when', 'script'])
    
    # Client Scripts
    components['client_scripts'] = client.query_table('sys_script_client',
                                                    query=f'sys_scope.scope={scope}',
                                                    fields=['name', 'table', 'ui_type', 'script'])
    
    # UI Policies
    components['ui_policies'] = client.query_table('ui_policy',
                                                 query=f'sys_scope.scope={scope}',
                                                 fields=['short_description', 'table', 'condition'])
    
    # Roles
    components['roles'] = client.query_table('sys_user_role',
                                           query=f'sys_scope.scope={scope}',
                                           fields=['name', 'description'])
    
    # Properties
    components['properties'] = client.query_table('sys_properties',
                                                 query=f'sys_scope.scope={scope}',
                                                 fields=['name', 'value', 'description'])
    
    # Calculate package size
    total_components = sum(len(comp_list) for comp_list in components.values())
    
    package_info = {
        'application': app,
        'components': components,
        'package_summary': {
            'total_components': total_components,
            'tables': len(components['tables']),
            'script_includes': len(components['script_includes']),
            'business_rules': len(components['business_rules']),
            'client_scripts': len(components['client_scripts']),
            'ui_policies': len(components['ui_policies']),
            'roles': len(components['roles']),
            'properties': len(components['properties'])
        },
        'package_date': client.get_server_time(),
        'include_data': include_data
    }
    
    log("package_application", {
        "app_sys_id": app_sys_id,
        "scope": scope,
        "total_components": total_components
    })
    
    return package_info

def create_table_with_navigation(client: ServiceNowClient, app_sys_id: str, 
                               table_name: str, table_label: str, extends: str = None,
                               create_navigation: bool = True, dry_run: bool = False) -> Dict[str, Any]:
    """Create a table and automatically add navigation modules for it"""
    
    if not dry_run:
        # Get application details
        app = client.get_record('sys_app', app_sys_id, fields=['name', 'scope'])
        if not app:
            return {'error': 'Application not found'}
        
        scope = app.get('scope')
        app_name = app.get('name')
    else:
        # For dry run, use mock values
        scope = 'x_mock_scope'
        app_name = 'Mock Application'
    
    # Ensure table name follows scoped naming convention
    if not table_name.startswith(f'x_{scope.replace("x_", "")}_'):
        table_name = f'x_{scope.replace("x_", "")}_{table_name}'
    
    # Create the table
    table_payload = {
        'name': table_name,
        'label': table_label,
        'sys_scope': app_sys_id,
        'is_extendable': 'false',
        'access': 'public'
    }
    
    if extends:
        table_payload['super_class'] = extends
    
    if dry_run:
        navigation_modules = []
        if create_navigation:
            navigation_modules = [
                f'{table_label} - All',
                f'{table_label} - Create New',
                f'{table_label} - My Records'
            ]
        
        return {
            'dry_run': True,
            'table': 'sys_db_object',
            'table_record': table_payload,
            'navigation_modules': navigation_modules,
            'app_info': {
                'name': app_name,
                'scope': scope
            }
        }
    
    # Create the table
    table_result = client.create_record('sys_db_object', table_payload)
    table_sys_id = table_result.get('sys_id')
    
    navigation_results = []
    
    if create_navigation:
        # Create "All [Table]" module
        all_module = client.create_record('sys_app_module', {
            'title': f'{table_label}',
            'hint': f'View all {table_label.lower()} records',
            'order': '200',
            'roles': f'{scope}_user',
            'active': 'true',
            'sys_scope': app_sys_id,
            'application': app_sys_id,
            'name': table_name,
            'link_type': 'LIST'
        })
        navigation_results.append(('all_records', all_module))
        
        # Create "Create New [Table]" module
        create_module = client.create_record('sys_app_module', {
            'title': f'Create {table_label}',
            'hint': f'Create a new {table_label.lower()} record',
            'order': '210',
            'roles': f'{scope}_user',
            'active': 'true',
            'sys_scope': app_sys_id,
            'application': app_sys_id,
            'name': f'{table_name}_create',
            'link_type': 'NEW',
            'query': f'sysparm_table={table_name}'
        })
        navigation_results.append(('create_new', create_module))
        
        # Create "My [Table]" module (if table has created_by field)
        my_records_module = client.create_record('sys_app_module', {
            'title': f'My {table_label}',
            'hint': f'View {table_label.lower()} records I created',
            'order': '220',
            'roles': f'{scope}_user',
            'active': 'true',
            'sys_scope': app_sys_id,
            'application': app_sys_id,
            'name': f'{table_name}_my',
            'link_type': 'LIST',
            'query': f'{table_name}_list.do?sysparm_query=sys_created_by=javascript:gs.getUserName()'
        })
        navigation_results.append(('my_records', my_records_module))
    
    log("create_table_with_navigation", {
        "table_sys_id": table_sys_id,
        "table_name": table_name,
        "app_sys_id": app_sys_id,
        "navigation_modules_created": len(navigation_results)
    })
    
    return {
        'table': table_result,
        'navigation_modules': {name: result for name, result in navigation_results},
        'table_name': table_name,
        'app_name': app_name,
        'navigation_created': len(navigation_results) > 0,
        'access_info': {
            'list_view': f'{table_name}_list.do',
            'form_view': f'{table_name}.do',
            'create_new': f'{table_name}.do?sys_id=-1'
        }
    }

def create_application_navigation_module(client: ServiceNowClient, app_sys_id: str,
                                       title: str, link_type: str, target: str = "",
                                       roles: str = None, order: int = 500,
                                       dry_run: bool = False) -> Dict[str, Any]:
    """Create a custom navigation module for an application"""
    
    if not dry_run:
        # Get application details
        app = client.get_record('sys_app', app_sys_id, fields=['name', 'scope'])
        if not app:
            return {'error': 'Application not found'}
        
        scope = app.get('scope')
    else:
        # For dry run, use mock values
        app = {'name': 'Mock Application', 'scope': 'x_mock_scope'}
        scope = 'x_mock_scope'
    
    # Default role if not specified
    if not roles:
        roles = f'{scope}_user'
    
    # Validate link type
    valid_link_types = ['LIST', 'NEW', 'HOMEPAGE', 'URL', 'SEPARATOR', 'REPORT']
    if link_type not in valid_link_types:
        return {
            'error': f'Invalid link type: {link_type}',
            'valid_types': valid_link_types
        }
    
    payload = {
        'title': title,
        'hint': f'Access {title}',
        'order': str(order),
        'roles': roles,
        'active': 'true',
        'sys_scope': app_sys_id,
        'application': app_sys_id,
        'link_type': link_type
    }
    
    # Add target-specific fields
    if link_type == 'LIST' and target:
        payload['name'] = target
    elif link_type == 'URL' and target:
        payload['query'] = target
    elif link_type == 'NEW' and target:
        payload['name'] = f'{target}_create'
        payload['query'] = f'sysparm_table={target}'
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'sys_app_module',
            'record': payload,
            'app_info': {
                'name': app.get('name'),
                'scope': scope
            }
        }
    
    result = client.create_record('sys_app_module', payload)
    
    log("create_application_navigation_module", {
        "sys_id": result.get("sys_id"),
        "title": title,
        "app_sys_id": app_sys_id,
        "link_type": link_type
    })
    
    return result

def audit_scoped_applications(client: ServiceNowClient) -> Dict[str, Any]:
    """Audit all scoped applications for best practices"""
    
    # Get all scoped applications
    apps = client.query_table('sys_app',
                             query='scope!=global',
                             fields=['sys_id', 'name', 'scope', 'version', 'active'])
    
    issues = []
    recommendations = []
    app_scores = []
    
    for app in apps:
        app_validation = validate_application_structure(client, app.get('sys_id'))
        app_name = app.get('name')
        
        issues.extend([f"App '{app_name}': {issue}" for issue in app_validation.get('issues', [])])
        recommendations.extend([f"App '{app_name}': {rec}" for rec in app_validation.get('recommendations', [])])
        app_scores.append(app_validation.get('compliance_score', 0))
    
    # Calculate overall score
    overall_score = sum(app_scores) / len(app_scores) if app_scores else 0
    
    return {
        'summary': {
            'total_applications': len(apps),
            'active_applications': len([a for a in apps if a.get('active') == 'true']),
            'total_issues': len(issues),
            'total_recommendations': len(recommendations)
        },
        'applications': [
            {
                'name': app.get('name'),
                'scope': app.get('scope'),
                'version': app.get('version'),
                'active': app.get('active') == 'true'
            }
            for app in apps
        ],
        'issues': issues,
        'recommendations': recommendations,
        'overall_compliance_score': round(overall_score, 2)
    }