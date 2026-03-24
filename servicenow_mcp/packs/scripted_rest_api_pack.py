"""
ServiceNow Scripted REST API Development Pack

This pack provides comprehensive REST API development capabilities with:
- Scoped application integration
- Authentication configuration
- API versioning and documentation
- Testing and validation
- Security best practices
- Performance optimization
"""

from typing import Dict, Any, List, Optional, Callable
import json
import re
from functools import lru_cache
from ..servicenow_client import ServiceNowClient
from ..utils.audit_simple import log

class RestApiConfig:
    """Configuration constants for REST API operations"""
    
    # Naming pattern validation
    API_NAMING_PATTERNS = {
        'api_name': r'^[a-z][a-z0-9_]*$',
        'resource_path': r'^\/[a-z][a-z0-9_]*(\/{[a-z_]+})*$',
        'version_pattern': r'^v\d+$'
    }
    
    # Supported HTTP methods
    HTTP_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']
    
    # Authentication types
    AUTHENTICATION_TYPES = ['none', 'basic', 'oauth', 'api_key', 'custom']
    
    # Default values
    DEFAULT_VERSION = "v1"
    DEFAULT_AUTHENTICATION = "none"
    MAX_SCRIPT_LENGTH = 100000  # 100KB limit for scripts
    
    # ServiceNow table names
    WS_DEFINITION_TABLE = 'sys_ws_definition'
    WS_OPERATION_TABLE = 'sys_ws_operation'
    WS_AUTH_TABLE = 'sys_ws_auth'


# Backward compatibility
API_NAMING_PATTERNS = RestApiConfig.API_NAMING_PATTERNS
HTTP_METHODS = RestApiConfig.HTTP_METHODS
AUTHENTICATION_TYPES = RestApiConfig.AUTHENTICATION_TYPES

def validate_api_naming(api_name: str, scope: str) -> Dict[str, Any]:
    """
    Validate REST API naming conventions according to ServiceNow best practices.
    
    Args:
        api_name: The proposed API name
        scope: The ServiceNow application scope (e.g., 'x_my_app')
        
    Returns:
        Dict containing validation results with keys:
        - valid: bool indicating if name is valid
        - issues: list of validation issues found
        - recommended_name: suggested compliant name
        - namespace: recommended namespace path
        
    Example:
        >>> validate_api_naming("my_api", "x_my_app")
        {'valid': True, 'issues': [], 'recommended_name': 'x_my_app_my_api', ...}
    """
    issues: List[str] = []
    
    # Check API name format
    if not re.match(API_NAMING_PATTERNS['api_name'], api_name):
        issues.append("API name must start with lowercase letter and contain only lowercase letters, numbers, and underscores")
    
    # Check scope integration
    expected_namespace = f"{scope}_{api_name}"
    scope_prefix = scope.replace('x_', '') if scope.startswith('x_') else scope
    
    if not api_name.startswith(scope_prefix):
        issues.append(f"API name should include scope prefix '{scope_prefix}' for namespace isolation")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'recommended_name': expected_namespace,
        'namespace': f"/{scope}/{api_name}"
    }

def validate_resource_path(path: str) -> Dict[str, Any]:
    """
    Validate REST resource path conventions with comprehensive checks.
    
    Args:
        path: The resource path to validate
        
    Returns:
        Dict with validation results and recommendations
    """
    if not path or not isinstance(path, str):
        return {
            'valid': False,
            'issues': ['Resource path cannot be empty'],
            'recommendations': [],
            'path_type': 'unknown'
        }
    
    # Sanitize path
    path = path.strip()
    issues = []
    recommendations = []
    
    # Basic format checks
    if not path.startswith('/'):
        issues.append("Resource path must start with '/'")
    
    # Length validation
    if len(path) > 255:
        issues.append("Resource path too long (max 255 characters)")
    
    # Pattern validation
    if not re.match(RestApiConfig.API_NAMING_PATTERNS['resource_path'], path):
        issues.append("Resource path must follow REST conventions: /resource/{id}/subresource")
        recommendations.append("Use lowercase letters, numbers, underscores, and path parameters in {braces}")
    
    # Security checks
    if '..' in path or '//' in path:
        issues.append("Resource path contains invalid sequences")
    
    # Check for proper HTTP method alignment
    path_type = _determine_path_type(path)
    method_recommendations = _get_method_recommendations(path_type)
    recommendations.extend(method_recommendations)
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'recommendations': recommendations,
        'path_type': path_type,
        'sanitized_path': path
    }


def _determine_path_type(path: str) -> str:
    """Determine the type of REST resource path"""
    if '{' in path:
        return 'item'
    elif path.rstrip('/').endswith('s'):
        return 'collection'
    else:
        return 'singleton'


def _get_method_recommendations(path_type: str) -> List[str]:
    """Get HTTP method recommendations based on path type"""
    recommendations = {
        'collection': ["Collection endpoints should support GET (list) and POST (create)"],
        'item': ["Item endpoints should support GET (read), PUT (update), DELETE (remove)"],
        'singleton': ["Singleton endpoints typically support GET and PUT operations"]
    }
    return recommendations.get(path_type, [])

