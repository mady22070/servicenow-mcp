
from typing import Any, Dict, List, Optional
from ..servicenow_client import ServiceNowClient
DEFAULT_SCOPE = "x_cloudorch_aiops"
def app_scaffold(client: ServiceNowClient, spec: Dict[str, Any], scope: Optional[str] = DEFAULT_SCOPE, dry_run: bool = False) -> Dict[str, Any]:
    actions = []
    for tbl in spec.get("tables", []):
        actions.append({"op": "create_table", "table_label": tbl["table_label"], "table_name": tbl["table_name"], "extends": tbl.get("extends"), "scope": scope})
        for f in tbl.get("fields", []):
            actions.append({"op": "add_field", "table_name": tbl["table_name"], "name": f["name"], "type": f.get("type","string"),
                            "label": f.get("label", f["name"]), "mandatory": f.get("mandatory", False),
                            "default": f.get("default"), "choices": f.get("choices"), "scope": scope})
    if dry_run:
        return {"dry_run": True, "planned_actions": actions, "counts": {"tables": sum(1 for a in actions if a['op']=='create_table'), "fields": sum(1 for a in actions if a['op']=='add_field') }}
    results = []
    for a in actions:
        if a["op"] == "create_table":
            results.append(client.create_table(a["table_label"], a["table_name"], a.get("extends"), a.get("scope")))
        elif a["op"] == "add_field":
            results.append(client.add_field(a["table_name"], a["name"], a["type"], a["label"], a["mandatory"], a.get("default"), a.get("choices"), a.get("scope")))
    return {"dry_run": False, "results": results}
def create_table_with_navigation_enhanced(client: ServiceNowClient, table_label: str, table_name: str, 
                                        extends: Optional[str] = None, scope: Optional[str] = DEFAULT_SCOPE, 
                                        create_navigation: bool = True, dry_run: bool = False) -> Dict[str, Any]:
    """Create table with navigation and duplicate prevention"""
    
    # Check if table already exists
    existing_table = client.query_table('sys_db_object', 
                                       query=f'name={table_name}',
                                       fields=['sys_id', 'name', 'label'])
    
    if existing_table:
        return {
            'warning': 'Table already exists',
            'existing_table': existing_table[0],
            'skipped': True,
            'message': f'Table {table_name} already exists with label "{existing_table[0].get("label")}"'
        }
    
    if dry_run:
        navigation_info = []
        if create_navigation:
            if scope == 'global':
                navigation_info = [
                    f'Global Application Menu: {table_label}',
                    f'All {table_label} module',
                    f'Create {table_label} module',
                    f'My {table_label} module'
                ]
            else:
                navigation_info = [
                    f'Scoped Application Menu under {scope}',
                    f'All {table_label} module',
                    f'Create {table_label} module', 
                    f'My {table_label} module'
                ]
        
        return {
            "dry_run": True, 
            "op": "create_table_with_navigation", 
            "table_label": table_label, 
            "table_name": table_name, 
            "extends": extends, 
            "scope": scope,
            "navigation_modules": navigation_info,
            "duplicate_check": "passed"
        }
    
    # Create the table
    table_result = client.create_table(table_label, table_name, extends, scope)
    
    navigation_results = []
    
    if create_navigation:
        if scope == 'global':
            # For global scope, create application menu if it doesn't exist
            navigation_results = _create_global_table_navigation(client, table_name, table_label)
        else:
            # For scoped applications, find the app and create navigation
            app = client.query_table('sys_app', query=f'scope={scope}', fields=['sys_id', 'name'])
            if app:
                app_sys_id = app[0]['sys_id']
                navigation_results = _create_scoped_table_navigation(client, app_sys_id, table_name, table_label, scope)
            else:
                navigation_results = [{'warning': f'No application found for scope {scope}'}]
    
    return {
        'table': table_result,
        'navigation_modules': navigation_results,
        'navigation_created': len(navigation_results) > 0,
        'scope': scope
    }

