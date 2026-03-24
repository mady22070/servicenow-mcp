"""
ServiceNow Documentation Pack

This pack provides comprehensive access to ServiceNow documentation including:
- Official ServiceNow documentation search
- Community article lookup
- Best practices recommendations
- Code examples and templates
- Version-specific documentation
- Contextual help and troubleshooting
"""

from typing import Dict, Any, List, Optional
import re
import json
from ..servicenow_client import ServiceNowClient
from ..utils.audit_simple import log

# ServiceNow Documentation Categories
DOC_CATEGORIES = {
    'platform': ['tables', 'fields', 'business_rules', 'client_scripts', 'ui_policies'],
    'development': ['scripting', 'rest_api', 'soap_api', 'scoped_apps', 'update_sets'],
    'administration': ['users', 'roles', 'acls', 'properties', 'notifications'],
    'itsm': ['incident', 'problem', 'change', 'request', 'knowledge'],
    'itom': ['discovery', 'orchestration', 'event_management', 'service_mapping'],
    'hrsd': ['hr_case', 'employee_center', 'hr_service_portal'],
    'csm': ['customer_service', 'case_management', 'knowledge_management'],
    'security': ['vulnerability', 'grc', 'threat_intelligence', 'security_operations']
}

# Common ServiceNow APIs and their documentation
SERVICENOW_APIS = {
    'GlideRecord': {
        'description': 'Server-side API for database operations',
        'methods': ['query', 'next', 'insert', 'update', 'deleteRecord', 'get', 'addQuery'],
        'best_practices': [
            'Use GlideRecordSecure for security',
            'Always check if record exists before operations',
            'Use setLimit() to prevent performance issues',
            'Prefer addQuery() over addEncodedQuery() when possible'
        ]
    },
    'GlideForm': {
        'description': 'Client-side API for form manipulation',
        'methods': ['getValue', 'setValue', 'setVisible', 'setMandatory', 'addInfoMessage'],
        'best_practices': [
            'Avoid direct DOM manipulation',
            'Use g_form.addInfoMessage() instead of alert()',
            'Check field existence before operations',
            'Use onChange() for field-specific logic'
        ]
    },
    'GlideSystem': {
        'description': 'Server-side system utilities',
        'methods': ['info', 'warn', 'error', 'debug', 'getUserID', 'getProperty'],
        'best_practices': [
            'Use appropriate log levels',
            'Use gs.getUserID() instead of gs.getUser().getID()',
            'Store configuration in system properties',
            'Handle exceptions properly'
        ]
    }
}

# ServiceNow Best Practices Database
BEST_PRACTICES = {
    'scripting': {
        'server_side': [
            'Use GlideRecordSecure instead of GlideRecord for security',
            'Always validate input parameters',
            'Use try-catch blocks for error handling',
            'Avoid hardcoding values, use system properties',
            'Use appropriate logging levels (gs.info, gs.warn, gs.error)',
            'Limit database queries in loops',
            'Use setLimit() to prevent performance issues'
        ],
        'client_side': [
            'Avoid alert() popups, use g_form.addInfoMessage()',
            'Check if fields exist before accessing them',
            'Use onChange() for field-specific validation',
            'Minimize server calls from client scripts',
            'Use g_form.setVisible() instead of hiding with CSS',
            'Validate data before submission'
        ]
    },
    'performance': [
        'Use indexed fields in queries',
        'Limit the number of records processed',
        'Avoid nested loops with database operations',
        'Use GlideAggregate for counting and statistics',
        'Cache frequently accessed data',
        'Use asynchronous processing for heavy operations'
    ],
    'security': [
        'Use GlideRecordSecure for data access',
        'Validate all user inputs',
        'Use ACLs to control data access',
        'Avoid exposing sensitive data in client scripts',
        'Use proper authentication for REST APIs',
        'Sanitize data before database operations'
    ]
}

