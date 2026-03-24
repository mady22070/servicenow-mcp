"""
ServiceNow Scoped Development Enforcement Pack

This pack ensures all development follows ServiceNow scoped application best practices:
- Enforces scoped development patterns
- Validates naming conventions
- Manages application boundaries
- Prevents global scope pollution
- Ensures proper dependency management
"""

from typing import Dict, Any, List, Optional, Set
import re
from ..servicenow_client import ServiceNowClient
from ..utils.audit_simple import log

# Scoped Development Constants
GLOBAL_SCOPE = "global"
RESERVED_PREFIXES = ["sys_", "sn_", "u_", "cmdb_", "task_", "sc_", "kb_", "hr_", "csm_"]
SCOPED_PREFIXES = ["x_"]

# Tables that should never be created in global scope
PROHIBITED_GLOBAL_TABLES = [
    "custom_table", "application_table", "business_table"
]

# Fields that should always be scoped
SCOPED_FIELD_PATTERNS = [
    r"^u_.*",  # Custom fields
    r"^x_.*"   # Scoped fields
]

class ScopedDevelopmentEnforcer:
    """Enforces scoped development best practices"""
    
    def __init__(self, client: ServiceNowClient):
        self.client = client
        self.current_scope = None
        self.violations = []
        self.warnings = []
    
    def set_development_scope(self, scope: str) -> Dict[str, Any]:
        """Set the current development scope and validate it"""
        
        if not scope or scope == GLOBAL_SCOPE:
            return {
                'error': 'Global scope development is not allowed',
                'recommendation': 'Create or use a scoped application',
                'example_scope': 'x_my_company_app'
            }
        
        if not scope.startswith('x_'):
            return {
                'error': 'Invalid scope format',
                'requirement': 'Scope must start with x_',
                'provided': scope,
                'example': 'x_my_company_app'
            }
        
        # Validate scope naming convention
        if not re.match(r'^x_[a-z][a-z0-9_]*$', scope):
            return {
                'error': 'Invalid scope naming convention',
                'requirements': [
                    'Must start with x_',
                    'Must contain only lowercase letters, numbers, and underscores',
                    'Must start with a letter after x_'
                ],
                'provided': scope,
                'example': 'x_my_company_app'
            }
        
        # Check if scope exists
        scope_exists = self.validate_scope_exists(scope)
        if not scope_exists['exists']:
            return {
                'error': 'Scope does not exist',
                'scope': scope,
                'recommendation': 'Create the scoped application first',
                'validation': scope_exists
            }
        
        self.current_scope = scope
        log("set_development_scope", {"scope": scope})
        
        return {
            'success': True,
            'scope': scope,
            'scope_info': scope_exists['info']
        }
    
    def validate_scope_exists(self, scope: str) -> Dict[str, Any]:
        """Validate that a scope exists as a scoped application"""
        
        apps = self.client.query_table('sys_app', 
                                     query=f'scope={scope}',
                                     fields=['sys_id', 'name', 'version', 'active'])
        
        if not apps:
            return {
                'exists': False,
                'scope': scope,
                'message': 'No scoped application found with this scope'
            }
        
        app = apps[0]
        return {
            'exists': True,
            'scope': scope,
            'info': {
                'sys_id': app.get('sys_id'),
                'name': app.get('name'),
                'version': app.get('version'),
                'active': app.get('active') == 'true'
            }
        }
    
    def validate_table_creation(self, table_name: str, scope: Optional[str] = None) -> Dict[str, Any]:
        """Validate table creation follows scoped development practices"""
        
        issues = []
        warnings = []
        
        # Use current scope if not provided
        if not scope:
            scope = self.current_scope
        
        if not scope:
            issues.append("No development scope set - global table creation not allowed")
        
        # Check table naming convention
        if not table_name.startswith('x_'):
            issues.append(f"Table name must start with 'x_' for scoped development")
        
        # Check if table name includes scope
        if scope and not table_name.startswith(f"x_{scope.replace('x_', '')}"):
            warnings.append(f"Table name should include scope prefix: {scope.replace('x_', '')}")
        
        # Check for prohibited patterns
        for prefix in RESERVED_PREFIXES:
            if table_name.startswith(prefix) and prefix != 'x_':
                issues.append(f"Table name cannot start with reserved prefix: {prefix}")
        
        # Check for global scope pollution
        if table_name in PROHIBITED_GLOBAL_TABLES:
            issues.append(f"Table type '{table_name}' must be created in scoped application")
        
        return {
            'valid': len(issues) == 0,
            'table_name': table_name,
            'scope': scope,
            'issues': issues,
            'warnings': warnings,
            'recommended_name': self.generate_scoped_table_name(table_name, scope) if issues else None
        }
    
    def validate_field_creation(self, table_name: str, field_name: str, 
                              scope: Optional[str] = None) -> Dict[str, Any]:
        """Validate field creation follows scoped development practices"""
        
        issues = []
        warnings = []
        
        # Use current scope if not provided
        if not scope:
            scope = self.current_scope
        
        # Check field naming convention
        if not field_name.startswith('u_') and not field_name.startswith('x_'):
            if not any(field_name.startswith(prefix) for prefix in RESERVED_PREFIXES):
                issues.append("Custom fields must start with 'u_' or scoped prefix 'x_'")
        
        # Check for proper scoping
        if scope and field_name.startswith('x_'):
            scope_prefix = scope.replace('x_', '')
            if not field_name.startswith(f'x_{scope_prefix}'):
                warnings.append(f"Scoped field should include scope prefix: x_{scope_prefix}_")
        
        # Check field name format
        if not re.match(r'^[a-z][a-z0-9_]*$', field_name):
            issues.append("Field name must start with lowercase letter and contain only lowercase letters, numbers, and underscores")
        
        return {
            'valid': len(issues) == 0,
            'table_name': table_name,
            'field_name': field_name,
            'scope': scope,
            'issues': issues,
            'warnings': warnings,
            'recommended_name': self.generate_scoped_field_name(field_name, scope) if issues else None
        }
    
    def validate_script_creation(self, script_type: str, table_name: str, 
                               script_name: str, scope: Optional[str] = None) -> Dict[str, Any]:
        """Validate script creation follows scoped development practices"""
        
        issues = []
        warnings = []
        
        # Use current scope if not provided
        if not scope:
            scope = self.current_scope
        
        if not scope:
            issues.append("No development scope set - scripts must be created in scoped applications")
        
        # Validate script naming based on type
        if script_type == 'business_rule':
            if not re.match(r'^[A-Z][a-zA-Z0-9\s]*$', script_name):
                issues.append("Business rule names should start with uppercase letter")
        
        elif script_type == 'script_include':
            if not re.match(r'^[A-Z][a-zA-Z0-9_]*$', script_name):
                issues.append("Script include names should use PascalCase")
            
            # Check for scope prefix in script include
            if scope:
                scope_prefix = scope.replace('x_', '').title().replace('_', '')
                if not script_name.startswith(scope_prefix):
                    warnings.append(f"Script include should start with scope prefix: {scope_prefix}")
        
        elif script_type == 'client_script':
            if not script_name:
                issues.append("Client script must have a descriptive name")
        
        # Check table scope alignment
        if table_name and not table_name.startswith('x_'):
            warnings.append("Scripts should primarily target scoped tables")
        
        return {
            'valid': len(issues) == 0,
            'script_type': script_type,
            'script_name': script_name,
            'table_name': table_name,
            'scope': scope,
            'issues': issues,
            'warnings': warnings
        }
    
    def generate_scoped_table_name(self, base_name: str, scope: str) -> str:
        """Generate a properly scoped table name"""
        if not scope:
            return f"x_{base_name}"
        
        scope_prefix = scope.replace('x_', '')
        base_clean = base_name.replace('x_', '').replace(scope_prefix + '_', '')
        
        return f"x_{scope_prefix}_{base_clean}"
    
    def generate_scoped_field_name(self, base_name: str, scope: str) -> str:
        """Generate a properly scoped field name"""
        if base_name.startswith('u_'):
            return base_name
        
        if not scope:
            return f"u_{base_name}"
        
        scope_prefix = scope.replace('x_', '')
        base_clean = base_name.replace('x_', '').replace('u_', '').replace(scope_prefix + '_', '')
        
        return f"x_{scope_prefix}_{base_clean}"
    
    def audit_scope_compliance(self, scope: str) -> Dict[str, Any]:
        """Audit a scoped application for compliance with best practices"""
        
        violations = []
        warnings = []
        
        # Check tables
        tables = self.client.query_table('sys_db_object',
                                       query=f'sys_scope.scope={scope}',
                                       fields=['name', 'label', 'sys_id'])
        
        for table in tables:
            table_name = table.get('name', '')
            validation = self.validate_table_creation(table_name, scope)
            violations.extend([f"Table '{table_name}': {issue}" for issue in validation['issues']])
            warnings.extend([f"Table '{table_name}': {warning}" for warning in validation['warnings']])
        
        # Check fields
        fields = self.client.query_table('sys_dictionary',
                                       query=f'sys_scope.scope={scope}',
                                       fields=['name', 'element', 'sys_id'])
        
        custom_fields = [f for f in fields if not f.get('element', '').startswith('sys_')]
        for field in custom_fields:
            table_name = field.get('name', '')
            field_name = field.get('element', '')
            validation = self.validate_field_creation(table_name, field_name, scope)
            violations.extend([f"Field '{table_name}.{field_name}': {issue}" for issue in validation['issues']])
            warnings.extend([f"Field '{table_name}.{field_name}': {warning}" for warning in validation['warnings']])
        
        # Check scripts
        scripts = self.client.query_table('sys_script',
                                        query=f'sys_scope.scope={scope}',
                                        fields=['name', 'table', 'sys_id'])
        
        for script in scripts:
            script_name = script.get('name', '')
            table_name = script.get('table', '')
            validation = self.validate_script_creation('business_rule', table_name, script_name, scope)
            violations.extend([f"Business Rule '{script_name}': {issue}" for issue in validation['issues']])
            warnings.extend([f"Business Rule '{script_name}': {warning}" for warning in validation['warnings']])
        
        # Calculate compliance score
        total_items = len(tables) + len(custom_fields) + len(scripts)
        violation_count = len(violations)
        warning_count = len(warnings)
        
        compliance_score = max(0, 100 - (violation_count * 10) - (warning_count * 2))
        
        return {
            'scope': scope,
            'summary': {
                'tables': len(tables),
                'custom_fields': len(custom_fields),
                'scripts': len(scripts),
                'violations': violation_count,
                'warnings': warning_count
            },
            'violations': violations,
            'warnings': warnings,
            'compliance_score': compliance_score,
            'compliance_level': self.get_compliance_level(compliance_score)
        }
    
    def get_compliance_level(self, score: int) -> str:
        """Get compliance level based on score"""
        if score >= 95:
            return "Excellent"
        elif score >= 85:
            return "Good"
        elif score >= 70:
            return "Fair"
        elif score >= 50:
            return "Poor"
        else:
            return "Critical"
    
    def get_scope_dependencies(self, scope: str) -> Dict[str, Any]:
        """Get dependencies for a scoped application"""
        
        # Get application sys_id
        apps = self.client.query_table('sys_app', 
                                     query=f'scope={scope}',
                                     fields=['sys_id', 'name'])
        
        if not apps:
            return {'error': 'Scoped application not found'}
        
        app_sys_id = apps[0].get('sys_id')
        
        # Get dependencies
        dependencies = self.client.query_table('sys_app_dependency',
                                             query=f'source={app_sys_id}',
                                             fields=['target.name', 'target.scope', 'min_version'])
        
        # Get reverse dependencies (what depends on this app)
        reverse_deps = self.client.query_table('sys_app_dependency',
                                             query=f'target={app_sys_id}',
                                             fields=['source.name', 'source.scope', 'min_version'])
        
        return {
            'scope': scope,
            'app_name': apps[0].get('name'),
            'dependencies': {
                'count': len(dependencies),
                'apps': [
                    {
                        'name': dep.get('target.name'),
                        'scope': dep.get('target.scope'),
                        'min_version': dep.get('min_version')
                    }
                    for dep in dependencies
                ]
            },
            'reverse_dependencies': {
                'count': len(reverse_deps),
                'apps': [
                    {
                        'name': dep.get('source.name'),
                        'scope': dep.get('source.scope'),
                        'min_version': dep.get('min_version')
                    }
                    for dep in reverse_deps
                ]
            }
        }