def create_scoped_rest_api(client: ServiceNowClient, name: str, scope: str, 
                          version: str = "v1", description: str = "",
                          authentication: str = "none", base_path: Optional[str] = None,
                          dry_run: bool = False) -> Dict[str, Any]:
    """Create a scoped REST API with best practices and API limitation handling"""
    
    # Validate inputs
    if authentication not in AUTHENTICATION_TYPES:
        return {
            'error': f'Invalid authentication type: {authentication}',
            'valid_types': AUTHENTICATION_TYPES
        }
    
    # Validate API naming
    name_validation = validate_api_naming(name, scope)
    if not name_validation['valid']:
        return {
            'error': 'Invalid API name',
            'validation': name_validation
        }
    
    # Generate proper base path
    if base_path is None:
        base_path = f"/{scope}/{version}/{name}"
    
    # Validate version format
    if not re.match(API_NAMING_PATTERNS['version_pattern'], version):
        return {
            'error': 'Version must follow format: v1, v2, etc.',
            'example': 'v1'
        }
    
    payload = {
        'name': f"{scope}_{name}",
        'api_name': f"{scope}_{name}",
        'base_path': base_path,
        'description': description,
        'version': version,
        'authentication_type': authentication,
        'active': 'true',
        'sys_scope': scope
    }
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'sys_ws_definition',
            'record': payload,
            'validation': name_validation,
            'generated_base_path': base_path,
            'best_practices': {
                'scoped': True,
                'versioned': True,
                'authenticated': authentication != 'none',
                'documented': bool(description)
            },
            'manual_steps': [
                "1. Navigate to System Web Services > Scripted REST APIs",
                "2. Click 'New' to create a new API",
                f"3. Set Name: {scope}_{name}",
                f"4. Set API ID: {scope}_{name}",
                f"5. Set Base API Path: {base_path}",
                f"6. Set Description: {description}",
                f"7. Set Version: {version}",
                f"8. Set Authentication: {authentication}",
                "9. Set Active: true",
                f"10. Set Application: {scope}"
            ]
        }
    
    try:
        # Check if we can access the sys_ws_definition table
        test_query = client.query_table('sys_ws_definition', limit=1)
        if not test_query:
            return {
                'error': 'API limitations detected',
                'message': 'Cannot programmatically create Scripted REST APIs through the ServiceNow REST API',
                'reason': 'ServiceNow restricts programmatic creation of sys_ws_definition records',
                'workaround': 'Manual creation required',
                'manual_steps': [
                    "1. Navigate to System Web Services > Scripted REST APIs",
                    "2. Click 'New' to create a new API",
                    f"3. Set Name: {scope}_{name}",
                    f"4. Set API ID: {scope}_{name}",
                    f"5. Set Base API Path: {base_path}",
                    f"6. Set Description: {description}",
                    f"7. Set Version: {version}",
                    f"8. Set Authentication: {authentication}",
                    "9. Set Active: true",
                    f"10. Set Application: {scope}",
                    "11. Save the record",
                    "12. Use add_rest_resource() to add endpoints programmatically"
                ],
                'alternative': 'Use existing REST API or create through ServiceNow UI first'
            }
        
        result = client.create_record('sys_ws_definition', payload)
        log("create_scoped_rest_api", {
            "sys_id": result.get("sys_id"),
            "name": name,
            "scope": scope,
            "base_path": base_path
        })
        
        return {
            'result': result,
            'validation': name_validation,
            'api_endpoint': f"{client.base}{base_path}",
            'success': True
        }
        
    except Exception as e:
        error_msg = str(e).lower()
        
        # Check for common API limitation errors
        if any(keyword in error_msg for keyword in ['access denied', 'forbidden', 'not authorized', 'acl']):
            return RestApiErrorHandler.create_access_denied_response(
                operation="create_rest_api",
                scope=scope,
                name=name,
                base_path=base_path,
                description=description,
                version=version,
                authentication=authentication,
                technical_details=str(e)
            )
        
        elif 'table' in error_msg and 'not found' in error_msg:
            return {
                'error': 'ServiceNow Table Access Issue',
                'message': 'sys_ws_definition table may not be accessible or available',
                'technical_details': str(e),
                'possible_causes': [
                    'ServiceNow version does not support REST API table access',
                    'Table is restricted by ACLs',
                    'Plugin not activated'
                ],
                'recommendations': [
                    'Verify ServiceNow version supports Scripted REST APIs',
                    'Check if Web Services plugin is active',
                    'Use manual creation through ServiceNow UI'
                ]
            }
        
        else:
            return {
                'error': 'Unexpected API Error',
                'message': 'Failed to create Scripted REST API',
                'technical_details': str(e),
                'recommendation': 'Try manual creation or contact ServiceNow administrator'
            }

# Constants for field names and error messages
class RestResourceConstants:
    OPERATION_SCRIPT_FIELD = 'operation_script'
    SCRIPT_WARNING_KEY = 'script_warning'
    WS_OPERATION_TABLE = 'sys_ws_operation'
    WS_DEFINITION_TABLE = 'sys_ws_definition'


class RestApiErrorHandler:
    """Centralized error handling for REST API operations"""
    
    @staticmethod
    def create_access_denied_response(operation: str, **context) -> Dict[str, Any]:
        """Create standardized access denied response"""
        base_response = {
            'error': 'ServiceNow API Access Limitation',
            'message': f'Insufficient permissions to {operation} programmatically',
            'technical_details': context.get('technical_details', ''),
            'required_roles': ['admin', 'rest_api_explorer', 'web_service_admin'],
            'manual_creation_required': True,
            'workaround': 'Create the resource manually first, then use MCP tools'
        }
        
        if operation == "create_rest_api":
            base_response['manual_steps'] = [
                "1. Log into ServiceNow with admin privileges",
                "2. Navigate to System Web Services > Scripted REST APIs",
                "3. Click 'New' to create a new API",
                f"4. Set Name: {context.get('scope', '')}_{context.get('name', '')}",
                f"5. Set API ID: {context.get('scope', '')}_{context.get('name', '')}",
                f"6. Set Base API Path: {context.get('base_path', '')}",
                f"7. Set Description: {context.get('description', '')}",
                f"8. Set Version: {context.get('version', '')}",
                f"9. Set Authentication: {context.get('authentication', '')}",
                "10. Set Active: true",
                f"11. Set Application: {context.get('scope', '')}",
                "12. Save the record",
                "13. Copy the sys_id and use add_rest_resource() to add endpoints"
            ]
        elif operation == "create_rest_resource":
            base_response['manual_steps'] = [
                f"1. Navigate to System Web Services > Scripted REST APIs",
                f"2. Open the API: {context.get('api_name', '')}",
                f"3. Go to Resources tab",
                f"4. Click 'New' to add a resource",
                f"5. Set HTTP Method: {context.get('http_method', '')}",
                f"6. Set Relative Path: {context.get('relative_path', '')}",
                f"7. Set Description: {context.get('description', '')}",
                f"8. Add the script in the Script field",
                f"9. Save the resource"
            ]
        
        return base_response


