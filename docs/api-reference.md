# API Reference

Complete reference for all ServiceNow MCP tools and functions.

## Core Management

### client_health_check
Check health status of ServiceNow client connections.

**Parameters:**
- `env` (optional): Environment to check (dev/test/prod). If None, checks all active environments.

**Returns:**
```json
{
  "dev": {
    "status": "healthy",
    "response_time": "0.234s",
    "last_checked": "2024-01-15T10:30:00Z"
  }
}
```

### clear_client_cache
Clear cached client for environment (useful for credential rotation).

**Parameters:**
- `env` (required): Environment name to clear

**Returns:**
```json
{
  "cleared": true,
  "environment": "dev"
}
```

## Incident Management

### create_incident
Create a new incident record.

**Parameters:**
- `short_description` (required): Brief description of the incident
- `description` (optional): Detailed description
- `additional_fields` (optional): Dictionary of additional fields
- `env` (optional): Environment (default: "dev")

**Example:**
```python
create_incident(
    short_description="Server outage in production",
    description="Web servers are not responding to requests",
    additional_fields={
        "urgency": "1",
        "impact": "1",
        "category": "Hardware"
    }
)
```

### get_incident
Retrieve an incident record by sys_id.

**Parameters:**
- `sys_id` (required): System ID of the incident
- `env` (optional): Environment (default: "dev")

## Story-Driven Development

### story_to_implementation
Complete story-to-implementation pipeline that parses a user story, analyzes requirements, and generates an executable plan.

**Parameters:**
- `story` (required): User story in format "As a [user], I want [goal] so that [benefit]"
- `env` (optional): Environment (default: "dev")

**Returns:**
```json
{
  "status": "success",
  "parsed_story": {
    "components": {
      "user": "service desk agent",
      "goal": "automatically assign incidents based on category",
      "benefit": "tickets are routed to the right team faster"
    }
  },
  "validation": {
    "is_complete": true,
    "score": 0.95
  },
  "requirements": {
    "technical_requirements": [...],
    "functional_requirements": [...]
  },
  "executable_plan": {
    "phases": [...],
    "estimated_effort": "4-6 hours"
  }
}
```

### parse_user_story
Parse user story using standard format.

**Parameters:**
- `story` (required): User story text

### extract_technical_requirements
Extract technical requirements from story components.

**Parameters:**
- `story_components` (required): Parsed story components
- `env` (optional): Environment (default: "dev")

### generate_implementation_tasks
Generate specific implementation tasks from requirements.

**Parameters:**
- `requirements` (required): Technical requirements
- `story_context` (required): Story context
- `env` (optional): Environment (default: "dev")

### create_executable_plan
Create an executable plan with specific ServiceNow operations.

**Parameters:**
- `tasks` (required): List of implementation tasks
- `story_context` (required): Story context
- `env` (optional): Environment (default: "dev")

### validate_story_completeness
Validate that a user story has sufficient detail for implementation.

**Parameters:**
- `story_analysis` (required): Analyzed story data

## Senior Developer Capabilities

### analyze_user_story
Analyze a user story and break it down into actionable development tasks.

**Parameters:**
- `story` (required): User story text
- `context` (optional): Additional context dictionary
- `env` (optional): Environment (default: "dev")

### troubleshoot_cmdb_duplicates
Advanced CMDB duplicate analysis and troubleshooting.

**Parameters:**
- `ci_class` (optional): CI class to analyze (default: "cmdb_ci")
- `analysis_fields` (optional): Fields to analyze for duplicates
- `limit` (optional): Maximum records to analyze (default: 100)
- `env` (optional): Environment (default: "dev")

**Returns:**
```json
{
  "duplicates_found": 15,
  "confidence_scores": {
    "high": 8,
    "medium": 5,
    "low": 2
  },
  "patterns": {
    "bulk_imports": 3,
    "rapid_creation": 2
  },
  "recommendations": [...]
}
```

### investigate_data_quality
Comprehensive data quality investigation.

**Parameters:**
- `table` (required): Table to investigate
- `quality_checks` (optional): List of quality checks to perform
- `sample_size` (optional): Sample size for analysis (default: 1000)
- `env` (optional): Environment (default: "dev")

