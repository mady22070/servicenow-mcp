"""
ServiceNow Best Practices Pack

This pack implements ServiceNow development best practices including:
- Naming convention validation
- Mandatory field validation
- Security best practices
- Performance optimization guidelines
- Code quality checks
"""

from typing import Dict, Any, List, Optional, Tuple
import re
from ..servicenow_client import ServiceNowClient
from ..utils.audit_simple import log

# ServiceNow Best Practices Constants
NAMING_PATTERNS = {
    'scoped_table': r'^x_[a-z0-9_]+_[a-z0-9_]+$',
    'custom_field': r'^u_[a-z0-9_]+$',
    'script_include': r'^[A-Z][a-zA-Z0-9_]*$',
    'business_rule': r'^[A-Z][a-zA-Z0-9_\s]*$'
}

MANDATORY_TABLE_FIELDS = ['sys_created_on', 'sys_created_by', 'sys_updated_on', 'sys_updated_by']
SECURITY_KEYWORDS = ['password', 'token', 'secret', 'key', 'credential']
PERFORMANCE_ANTI_PATTERNS = [
    'while(gr.next())',
    'gs.sleep(',
    'new GlideRecord(',  # Should suggest GlideRecordSecure
    'gs.getUser().getID()',  # Should use gs.getUserID()
]

def validate_naming_conventions(name: str, object_type: str) -> Dict[str, Any]:
    """Validate ServiceNow naming conventions"""
    issues = []
    pattern = NAMING_PATTERNS.get(object_type)
    
    if pattern and not re.match(pattern, name):
        issues.append(f"{object_type} name '{name}' doesn't follow ServiceNow naming convention: {pattern}")
    
    # Additional checks
    if object_type == 'scoped_table' and not name.startswith('x_'):
        issues.append("Scoped table names must start with 'x_'")
    
    if object_type == 'custom_field' and not name.startswith('u_'):
        issues.append("Custom field names must start with 'u_'")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'object_type': object_type,
        'name': name
    }