def search_documentation(topic: str, category: Optional[str] = None, 
                        version: str = "latest") -> Dict[str, Any]:
    """Search ServiceNow documentation for specific topics"""
    
    results = []
    
    # Search in API documentation
    for api_name, api_info in SERVICENOW_APIS.items():
        if topic.lower() in api_name.lower() or topic.lower() in api_info['description'].lower():
            results.append({
                'type': 'api_reference',
                'title': f"{api_name} API",
                'description': api_info['description'],
                'methods': api_info['methods'],
                'best_practices': api_info['best_practices'],
                'relevance_score': calculate_relevance(topic, api_name, api_info['description'])
            })
    
    # Search in best practices
    if category and category in BEST_PRACTICES:
        practices = BEST_PRACTICES[category]
        if isinstance(practices, dict):
            for subcategory, practice_list in practices.items():
                matching_practices = [p for p in practice_list if topic.lower() in p.lower()]
                if matching_practices:
                    results.append({
                        'type': 'best_practices',
                        'title': f"{category.title()} - {subcategory.title()} Best Practices",
                        'practices': matching_practices,
                        'relevance_score': len(matching_practices) * 10
                    })
        else:
            matching_practices = [p for p in practices if topic.lower() in p.lower()]
            if matching_practices:
                results.append({
                    'type': 'best_practices',
                    'title': f"{category.title()} Best Practices",
                    'practices': matching_practices,
                    'relevance_score': len(matching_practices) * 10
                })
    
    # Search across all categories if no specific category
    if not category:
        for cat_name, practices in BEST_PRACTICES.items():
            if isinstance(practices, dict):
                for subcategory, practice_list in practices.items():
                    matching_practices = [p for p in practice_list if topic.lower() in p.lower()]
                    if matching_practices:
                        results.append({
                            'type': 'best_practices',
                            'title': f"{cat_name.title()} - {subcategory.title()} Best Practices",
                            'practices': matching_practices,
                            'relevance_score': len(matching_practices) * 5
                        })
            else:
                matching_practices = [p for p in practices if topic.lower() in p.lower()]
                if matching_practices:
                    results.append({
                        'type': 'best_practices',
                        'title': f"{cat_name.title()} Best Practices",
                        'practices': matching_practices,
                        'relevance_score': len(matching_practices) * 5
                    })
    
    # Sort by relevance score
    results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    return {
        'query': topic,
        'category': category,
        'version': version,
        'results_count': len(results),
        'results': results[:10]  # Limit to top 10 results
    }

def calculate_relevance(query: str, title: str, description: str) -> int:
    """Calculate relevance score for search results"""
    score = 0
    query_lower = query.lower()
    
    # Exact match in title gets highest score
    if query_lower == title.lower():
        score += 100
    elif query_lower in title.lower():
        score += 50
    
    # Partial match in description
    if query_lower in description.lower():
        score += 25
    
    # Word matches
    query_words = query_lower.split()
    title_words = title.lower().split()
    desc_words = description.lower().split()
    
    for word in query_words:
        if word in title_words:
            score += 10
        if word in desc_words:
            score += 5
    
    return score