### generate_development_plan
Generate a comprehensive development plan from story analysis.

**Parameters:**
- `story_analysis` (required): Analyzed story data
- `environment` (optional): Target environment (default: "dev")
- `env` (optional): ServiceNow environment (default: "dev")

### root_cause_analysis
Perform root cause analysis for ServiceNow issues.

**Parameters:**
- `issue_description` (required): Description of the issue
- `related_table` (optional): Table related to the issue
- `time_range_hours` (optional): Time range for analysis (default: 24)
- `env` (optional): Environment (default: "dev")

## Query Operations

### query_table
Query records from a ServiceNow table.

**Parameters:**
- `table` (required): Table name
- `query` (optional): Encoded query string
- `fields` (optional): List of fields to return
- `limit` (optional): Maximum records to return (default: 100)
- `display` (optional): Return display values (default: false)
- `env` (optional): Environment (default: "dev")

**Example:**
```python
query_table(
    table="incident",
    query="state=1^urgency=1",
    fields=["number", "short_description", "state", "assigned_to"],
    limit=50
)
```

### stats
Generate statistics for table data.

**Parameters:**
- `table` (required): Table name
- `query` (optional): Filter query
- `group_by` (optional): Fields to group by
- `count` (optional): Include count (default: true)
- `sum` (optional): Fields to sum
- `avg` (optional): Fields to average
- `minv` (optional): Fields to find minimum
- `maxv` (optional): Fields to find maximum
- `env` (optional): Environment (default: "dev")

### ci_graph
Generate configuration item relationship graph.

**Parameters:**
- `root_sys_id` (required): Root CI system ID
- `direction` (optional): Relationship direction ("both", "upstream", "downstream")
- `depth` (optional): Relationship depth (default: 2)
- `limit` (optional): Maximum CIs to return (default: 200)
- `env` (optional): Environment (default: "dev")

## Development Tools

### create_script_include
Create a new script include.

**Parameters:**
- `name` (required): Script include name
- `script` (required): JavaScript code
- `api_name` (optional): API name for the script
- `active` (optional): Whether script is active (default: true)
- `scope` (optional): Application scope (default: "x_cloudorch_aiops")
- `table` (optional): Target table (default: "sys_script_include")
- `dry_run` (optional): Test mode without creating (default: false)
- `env` (optional): Environment (default: "dev")

### create_business_rule
Create a new business rule.

**Parameters:**
- `table_name` (required): Table the rule applies to
- `name` (required): Business rule name
- `when` (required): When to execute ("before", "after", "async", "display")
- `actions` (required): Actions dictionary (insert, update, delete, query)
- `condition` (optional): Condition script
- `script` (optional): Rule script
- `active` (optional): Whether rule is active (default: true)
- `table` (optional): Target table (default: "sys_script")
- `dry_run` (optional): Test mode (default: false)
- `env` (optional): Environment (default: "dev")

### create_ui_policy
Create a new UI policy.

**Parameters:**
- `table_name` (required): Table the policy applies to
- `short_description` (required): Policy description
- `active` (optional): Whether policy is active (default: true)
- `condition` (optional): Condition script
- `actions` (optional): List of policy actions
- `policy_table` (optional): Policy table (default: "ui_policy")
- `action_table` (optional): Action table (default: "ui_policy_action")
- `dry_run` (optional): Test mode (default: false)
- `env` (optional): Environment (default: "dev")

## Table Operations

### update_record
Update an existing record.

**Parameters:**
- `table` (required): Table name
- `sys_id` (required): Record system ID
- `fields` (required): Fields to update
- `dry_run` (optional): Test mode (default: false)
- `env` (optional): Environment (default: "dev")

### delete_record
Delete a record.

**Parameters:**
- `table` (required): Table name
- `sys_id` (required): Record system ID
- `dry_run` (optional): Test mode (default: false)
- `env` (optional): Environment (default: "dev")

### get_record
Retrieve a single record.

**Parameters:**
- `table` (required): Table name
- `sys_id` (required): Record system ID
- `fields` (optional): Fields to return
- `env` (optional): Environment (default: "dev")