def _create_global_table_navigation(client: ServiceNowClient, table_name: str, table_label: str) -> List[Dict[str, Any]]:
    """Create navigation modules for global scope tables"""
    
    navigation_results = []
    
    # Check if application menu already exists for this table
    existing_menu = client.query_table('sys_app_module',
                                      query=f'title={table_label}^name={table_name}',
                                      fields=['sys_id', 'title'])
    
    if existing_menu:
        navigation_results.append({
            'type': 'existing_menu',
            'message': f'Navigation menu for {table_label} already exists',
            'sys_id': existing_menu[0]['sys_id']
        })
        return navigation_results
    
    # Create main table module (All records)
    all_module = client.create_record('sys_app_module', {
        'title': table_label,
        'hint': f'View all {table_label.lower()} records',
        'order': '100',
        'roles': 'admin',  # Global scope uses admin role
        'active': 'true',
        'name': table_name,
        'link_type': 'LIST'
    })
    navigation_results.append(('all_records', all_module))
    
    # Create "Create New" module
    create_module = client.create_record('sys_app_module', {
        'title': f'Create {table_label}',
        'hint': f'Create a new {table_label.lower()} record',
        'order': '110',
        'roles': 'admin',
        'active': 'true',
        'name': f'{table_name}_create',
        'link_type': 'NEW',
        'query': f'sysparm_table={table_name}'
    })
    navigation_results.append(('create_new', create_module))
    
    return navigation_results

def _create_scoped_table_navigation(client: ServiceNowClient, app_sys_id: str, table_name: str, 
                                   table_label: str, scope: str) -> List[Dict[str, Any]]:
    """Create navigation modules for scoped application tables with proper application menu setup"""
    
    navigation_results = []
    
    # Check if navigation modules already exist
    existing_modules = client.query_table('sys_app_module',
                                         query=f'application={app_sys_id}^name={table_name}',
                                         fields=['sys_id', 'title', 'name'])
    
    if existing_modules:
        navigation_results.append({
            'type': 'existing_modules',
            'message': f'Navigation modules for {table_label} already exist',
            'count': len(existing_modules)
        })
        return navigation_results
    
    # FIXED: Get the application record to ensure proper scope and role setup
    app_record = client.get_record('sys_app', app_sys_id, fields=['scope', 'name', 'sys_id'])
    if not app_record:
        navigation_results.append({
            'type': 'error',
            'message': f'Cannot find application with sys_id: {app_sys_id}'
        })
        return navigation_results
    
    app_scope = app_record.get('scope', scope)
    app_name = app_record.get('name', scope)
    
    # FIXED: Create proper role name based on application scope
    # ServiceNow automatically creates roles like "x_scope_user" for scoped apps
    role_name = f"{app_scope}.user" if '.' not in app_scope else f"{app_scope}_user"
    
    # Create "All Records" module with proper application menu setup
    all_module_payload = {
        'title': table_label,
        'hint': f'View all {table_label.lower()} records',
        'order': '200',
        'roles': role_name,
        'active': 'true',
        'sys_scope': app_scope,  # FIXED: Use proper scope from app record
        'application': app_sys_id,
        'name': table_name,
        'link_type': 'LIST',
        'table': table_name,  # FIXED: Add table reference for proper menu setup
        'path': f'{table_name}_list.do'  # FIXED: Add explicit path
    }
    
    all_module = client.create_record('sys_app_module', all_module_payload)
    navigation_results.append(('all_records', all_module))
    
    # Create "Create New" module with proper setup
    create_module_payload = {
        'title': f'Create {table_label}',
        'hint': f'Create a new {table_label.lower()} record',
        'order': '210',
        'roles': role_name,
        'active': 'true',
        'sys_scope': app_scope,
        'application': app_sys_id,
        'name': f'{table_name}_create',
        'link_type': 'NEW',
        'table': table_name,  # FIXED: Add table reference
        'path': f'{table_name}.do?sys_id=-1',  # FIXED: Proper new record path
        'query': f'sysparm_table={table_name}'
    }
    
    create_module = client.create_record('sys_app_module', create_module_payload)
    navigation_results.append(('create_new', create_module))
    
    # Create "My Records" module with proper filtering
    my_records_payload = {
        'title': f'My {table_label}',
        'hint': f'View {table_label.lower()} records I created',
        'order': '220',
        'roles': role_name,
        'active': 'true',
        'sys_scope': app_scope,
        'application': app_sys_id,
        'name': f'{table_name}_my',
        'link_type': 'LIST',
        'table': table_name,  # FIXED: Add table reference
        'path': f'{table_name}_list.do',  # FIXED: Proper list path
        'query': f'sys_created_by=javascript:gs.getUserName()',  # FIXED: Simplified query
        'filter': f'sys_created_by=javascript:gs.getUserName()'  # FIXED: Add filter field
    }
    
    my_records_module = client.create_record('sys_app_module', my_records_payload)
    navigation_results.append(('my_records', my_records_module))
    
    # FIXED: Ensure application menu is properly configured
    # Check if the application has a proper menu structure
    app_menu_check = client.query_table('sys_app_module',
                                       query=f'application={app_sys_id}^title={app_name}',
                                       fields=['sys_id', 'title'])
    
    if not app_menu_check:
        # Create main application menu if it doesn't exist
        main_menu_payload = {
            'title': app_name,
            'hint': f'{app_name} application menu',
            'order': '100',
            'roles': role_name,
            'active': 'true',
            'sys_scope': app_scope,
            'application': app_sys_id,
            'name': f'{app_scope}_main',
            'link_type': 'SEPARATOR'  # This creates a menu separator/header
        }
        
        main_menu = client.create_record('sys_app_module', main_menu_payload)
        navigation_results.append(('main_menu', main_menu))
    
    return navigation_results