def get_code_examples(api_name: str, method: Optional[str] = None) -> Dict[str, Any]:
    """Get code examples for ServiceNow APIs"""
    
    examples = {
        'GlideRecord': {
            'query': '''
// Query records with conditions
var gr = new GlideRecord('incident');
gr.addQuery('state', 1);
gr.addQuery('priority', 1);
gr.setLimit(10);
gr.query();

while (gr.next()) {
    gs.info('Incident: ' + gr.number + ' - ' + gr.short_description);
}
            ''',
            'insert': '''
// Create new record
var gr = new GlideRecord('incident');
gr.initialize();
gr.short_description = 'New incident';
gr.description = 'Detailed description';
gr.caller_id = gs.getUserID();
gr.state = 1;
gr.priority = 3;

var sys_id = gr.insert();
if (sys_id) {
    gs.info('Created incident: ' + sys_id);
}
            ''',
            'update': '''
// Update existing record
var gr = new GlideRecord('incident');
if (gr.get('sys_id_here')) {
    gr.state = 6; // Resolved
    gr.resolution_notes = 'Issue resolved';
    gr.update();
    gs.info('Updated incident: ' + gr.number);
}
            ''',
            'delete': '''
// Delete record (use with caution)
var gr = new GlideRecord('incident');
if (gr.get('sys_id_here')) {
    gr.deleteRecord();
    gs.info('Deleted incident: ' + gr.number);
}
            '''
        },
        'GlideForm': {
            'getValue': '''
// Get field value
function onChange(control, oldValue, newValue, isLoading, isTemplate) {
    var priority = g_form.getValue('priority');
    if (priority == '1') {
        g_form.addInfoMessage('High priority incident requires approval');
    }
}
            ''',
            'setValue': '''
// Set field value
function onLoad() {
    // Set default values
    if (g_form.isNewRecord()) {
        g_form.setValue('state', '1');
        g_form.setValue('priority', '3');
    }
}
            ''',
            'setVisible': '''
// Control field visibility
function onChange(control, oldValue, newValue, isLoading, isTemplate) {
    if (newValue == 'hardware') {
        g_form.setVisible('hardware_details', true);
        g_form.setMandatory('hardware_details', true);
    } else {
        g_form.setVisible('hardware_details', false);
        g_form.setMandatory('hardware_details', false);
    }
}
            '''
        },
        'REST_API': {
            'get': '''
// GET request example
(function process(/*RESTAPIRequest*/ request, /*RESTAPIResponse*/ response) {
    try {
        var id = request.pathParams.id;
        var gr = new GlideRecord('incident');
        
        if (gr.get(id)) {
            var result = {
                sys_id: gr.getUniqueValue(),
                number: gr.getValue('number'),
                short_description: gr.getValue('short_description'),
                state: gr.getValue('state')
            };
            
            response.setStatus(200);
            response.setBody(result);
        } else {
            response.setStatus(404);
            response.setBody({error: 'Record not found'});
        }
    } catch (ex) {
        response.setStatus(500);
        response.setBody({error: ex.message});
    }
})(request, response);
            ''',
            'post': '''
// POST request example
(function process(/*RESTAPIRequest*/ request, /*RESTAPIResponse*/ response) {
    try {
        var data = request.body.data;
        
        if (!data || !data.short_description) {
            response.setStatus(400);
            response.setBody({error: 'short_description is required'});
            return;
        }
        
        var gr = new GlideRecord('incident');
        gr.initialize();
        gr.short_description = data.short_description;
        gr.description = data.description || '';
        gr.caller_id = gs.getUserID();
        
        var sys_id = gr.insert();
        
        if (sys_id) {
            response.setStatus(201);
            response.setBody({
                sys_id: sys_id,
                number: gr.getValue('number')
            });
        } else {
            response.setStatus(400);
            response.setBody({error: 'Failed to create record'});
        }
    } catch (ex) {
        response.setStatus(500);
        response.setBody({error: ex.message});
    }
})(request, response);
            '''
        }
    }
    
    if api_name not in examples:
        return {
            'error': f'No examples found for API: {api_name}',
            'available_apis': list(examples.keys())
        }
    
    api_examples = examples[api_name]
    
    if method and method in api_examples:
        return {
            'api': api_name,
            'method': method,
            'example': api_examples[method].strip(),
            'description': f'Example usage of {api_name}.{method}()'
        }
    
    return {
        'api': api_name,
        'available_methods': list(api_examples.keys()),
        'examples': {k: v.strip() for k, v in api_examples.items()}
    }

def get_troubleshooting_guide(error_type: str, context: Optional[str] = None) -> Dict[str, Any]:
    """Get troubleshooting guide for common ServiceNow issues"""
    
    troubleshooting_guides = {
        'script_error': {
            'title': 'Script Execution Errors',
            'common_causes': [
                'Null pointer exceptions',
                'Invalid field references',
                'Missing permissions',
                'Syntax errors',
                'Infinite loops'
            ],
            'solutions': [
                'Check for null values before accessing properties',
                'Verify field names and table structure',
                'Ensure user has proper roles and ACLs',
                'Use try-catch blocks for error handling',
                'Add loop counters and exit conditions'
            ],
            'prevention': [
                'Use GlideRecordSecure for security',
                'Validate inputs before processing',
                'Test scripts in development environment',
                'Use proper logging for debugging'
            ]
        },
        'performance_issue': {
            'title': 'Performance Issues',
            'common_causes': [
                'Inefficient database queries',
                'Missing indexes',
                'Large result sets',
                'Nested loops with database calls',
                'Heavy client-side processing'
            ],
            'solutions': [
                'Use indexed fields in queries',
                'Implement proper query limits',
                'Use GlideAggregate for statistics',
                'Optimize business rule conditions',
                'Move heavy processing to server-side'
            ],
            'prevention': [
                'Profile and monitor script performance',
                'Use appropriate data structures',
                'Implement caching where appropriate',
                'Regular performance testing'
            ]
        },
        'security_issue': {
            'title': 'Security Issues',
            'common_causes': [
                'Insufficient access controls',
                'Data exposure in client scripts',
                'Missing input validation',
                'Improper authentication',
                'Privilege escalation'
            ],
            'solutions': [
                'Implement proper ACLs',
                'Use server-side validation',
                'Sanitize all user inputs',
                'Use GlideRecordSecure',
                'Follow principle of least privilege'
            ],
            'prevention': [
                'Regular security audits',
                'Code review processes',
                'Security training for developers',
                'Use security best practices'
            ]
        },
        'integration_issue': {
            'title': 'Integration Issues',
            'common_causes': [
                'Authentication failures',
                'Network connectivity issues',
                'Data format mismatches',
                'API rate limiting',
                'Certificate problems'
            ],
            'solutions': [
                'Verify credentials and permissions',
                'Check network connectivity and firewall rules',
                'Validate data formats and schemas',
                'Implement retry logic with backoff',
                'Update certificates and trust stores'
            ],
            'prevention': [
                'Monitor integration health',
                'Implement proper error handling',
                'Use connection pooling',
                'Regular testing of integrations'
            ]
        }
    }
    
    if error_type not in troubleshooting_guides:
        return {
            'error': f'No troubleshooting guide found for: {error_type}',
            'available_guides': list(troubleshooting_guides.keys())
        }
    
    guide = troubleshooting_guides[error_type]
    
    # Add context-specific recommendations
    if context:
        guide['context_specific'] = get_context_specific_advice(error_type, context)
    
    return guide