### batch_insert_records
Insert multiple records in batch.

**Parameters:**
- `table` (required): Table name
- `records` (required): List of record dictionaries
- `dry_run` (optional): Test mode (default: false)
- `env` (optional): Environment (default: "dev")

### batch_update_records
Update multiple records in batch.

**Parameters:**
- `table` (required): Table name
- `updates` (required): List of update dictionaries
- `id_field` (optional): ID field name (default: "sys_id")
- `dry_run` (optional): Test mode (default: false)
- `env` (optional): Environment (default: "dev")

## ITSM Operations

### create_change_request
Create a new change request.

**Parameters:**
- `fields` (required): Change request fields
- `table` (optional): Target table (default: "change_request")
- `dry_run` (optional): Test mode (default: false)
- `env` (optional): Environment (default: "dev")

### create_problem
Create a new problem record.

**Parameters:**
- `fields` (required): Problem fields
- `table` (optional): Target table (default: "problem")
- `dry_run` (optional): Test mode (default: false)
- `env` (optional): Environment (default: "dev")

### create_request
Create a new service request.

**Parameters:**
- `fields` (required): Request fields
- `table` (optional): Target table (default: "sc_request")
- `dry_run` (optional): Test mode (default: false)
- `env` (optional): Environment (default: "dev")

## User Management

### create_user
Create a new user account.

**Parameters:**
- `fields` (required): User fields
- `table` (optional): Target table (default: "sys_user")
- `dry_run` (optional): Test mode (default: false)
- `env` (optional): Environment (default: "dev")

### get_user_by_email
Find user by email address.

**Parameters:**
- `email` (required): User email address
- `table` (optional): Target table (default: "sys_user")
- `env` (optional): Environment (default: "dev")

### create_group
Create a new user group.

**Parameters:**
- `fields` (required): Group fields
- `table` (optional): Target table (default: "sys_user_group")
- `dry_run` (optional): Test mode (default: false)
- `env` (optional): Environment (default: "dev")

### add_user_to_group
Add user to a group.

**Parameters:**
- `user_sys_id` (required): User system ID
- `group_sys_id` (required): Group system ID
- `table` (optional): Target table (default: "sys_user_grmember")
- `dry_run` (optional): Test mode (default: false)
- `env` (optional): Environment (default: "dev")

## Workspace Management

### ws_list
List available workspaces.

**Returns:**
```json
{
  "workspaces": ["default", "development", "testing"]
}
```

### ws_get
Get workspace configuration.

**Parameters:**
- `name` (optional): Workspace name (default: "default")

### ws_set
Set workspace configuration.

**Parameters:**
- `name` (optional): Workspace name (default: "default")
- `env` (optional): Environment setting
- `scope` (optional): Application scope
- `confirm` (optional): Confirmation setting (default: false)

## Plan Execution

### execute_plan
Execute a multi-step plan.

**Parameters:**
- `plan` (required): List of plan steps
- `confirm` (optional): Require confirmation (default: false)
- `continue_on_error` (optional): Continue if step fails (default: false)
- `env` (optional): Environment (default: "dev")

**Plan Step Format:**
```json
{
  "action": "create_incident",
  "params": {
    "short_description": "Test incident",
    "urgency": "3"
  }
}
```

## Error Handling

All tools return consistent error formats:

```json
{
  "error": "error_type",
  "message": "Human readable error message",
  "details": {
    "additional": "context"
  },
  "_meta": {
    "execution_time_ms": 150,
    "function": "function_name",
    "error": true
  }
}
```

Common error types:
- `invalid_environment`: Invalid environment specified
- `guard_block`: Table access blocked by security guard
- `missing_required_parameters`: Required parameters not provided
- `execution_error`: General execution error
- `authentication_error`: ServiceNow authentication failed
- `permission_error`: Insufficient permissions
- `not_found`: Record or resource not found
- `validation_error`: Data validation failed

## Response Metadata

Successful responses include metadata:

```json
{
  "result": {...},
  "_meta": {
    "execution_time_ms": 234,
    "function": "query_table",
    "cached": false,
    "environment": "dev"
  }
}
```