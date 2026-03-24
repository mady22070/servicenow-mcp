"""
ServiceNow Background Script Execution Pack

This pack provides comprehensive background script execution capabilities including:
- Safe script execution with validation
- Script templates and examples
- Performance monitoring
- Error handling and logging
- Security validation
- Execution history tracking
"""

from typing import Dict, Any, List, Optional
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime
from ..servicenow_client import ServiceNowClient
from ..utils.audit_simple import log

# Background script safety patterns
DANGEROUS_SCRIPT_PATTERNS = [
    r'while\s*\(\s*true\s*\)',  # Infinite loops
    r'for\s*\(\s*;\s*;\s*\)',   # Infinite for loops
    r'\.deleteRecord\(\)',       # Delete operations
    r'\.deleteMultiple\(\)',     # Bulk delete operations
    r'gs\.sleep\(\s*\d{4,}\s*\)', # Long sleep operations (>= 1000ms)
    r'new\s+GlideRecord\s*\(\s*["\']sys_user["\']', # User table access
    r'new\s+GlideRecord\s*\(\s*["\']sys_user_role["\']', # Role table access
]

# Performance warning patterns
PERFORMANCE_WARNINGS = [
    r'while\s*\(\s*\w+\.next\(\)\s*\)',  # Potential large result sets
    r'for\s*\(\s*var\s+\w+\s*=\s*0\s*;.*\.length',  # Array iterations
    r'new\s+GlideRecord\s*\([^)]+\)(?!.*setLimit)',  # Queries without limits
]

# Required security patterns for production scripts
SECURITY_REQUIREMENTS = [
    r'new\s+GlideRecordSecure',  # Should use secure record access
    r'gs\.hasRole\(',            # Role checking
    r'gs\.getUser\(\)',          # User context validation
]

# Execution constants
DEFAULT_EXECUTION_TIMEOUT = 30
MAX_EXECUTION_TIMEOUT = 300
EXECUTION_STATUS_CHECK_INTERVAL = 1

# Strategy Pattern for Script Execution Methods
class ScriptExecutionStrategy(ABC):
    """Abstract base class for script execution strategies"""
    
    def __init__(self, client):
        self.client = client
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this execution method is available"""
        pass
    
    @abstractmethod
    def execute(self, script: str, execution_id: str, timeout: int) -> Dict[str, Any]:
        """Execute the script using this strategy"""
        pass


class SysScriptExecutionStrategy(ScriptExecutionStrategy):
    """Execute via ServiceNow background script execution endpoint (FIXED)"""
    
    def is_available(self) -> bool:
        try:
            # Test if we can access background script execution
            # Try a simple test script first
            test_endpoint = f"{self.client.base}/sys_script_execution.do"
            response = self.client.session.get(test_endpoint, timeout=5)
            return response.status_code in [200, 302]  # 302 might be redirect to login
        except:
            return False
    
    def execute(self, script: str, execution_id: str, timeout: int) -> Dict[str, Any]:
        # FIXED: Use correct ServiceNow background script execution endpoint
        endpoint = f"{self.client.base}/sys_script_execution.do"
        
        payload = {
            'sysparm_script': script,
            'sysparm_record_target': 'sys_script_execution_history',
            'sysparm_record_row': 'new',
            'sysparm_record_list': '',
            'sysparm_record_uuid': execution_id,
            'sysparm_processor': 'com.glide.script.fencing.ScopedScriptProcessor',
            'sysparm_scope': 'global'
        }
        
        try:
            response = self.client.session.post(endpoint, data=payload, timeout=timeout)
            
            if response.status_code == 200:
                response_text = response.text
                
                # Parse response for execution results
                if 'Script completed' in response_text or 'Output:' in response_text:
                    return {
                        'success': True,
                        'output': response_text,
                        'execution_method': 'sys_script_execution_endpoint',
                        'execution_id': execution_id
                    }
                else:
                    return {
                        'success': True,
                        'output': response_text,
                        'execution_method': 'sys_script_execution_endpoint',
                        'execution_id': execution_id,
                        'note': 'Script executed but output format may vary'
                    }
            else:
                raise Exception(f"Background script execution returned {response.status_code}: {response.text}")
                
        except Exception as e:
            raise Exception(f"Background script execution failed: {str(e)}")
    
    def _monitor_execution_status(self, execution_sys_id: str, timeout: int) -> Dict[str, Any]:
        """Monitor script execution status"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            execution_record = self.client.get_record('sys_script_execution', execution_sys_id,
                                                    fields=['state', 'result', 'error_message'])
            
            if execution_record:
                state = execution_record.get('state')
                
                if state == 'completed':
                    return {
                        'state': 'completed',
                        'result': execution_record.get('result'),
                        'sys_id': execution_sys_id
                    }
                elif state == 'error':
                    return {
                        'state': 'error',
                        'error': execution_record.get('error_message'),
                        'sys_id': execution_sys_id
                    }
            
            time.sleep(EXECUTION_STATUS_CHECK_INTERVAL)
        
        return {
            'state': 'timeout',
            'message': f'Script execution timed out after {timeout} seconds',
            'sys_id': execution_sys_id
        }