class RestResourceValidator:
    """Handles validation of REST resource parameters"""
    
    @staticmethod
    def validate_inputs(http_method: str, relative_path: str, script: str) -> Dict[str, Any]:
        """Validate all input parameters"""
        # Validate HTTP method
        if http_method.upper() not in HTTP_METHODS:
            return {
                'valid': False,
                'error': f'Invalid HTTP method: {http_method}',
                'valid_methods': HTTP_METHODS
            }
        
        # Validate resource path
        path_validation = validate_resource_path(relative_path)
        if not path_validation['valid']:
            return {
                'valid': False,
                'error': 'Invalid resource path',
                'validation': path_validation
            }
        
        # Validate script for common issues
        script_issues = validate_rest_script(script, http_method.upper())
        if script_issues['issues']:
            return {
                'valid': False,
                'warning': 'Script has validation issues',
                'script_validation': script_issues,
                'recommendation': 'Fix script issues before creating resource'
            }
        
        return {
            'valid': True,
            'path_validation': path_validation,
            'script_validation': script_issues
        }


class RestResourceCreator:
    """Handles REST resource creation with proper separation of concerns"""
    
    def __init__(self, client: ServiceNowClient):
        self.client = client
        self.validator = RestResourceValidator()
    
    def _validate_inputs(self, http_method: str, relative_path: str, script: str) -> Dict[str, Any]:
        """
        Validate all input parameters for REST resource creation.
        
        Args:
            http_method: HTTP method (GET, POST, etc.)
            relative_path: Resource path relative to API base
            script: ServiceNow server-side script
            
        Returns:
            Validation result with success status and any issues found
        """
        validation_result = {
            'valid': True,
            'path_validation': {},
            'script_validation': {}
        }
        
        # Validate HTTP method
        if not self._is_valid_http_method(http_method):
            return self._create_validation_error(
                f'Invalid HTTP method: {http_method}',
                {'valid_methods': RestApiConfig.HTTP_METHODS}
            )
        
        # Validate resource path
        path_validation = validate_resource_path(relative_path)
        if not path_validation['valid']:
            return self._create_validation_error(
                'Invalid resource path',
                {'validation': path_validation}
            )
        validation_result['path_validation'] = path_validation
        
        # Validate script for common issues
        script_validation = validate_rest_script(script, http_method.upper())
        if script_validation['issues']:
            return {
                'valid': False,
                'warning': 'Script has validation issues',
                'script_validation': script_validation,
                'recommendation': 'Fix script issues before creating resource'
            }
        validation_result['script_validation'] = script_validation
        
        return validation_result
    
    def _is_valid_http_method(self, method: str) -> bool:
        """Check if HTTP method is supported"""
        return method.upper() in RestApiConfig.HTTP_METHODS
    
    def _create_validation_error(self, message: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create standardized validation error response"""
        error_response = {
            'valid': False,
            'error': message
        }
        if details:
            error_response.update(details)
        return error_response
    
    def _verify_api_exists(self, api_sys_id: str) -> Dict[str, Any]:
        """
        Verify the parent API exists with caching for performance.
        
        Args:
            api_sys_id: System ID of the REST API
            
        Returns:
            Dict with existence status and API information
        """
        # Check cache first (if implemented)
        cache_key = f"api_exists_{api_sys_id}"
        
        try:
            # Optimized field selection for better performance
            required_fields = ['name', 'api_name', 'base_path', 'sys_scope', 'active']
            
            api_info = self.client.get_record(
                RestResourceConstants.WS_DEFINITION_TABLE, 
                api_sys_id, 
                fields=required_fields
            )
            
            if not api_info or api_info.get('error'):
                return self._create_api_not_found_response(api_sys_id)
            
            # Validate API is active
            if api_info.get('active') == 'false':
                return {
                    'exists': True,
                    'api_info': api_info,
                    'warning': 'REST API exists but is inactive'
                }
            
            return {'exists': True, 'api_info': api_info}
            
        except Exception as e:
            log("api_verification_error", {
                "api_sys_id": api_sys_id,
                "error": str(e)
            })
            return {
                'exists': False,
                'error': 'Cannot verify REST API existence',
                'message': str(e),
                'recommendation': 'Ensure the API sys_id is correct and you have access to the sys_ws_definition table'
            }
    
    def _create_api_not_found_response(self, api_sys_id: str) -> Dict[str, Any]:
        """Create standardized API not found response"""
        return {
            'exists': False,
            'error': 'REST API not found',
            'message': f'No REST API found with sys_id: {api_sys_id}',
            'recommendation': 'Create the REST API first using create_scoped_rest_api() or manually in ServiceNow UI',
            'troubleshooting': [
                'Verify the sys_id is correct',
                'Check if the API was deleted',
                'Ensure you have read access to sys_ws_definition table'
            ]
        }
    
    def _build_payload(self, api_sys_id: str, http_method: str, relative_path: str, 
                      script: str, name: str, description: str, operation_id: str,
                      request_schema: Optional[Dict[str, Any]], 
                      response_schema: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build the payload for resource creation"""
        payload = {
            'web_service_definition': api_sys_id,
            'http_method': http_method.upper(),
            'relative_path': relative_path,
            'operation_script': script,  # CRITICAL FIX: Include script in initial payload
            'name': name,
            'operation_id': operation_id,
            'operation_description': description,
            'active': 'true'
        }
        
        # Add schema validation if provided
        if request_schema:
            payload['request_schema'] = json.dumps(request_schema)
        if response_schema:
            payload['response_schema'] = json.dumps(response_schema)
        
        return payload
    
    def _apply_script_fix(self, resource_sys_id: str, script: str) -> Dict[str, Any]:
        """Apply script content separately to ensure it's properly saved"""
        if not resource_sys_id or not script:
            return {'applied': False, 'reason': 'Missing resource_sys_id or script'}
        
        script_update = {RestResourceConstants.OPERATION_SCRIPT_FIELD: script}
        
        try:
            self.client.update_record(
                RestResourceConstants.WS_OPERATION_TABLE, 
                resource_sys_id, 
                script_update
            )
            log("add_rest_resource_script_updated", {
                "resource_sys_id": resource_sys_id,
                "script_length": len(script)
            })
            return {'applied': True}
        except Exception as script_error:
            log("add_rest_resource_script_update_failed", {
                "resource_sys_id": resource_sys_id,
                "error": str(script_error)
            })
            return {
                'applied': False,
                'error': str(script_error),
                'warning': f"Resource created but script update failed: {str(script_error)}"
            }
    
    def _generate_operation_id(self, http_method: str, relative_path: str) -> str:
        """Generate operation ID from method and path"""
        return f"{http_method.lower()}_{relative_path.replace('/', '_').replace('{', '').replace('}', '').strip('_')}"


def add_rest_resource(client: ServiceNowClient, api_sys_id: str, http_method: str,
                     relative_path: str, script: str, name: str,
                     description: str = "", operation_id: str = None,
                     request_schema: Optional[Dict[str, Any]] = None,
                     response_schema: Optional[Dict[str, Any]] = None,
                     dry_run: bool = False) -> Dict[str, Any]:
    """Add REST resource with comprehensive validation and API limitation handling"""
    
    creator = RestResourceCreator(client)
    
    # Validate inputs
    validation_result = creator._validate_inputs(http_method, relative_path, script)
    if not validation_result['valid']:
        return validation_result
    
    # Verify API exists
    api_result = creator._verify_api_exists(api_sys_id)
    if not api_result['exists']:
        return api_result
    
    api_info = api_result['api_info']
    
    # Generate operation ID if not provided
    if not operation_id:
        operation_id = creator._generate_operation_id(http_method, relative_path)
    
    # Build payload
    payload = creator._build_payload(
        api_sys_id, http_method, relative_path, script, name, 
        description, operation_id, request_schema, response_schema
    )
    
    if dry_run:
        return {
            'dry_run': True,
            'table': RestResourceConstants.WS_OPERATION_TABLE,
            'record': payload,
            'path_validation': validation_result['path_validation'],
            'script_validation': validation_result['script_validation'],
            'api_info': api_info,
            'has_schemas': {
                'request': request_schema is not None,
                'response': response_schema is not None
            },
            'manual_steps_if_needed': [
                f"1. Navigate to System Web Services > Scripted REST APIs",
                f"2. Open the API: {api_info.get('name')}",
                f"3. Go to Resources tab",
                f"4. Click 'New' to add a resource",
                f"5. Set HTTP Method: {http_method.upper()}",
                f"6. Set Relative Path: {relative_path}",
                f"7. Set Description: {description}",
                f"8. Add the script in the Script field",
                f"9. Save the resource"
            ]
        }
    
    try:
        # Create the resource
        result = client.create_record(RestResourceConstants.WS_OPERATION_TABLE, payload)
        resource_sys_id = result.get("sys_id")
        
        # Apply script fix as backup (script should already be in create payload)
        script_result = creator._apply_script_fix(resource_sys_id, script)
        
        # Add warning to result if script application failed
        if not script_result['applied'] and script_result.get('warning'):
            result[RestResourceConstants.SCRIPT_WARNING_KEY] = script_result['warning']
            log("add_rest_resource_script_backup_failed", {
                "resource_sys_id": resource_sys_id,
                "warning": script_result['warning']
            })
        
        log("add_rest_resource", {
            "sys_id": resource_sys_id,
            "api_sys_id": api_sys_id,
            "method": http_method.upper(),
            "path": relative_path,
            "script_applied": script_result['applied']
        })
        
        return {
            'result': result,
            'path_validation': validation_result['path_validation'],
            'script_validation': validation_result['script_validation'],
            'api_info': api_info,
            'script_applied': script_result['applied'],
            'success': True
        }
        
    except Exception as e:
        error_msg = str(e).lower()
        
        if any(keyword in error_msg for keyword in ['access denied', 'forbidden', 'not authorized', 'acl']):
            return {
                'error': 'ServiceNow API Access Limitation',
                'message': 'Insufficient permissions to create REST API resources programmatically',
                'technical_details': str(e),
                'manual_creation_required': True,
                'manual_steps': [
                    f"1. Navigate to System Web Services > Scripted REST APIs",
                    f"2. Open the API: {api_info.get('name')}",
                    f"3. Go to Resources tab",
                    f"4. Click 'New' to add a resource",
                    f"5. Set HTTP Method: {http_method.upper()}",
                    f"6. Set Relative Path: {relative_path}",
                    f"7. Set Description: {description}",
                    f"8. Add the following script:",
                    f"   {script[:200]}{'...' if len(script) > 200 else ''}",
                    f"9. Save the resource"
                ],
                'script_template': script,
                'workaround': 'Create the resource manually using the provided script template'
            }
        
        else:
            return {
                'error': 'Failed to create REST resource',
                'message': str(e),
                'api_info': api_info,
                'payload': payload,
                'recommendation': 'Try manual creation or check ServiceNow logs for details'
            }

class RestScriptValidator:
    """Validates REST API scripts for best practices and common issues"""
    
    # Validation rules configuration
    VALIDATION_RULES = {
        'required_patterns': {
            'response_status': {
                'pattern': 'response.setStatus(',
                'message': "Script should set appropriate HTTP status codes",
                'severity': 'error'
            },
            'error_handling': {
                'pattern': ['try', 'catch'],
                'message': "Consider adding try-catch error handling",
                'severity': 'warning'
            },
            'logging': {
                'pattern': ['gs.info(', 'gs.log(', 'gs.error('],
                'message': "Add logging for debugging and monitoring",
                'severity': 'warning'
            }
        },
        'method_specific': {
            'GET': {
                'query_params': {
                    'pattern': 'request.queryParams',
                    'message': "GET endpoints should handle query parameters",
                    'severity': 'warning'
                }
            },
            'POST': {
                'created_status': {
                    'pattern': 'response.setStatus(201)',
                    'message': "POST should return 201 status for successful creation",
                    'severity': 'warning'
                },
                'response_body': {
                    'pattern': 'response.setBody(',
                    'message': "POST should set response body",
                    'severity': 'error'
                }
            },
            'PUT': {
                'success_status': {
                    'pattern': ['response.setStatus(200)', 'response.setStatus(204)'],
                    'message': "PUT should return 200 or 204 status",
                    'severity': 'warning'
                }
            },
            'DELETE': {
                'success_status': {
                    'pattern': 'response.setStatus(204)',
                    'message': "DELETE should return 204 status for successful deletion",
                    'severity': 'warning'
                }
            }
        },
        'security_checks': {
            'authentication': {
                'pattern': 'gs.getUser()',
                'message': "Consider adding user authentication checks",
                'severity': 'warning',
                'exclude_methods': ['OPTIONS']
            },
            'input_validation': {
                'condition': lambda script, method: (
                    method in ['POST', 'PUT', 'PATCH'] and 
                    'request.body' in script and 
                    'JSON.parse' in script and 
                    'JSON.stringify' not in script
                ),
                'message': "Validate JSON input before parsing",
                'severity': 'warning'
            }
        }
    }
    
    @classmethod
    def validate_script(cls, script: str, http_method: str) -> Dict[str, Any]:
        """
        Validate REST API script for best practices.
        
        Args:
            script: The ServiceNow server-side script
            http_method: HTTP method (GET, POST, etc.)
            
        Returns:
            Validation result with issues and recommendations
        """
        validator = cls()
        return validator._perform_validation(script, http_method)
    
    def _perform_validation(self, script: str, http_method: str) -> Dict[str, Any]:
        """Perform comprehensive script validation"""
        issues = []
        recommendations = []
        
        # Check required patterns
        self._check_required_patterns(script, issues, recommendations)
        
        # Check method-specific requirements
        self._check_method_specific(script, http_method, issues, recommendations)
        
        # Check security practices
        self._check_security_practices(script, http_method, recommendations)
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'recommendations': recommendations,
            'method': http_method
        }
    
    def _check_required_patterns(self, script: str, issues: List[str], recommendations: List[str]):
        """Check for required patterns in script"""
        for rule_name, rule in self.VALIDATION_RULES['required_patterns'].items():
            if not self._pattern_exists(script, rule['pattern']):
                if rule['severity'] == 'error':
                    issues.append(rule['message'])
                else:
                    recommendations.append(rule['message'])
    
    def _check_method_specific(self, script: str, method: str, issues: List[str], recommendations: List[str]):
        """Check method-specific validation rules"""
        method_rules = self.VALIDATION_RULES['method_specific'].get(method, {})
        
        for rule_name, rule in method_rules.items():
            if not self._pattern_exists(script, rule['pattern']):
                if rule['severity'] == 'error':
                    issues.append(rule['message'])
                else:
                    recommendations.append(rule['message'])
    
    def _check_security_practices(self, script: str, method: str, recommendations: List[str]):
        """Check security-related practices"""
        security_rules = self.VALIDATION_RULES['security_checks']
        
        for rule_name, rule in security_rules.items():
            if 'condition' in rule:
                if rule['condition'](script, method):
                    recommendations.append(rule['message'])
            elif 'exclude_methods' in rule and method in rule['exclude_methods']:
                continue
            elif not self._pattern_exists(script, rule['pattern']):
                recommendations.append(rule['message'])
    
    def _pattern_exists(self, script: str, pattern) -> bool:
        """Check if pattern exists in script"""
        if isinstance(pattern, str):
            return pattern in script
        elif isinstance(pattern, list):
            return any(p in script for p in pattern)
        return False