# Convenience functions for the pack
def enforce_scoped_development(client: ServiceNowClient, scope: str) -> Dict[str, Any]:
    """Initialize scoped development enforcement"""
    enforcer = ScopedDevelopmentEnforcer(client)
    return enforcer.set_development_scope(scope)

def validate_scoped_table_creation(client: ServiceNowClient, table_name: str, 
                                 scope: str) -> Dict[str, Any]:
    """Validate table creation for scoped development"""
    enforcer = ScopedDevelopmentEnforcer(client)
    enforcer.set_development_scope(scope)
    return enforcer.validate_table_creation(table_name, scope)

def validate_scoped_field_creation(client: ServiceNowClient, table_name: str, 
                                 field_name: str, scope: str) -> Dict[str, Any]:
    """Validate field creation for scoped development"""
    enforcer = ScopedDevelopmentEnforcer(client)
    enforcer.set_development_scope(scope)
    return enforcer.validate_field_creation(table_name, field_name, scope)

def audit_scoped_application(client: ServiceNowClient, scope: str) -> Dict[str, Any]:
    """Audit scoped application for compliance"""
    enforcer = ScopedDevelopmentEnforcer(client)
    return enforcer.audit_scope_compliance(scope)

def get_application_dependencies(client: ServiceNowClient, scope: str) -> Dict[str, Any]:
    """Get application dependencies"""
    enforcer = ScopedDevelopmentEnforcer(client)
    return enforcer.get_scope_dependencies(scope)

def generate_scoped_naming_suggestions(base_name: str, scope: str, 
                                     object_type: str) -> Dict[str, Any]:
    """Generate naming suggestions for scoped objects"""
    
    enforcer = ScopedDevelopmentEnforcer(None)
    
    suggestions = {}
    
    if object_type == 'table':
        suggestions['recommended'] = enforcer.generate_scoped_table_name(base_name, scope)
        suggestions['pattern'] = f"x_{scope.replace('x_', '')}_{{table_name}}"
    
    elif object_type == 'field':
        suggestions['recommended'] = enforcer.generate_scoped_field_name(base_name, scope)
        suggestions['patterns'] = [
            f"u_{{field_name}}",  # Standard custom field
            f"x_{scope.replace('x_', '')}_{{field_name}}"  # Scoped field
        ]
    
    elif object_type == 'script_include':
        scope_prefix = scope.replace('x_', '').title().replace('_', '')
        suggestions['recommended'] = f"{scope_prefix}{base_name}"
        suggestions['pattern'] = f"{scope_prefix}{{ClassName}}"
    
    return {
        'base_name': base_name,
        'scope': scope,
        'object_type': object_type,
        'suggestions': suggestions
    }