class BackgroundScriptAPIStrategy(ScriptExecutionStrategy):
    """Execute via background script API endpoint"""
    
    def is_available(self) -> bool:
        # This would need to be tested based on ServiceNow version/configuration
        return True
    
    def execute(self, script: str, execution_id: str, timeout: int) -> Dict[str, Any]:
        endpoint = f"{self.client.base}/api/now/background_script"
        
        payload = {
            'script': script,
            'execution_id': execution_id
        }
        
        response = self.client.session.post(endpoint, json=payload, timeout=timeout)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Background script API returned {response.status_code}: {response.text}")


class ScriptIncludeWrapperStrategy(ScriptExecutionStrategy):
    """Execute via a script include wrapper (fallback method)"""
    
    def is_available(self) -> bool:
        try:
            # Test if we can create script includes
            self.client.query_table('sys_script_include', limit=1)
            return True
        except:
            return False
    
    def execute(self, script: str, execution_id: str, timeout: int) -> Dict[str, Any]:
        wrapper_script = f'''
var ScriptExecutor = Class.create();
ScriptExecutor.prototype = {{
    execute: function() {{
        try {{
            var result = (function() {{
                {script}
            }})();
            return {{
                success: true,
                result: result,
                execution_id: '{execution_id}'
            }};
        }} catch (ex) {{
            return {{
                success: false,
                error: ex.message,
                execution_id: '{execution_id}'
            }};
        }}
    }},
    type: 'ScriptExecutor'
}};
        '''
        
        script_include_payload = {
            'name': f'TempExecutor_{execution_id}',
            'script': wrapper_script,
            'active': 'true',
            'api_name': f'TempExecutor_{execution_id}'
        }
        
        script_include = self.client.create_record('sys_script_include', script_include_payload)
        
        try:
            execution_script = f'''
var executor = new TempExecutor_{execution_id}();
var result = executor.execute();
gs.info('Script execution result: ' + JSON.stringify(result));
result;
            '''
            
            return self._execute_direct_script(execution_script, timeout)
            
        finally:
            if script_include and script_include.get('sys_id'):
                try:
                    self.client.delete_record('sys_script_include', script_include['sys_id'])
                except:
                    pass
    
    def _execute_direct_script(self, script: str, timeout: int) -> Dict[str, Any]:
        """Direct script execution using ServiceNow's script execution endpoint"""
        endpoint = f"{self.client.base}/sys.do"
        
        payload = {
            'sysparm_processor': 'com.glide.script.fencing.ScopedScriptProcessor',
            'sysparm_scope': 'global',
            'sysparm_script': script
        }
        
        response = self.client.session.post(endpoint, data=payload, timeout=timeout)
        
        if response.status_code == 200:
            return {
                'output': response.text,
                'status_code': response.status_code
            }
        else:
            raise Exception(f"Direct script execution failed: {response.status_code}")