def validate_rest_script(script: str, http_method: str) -> Dict[str, Any]:
    """Validate REST API script for best practices"""
    return RestScriptValidator.validate_script(script, http_method)

class RestScriptTemplateFactory:
    """Factory for generating REST API script templates"""
    
    @staticmethod
    def create_template(http_method: str, resource_type: str = 'item', 
                       table_name: Optional[str] = None) -> str:
        """Generate REST script template based on method and resource type"""
        template_generator = RestScriptTemplateFactory._get_template_generator(http_method)
        return template_generator(resource_type, table_name)
    
    @staticmethod
    def _get_template_generator(http_method: str):
        """Get appropriate template generator for HTTP method"""
        generators = {
            'GET': RestScriptTemplateFactory._generate_get_template,
            'POST': RestScriptTemplateFactory._generate_post_template,
            'PUT': RestScriptTemplateFactory._generate_put_template,
            'DELETE': RestScriptTemplateFactory._generate_delete_template
        }
        return generators.get(http_method.upper(), RestScriptTemplateFactory._generate_default_template)
    
    @staticmethod
    def _generate_get_template(resource_type: str, table_name: Optional[str]) -> str:
        """Generate GET method template"""
        if resource_type == 'collection':
            return RestScriptTemplateFactory._get_collection_template(table_name)
        return RestScriptTemplateFactory._get_item_template(table_name)
    
    @staticmethod
    def _get_collection_template(table_name: Optional[str]) -> str:
        return f'''
(function process(/*RESTAPIRequest*/ request, /*RESTAPIResponse*/ response) {{
    try {{
        // Get query parameters
        var limit = request.queryParams.limit || 100;
        var offset = request.queryParams.offset || 0;
        var query = request.queryParams.query || '';
        
        // Query the table
        var gr = new GlideRecordSecure('{table_name or "your_table"}');
        if (query) {{
            gr.addEncodedQuery(query);
        }}
        gr.setLimit(limit);
        gr.query();
        
        var results = [];
        while (gr.next()) {{
            results.push({{
                sys_id: gr.getUniqueValue(),
                // Add your fields here
            }});
        }}
        
        response.setStatus(200);
        response.setBody({{
            result: results,
            total: gr.getRowCount()
        }});
        
    }} catch (ex) {{
        gs.error('REST API Error: ' + ex.message);
        response.setStatus(500);
        response.setBody({{error: 'Internal server error'}});
    }}
}})(request, response);
        '''.strip()
    
    @staticmethod
    def _get_item_template(table_name: Optional[str]) -> str:
        return f'''
(function process(/*RESTAPIRequest*/ request, /*RESTAPIResponse*/ response) {{
    try {{
        var id = request.pathParams.id;
        if (!id) {{
            response.setStatus(400);
            response.setBody({{error: 'ID parameter required'}});
            return;
        }}
        
        var gr = new GlideRecordSecure('{table_name or "your_table"}');
        if (gr.get(id)) {{
            response.setStatus(200);
            response.setBody({{
                sys_id: gr.getUniqueValue(),
                // Add your fields here
            }});
        }} else {{
            response.setStatus(404);
            response.setBody({{error: 'Record not found'}});
        }}
        
    }} catch (ex) {{
        gs.error('REST API Error: ' + ex.message);
        response.setStatus(500);
        response.setBody({{error: 'Internal server error'}});
    }}
}})(request, response);
        '''.strip()
    
    @staticmethod
    def _generate_post_template(resource_type: str, table_name: Optional[str]) -> str:
        return f'''
(function process(/*RESTAPIRequest*/ request, /*RESTAPIResponse*/ response) {{
    try {{
        var data = request.body.data;
        if (!data) {{
            response.setStatus(400);
            response.setBody({{error: 'Request body required'}});
            return;
        }}
        
        var gr = new GlideRecordSecure('{table_name or "your_table"}');
        gr.initialize();
        
        // Set fields from request data
        // gr.setValue('field_name', data.field_name);
        
        var sys_id = gr.insert();
        if (sys_id) {{
            response.setStatus(201);
            response.setBody({{
                sys_id: sys_id,
                message: 'Record created successfully'
            }});
        }} else {{
            response.setStatus(400);
            response.setBody({{error: 'Failed to create record'}});
        }}
        
    }} catch (ex) {{
        gs.error('REST API Error: ' + ex.message);
        response.setStatus(500);
        response.setBody({{error: 'Internal server error'}});
    }}
}})(request, response);
        '''.strip()
    
    @staticmethod
    def _generate_put_template(resource_type: str, table_name: Optional[str]) -> str:
        return f'''
(function process(/*RESTAPIRequest*/ request, /*RESTAPIResponse*/ response) {{
    try {{
        var id = request.pathParams.id;
        var data = request.body.data;
        
        if (!id || !data) {{
            response.setStatus(400);
            response.setBody({{error: 'ID and request body required'}});
            return;
        }}
        
        var gr = new GlideRecordSecure('{table_name or "your_table"}');
        if (gr.get(id)) {{
            // Update fields from request data
            // gr.setValue('field_name', data.field_name);
            
            gr.update();
            response.setStatus(200);
            response.setBody({{
                sys_id: id,
                message: 'Record updated successfully'
            }});
        }} else {{
            response.setStatus(404);
            response.setBody({{error: 'Record not found'}});
        }}
        
    }} catch (ex) {{
        gs.error('REST API Error: ' + ex.message);
        response.setStatus(500);
        response.setBody({{error: 'Internal server error'}});
    }}
}})(request, response);
        '''.strip()
    
    @staticmethod
    def _generate_delete_template(resource_type: str, table_name: Optional[str]) -> str:
        return f'''
(function process(/*RESTAPIRequest*/ request, /*RESTAPIResponse*/ response) {{
    try {{
        var id = request.pathParams.id;
        if (!id) {{
            response.setStatus(400);
            response.setBody({{error: 'ID parameter required'}});
            return;
        }}
        
        var gr = new GlideRecordSecure('{table_name or "your_table"}');
        if (gr.get(id)) {{
            gr.deleteRecord();
            response.setStatus(204);
        }} else {{
            response.setStatus(404);
            response.setBody({{error: 'Record not found'}});
        }}
        
    }} catch (ex) {{
        gs.error('REST API Error: ' + ex.message);
        response.setStatus(500);
        response.setBody({{error: 'Internal server error'}});
    }}
}})(request, response);
        '''.strip()
    
    @staticmethod
    def _generate_default_template(resource_type: str, table_name: Optional[str]) -> str:
        return '''
(function process(/*RESTAPIRequest*/ request, /*RESTAPIResponse*/ response) {
    // TODO: Implement logic
    response.setStatus(501);
    response.setBody({error: 'Not implemented'});
})(request, response);
        '''.strip()


