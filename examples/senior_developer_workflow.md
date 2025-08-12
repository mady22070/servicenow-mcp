# Senior Developer Workflow Examples

This document demonstrates how to use the enhanced ServiceNow MCP server as a Senior Developer for story-driven development and advanced troubleshooting.

## Story-Driven Development

### Example 1: Complete Story-to-Implementation Pipeline

```python
# Input user story
story = "As a service desk agent, I want to automatically categorize incidents based on their description so that I can route them to the correct team faster"

# Use the complete pipeline
result = story_to_implementation(story=story, env="dev")

# The result includes:
# - Parsed story components (user, goal, benefit)
# - Validation of story completeness
# - Technical requirements extraction
# - Executable implementation plan
```

### Example 2: Step-by-Step Story Analysis

```python
# Step 1: Parse the story
parsed = parse_user_story(story="As a service desk agent, I want to automatically categorize incidents...")

# Step 2: Validate completeness
validation = validate_story_completeness(story_analysis=parsed)

# Step 3: Extract technical requirements
requirements = extract_technical_requirements(story_components=parsed["components"])

# Step 4: Generate implementation tasks
tasks = generate_implementation_tasks(requirements=requirements, story_context=parsed)

# Step 5: Create executable plan
plan = create_executable_plan(tasks=tasks["tasks"], story_context=parsed)
```

## Advanced CMDB Troubleshooting

### Example 1: Investigate Duplicate Configuration Items

```python
# Analyze duplicates in server CIs
duplicates = troubleshoot_cmdb_duplicates(
    ci_class="cmdb_ci_server",
    analysis_fields=["name", "serial_number", "ip_address"],
    limit=500,
    env="prod"
)

# Results include:
# - Duplicate groups with confidence scores
# - Creation pattern analysis
# - Recommendations for prevention
```

### Example 2: Advanced Duplicate Pattern Detection

```python
# Deep duplicate analysis with pattern recognition
patterns = detect_duplicate_patterns(
    ci_class="cmdb_ci_computer",
    detection_fields=["serial_number", "asset_tag", "mac_address"],
    limit=1000,
    env="prod"
)

# Provides:
# - Normalized field matching
# - Bulk import detection
# - Creator pattern analysis
# - Confidence scoring
```

### Example 3: CI Lifecycle Investigation

```python
# Comprehensive CI lifecycle analysis
lifecycle = analyze_ci_lifecycle(
    ci_sys_id="abc123def456",
    include_relationships=True,
    env="prod"
)

# Returns:
# - Complete audit history
# - Status change timeline
# - Relationship changes
# - Data quality issues
```

## Root Cause Analysis

### Example 1: System Issue Investigation

```python
# Investigate a reported issue
analysis = root_cause_analysis(
    issue_description="Users reporting slow form loading on incident table",
    related_table="incident",
    time_range_hours=48,
    env="prod"
)

# Provides:
# - System log analysis
# - Recent change correlation
# - Potential cause identification
# - Remediation recommendations
```

### Example 2: Data Quality Investigation

```python
# Comprehensive data quality check
quality = investigate_data_quality(
    table="cmdb_ci_server",
    quality_checks=["completeness", "consistency", "validity", "duplicates"],
    sample_size=2000,
    env="prod"
)

# Results include:
# - Field completeness analysis
# - Data consistency patterns
# - Format validation
# - Anomaly detection
```

## CI Relationship Analysis

### Example 1: Deep Relationship Investigation

```python
# Investigate CI dependencies and relationships
relationships = investigate_ci_relationships(
    ci_sys_id="server123",
    max_depth=3,
    relationship_types=["Depends on::Used by", "Runs on::Runs"],
    env="prod"
)

# Provides:
# - Complete relationship map
# - Dependency analysis
# - Circular dependency detection
# - Orphaned relationship identification
```

## Practical Workflow Examples

### Scenario 1: New Feature Development

```python
# 1. Analyze the user story
story = "As a change manager, I want to see the impact of a change on related CIs so that I can assess risk"
analysis = analyze_user_story(story=story, env="dev")

# 2. Generate development plan
dev_plan = generate_development_plan(story_analysis=analysis, environment="dev")

# 3. Execute the plan (with confirmation)
execution = execute_plan(plan=dev_plan["execution_steps"], confirm=True, env="dev")
```

### Scenario 2: CMDB Cleanup Project

```python
# 1. Identify duplicate patterns across CI classes
server_dups = detect_duplicate_patterns(ci_class="cmdb_ci_server", env="prod")
network_dups = detect_duplicate_patterns(ci_class="cmdb_ci_network_gear", env="prod")

# 2. Investigate specific problematic CIs
for dup_group in server_dups["duplicate_groups"]:
    if dup_group["confidence"] > 0.8:
        for ci in dup_group["cis"]:
            lifecycle = analyze_ci_lifecycle(ci_sys_id=ci["sys_id"], env="prod")
            # Analyze and plan cleanup

# 3. Generate cleanup recommendations
# Based on analysis results, create cleanup plans
```

### Scenario 3: Performance Issue Investigation

```python
# 1. Start with root cause analysis
issue = "Form performance degraded after recent deployment"
rca = root_cause_analysis(
    issue_description=issue,
    related_table="incident",
    time_range_hours=72,
    env="prod"
)

# 2. Investigate data quality if needed
if "data" in issue.lower():
    quality = investigate_data_quality(
        table="incident",
        quality_checks=["completeness", "consistency"],
        sample_size=5000,
        env="prod"
    )

# 3. Check for relationship issues if CMDB-related
if "cmdb" in issue.lower() or "ci" in issue.lower():
    # Investigate key CIs for relationship problems
    pass
```

## Best Practices

1. **Always start with story validation** before implementation
2. **Use dry_run=True** for development and testing
3. **Analyze patterns** before making bulk changes
4. **Investigate relationships** when dealing with CMDB issues
5. **Document findings** and recommendations for future reference
6. **Use confidence scores** to prioritize duplicate cleanup efforts
7. **Correlate timing** of issues with recent changes or deployments

## Integration with Existing Tools

The senior developer capabilities integrate seamlessly with existing MCP tools:

- Use `query_table` for initial data gathering
- Use `stats` for quantitative analysis
- Use `execute_plan` for implementing solutions
- Use `create_update_set` for change management
- Use `atf_create_suite` for testing implementations