def get_context_specific_advice(error_type: str, context: str) -> List[str]:
    """Get context-specific troubleshooting advice"""
    
    advice = []
    context_lower = context.lower()
    
    if error_type == 'script_error':
        if 'business rule' in context_lower:
            advice.extend([
                'Check business rule conditions and timing',
                'Verify table access permissions',
                'Ensure proper field references'
            ])
        elif 'client script' in context_lower:
            advice.extend([
                'Check for proper form field references',
                'Verify client-side API usage',
                'Ensure proper event handling'
            ])
        elif 'rest api' in context_lower:
            advice.extend([
                'Validate request/response formats',
                'Check authentication configuration',
                'Verify HTTP method handling'
            ])
    
    elif error_type == 'performance_issue':
        if 'query' in context_lower:
            advice.extend([
                'Add appropriate indexes to queried fields',
                'Use setLimit() to restrict result sets',
                'Consider using GlideAggregate for counts'
            ])
        elif 'form' in context_lower:
            advice.extend([
                'Minimize client script complexity',
                'Reduce number of server calls',
                'Optimize UI policies and business rules'
            ])
    
    return advice

def get_version_specific_info(feature: str, version: str = "latest") -> Dict[str, Any]:
    """Get version-specific information about ServiceNow features"""
    
    version_info = {
        'scoped_applications': {
            'introduced': 'Helsinki',
            'latest_changes': {
                'Vancouver': ['Enhanced application cross-scope access'],
                'Washington': ['Improved application store integration'],
                'Xanadu': ['Advanced application analytics']
            },
            'best_practices': [
                'Always develop in scoped applications',
                'Use proper naming conventions',
                'Manage dependencies carefully',
                'Test across different scopes'
            ]
        },
        'rest_api': {
            'introduced': 'Eureka',
            'latest_changes': {
                'Vancouver': ['Enhanced authentication options'],
                'Washington': ['Improved rate limiting'],
                'Xanadu': ['Better error handling and logging']
            },
            'best_practices': [
                'Use proper HTTP status codes',
                'Implement authentication',
                'Add comprehensive error handling',
                'Document APIs thoroughly'
            ]
        },
        'ui_builder': {
            'introduced': 'Quebec',
            'latest_changes': {
                'Vancouver': ['New component library'],
                'Washington': ['Enhanced data binding'],
                'Xanadu': ['Improved performance and accessibility']
            },
            'best_practices': [
                'Use declarative components when possible',
                'Implement proper data binding',
                'Follow accessibility guidelines',
                'Test across different devices'
            ]
        }
    }
    
    if feature not in version_info:
        return {
            'error': f'No version information found for: {feature}',
            'available_features': list(version_info.keys())
        }
    
    info = version_info[feature]
    
    return {
        'feature': feature,
        'version_requested': version,
        'introduced_in': info['introduced'],
        'recent_changes': info['latest_changes'],
        'best_practices': info['best_practices'],
        'current_status': 'Active' if version == 'latest' else 'Check release notes'
    }