def generate_rest_script_template(http_method: str, resource_type: str = 'item',
                                table_name: Optional[str] = None) -> str:
    """Generate REST script template based on method and resource type"""
    return RestScriptTemplateFactory.create_template(http_method, resource_type, table_name)


# Legacy template structure for backward compatibility
def _get_legacy_templates():
    return {
        'GET': {
            'collection': f'''
(function process(/*RESTAPIRequest*/ request, /*RESTAPIResponse*/ response) {{
    try {{
        // Get query parameters
        var limit = request.queryParams.limit || 100;
        var offset = request.queryParams.offset || 0;
        var query = request.queryParams.query || '';
        
        // Query the table
        var gr = new GlideRecordSecure('{table_name or "your_table"}');
        if (query) {{
            gr.addEncodedQuery(query);
        }}
        gr.setLimit(limit);
        gr.query();
        
        var results = [];
        while (gr.next()) {{
            results.push({{
                sys_id: gr.getUniqueValue(),
                // Add your fields here
            }});
        }}
        
        response.setStatus(200);
        response.setBody({{
            result: results,
            total: gr.getRowCount()
        }});
        
    }} catch (ex) {{
        gs.error('REST API Error: ' + ex.message);
        response.setStatus(500);
        response.setBody({{error: 'Internal server error'}});
    }}
}})(request, response);
            ''',
            'item': f'''
(function process(/*RESTAPIRequest*/ request, /*RESTAPIResponse*/ response) {{
    try {{
        var id = request.pathParams.id;
        if (!id) {{
            response.setStatus(400);
            response.setBody({{error: 'ID parameter required'}});
            return;
        }}
        
        var gr = new GlideRecordSecure('{table_name or "your_table"}');
        if (gr.get(id)) {{
            response.setStatus(200);
            response.setBody({{
                sys_id: gr.getUniqueValue(),
                // Add your fields here
            }});
        }} else {{
            response.setStatus(404);
            response.setBody({{error: 'Record not found'}});
        }}
        
    }} catch (ex) {{
        gs.error('REST API Error: ' + ex.message);
        response.setStatus(500);
        response.setBody({{error: 'Internal server error'}});
    }}
}})(request, response);
            '''
        },
        'POST': {
            'collection': f'''
(function process(/*RESTAPIRequest*/ request, /*RESTAPIResponse*/ response) {{
    try {{
        var data = request.body.data;
        if (!data) {{
            response.setStatus(400);
            response.setBody({{error: 'Request body required'}});
            return;
        }}
        
        var gr = new GlideRecordSecure('{table_name or "your_table"}');
        gr.initialize();
        
        // Set fields from request data
        // gr.setValue('field_name', data.field_name);
        
        var sys_id = gr.insert();
        if (sys_id) {{
            response.setStatus(201);
            response.setBody({{
                sys_id: sys_id,
                message: 'Record created successfully'
            }});
        }} else {{
            response.setStatus(400);
            response.setBody({{error: 'Failed to create record'}});
        }}
        
    }} catch (ex) {{
        gs.error('REST API Error: ' + ex.message);
        response.setStatus(500);
        response.setBody({{error: 'Internal server error'}});
    }}
}})(request, response);
            '''
        },
        'PUT': {
            'item': f'''
(function process(/*RESTAPIRequest*/ request, /*RESTAPIResponse*/ response) {{
    try {{
        var id = request.pathParams.id;
        var data = request.body.data;
        
        if (!id || !data) {{
            response.setStatus(400);
            response.setBody({{error: 'ID and request body required'}});
            return;
        }}
        
        var gr = new GlideRecordSecure('{table_name or "your_table"}');
        if (gr.get(id)) {{
            // Update fields from request data
            // gr.setValue('field_name', data.field_name);
            
            gr.update();
            response.setStatus(200);
            response.setBody({{
                sys_id: id,
                message: 'Record updated successfully'
            }});
        }} else {{
            response.setStatus(404);
            response.setBody({{error: 'Record not found'}});
        }}
        
    }} catch (ex) {{
        gs.error('REST API Error: ' + ex.message);
        response.setStatus(500);
        response.setBody({{error: 'Internal server error'}});
    }}
}})(request, response);
            '''
        },
        'DELETE': {
            'item': f'''
(function process(/*RESTAPIRequest*/ request, /*RESTAPIResponse*/ response) {{
    try {{
        var id = request.pathParams.id;
        if (!id) {{
            response.setStatus(400);
            response.setBody({{error: 'ID parameter required'}});
            return;
        }}
        
        var gr = new GlideRecordSecure('{table_name or "your_table"}');
        if (gr.get(id)) {{
            gr.deleteRecord();
            response.setStatus(204);
        }} else {{
            response.setStatus(404);
            response.setBody({{error: 'Record not found'}});
        }}
        
    }} catch (ex) {{
        gs.error('REST API Error: ' + ex.message);
        response.setStatus(500);
        response.setBody({{error: 'Internal server error'}});
    }}
}})(request, response);
            '''
        }
    }
    
    template = templates.get(http_method, {}).get(resource_type)
    if not template:
        return f'''
(function process(/*RESTAPIRequest*/ request, /*RESTAPIResponse*/ response) {{
    // TODO: Implement {http_method} {resource_type} logic
    response.setStatus(501);
    response.setBody({{error: 'Not implemented'}});
}})(request, response);
        '''
    
    return template.strip()