class ScriptExecutionErrorAnalyzer:
    """Analyzes script execution errors and provides recommendations"""
    
    ERROR_PATTERNS = {
        'table_access_error': {
            'patterns': ['invalid table'],
            'message': 'Invalid table name or insufficient table access permissions',
            'recommendations': [
                'Verify table name is correct',
                'Check table access permissions',
                'Ensure table exists in the current scope'
            ]
        },
        'permission_error': {
            'patterns': ['access denied', 'forbidden'],
            'message': 'Insufficient permissions for script execution',
            'recommendations': [
                'Verify user has admin or script execution roles',
                'Check ACL permissions for script execution',
                'Contact ServiceNow administrator'
            ]
        },
        'timeout_error': {
            'patterns': ['timeout'],
            'message': 'Script execution timed out',
            'recommendations': [
                'Optimize script performance',
                'Add query limits to reduce processing time',
                'Break large operations into smaller chunks'
            ]
        },
        'syntax_error': {
            'patterns': ['syntax error', 'unexpected token'],
            'message': 'JavaScript syntax error in script',
            'recommendations': [
                'Review script syntax',
                'Check for missing semicolons or brackets',
                'Validate variable declarations'
            ]
        }
    }
    
    @classmethod
    def analyze(cls, error_msg: str) -> Dict[str, Any]:
        """Analyze error message and return structured error information"""
        error_msg_lower = error_msg.lower()
        
        for error_type, config in cls.ERROR_PATTERNS.items():
            if any(pattern in error_msg_lower for pattern in config['patterns']):
                return {
                    'type': error_type,
                    'message': config['message'],
                    'recommendations': config['recommendations']
                }
        
        return {
            'type': 'unknown_error',
            'message': 'Unknown execution error',
            'recommendations': [
                'Review ServiceNow system logs',
                'Check script logic for potential issues',
                'Contact ServiceNow administrator if problem persists'
            ]
        }


class ScriptExecutionContext:
    """Context object to track script execution state"""
    
    def __init__(self, script: str, timeout: int):
        self.script = script
        self.timeout = timeout
        self.execution_id = f"exec_{int(time.time())}"
        self.start_time = time.time()
        self.end_time = None
    
    @property
    def execution_time(self) -> float:
        """Get execution time in seconds"""
        end = self.end_time or time.time()
        return end - self.start_time
    
    def mark_completed(self):
        """Mark execution as completed"""
        self.end_time = time.time()