def validate_mandatory_fields(table_name: str, fields: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate that mandatory fields are present"""
    field_names = [f.get('name', f.get('element', '')) for f in fields]
    missing_mandatory = [f for f in MANDATORY_TABLE_FIELDS if f not in field_names]
    
    return {
        'valid': len(missing_mandatory) == 0,
        'missing_fields': missing_mandatory,
        'table_name': table_name
    }

def validate_security_best_practices(script: str, context: str = 'server') -> Dict[str, Any]:
    """Validate security best practices in scripts"""
    issues = []
    
    # Check for hardcoded sensitive data
    for keyword in SECURITY_KEYWORDS:
        if keyword.lower() in script.lower():
            issues.append(f"Potential hardcoded {keyword} found - use system properties instead")
    
    # Server-side security checks
    if context == 'server':
        if 'new GlideRecord(' in script and 'GlideRecordSecure' not in script:
            issues.append("Consider using GlideRecordSecure instead of GlideRecord for better security")
        
        if 'gs.getUser().getID()' in script:
            issues.append("Use gs.getUserID() instead of gs.getUser().getID() for better performance")
    
    # Client-side security checks
    if context == 'client':
        if 'g_user.userID' in script:
            issues.append("Avoid accessing user information directly on client side")
        
        if 'eval(' in script:
            issues.append("Avoid using eval() - security risk")
        
        if 'alert(' in script:
            issues.append("Avoid alert() - use g_form.addInfoMessage() instead")
        
        if 'onSubmit' in script and 'return' not in script:
            issues.append("onSubmit scripts should return true/false")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'context': context
    }

def validate_performance_best_practices(script: str) -> Dict[str, Any]:
    """Validate performance best practices"""
    issues = []
    
    for pattern in PERFORMANCE_ANTI_PATTERNS:
        if pattern in script:
            if pattern == 'while(gr.next())':
                issues.append("Use for loop instead of while(gr.next()) for better performance")
            elif pattern == 'gs.sleep(':
                issues.append("Avoid gs.sleep() in scripts - can cause performance issues")
            elif pattern == 'new GlideRecord(':
                issues.append("Consider using GlideRecordSecure for security and performance")
            elif pattern == 'gs.getUser().getID()':
                issues.append("Use gs.getUserID() for better performance")
    
    # Check for excessive queries in loops
    if 'while(' in script and 'GlideRecord' in script:
        issues.append("Potential N+1 query problem - avoid database queries in loops")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues
    }

def create_scoped_application(client: ServiceNowClient, name: str, scope: str, version: str = "1.0.0", 
                            description: str = "", dry_run: bool = False) -> Dict[str, Any]:
    """Create a new scoped application following best practices"""
    
    # Validate scope naming
    scope_validation = validate_naming_conventions(scope, 'scope')
    if not scope_validation['valid']:
        return {'error': 'Invalid scope name', 'validation': scope_validation}
    
    payload = {
        'name': name,
        'scope': scope,
        'version': version,
        'short_description': description,
        'active': 'true',
        'can_edit_in_studio': 'true'
    }
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'sys_app',
            'record': payload,
            'validation': scope_validation
        }
    
    result = client.create_record('sys_app', payload)
    log("create_scoped_application", {
        "sys_id": result.get("sys_id"), 
        "name": name, 
        "scope": scope
    })
    
    return {
        'result': result,
        'validation': scope_validation
    }

def create_table_with_best_practices(client: ServiceNowClient, table_label: str, table_name: str, 
                                   scope: str, extends: Optional[str] = None, 
                                   dry_run: bool = False) -> Dict[str, Any]:
    """Create table following ServiceNow best practices"""
    
    # Validate table name
    full_table_name = f"x_{scope}_{table_name}" if not table_name.startswith('x_') else table_name
    name_validation = validate_naming_conventions(full_table_name, 'scoped_table')
    
    if not name_validation['valid']:
        return {'error': 'Invalid table name', 'validation': name_validation}
    
    payload = {
        'name': full_table_name,
        'label': table_label,
        'sys_scope': scope
    }
    
    if extends:
        payload['super_class'] = extends
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'sys_db_object',
            'record': payload,
            'validation': name_validation,
            'recommended_fields': MANDATORY_TABLE_FIELDS
        }
    
    result = client.create_record('sys_db_object', payload)
    log("create_table_with_best_practices", {
        "sys_id": result.get("sys_id"),
        "name": full_table_name,
        "scope": scope
    })
    
    return {
        'result': result,
        'validation': name_validation,
        'table_name': full_table_name
    }

def create_field_with_validation(client: ServiceNowClient, table_name: str, field_name: str, 
                               field_type: str, label: str, mandatory: bool = False,
                               scope: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
    """Create field with best practices validation"""
    
    # Validate field name
    full_field_name = f"u_{field_name}" if not field_name.startswith('u_') and not field_name.startswith('sys_') else field_name
    name_validation = validate_naming_conventions(full_field_name, 'custom_field')
    
    payload = {
        'name': table_name,
        'element': full_field_name,
        'internal_type': field_type,
        'column_label': label,
        'mandatory': 'true' if mandatory else 'false'
    }
    
    if scope:
        payload['sys_scope'] = scope
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'sys_dictionary',
            'record': payload,
            'validation': name_validation
        }
    
    result = client.create_record('sys_dictionary', payload)
    log("create_field_with_validation", {
        "sys_id": result.get("sys_id"),
        "table": table_name,
        "field": full_field_name
    })
    
    return {
        'result': result,
        'validation': name_validation,
        'field_name': full_field_name
    }

def validate_script_best_practices(script: str, script_type: str = 'server') -> Dict[str, Any]:
    """Comprehensive script validation"""
    
    security_validation = validate_security_best_practices(script, script_type)
    performance_validation = validate_performance_best_practices(script)
    
    all_issues = security_validation['issues'] + performance_validation['issues']
    
    return {
        'valid': len(all_issues) == 0,
        'security': security_validation,
        'performance': performance_validation,
        'all_issues': all_issues,
        'script_type': script_type
    }

def create_business_rule_with_validation(client: ServiceNowClient, table_name: str, name: str, 
                                       when: str, script: str, condition: str = "",
                                       scope: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
    """Create business rule with best practices validation"""
    
    # Validate name
    name_validation = validate_naming_conventions(name, 'business_rule')
    script_validation = validate_script_best_practices(script, 'server')
    
    payload = {
        'name': name,
        'table': table_name,
        'when': when,
        'script': script,
        'condition': condition,
        'active': 'true'
    }
    
    if scope:
        payload['sys_scope'] = scope
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'sys_script',
            'record': payload,
            'name_validation': name_validation,
            'script_validation': script_validation
        }
    
    if not script_validation['valid']:
        return {
            'warning': 'Script has validation issues',
            'script_validation': script_validation,
            'proceed_anyway': False
        }
    
    result = client.create_record('sys_script', payload)
    log("create_business_rule_with_validation", {
        "sys_id": result.get("sys_id"),
        "name": name,
        "table": table_name
    })
    
    return {
        'result': result,
        'name_validation': name_validation,
        'script_validation': script_validation
    }

def audit_application_best_practices(client: ServiceNowClient, scope: str) -> Dict[str, Any]:
    """Audit an entire application for best practices compliance"""
    
    issues = []
    recommendations = []
    
    # Check tables
    tables = client.query_table('sys_db_object', 
                               query=f'sys_scope.scope={scope}',
                               fields=['name', 'label', 'sys_id'])
    
    for table in tables:
        table_name = table.get('name', '')
        name_validation = validate_naming_conventions(table_name, 'scoped_table')
        if not name_validation['valid']:
            issues.extend(name_validation['issues'])
    
    # Check fields
    fields = client.query_table('sys_dictionary',
                               query=f'sys_scope.scope={scope}',
                               fields=['name', 'element', 'sys_id'])
    
    custom_fields = [f for f in fields if not f.get('element', '').startswith('sys_')]
    for field in custom_fields:
        field_name = field.get('element', '')
        name_validation = validate_naming_conventions(field_name, 'custom_field')
        if not name_validation['valid']:
            issues.extend(name_validation['issues'])
    
    # Check business rules
    business_rules = client.query_table('sys_script',
                                       query=f'sys_scope.scope={scope}',
                                       fields=['name', 'script', 'sys_id'])
    
    for br in business_rules:
        script = br.get('script', '')
        if script:
            script_validation = validate_script_best_practices(script, 'server')
            if not script_validation['valid']:
                issues.extend([f"Business Rule '{br.get('name')}': {issue}" 
                             for issue in script_validation['all_issues']])
    
    # Generate recommendations
    if len(tables) == 0:
        recommendations.append("Consider creating at least one custom table for your application")
    
    if len(custom_fields) == 0:
        recommendations.append("Consider adding custom fields to extend functionality")
    
    return {
        'scope': scope,
        'summary': {
            'tables': len(tables),
            'custom_fields': len(custom_fields),
            'business_rules': len(business_rules),
            'issues_count': len(issues)
        },
        'issues': issues,
        'recommendations': recommendations,
        'compliance_score': max(0, 100 - (len(issues) * 10))  # Simple scoring
    }