def configure_api_authentication(client: ServiceNowClient, api_sys_id: str,
                               auth_type: str, config: Dict[str, Any],
                               dry_run: bool = False) -> Dict[str, Any]:
    """Configure authentication for REST API"""
    
    if auth_type not in AUTHENTICATION_TYPES:
        return {
            'error': f'Invalid authentication type: {auth_type}',
            'valid_types': AUTHENTICATION_TYPES
        }
    
    auth_config = {
        'web_service_definition': api_sys_id,
        'authentication_type': auth_type,
        'active': 'true'
    }
    
    # Configure based on authentication type
    if auth_type == 'oauth':
        required_fields = ['client_id', 'client_secret', 'scope']
        missing_fields = [f for f in required_fields if f not in config]
        if missing_fields:
            return {
                'error': f'Missing OAuth configuration: {missing_fields}',
                'required_fields': required_fields
            }
        auth_config.update(config)
    
    elif auth_type == 'api_key':
        if 'key_name' not in config:
            return {
                'error': 'API key configuration requires key_name',
                'example': {'key_name': 'X-API-Key'}
            }
        auth_config.update(config)
    
    elif auth_type == 'basic':
        auth_config['require_basic_auth'] = 'true'
    
    if dry_run:
        return {
            'dry_run': True,
            'table': 'sys_ws_auth',
            'record': auth_config,
            'auth_type': auth_type
        }
    
    result = client.create_record('sys_ws_auth', auth_config)
    log("configure_api_authentication", {
        "sys_id": result.get("sys_id"),
        "api_sys_id": api_sys_id,
        "auth_type": auth_type
    })
    
    return result