def create_table(client: ServiceNowClient, table_label: str, table_name: str, extends: Optional[str] = None, scope: Optional[str] = DEFAULT_SCOPE, dry_run: bool = False) -> Dict[str, Any]:
    """Legacy create table function - now calls enhanced version"""
    return create_table_with_navigation_enhanced(client, table_label, table_name, extends, scope, True, dry_run)
def add_field(client: ServiceNowClient, table_name: str, name: str, ftype: str, label: str, mandatory: bool = False, default: Optional[str] = None, choices: Optional[List[str]] = None, scope: Optional[str] = DEFAULT_SCOPE, dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "op": "add_field", "table_name": table_name, "name": name, "type": ftype, "label": label, "mandatory": mandatory, "default": default, "choices": choices, "scope": scope}
    return client.add_field(table_name, name, ftype, label, mandatory, default, choices, scope)
def add_choice(client: ServiceNowClient, table_name: str, element: str, choices: List[str], dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "op": "add_choice", "table_name": table_name, "element": element, "choices": choices}
    return client.add_choice(table_name, element, choices)
def create_catalog_item(client: ServiceNowClient, name: str, category: str, description: str = "", active: bool = True, scope: Optional[str] = DEFAULT_SCOPE, dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "op": "create_catalog_item", "name": name, "category": category, "description": description, "active": active, "scope": scope}
    return client.create_record("sc_cat_item", {"name":name,"short_description":description,"active":"true" if active else "false","category":category})
def add_catalog_variables(client: ServiceNowClient, item_sys_id: str, variables_spec: List[Dict[str, Any]], dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "op": "add_catalog_variables", "item_sys_id": item_sys_id, "variables_count": len(variables_spec)}
    created = []
    for v in variables_spec:
        created.append(client.add_catalog_variable(item_sys_id, v.get("type","string"), v["name"], v.get("question", v["name"]), v.get("choices")))
    return {"created": created}
def add_catalog_client_script(client: ServiceNowClient, item_sys_id: str, ui_type: str, script: str, dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "op": "add_catalog_client_script", "item_sys_id": item_sys_id, "ui_type": ui_type, "lines": len(script.splitlines())}
    return client.add_catalog_client_script(item_sys_id, ui_type, script)
