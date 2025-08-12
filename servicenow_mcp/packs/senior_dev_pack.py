"""
Senior Developer Pack - Advanced development and troubleshooting capabilities
"""

from typing import Dict, Any, List, Optional
from ..servicenow_client import ServiceNowClient
import json
import re
from datetime import datetime, timedelta

def analyze_story(client: ServiceNowClient, story: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Analyze a user story and break it down into actionable development tasks
    """
    # Extract key components from story
    story_analysis = {
        "story": story,
        "analysis": {},
        "tasks": [],
        "recommendations": [],
        "risks": []
    }
    
    # Basic story parsing
    if "as a" in story.lower() and "i want" in story.lower():
        story_analysis["analysis"]["format"] = "user_story"
        story_analysis["analysis"]["valid"] = True
    else:
        story_analysis["analysis"]["format"] = "requirement"
        story_analysis["analysis"]["valid"] = False
        story_analysis["recommendations"].append("Consider reformatting as: 'As a [user], I want [goal] so that [benefit]'")
    
    # Identify ServiceNow components mentioned
    components = []
    if any(word in story.lower() for word in ["table", "form", "field"]):
        components.append("data_model")
    if any(word in story.lower() for word in ["workflow", "flow", "approval"]):
        components.append("workflow")
    if any(word in story.lower() for word in ["script", "business rule", "client script"]):
        components.append("scripting")
    if any(word in story.lower() for word in ["ui", "interface", "page", "portal"]):
        components.append("ui")
    if any(word in story.lower() for word in ["integration", "api", "rest", "soap"]):
        components.append("integration")
    
    story_analysis["analysis"]["components"] = components
    
    # Generate development tasks based on components
    for component in components:
        if component == "data_model":
            story_analysis["tasks"].append({
                "type": "analysis",
                "description": "Analyze existing table structure and identify required changes",
                "pack": "query",
                "estimated_effort": "low"
            })
            story_analysis["tasks"].append({
                "type": "development",
                "description": "Create or modify table schema",
                "pack": "build",
                "estimated_effort": "medium"
            })
        elif component == "workflow":
            story_analysis["tasks"].append({
                "type": "development", 
                "description": "Design and implement workflow logic",
                "pack": "flow",
                "estimated_effort": "high"
            })
        elif component == "scripting":
            story_analysis["tasks"].append({
                "type": "development",
                "description": "Implement business logic scripts",
                "pack": "scripts",
                "estimated_effort": "medium"
            })
    
    return story_analysis

def troubleshoot_cmdb_duplicates(client: ServiceNowClient, ci_class: str = "cmdb_ci", 
                                analysis_fields: Optional[List[str]] = None, 
                                limit: int = 100) -> Dict[str, Any]:
    """
    Advanced CMDB duplicate analysis and troubleshooting
    """
    if not analysis_fields:
        analysis_fields = ["name", "serial_number", "ip_address", "mac_address", "asset_tag"]
    
    # Query potential duplicates
    duplicates_analysis = {
        "ci_class": ci_class,
        "analysis_fields": analysis_fields,
        "duplicates": [],
        "patterns": {},
        "recommendations": []
    }
    
    # Get all CIs of the specified class
    cis = client.query_table(ci_class, fields=["sys_id", "name", "sys_created_on", "sys_created_by"] + analysis_fields, limit=limit)
    
    # Group by potential duplicate fields
    field_groups = {}
    for field in analysis_fields:
        field_groups[field] = {}
        for ci in cis:
            value = ci.get(field, "").strip().lower()
            if value and value != "":
                if value not in field_groups[field]:
                    field_groups[field][value] = []
                field_groups[field][value].append(ci)
    
    # Identify duplicates
    for field, groups in field_groups.items():
        for value, ci_list in groups.items():
            if len(ci_list) > 1:
                duplicate_group = {
                    "field": field,
                    "value": value,
                    "count": len(ci_list),
                    "cis": ci_list,
                    "creation_pattern": analyze_creation_pattern(ci_list)
                }
                duplicates_analysis["duplicates"].append(duplicate_group)
    
    # Analyze patterns
    creation_sources = {}
    for dup in duplicates_analysis["duplicates"]:
        for ci in dup["cis"]:
            source = ci.get("sys_created_by", "unknown")
            if source not in creation_sources:
                creation_sources[source] = 0
            creation_sources[source] += 1
    
    duplicates_analysis["patterns"]["creation_sources"] = creation_sources
    
    # Generate recommendations
    if creation_sources:
        top_source = max(creation_sources.items(), key=lambda x: x[1])
        duplicates_analysis["recommendations"].append(f"Primary duplicate source: {top_source[0]} ({top_source[1]} duplicates)")
    
    if duplicates_analysis["duplicates"]:
        duplicates_analysis["recommendations"].append("Consider implementing duplicate prevention rules")
        duplicates_analysis["recommendations"].append("Review discovery and import processes")
    
    return duplicates_analysis

def analyze_creation_pattern(ci_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the creation pattern of duplicate CIs"""
    if not ci_list:
        return {}
    
    # Sort by creation date
    sorted_cis = sorted(ci_list, key=lambda x: x.get("sys_created_on", ""))
    
    pattern = {
        "first_created": sorted_cis[0].get("sys_created_on"),
        "last_created": sorted_cis[-1].get("sys_created_on"),
        "creators": list(set(ci.get("sys_created_by", "") for ci in ci_list)),
        "time_span_analysis": "rapid" if len(ci_list) > 2 else "normal"
    }
    
    return pattern

def investigate_data_quality(client: ServiceNowClient, table: str, 
                           quality_checks: Optional[List[str]] = None,
                           sample_size: int = 1000) -> Dict[str, Any]:
    """
    Comprehensive data quality investigation
    """
    if not quality_checks:
        quality_checks = ["completeness", "consistency", "validity", "duplicates"]
    
    investigation = {
        "table": table,
        "sample_size": sample_size,
        "checks_performed": quality_checks,
        "results": {},
        "issues": [],
        "recommendations": []
    }
    
    # Get sample data
    records = client.query_table(table, limit=sample_size)
    if not records:
        return {"error": "No records found in table"}
    
    # Get table schema
    try:
        schema = client.query_table("sys_dictionary", 
                                  query=f"name={table}", 
                                  fields=["element", "column_label", "mandatory", "max_length"])
        field_info = {s["element"]: s for s in schema}
    except:
        field_info = {}
    
    # Completeness check
    if "completeness" in quality_checks:
        completeness = analyze_completeness(records, field_info)
        investigation["results"]["completeness"] = completeness
        
        # Flag fields with low completeness
        for field, stats in completeness.items():
            if stats.get("completion_rate", 0) < 0.8:
                investigation["issues"].append(f"Low completeness in field '{field}': {stats.get('completion_rate', 0):.1%}")
    
    # Consistency check
    if "consistency" in quality_checks:
        consistency = analyze_consistency(records)
        investigation["results"]["consistency"] = consistency
    
    # Generate recommendations
    if investigation["issues"]:
        investigation["recommendations"].append("Implement data validation rules")
        investigation["recommendations"].append("Consider data cleanup scripts")
    
    return investigation

def analyze_completeness(records: List[Dict[str, Any]], field_info: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze data completeness"""
    if not records:
        return {}
    
    completeness = {}
    total_records = len(records)
    
    # Get all fields from first record as sample
    sample_fields = records[0].keys() if records else []
    
    for field in sample_fields:
        non_empty_count = sum(1 for record in records if record.get(field) and str(record.get(field)).strip())
        completeness[field] = {
            "total_records": total_records,
            "non_empty_count": non_empty_count,
            "completion_rate": non_empty_count / total_records if total_records > 0 else 0,
            "is_mandatory": field_info.get(field, {}).get("mandatory", False)
        }
    
    return completeness

def analyze_consistency(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze data consistency patterns"""
    consistency = {
        "format_patterns": {},
        "value_distributions": {},
        "anomalies": []
    }
    
    # Analyze format patterns for key fields
    text_fields = ["name", "description", "short_description"]
    for field in text_fields:
        if any(field in record for record in records):
            values = [str(record.get(field, "")) for record in records if record.get(field)]
            if values:
                consistency["format_patterns"][field] = analyze_text_patterns(values)
    
    return consistency

def analyze_text_patterns(values: List[str]) -> Dict[str, Any]:
    """Analyze text patterns for consistency"""
    patterns = {
        "avg_length": sum(len(v) for v in values) / len(values) if values else 0,
        "length_variance": "high" if len(set(len(v) for v in values)) > len(values) * 0.5 else "low",
        "common_prefixes": [],
        "special_chars": any(not v.replace(" ", "").replace("-", "").replace("_", "").isalnum() for v in values)
    }
    
    return patterns

def generate_development_plan(client: ServiceNowClient, story_analysis: Dict[str, Any], 
                            environment: str = "dev") -> Dict[str, Any]:
    """
    Generate a comprehensive development plan from story analysis
    """
    plan = {
        "story": story_analysis.get("story", ""),
        "environment": environment,
        "phases": [],
        "estimated_timeline": "",
        "dependencies": [],
        "risks": []
    }
    
    tasks = story_analysis.get("tasks", [])
    
    # Group tasks by type and create phases
    analysis_tasks = [t for t in tasks if t.get("type") == "analysis"]
    development_tasks = [t for t in tasks if t.get("type") == "development"]
    testing_tasks = [t for t in tasks if t.get("type") == "testing"]
    
    if analysis_tasks:
        plan["phases"].append({
            "name": "Analysis & Design",
            "tasks": analysis_tasks,
            "estimated_duration": "1-2 days"
        })
    
    if development_tasks:
        plan["phases"].append({
            "name": "Development",
            "tasks": development_tasks,
            "estimated_duration": "3-5 days"
        })
    
    if testing_tasks:
        plan["phases"].append({
            "name": "Testing & Validation",
            "tasks": testing_tasks,
            "estimated_duration": "1-2 days"
        })
    
    # Add deployment phase
    plan["phases"].append({
        "name": "Deployment",
        "tasks": [{
            "type": "deployment",
            "description": "Deploy to target environment",
            "pack": "pipeline",
            "estimated_effort": "low"
        }],
        "estimated_duration": "0.5 days"
    })
    
    return plan

def root_cause_analysis(client: ServiceNowClient, issue_description: str, 
                       related_table: Optional[str] = None,
                       time_range_hours: int = 24) -> Dict[str, Any]:
    """
    Perform root cause analysis for ServiceNow issues
    """
    analysis = {
        "issue": issue_description,
        "investigation_scope": {
            "table": related_table,
            "time_range_hours": time_range_hours
        },
        "findings": [],
        "potential_causes": [],
        "recommendations": []
    }
    
    # Check system logs for related errors
    if "error" in issue_description.lower() or "fail" in issue_description.lower():
        try:
            logs = client.query_table("syslog", 
                                    query=f"sys_created_on>=javascript:gs.daysAgoStart({time_range_hours//24})",
                                    fields=["level", "message", "source", "sys_created_on"],
                                    limit=100)
            
            error_logs = [log for log in logs if log.get("level") in ["error", "warn"]]
            if error_logs:
                analysis["findings"].append(f"Found {len(error_logs)} error/warning logs in the specified time range")
                analysis["potential_causes"].extend([log.get("message", "") for log in error_logs[:5]])
        except:
            analysis["findings"].append("Unable to access system logs")
    
    # Check for recent changes if table is specified
    if related_table:
        try:
            recent_changes = client.query_table("sys_audit", 
                                              query=f"tablename={related_table}^sys_created_on>=javascript:gs.hoursAgoStart({time_range_hours})",
                                              fields=["operation", "fieldname", "oldvalue", "newvalue", "user"],
                                              limit=50)
            
            if recent_changes:
                analysis["findings"].append(f"Found {len(recent_changes)} recent changes to {related_table}")
                
                # Analyze change patterns
                operations = {}
                for change in recent_changes:
                    op = change.get("operation", "unknown")
                    operations[op] = operations.get(op, 0) + 1
                
                analysis["findings"].append(f"Change operations: {operations}")
        except:
            analysis["findings"].append(f"Unable to access audit logs for {related_table}")
    
    # Generate recommendations based on findings
    if analysis["potential_causes"]:
        analysis["recommendations"].append("Review error logs for detailed error messages")
        analysis["recommendations"].append("Check recent system changes and deployments")
    
    if not analysis["findings"]:
        analysis["recommendations"].append("Expand investigation scope or check different time ranges")
        analysis["recommendations"].append("Review application logs and performance metrics")
    
    return analysis