def generate_api_documentation(client: ServiceNowClient, api_sys_id: str) -> Dict[str, Any]:
    """Generate comprehensive API documentation"""
    
    # Get API details
    api = client.get_record('sys_ws_definition', api_sys_id,
                          fields=['name', 'base_path', 'description', 'version'])
    
    if not api:
        return {'error': 'API not found'}
    
    # Get all resources
    resources = client.query_table('sys_ws_operation',
                                 query=f'web_service_definition={api_sys_id}',
                                 fields=['http_method', 'relative_path', 'operation_description'])
    
    # Generate OpenAPI/Swagger documentation
    openapi_doc = {
        'openapi': '3.0.0',
        'info': {
            'title': api.get('name'),
            'description': api.get('description', ''),
            'version': api.get('version', '1.0.0')
        },
        'servers': [
            {
                'url': f"{client.base}{api.get('base_path')}",
                'description': 'ServiceNow instance'
            }
        ],
        'paths': {}
    }
    
    # Add paths from resources
    for resource in resources:
        path = resource.get('relative_path')
        method = resource.get('http_method', '').lower()
        description = resource.get('operation_description', '')
        
        if path not in openapi_doc['paths']:
            openapi_doc['paths'][path] = {}
        
        openapi_doc['paths'][path][method] = {
            'summary': description,
            'responses': {
                '200': {'description': 'Success'},
                '400': {'description': 'Bad Request'},
                '401': {'description': 'Unauthorized'},
                '404': {'description': 'Not Found'},
                '500': {'description': 'Internal Server Error'}
            }
        }
    
    return {
        'api_name': api.get('name'),
        'base_path': api.get('base_path'),
        'resources_count': len(resources),
        'openapi_documentation': openapi_doc,
        'markdown_documentation': generate_markdown_docs(api, resources)
    }