def search_community_solutions(problem: str, category: Optional[str] = None) -> Dict[str, Any]:
    """Search for community solutions and discussions"""
    
    # Simulated community solutions database
    community_solutions = [
        {
            'title': 'How to optimize GlideRecord queries for better performance',
            'category': 'performance',
            'tags': ['gliderecord', 'performance', 'optimization'],
            'solution': 'Use indexed fields, setLimit(), and avoid nested queries',
            'votes': 45,
            'author': 'ServiceNow Expert',
            'url': 'https://community.servicenow.com/example1'
        },
        {
            'title': 'Best practices for scoped application development',
            'category': 'development',
            'tags': ['scoped_apps', 'best_practices', 'development'],
            'solution': 'Follow naming conventions, manage dependencies, use proper scope isolation',
            'votes': 38,
            'author': 'Senior Developer',
            'url': 'https://community.servicenow.com/example2'
        },
        {
            'title': 'Troubleshooting REST API authentication issues',
            'category': 'integration',
            'tags': ['rest_api', 'authentication', 'troubleshooting'],
            'solution': 'Check credentials, verify ACLs, test with Postman',
            'votes': 32,
            'author': 'Integration Specialist',
            'url': 'https://community.servicenow.com/example3'
        }
    ]
    
    # Filter by category if specified
    if category:
        community_solutions = [s for s in community_solutions if s['category'] == category]
    
    # Search for relevant solutions
    problem_lower = problem.lower()
    relevant_solutions = []
    
    for solution in community_solutions:
        relevance = 0
        
        # Check title match
        if any(word in solution['title'].lower() for word in problem_lower.split()):
            relevance += 10
        
        # Check tag match
        if any(word in ' '.join(solution['tags']).lower() for word in problem_lower.split()):
            relevance += 5
        
        # Check solution content match
        if any(word in solution['solution'].lower() for word in problem_lower.split()):
            relevance += 3
        
        if relevance > 0:
            solution['relevance_score'] = relevance
            relevant_solutions.append(solution)
    
    # Sort by relevance and votes
    relevant_solutions.sort(key=lambda x: (x['relevance_score'], x['votes']), reverse=True)
    
    return {
        'query': problem,
        'category': category,
        'results_count': len(relevant_solutions),
        'solutions': relevant_solutions[:5]  # Top 5 results
    }

def generate_learning_path(topic: str, skill_level: str = 'beginner') -> Dict[str, Any]:
    """Generate a learning path for ServiceNow topics"""
    
    learning_paths = {
        'scripting': {
            'beginner': [
                'JavaScript fundamentals',
                'ServiceNow platform basics',
                'GlideRecord API introduction',
                'Client scripts basics',
                'Business rules fundamentals',
                'Basic debugging techniques'
            ],
            'intermediate': [
                'Advanced GlideRecord operations',
                'GlideForm API mastery',
                'UI policies and actions',
                'Script includes development',
                'Error handling and logging',
                'Performance optimization'
            ],
            'advanced': [
                'Advanced scripting patterns',
                'Custom API development',
                'Integration scripting',
                'Performance tuning',
                'Security best practices',
                'Code review and testing'
            ]
        },
        'rest_api': {
            'beginner': [
                'REST API concepts',
                'ServiceNow REST API basics',
                'Authentication methods',
                'Basic CRUD operations',
                'Testing with Postman',
                'Error handling basics'
            ],
            'intermediate': [
                'Scripted REST APIs',
                'Advanced authentication',
                'Request/response validation',
                'API documentation',
                'Rate limiting and throttling',
                'Integration patterns'
            ],
            'advanced': [
                'Custom authentication methods',
                'Advanced error handling',
                'API versioning strategies',
                'Performance optimization',
                'Security hardening',
                'Monitoring and analytics'
            ]
        },
        'scoped_apps': {
            'beginner': [
                'Scoped application concepts',
                'Creating your first scoped app',
                'Naming conventions',
                'Basic application structure',
                'Application scope isolation',
                'Publishing to app store'
            ],
            'intermediate': [
                'Advanced application architecture',
                'Dependency management',
                'Cross-scope communication',
                'Application lifecycle management',
                'Version control integration',
                'Testing strategies'
            ],
            'advanced': [
                'Enterprise application patterns',
                'Advanced dependency management',
                'Application performance optimization',
                'Security considerations',
                'Deployment automation',
                'Monitoring and maintenance'
            ]
        }
    }
    
    if topic not in learning_paths:
        return {
            'error': f'No learning path found for: {topic}',
            'available_topics': list(learning_paths.keys())
        }
    
    if skill_level not in learning_paths[topic]:
        return {
            'error': f'Invalid skill level: {skill_level}',
            'available_levels': list(learning_paths[topic].keys())
        }
    
    path = learning_paths[topic][skill_level]
    
    return {
        'topic': topic,
        'skill_level': skill_level,
        'learning_path': path,
        'estimated_duration': f"{len(path) * 2} weeks",
        'next_level': get_next_skill_level(skill_level),
        'resources': [
            'ServiceNow official documentation',
            'ServiceNow Community',
            'Developer blog posts',
            'Hands-on practice exercises'
        ]
    }

def get_next_skill_level(current_level: str) -> Optional[str]:
    """Get the next skill level in progression"""
    levels = ['beginner', 'intermediate', 'advanced']
    try:
        current_index = levels.index(current_level)
        return levels[current_index + 1] if current_index < len(levels) - 1 else None
    except ValueError:
        return None