class BackgroundScriptExecutor:
    """Handles safe background script execution with enhanced error handling"""
    
    def __init__(self, client: ServiceNowClient):
        self.client = client
        self.execution_history = []
    
    def validate_permissions(self) -> Dict[str, Any]:
        """Validate user permissions for script execution"""
        try:
            # Check if user can access script execution endpoints
            test_query = self.client.query_table('sys_script_execution_history', limit=1)
            return {
                'can_execute': True,
                'has_history_access': True,
                'validation_passed': True
            }
        except Exception as e:
            error_msg = str(e).lower()
            if 'access denied' in error_msg or 'forbidden' in error_msg:
                return {
                    'can_execute': False,
                    'error': 'Insufficient permissions for background script execution',
                    'required_roles': ['admin', 'script_executor'],
                    'validation_passed': False
                }
            return {
                'can_execute': True,
                'warning': 'Cannot validate permissions, proceeding with caution',
                'validation_passed': True
            }
    
    def execute_script_enhanced(self, script: str, validate_permissions: bool = True,
                              timeout: int = DEFAULT_EXECUTION_TIMEOUT) -> Dict[str, Any]:
        """Execute background script with enhanced error handling and validation"""
        
        # Pre-execution validation
        validation_result = self._perform_pre_execution_validation(script, validate_permissions)
        if not validation_result['success']:
            return validation_result
        
        execution_context = ScriptExecutionContext(script, timeout)
        
        try:
            result = self._execute_with_monitoring(execution_context)
            return self._create_success_response(execution_context, result, validation_result['validation'])
            
        except Exception as e:
            return self._create_error_response(execution_context, e, validation_result['validation'])
    
    def _perform_pre_execution_validation(self, script: str, validate_permissions: bool) -> Dict[str, Any]:
        """Perform all pre-execution validation checks"""
        if validate_permissions:
            perm_check = self.validate_permissions()
            if not perm_check['validation_passed']:
                return {'success': False, **perm_check}
        
        validation = validate_background_script(script)
        if validation['risk_level'] == 'high':
            return {
                'success': False,
                'error': 'High-risk script detected',
                'validation': validation,
                'recommendation': 'Review and modify script before execution'
            }
        
        return {'success': True, 'validation': validation}
    
    def _execute_with_monitoring(self, context: 'ScriptExecutionContext') -> Dict[str, Any]:
        """Execute script with monitoring and return result"""
        return self._try_execution_methods(context.script, context.execution_id, context.timeout)
    
    def _create_success_response(self, context: 'ScriptExecutionContext', result: Dict[str, Any], 
                               validation: Dict[str, Any]) -> Dict[str, Any]:
        """Create success response with logging"""
        context.mark_completed()
        
        log("background_script_execution", {
            "execution_id": context.execution_id,
            "execution_time": context.execution_time,
            "script_length": len(context.script),
            "success": True
        })
        
        return {
            'success': True,
            'execution_id': context.execution_id,
            'execution_time': context.execution_time,
            'result': result,
            'validation': validation
        }
    
    def _create_error_response(self, context: 'ScriptExecutionContext', error: Exception, 
                             validation: Dict[str, Any]) -> Dict[str, Any]:
        """Create error response with analysis and logging"""
        context.mark_completed()
        error_msg = str(error)
        error_analysis = self._analyze_execution_error(error_msg)
        
        log("background_script_execution_error", {
            "execution_id": context.execution_id,
            "execution_time": context.execution_time,
            "error": error_msg,
            "error_type": error_analysis['type']
        })
        
        return {
            'success': False,
            'execution_id': context.execution_id,
            'execution_time': context.execution_time,
            'error': error_msg,
            'error_analysis': error_analysis,
            'validation': validation
        }
    
    def _try_execution_methods(self, script: str, execution_id: str, timeout: int) -> Dict[str, Any]:
        """Try different execution methods based on ServiceNow capabilities"""
        
        execution_strategies = [
            SysScriptExecutionStrategy(self.client),
            BackgroundScriptAPIStrategy(self.client),
            ScriptIncludeWrapperStrategy(self.client)
        ]
        
        last_error = None
        
        for strategy in execution_strategies:
            try:
                if strategy.is_available():
                    return strategy.execute(script, execution_id, timeout)
            except Exception as e:
                last_error = e
                continue
        
        # If all methods fail, raise the last error
        raise last_error or Exception("No execution strategies available")
    

    
    def _analyze_execution_error(self, error_msg: str) -> Dict[str, Any]:
        """Analyze execution error and provide recommendations"""
        return ScriptExecutionErrorAnalyzer.analyze(error_msg)
    
    def validate_script_safety(self, script: str, allow_dangerous: bool = False) -> Dict[str, Any]:
        """Validate script for safety before execution"""
        
        issues = []
        warnings = []
        security_issues = []
        
        # Check for dangerous patterns
        for pattern in DANGEROUS_SCRIPT_PATTERNS:
            if re.search(pattern, script, re.IGNORECASE):
                issues.append(f"Dangerous pattern detected: {pattern}")
        
        # Check for performance warnings
        for pattern in PERFORMANCE_WARNINGS:
            if re.search(pattern, script, re.IGNORECASE):
                warnings.append(f"Performance concern: {pattern}")
        
        # Check for security requirements in production scripts
        has_security = any(re.search(pattern, script, re.IGNORECASE) for pattern in SECURITY_REQUIREMENTS)
        if not has_security and len(script) > 100:  # Only for substantial scripts
            security_issues.append("Script should include security validation (user context, roles)")
        
        # Check for basic script structure
        if 'try' not in script and 'catch' not in script and len(script) > 50:
            warnings.append("Consider adding try-catch error handling")
        
        # Check for logging
        if not any(log_func in script for log_func in ['gs.info', 'gs.log', 'gs.warn', 'gs.error']):
            warnings.append("Consider adding logging for monitoring and debugging")
        
        return {
            'safe': len(issues) == 0 or allow_dangerous,
            'issues': issues,
            'warnings': warnings,
            'security_issues': security_issues,
            'allow_dangerous': allow_dangerous,
            'script_length': len(script),
            'estimated_risk': self.calculate_risk_score(issues, warnings, security_issues)
        }
    
    def calculate_risk_score(self, issues: List[str], warnings: List[str], security_issues: List[str]) -> str:
        """Calculate risk score for script execution"""
        score = len(issues) * 10 + len(warnings) * 3 + len(security_issues) * 5
        
        if score == 0:
            return "LOW"
        elif score <= 10:
            return "MEDIUM"
        elif score <= 20:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def execute_background_script(self, script: str, description: str = "", 
                                 validate_safety: bool = True, allow_dangerous: bool = False,
                                 dry_run: bool = False) -> Dict[str, Any]:
        """Execute background script with safety validation"""
        
        execution_id = f"exec_{int(time.time())}"
        start_time = datetime.utcnow()
        
        # Validate script safety
        if validate_safety:
            safety_check = self.validate_script_safety(script, allow_dangerous)
            if not safety_check['safe']:
                return {
                    'execution_id': execution_id,
                    'status': 'blocked',
                    'reason': 'Safety validation failed',
                    'safety_check': safety_check,
                    'recommendation': 'Review and fix safety issues or use allow_dangerous=True'
                }
        else:
            safety_check = {'safe': True, 'issues': [], 'warnings': [], 'security_issues': []}
        
        if dry_run:
            return {
                'execution_id': execution_id,
                'status': 'dry_run',
                'script': script,
                'description': description,
                'safety_check': safety_check,
                'would_execute': safety_check['safe']
            }
        
        # Execute the script
        try:
            # Wrap script with execution tracking
            wrapped_script = self.wrap_script_for_execution(script, execution_id, description)
            
            # Execute via ServiceNow's background script API
            result = self.client.request(
                'POST',
                '/api/now/table/sys_script_execution',
                json={
                    'script': wrapped_script,
                    'description': description or f"MCP Background Script - {execution_id}"
                }
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Track execution
            execution_record = {
                'execution_id': execution_id,
                'script': script,
                'description': description,
                'start_time': start_time.isoformat(),
                'execution_time_seconds': execution_time,
                'safety_check': safety_check,
                'result': result,
                'status': 'completed'
            }
            
            self.execution_history.append(execution_record)
            
            log("execute_background_script", {
                "execution_id": execution_id,
                "description": description,
                "execution_time": execution_time,
                "safety_score": safety_check.get('estimated_risk', 'UNKNOWN')
            })
            
            return {
                'execution_id': execution_id,
                'status': 'completed',
                'result': result,
                'execution_time_seconds': execution_time,
                'safety_check': safety_check,
                'sys_id': result.get('result', {}).get('sys_id') if isinstance(result.get('result'), dict) else None
            }
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            error_record = {
                'execution_id': execution_id,
                'script': script,
                'description': description,
                'start_time': start_time.isoformat(),
                'execution_time_seconds': execution_time,
                'safety_check': safety_check,
                'error': str(e),
                'status': 'failed'
            }
            
            self.execution_history.append(error_record)
            
            return {
                'execution_id': execution_id,
                'status': 'failed',
                'error': str(e),
                'execution_time_seconds': execution_time,
                'safety_check': safety_check
            }
    
    def wrap_script_for_execution(self, script: str, execution_id: str, description: str) -> str:
        """Wrap script with execution tracking and error handling"""
        
        wrapped_script = f'''
// MCP Background Script Execution
// Execution ID: {execution_id}
// Description: {description}
// Timestamp: {datetime.utcnow().isoformat()}

(function() {{
    var startTime = new Date();
    var executionId = '{execution_id}';
    
    try {{
        gs.info('MCP Background Script Started - ID: ' + executionId);
        
        // User provided script starts here
        {script}
        // User provided script ends here
        
        var endTime = new Date();
        var duration = endTime.getTime() - startTime.getTime();
        gs.info('MCP Background Script Completed - ID: ' + executionId + ', Duration: ' + duration + 'ms');
        
    }} catch (ex) {{
        var endTime = new Date();
        var duration = endTime.getTime() - startTime.getTime();
        gs.error('MCP Background Script Failed - ID: ' + executionId + ', Duration: ' + duration + 'ms, Error: ' + ex.message);
        throw ex;
    }}
}})();
        '''
        
        return wrapped_script.strip()
    
    def get_execution_history(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent execution history"""
        
        recent_executions = self.execution_history[-limit:] if self.execution_history else []
        
        return {
            'total_executions': len(self.execution_history),
            'recent_executions': recent_executions,
            'success_rate': self.calculate_success_rate(),
            'average_execution_time': self.calculate_average_execution_time()
        }
    
    def calculate_success_rate(self) -> float:
        """Calculate success rate of executions"""
        if not self.execution_history:
            return 0.0
        
        successful = len([e for e in self.execution_history if e['status'] == 'completed'])
        return (successful / len(self.execution_history)) * 100
    
    def calculate_average_execution_time(self) -> float:
        """Calculate average execution time"""
        if not self.execution_history:
            return 0.0
        
        total_time = sum(e.get('execution_time_seconds', 0) for e in self.execution_history)
        return total_time / len(self.execution_history)

def generate_script_templates() -> Dict[str, str]:
    """Generate common background script templates"""
    
    templates = {
        'data_cleanup': '''
// Data Cleanup Script Template
// Description: Clean up old records based on criteria

(function() {
    var tableName = 'your_table_name';
    var daysOld = 90;
    var maxRecords = 1000;
    
    // Calculate date threshold
    var cutoffDate = new GlideDateTime();
    cutoffDate.addDaysLocalTime(-daysOld);
    
    var gr = new GlideRecordSecure(tableName);
    gr.addQuery('sys_created_on', '<', cutoffDate);
    gr.addQuery('state', 'closed'); // Add your criteria
    gr.setLimit(maxRecords);
    gr.query();
    
    var count = 0;
    while (gr.next()) {
        // Add your cleanup logic here
        // gr.deleteRecord(); // Uncomment if you want to delete
        count++;
    }
    
    gs.info('Processed ' + count + ' records for cleanup');
})();
        ''',
        
        'data_migration': '''
// Data Migration Script Template
// Description: Migrate data between tables or update records

(function() {
    var sourceTable = 'source_table';
    var targetTable = 'target_table';
    var batchSize = 100;
    
    var sourceGr = new GlideRecordSecure(sourceTable);
    sourceGr.addQuery('migrated', false); // Add your criteria
    sourceGr.setLimit(batchSize);
    sourceGr.query();
    
    var migrated = 0;
    while (sourceGr.next()) {
        try {
            var targetGr = new GlideRecordSecure(targetTable);
            targetGr.initialize();
            
            // Map fields from source to target
            targetGr.setValue('field1', sourceGr.getValue('field1'));
            targetGr.setValue('field2', sourceGr.getValue('field2'));
            
            var newSysId = targetGr.insert();
            if (newSysId) {
                sourceGr.setValue('migrated', true);
                sourceGr.setValue('migrated_to', newSysId);
                sourceGr.update();
                migrated++;
            }
        } catch (ex) {
            gs.error('Migration failed for record ' + sourceGr.getUniqueValue() + ': ' + ex.message);
        }
    }
    
    gs.info('Successfully migrated ' + migrated + ' records');
})();
        ''',
        
        'bulk_update': '''
// Bulk Update Script Template
// Description: Update multiple records based on criteria

(function() {
    var tableName = 'your_table_name';
    var batchSize = 500;
    
    var gr = new GlideRecordSecure(tableName);
    gr.addQuery('field_to_check', 'old_value'); // Add your criteria
    gr.setLimit(batchSize);
    gr.query();
    
    var updated = 0;
    while (gr.next()) {
        try {
            // Update logic
            gr.setValue('field_to_update', 'new_value');
            gr.setValue('last_updated_by', 'background_script');
            gr.update();
            updated++;
        } catch (ex) {
            gs.error('Update failed for record ' + gr.getUniqueValue() + ': ' + ex.message);
        }
    }
    
    gs.info('Successfully updated ' + updated + ' records');
})();
        ''',
        
        'data_analysis': '''
// Data Analysis Script Template
// Description: Analyze data and generate reports

(function() {
    var tableName = 'your_table_name';
    
    // Use GlideAggregate for efficient counting and grouping
    var ga = new GlideAggregate(tableName);
    ga.addAggregate('COUNT');
    ga.groupBy('state');
    ga.query();
    
    var results = {};
    while (ga.next()) {
        var state = ga.getValue('state');
        var count = ga.getAggregate('COUNT');
        results[state] = count;
        gs.info('State: ' + state + ', Count: ' + count);
    }
    
    // Additional analysis
    var totalRecords = 0;
    for (var state in results) {
        totalRecords += parseInt(results[state]);
    }
    
    gs.info('Total records analyzed: ' + totalRecords);
    gs.info('Analysis results: ' + JSON.stringify(results));
})();
        ''',
        
        'system_maintenance': '''
// System Maintenance Script Template
// Description: Perform system maintenance tasks

(function() {
    var maintenanceLog = [];
    
    try {
        // Clear cache
        gs.getProperty('glide.cache.clear_all', 'false');
        maintenanceLog.push('Cache cleared');
        
        // Update system properties if needed
        var prop = new GlideRecord('sys_properties');
        if (prop.get('name', 'your.property.name')) {
            prop.setValue('value', 'new_value');
            prop.update();
            maintenanceLog.push('Property updated: your.property.name');
        }
        
        // Clean up temporary files or data
        var tempGr = new GlideRecordSecure('your_temp_table');
        tempGr.addQuery('sys_created_on', '<', gs.daysAgoStart(7)); // Older than 7 days
        tempGr.query();
        
        var cleaned = 0;
        while (tempGr.next()) {
            tempGr.deleteRecord();
            cleaned++;
        }
        maintenanceLog.push('Cleaned up ' + cleaned + ' temporary records');
        
        gs.info('Maintenance completed: ' + maintenanceLog.join(', '));
        
    } catch (ex) {
        gs.error('Maintenance script failed: ' + ex.message);
    }
})();
        '''
    }
    
    return templates

def validate_script_syntax(script: str) -> Dict[str, Any]:
    """Basic JavaScript syntax validation"""
    
    issues = []
    warnings = []
    
    # Check for basic syntax issues
    open_braces = script.count('{')
    close_braces = script.count('}')
    if open_braces != close_braces:
        issues.append(f"Mismatched braces: {open_braces} opening, {close_braces} closing")
    
    open_parens = script.count('(')
    close_parens = script.count(')')
    if open_parens != close_parens:
        issues.append(f"Mismatched parentheses: {open_parens} opening, {close_parens} closing")
    
    # Check for common mistakes
    if 'var ' not in script and 'let ' not in script and 'const ' not in script and len(script) > 50:
        warnings.append("No variable declarations found - consider using 'var', 'let', or 'const'")
    
    if script.count(';') < script.count('\n') / 3:
        warnings.append("Few semicolons found - consider adding semicolons for clarity")
    
    # Check for ServiceNow specific patterns
    if 'GlideRecord' in script and 'query()' not in script:
        warnings.append("GlideRecord found but no query() call - did you forget to call query()?")
    
    if 'while(' in script and 'next()' in script and 'setLimit(' not in script:
        warnings.append("Potential performance issue: while loop without setLimit()")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'syntax_score': max(0, 100 - (len(issues) * 20) - (len(warnings) * 5))
    }

# Convenience functions for the pack
def execute_background_script(client: ServiceNowClient, script: str, description: str = "",
                            validate_safety: bool = True, allow_dangerous: bool = False,
                            dry_run: bool = False) -> Dict[str, Any]:
    """Execute background script with safety validation"""
    executor = BackgroundScriptExecutor(client)
    return executor.execute_background_script(script, description, validate_safety, allow_dangerous, dry_run)

def validate_script_safety(script: str, allow_dangerous: bool = False) -> Dict[str, Any]:
    """Validate script for safety before execution"""
    executor = BackgroundScriptExecutor(None)
    return executor.validate_script_safety(script, allow_dangerous)

def get_script_templates() -> Dict[str, str]:
    """Get common background script templates"""
    return generate_script_templates()

def get_execution_history(client: ServiceNowClient, limit: int = 10) -> Dict[str, Any]:
    """Get recent execution history"""
    executor = BackgroundScriptExecutor(client)
    return executor.get_execution_history(limit)

def analyze_script_performance(script: str) -> Dict[str, Any]:
    """Analyze script for potential performance issues"""
    
    performance_issues = []
    recommendations = []
    
    # Check for performance anti-patterns
    if re.search(r'while\s*\(\s*\w+\.next\(\)\s*\)', script):
        if 'setLimit(' not in script:
            performance_issues.append("Unbounded while loop - use setLimit() to prevent performance issues")
    
    if re.search(r'new\s+GlideRecord\s*\([^)]+\)', script):
        if 'GlideRecordSecure' not in script:
            recommendations.append("Consider using GlideRecordSecure for better security")
    
    if script.count('new GlideRecord') > 3:
        performance_issues.append("Multiple GlideRecord instantiations - consider optimizing queries")
    
    if 'gs.sleep(' in script:
        performance_issues.append("Script contains sleep() calls - may impact performance")
    
    # Check for efficient patterns
    if 'GlideAggregate' in script:
        recommendations.append("Good: Using GlideAggregate for efficient data aggregation")
    
    if 'setLimit(' in script:
        recommendations.append("Good: Using setLimit() to control result set size")
    
    if 'try' in script and 'catch' in script:
        recommendations.append("Good: Using try-catch for error handling")
    
    return {
        'performance_score': max(0, 100 - (len(performance_issues) * 15)),
        'performance_issues': performance_issues,
        'recommendations': recommendations,
        'estimated_execution_time': estimate_execution_time(script)
    }

def estimate_execution_time(script: str) -> str:
    """Estimate script execution time based on complexity"""
    
    complexity_score = 0
    
    # Count operations that affect execution time
    complexity_score += script.count('new GlideRecord') * 2
    complexity_score += script.count('while(') * 3
    complexity_score += script.count('for(') * 2
    complexity_score += script.count('.next()') * 1
    complexity_score += script.count('.update()') * 2
    complexity_score += script.count('.insert()') * 2
    complexity_score += script.count('.deleteRecord()') * 3
    
    if complexity_score <= 5:
        return "< 1 second"
    elif complexity_score <= 15:
        return "1-10 seconds"
    elif complexity_score <= 30:
        return "10-60 seconds"
    else:
        return "> 1 minute (consider optimization)"