def generate_markdown_docs(api: Dict[str, Any], resources: List[Dict[str, Any]]) -> str:
    """Generate markdown documentation for the API"""
    
    docs = [
        f"# {api.get('name')} API Documentation",
        "",
        f"**Base URL**: `{api.get('base_path')}`",
        f"**Version**: {api.get('version', '1.0.0')}",
        "",
        api.get('description', ''),
        "",
        "## Endpoints",
        ""
    ]
    
    for resource in resources:
        method = resource.get('http_method', '').upper()
        path = resource.get('relative_path', '')
        description = resource.get('operation_description', '')
        
        docs.extend([
            f"### {method} {path}",
            "",
            description,
            "",
            "**Response Codes:**",
            "- 200: Success",
            "- 400: Bad Request", 
            "- 401: Unauthorized",
            "- 404: Not Found",
            "- 500: Internal Server Error",
            ""
        ])
    
    return "\n".join(docs)

def validate_api_setup(client: ServiceNowClient, api_sys_id: str) -> Dict[str, Any]:
    """Validate complete API setup for best practices"""
    
    issues = []
    recommendations = []
    
    # Get API details
    api = client.get_record('sys_ws_definition', api_sys_id)
    if not api:
        return {'error': 'API not found'}
    
    # Check basic API configuration
    if not api.get('description'):
        issues.append("API missing description")
    
    if not api.get('version'):
        recommendations.append("Consider adding version information")
    
    # Check resources
    resources = client.query_table('sys_ws_operation',
                                 query=f'web_service_definition={api_sys_id}')
    
    if len(resources) == 0:
        issues.append("API has no resources defined")
    
    # Check authentication
    auth_configs = client.query_table('sys_ws_auth',
                                    query=f'web_service_definition={api_sys_id}')
    
    if len(auth_configs) == 0:
        recommendations.append("Consider adding authentication for security")
    
    # Validate each resource
    resource_issues = []
    for resource in resources:
        method = resource.get('http_method')
        path = resource.get('relative_path')
        script = resource.get('script', '')
        
        if not script:
            resource_issues.append(f"{method} {path}: Missing implementation script")
        else:
            script_validation = validate_rest_script(script, method)
            if script_validation['issues']:
                resource_issues.extend([f"{method} {path}: {issue}" for issue in script_validation['issues']])
    
    return {
        'api_name': api.get('name'),
        'resources_count': len(resources),
        'auth_configured': len(auth_configs) > 0,
        'issues': issues + resource_issues,
        'recommendations': recommendations,
        'compliance_score': max(0, 100 - (len(issues) * 15) - (len(recommendations) * 5))
    }