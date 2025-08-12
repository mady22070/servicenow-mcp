# Configuration Guide

This guide covers how to configure the ServiceNow MCP server for different environments and use cases.

## Environment Variables

### Required Configuration

#### Development Environment
```bash
export SERVICENOW_DEV_INSTANCE_URL=https://devXXX.service-now.com
export SERVICENOW_DEV_USERNAME=your_username
export SERVICENOW_DEV_PASSWORD=your_password
```

#### Test Environment
```bash
export SERVICENOW_TEST_INSTANCE_URL=https://testXXX.service-now.com
export SERVICENOW_TEST_USERNAME=test_username
export SERVICENOW_TEST_PASSWORD=test_password
```

#### Production Environment
```bash
export SERVICENOW_PROD_INSTANCE_URL=https://yourinstance.service-now.com
export SERVICENOW_PROD_USERNAME=prod_username
export SERVICENOW_PROD_PASSWORD=prod_password
```

### Optional Configuration

#### Table Access Control
Restrict which tables the MCP server can access:
```bash
export MCP_ALLOW_TABLES=sys_script,sys_script_include,ui_policy,ui_policy_action
```

#### Logging Configuration
```bash
export MCP_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
export MCP_LOG_FILE=/path/to/logfile.log
```

#### Performance Tuning
```bash
export MCP_CONNECTION_TIMEOUT=30  # seconds
export MCP_REQUEST_TIMEOUT=60     # seconds
export MCP_MAX_RETRIES=3
export MCP_CACHE_TTL=300         # seconds
```

## MCP Client Configuration

### Claude Desktop
Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "servicenow": {
      "command": "python",
      "args": ["/path/to/servicenow-mcp/mcp_adapter.py"],
      "env": {
        "SERVICENOW_DEV_INSTANCE_URL": "https://devXXX.service-now.com",
        "SERVICENOW_DEV_USERNAME": "your_username",
        "SERVICENOW_DEV_PASSWORD": "your_password"
      }
    }
  }
}
```

### Using uvx (Recommended)
```json
{
  "mcpServers": {
    "servicenow": {
      "command": "uvx",
      "args": ["servicenow-mcp"],
      "env": {
        "SERVICENOW_DEV_INSTANCE_URL": "https://devXXX.service-now.com",
        "SERVICENOW_DEV_USERNAME": "your_username",
        "SERVICENOW_DEV_PASSWORD": "your_password"
      }
    }
  }
}
```

## ServiceNow User Permissions

### Minimum Required Roles
- `rest_service` - For REST API access
- `web_service_admin` - For advanced API operations

### Recommended Roles for Full Functionality
- `admin` - Full system access (development environments)
- `itil` - ITSM operations
- `cmdb_admin` - CMDB management
- `script_admin` - Script development
- `flow_designer` - Workflow automation

### Custom Role Configuration
For production environments, create a custom role with specific permissions:

```javascript
// ServiceNow Script - Create custom MCP role
var role = new GlideRecord('sys_user_role');
role.initialize();
role.name = 'mcp_integration';
role.description = 'ServiceNow MCP Integration Role';
role.insert();

// Add specific table permissions as needed
var acl = new GlideRecord('sys_security_acl');
acl.initialize();
acl.name = 'mcp_integration.incident';
acl.type = 'record';
acl.operation = 'read,write,create,delete';
acl.active = true;
acl.insert();
```

## Security Configuration

### Table Guards
Configure table access restrictions in your environment:

```python
# In your environment configuration
MCP_GUARD_CONFIG = {
    "allowed_tables": [
        "incident",
        "problem", 
        "change_request",
        "sys_script",
        "sys_script_include"
    ],
    "blocked_tables": [
        "sys_user",
        "sys_user_password",
        "oauth_entity"
    ],
    "read_only_tables": [
        "sys_audit",
        "sys_journal_field"
    ]
}
```

### Network Security
- Use HTTPS for all ServiceNow connections
- Configure firewall rules for MCP server access
- Use VPN or private networks for production access
- Implement IP whitelisting where possible

### Credential Management
- Use environment variables, never hardcode credentials
- Rotate passwords regularly
- Use ServiceNow OAuth for enhanced security
- Consider using secret management systems (AWS Secrets Manager, Azure Key Vault, etc.)

## Advanced Configuration

### Multi-Instance Setup
Configure multiple ServiceNow instances:

```bash
# Development
export SERVICENOW_DEV_INSTANCE_URL=https://dev123.service-now.com
export SERVICENOW_DEV_USERNAME=dev_user
export SERVICENOW_DEV_PASSWORD=dev_pass

# Test
export SERVICENOW_TEST_INSTANCE_URL=https://test123.service-now.com
export SERVICENOW_TEST_USERNAME=test_user
export SERVICENOW_TEST_PASSWORD=test_pass

# Production
export SERVICENOW_PROD_INSTANCE_URL=https://prod123.service-now.com
export SERVICENOW_PROD_USERNAME=prod_user
export SERVICENOW_PROD_PASSWORD=prod_pass
```

### Custom Configuration File
Create a configuration file for complex setups:

```python
# config.local.py
ENVIRONMENTS = {
    'dev': {
        'instance_url': 'https://dev123.service-now.com',
        'username': 'dev_user',
        'password': 'dev_pass',
        'timeout': 30,
        'max_retries': 3
    },
    'prod': {
        'instance_url': 'https://prod123.service-now.com',
        'username': 'prod_user',
        'password': 'prod_pass',
        'timeout': 60,
        'max_retries': 5
    }
}

GUARD_CONFIG = {
    'dev': {
        'allowed_tables': ['*'],  # Allow all in dev
        'blocked_tables': []
    },
    'prod': {
        'allowed_tables': ['incident', 'problem', 'change_request'],
        'blocked_tables': ['sys_user', 'sys_user_password']
    }
}
```

## Troubleshooting Configuration

### Connection Issues
```bash
# Test connection
python -c "from servicenow_mcp.client_manager import client_manager; print(client_manager.health_check())"

# Verify environment variables
env | grep SERVICENOW

# Test with doctor script
python doctor.py
```

### Permission Issues
```bash
# Check user roles in ServiceNow
# Navigate to: User Administration > Users
# Select your user and check "Roles" tab

# Test specific table access
python -c "
from servicenow_mcp.client_manager import client_manager
client = client_manager.get_client('dev')
result = client.query_table('incident', limit=1)
print(result)
"
```

### Performance Issues
```bash
# Enable debug logging
export MCP_LOG_LEVEL=DEBUG

# Monitor connection pool
python -c "
from servicenow_mcp.client_manager import client_manager
print(client_manager.get_active_environments())
print(client_manager.health_check())
"
```

## Environment-Specific Best Practices

### Development Environment
- Use broad permissions for experimentation
- Enable debug logging
- Use shorter cache TTL for rapid iteration
- Allow all tables for testing

### Test Environment
- Mirror production permissions
- Use realistic data volumes
- Test with production-like network conditions
- Validate security configurations

### Production Environment
- Use minimal required permissions
- Implement comprehensive logging
- Use longer cache TTL for performance
- Restrict table access strictly
- Monitor performance metrics
- Implement alerting for failures

## Configuration Validation

### Startup Checks
The MCP server performs these validation checks on startup:

1. **Environment Variables**: Verifies required variables are set
2. **ServiceNow Connectivity**: Tests connection to each configured instance
3. **User Permissions**: Validates minimum required roles
4. **Table Access**: Checks guard configurations
5. **MCP Protocol**: Verifies MCP server functionality

### Health Monitoring
Regular health checks include:

- ServiceNow instance availability
- Authentication status
- Response time monitoring
- Error rate tracking
- Resource utilization

Use the built-in health check tools:
```bash
# Basic health check
python doctor.py

# Detailed health monitoring
python -c "
from servicenow_mcp.client_manager import client_manager
import json
print(json.dumps(client_manager.health_check(), indent=2))
"
```