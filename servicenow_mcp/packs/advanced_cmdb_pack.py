"""
Advanced CMDB Pack - Sophisticated CMDB analysis and troubleshooting
"""

from typing import Dict, Any, List, Optional
from ..servicenow_client import ServiceNowClient
import json
from datetime import datetime, timedelta

def analyze_ci_lifecycle(client: ServiceNowClient, ci_sys_id: str, 
                        include_relationships: bool = True) -> Dict[str, Any]:
    """
    Comprehensive CI lifecycle analysis
    """
    analysis = {
        "ci_sys_id": ci_sys_id,
        "lifecycle_events": [],
        "relationship_changes": [],
        "data_quality_issues": [],
        "recommendations": []
    }
    
    # Get CI details
    try:
        ci = client.get_record("cmdb_ci", ci_sys_id)
        analysis["ci_details"] = ci
        ci_class = ci.get("sys_class_name", "cmdb_ci")
    except Exception as e:
        return {"error": f"Failed to retrieve CI: {str(e)}"}
    
    # Get audit history
    try:
        audit_records = client.query_table("sys_audit",
                                         query=f"documentkey={ci_sys_id}",
                                         fields=["fieldname", "oldvalue", "newvalue", "user", "sys_created_on"],
                                         limit=200)
        
        # Analyze lifecycle events
        for audit in audit_records:
            field = audit.get("fieldname", "")
            if field in ["install_status", "operational_status", "u_lifecycle_status"]:
                analysis["lifecycle_events"].append({
                    "timestamp": audit.get("sys_created_on"),
                    "field": field,
                    "old_value": audit.get("oldvalue"),
                    "new_value": audit.get("newvalue"),
                    "user": audit.get("user")
                })
    except Exception as e:
        analysis["lifecycle_events"] = [{"error": f"Failed to get audit history: {str(e)}"}]
    
    # Analyze relationships if requested
    if include_relationships:
        try:
            relationships = client.query_table("cmdb_rel_ci",
                                             query=f"parent={ci_sys_id}^ORchild={ci_sys_id}",
                                             fields=["parent", "child", "type", "sys_created_on"],
                                             limit=100)
            
            analysis["current_relationships"] = len(relationships)
            
            # Check for relationship changes in audit
            rel_changes = client.query_table("sys_audit",
                                            query=f"tablename=cmdb_rel_ci^newvalue CONTAINS {ci_sys_id}^ORoldvalue CONTAINS {ci_sys_id}",
                                            fields=["operation", "fieldname", "oldvalue", "newvalue", "sys_created_on"],
                                            limit=50)
            
            analysis["relationship_changes"] = rel_changes
            
        except Exception as e:
            analysis["relationship_changes"] = [{"error": f"Failed to analyze relationships: {str(e)}"}]
    
    # Data quality analysis
    analysis["data_quality_issues"] = analyze_ci_data_quality(ci)
    
    # Generate recommendations
    if analysis["data_quality_issues"]:
        analysis["recommendations"].append("Address data quality issues to improve CI reliability")
    
    if len(analysis["lifecycle_events"]) > 10:
        analysis["recommendations"].append("High number of status changes - review change management process")
    
    return analysis

def analyze_ci_data_quality(ci_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Analyze data quality issues in a CI record
    """
    issues = []
    
    # Check for empty mandatory fields
    mandatory_fields = ["name", "operational_status", "install_status"]
    for field in mandatory_fields:
        if not ci_data.get(field) or str(ci_data.get(field)).strip() == "":
            issues.append({
                "type": "missing_mandatory_data",
                "field": field,
                "severity": "high",
                "description": f"Mandatory field '{field}' is empty"
            })
    
    # Check for suspicious data patterns
    name = ci_data.get("name", "")
    if name and (len(name) < 3 or name.lower() in ["test", "temp", "unknown"]):
        issues.append({
            "type": "suspicious_name",
            "field": "name", 
            "severity": "medium",
            "description": f"CI name '{name}' appears to be placeholder or test data"
        })
    
    # Check for inconsistent status combinations
    install_status = ci_data.get("install_status", "")
    operational_status = ci_data.get("operational_status", "")
    
    if install_status == "Retired" and operational_status == "Operational":
        issues.append({
            "type": "inconsistent_status",
            "field": "status_combination",
            "severity": "high", 
            "description": "CI marked as Retired but Operational - inconsistent status"
        })
    
    return issues

def detect_duplicate_patterns(client: ServiceNowClient, ci_class: str = "cmdb_ci",
                            detection_fields: Optional[List[str]] = None,
                            limit: int = 1000) -> Dict[str, Any]:
    """
    Advanced duplicate detection with pattern analysis
    """
    if not detection_fields:
        detection_fields = ["name", "serial_number", "ip_address", "mac_address", "asset_tag", "fqdn"]
    
    analysis = {
        "ci_class": ci_class,
        "detection_fields": detection_fields,
        "duplicate_groups": [],
        "patterns": {},
        "statistics": {},
        "recommendations": []
    }
    
    # Get CIs for analysis
    try:
        cis = client.query_table(ci_class, 
                               fields=["sys_id", "sys_created_on", "sys_created_by", "sys_updated_on"] + detection_fields,
                               limit=limit)
    except Exception as e:
        return {"error": f"Failed to query CIs: {str(e)}"}
    
    # Group by each detection field
    field_groups = {}
    for field in detection_fields:
        field_groups[field] = {}
        for ci in cis:
            value = normalize_field_value(ci.get(field, ""))
            if value:  # Only process non-empty values
                if value not in field_groups[field]:
                    field_groups[field][value] = []
                field_groups[field][value].append(ci)
    
    # Identify duplicate groups
    for field, groups in field_groups.items():
        for value, ci_list in groups.items():
            if len(ci_list) > 1:
                duplicate_group = {
                    "field": field,
                    "value": value,
                    "count": len(ci_list),
                    "cis": ci_list,
                    "creation_analysis": analyze_duplicate_creation_pattern(ci_list),
                    "confidence": calculate_duplicate_confidence(ci_list, field)
                }
                analysis["duplicate_groups"].append(duplicate_group)
    
    # Pattern analysis
    analysis["patterns"] = analyze_duplicate_patterns(analysis["duplicate_groups"])
    
    # Statistics
    analysis["statistics"] = {
        "total_cis_analyzed": len(cis),
        "duplicate_groups_found": len(analysis["duplicate_groups"]),
        "total_duplicate_cis": sum(group["count"] for group in analysis["duplicate_groups"]),
        "duplicate_percentage": (sum(group["count"] for group in analysis["duplicate_groups"]) / len(cis) * 100) if cis else 0
    }
    
    # Recommendations
    if analysis["duplicate_groups"]:
        analysis["recommendations"].extend(generate_duplicate_recommendations(analysis))
    
    return analysis

def normalize_field_value(value: Any) -> str:
    """
    Normalize field values for duplicate detection
    """
    if not value:
        return ""
    
    normalized = str(value).strip().lower()
    
    # Remove common variations
    normalized = normalized.replace("-", "").replace("_", "").replace(" ", "")
    
    return normalized

def analyze_duplicate_creation_pattern(ci_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze the creation pattern of duplicate CIs
    """
    if not ci_list:
        return {}
    
    # Sort by creation date
    sorted_cis = sorted(ci_list, key=lambda x: x.get("sys_created_on", ""))
    
    creators = [ci.get("sys_created_by", "") for ci in ci_list]
    creation_times = [ci.get("sys_created_on", "") for ci in ci_list]
    
    pattern = {
        "first_created": sorted_cis[0].get("sys_created_on"),
        "last_created": sorted_cis[-1].get("sys_created_on"),
        "unique_creators": list(set(creators)),
        "creator_count": len(set(creators)),
        "same_creator": len(set(creators)) == 1,
        "rapid_creation": is_rapid_creation(creation_times),
        "bulk_import_likely": len(ci_list) > 5 and len(set(creators)) == 1
    }
    
    return pattern

def is_rapid_creation(creation_times: List[str]) -> bool:
    """
    Determine if CIs were created rapidly (within minutes)
    """
    if len(creation_times) < 2:
        return False
    
    try:
        # Simple check - if all created within same hour, consider rapid
        hours = set(time[:13] for time in creation_times if time)  # YYYY-MM-DD HH
        return len(hours) <= 1
    except:
        return False

def calculate_duplicate_confidence(ci_list: List[Dict[str, Any]], field: str) -> float:
    """
    Calculate confidence that these are actual duplicates
    """
    if len(ci_list) < 2:
        return 0.0
    
    confidence = 0.5  # Base confidence
    
    # Higher confidence for certain fields
    high_confidence_fields = ["serial_number", "asset_tag", "mac_address"]
    if field in high_confidence_fields:
        confidence += 0.3
    
    # Check creation pattern
    pattern = analyze_duplicate_creation_pattern(ci_list)
    if pattern.get("same_creator"):
        confidence += 0.2
    if pattern.get("rapid_creation"):
        confidence += 0.2
    
    return min(confidence, 1.0)

def analyze_duplicate_patterns(duplicate_groups: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze patterns across all duplicate groups
    """
    patterns = {
        "most_common_fields": {},
        "creation_sources": {},
        "time_patterns": {},
        "bulk_import_indicators": []
    }
    
    # Count duplicates by field
    for group in duplicate_groups:
        field = group["field"]
        patterns["most_common_fields"][field] = patterns["most_common_fields"].get(field, 0) + 1
    
    # Analyze creation sources
    for group in duplicate_groups:
        creators = group.get("creation_analysis", {}).get("unique_creators", [])
        for creator in creators:
            patterns["creation_sources"][creator] = patterns["creation_sources"].get(creator, 0) + 1
    
    # Identify bulk import patterns
    for group in duplicate_groups:
        if group.get("creation_analysis", {}).get("bulk_import_likely"):
            patterns["bulk_import_indicators"].append({
                "field": group["field"],
                "value": group["value"],
                "count": group["count"],
                "creator": group.get("creation_analysis", {}).get("unique_creators", ["unknown"])[0]
            })
    
    return patterns

def generate_duplicate_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """
    Generate recommendations based on duplicate analysis
    """
    recommendations = []
    
    patterns = analysis.get("patterns", {})
    stats = analysis.get("statistics", {})
    
    # High-level recommendations
    if stats.get("duplicate_percentage", 0) > 10:
        recommendations.append("High duplicate percentage detected - implement duplicate prevention controls")
    
    # Field-specific recommendations
    common_fields = patterns.get("most_common_fields", {})
    if "serial_number" in common_fields:
        recommendations.append("Serial number duplicates found - review hardware discovery processes")
    
    if "ip_address" in common_fields:
        recommendations.append("IP address duplicates detected - check network discovery configuration")
    
    # Source-specific recommendations
    creation_sources = patterns.get("creation_sources", {})
    if creation_sources:
        top_source = max(creation_sources.items(), key=lambda x: x[1])
        recommendations.append(f"Primary duplicate source: {top_source[0]} - review their data import processes")
    
    # Bulk import recommendations
    bulk_imports = patterns.get("bulk_import_indicators", [])
    if bulk_imports:
        recommendations.append("Bulk import duplicates detected - implement pre-import duplicate checking")
    
    return recommendations

def investigate_ci_relationships(client: ServiceNowClient, ci_sys_id: str,
                               max_depth: int = 3, relationship_types: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Deep investigation of CI relationships and dependencies
    """
    investigation = {
        "root_ci": ci_sys_id,
        "max_depth": max_depth,
        "relationship_map": {},
        "dependency_analysis": {},
        "issues": [],
        "recommendations": []
    }
    
    try:
        # Get root CI details
        root_ci = client.get_record("cmdb_ci", ci_sys_id)
        investigation["root_ci_details"] = root_ci
    except Exception as e:
        return {"error": f"Failed to get root CI: {str(e)}"}
    
    # Build relationship map
    visited = set()
    relationship_map = build_relationship_map(client, ci_sys_id, max_depth, visited, relationship_types)
    investigation["relationship_map"] = relationship_map
    
    # Analyze dependencies
    investigation["dependency_analysis"] = analyze_dependencies(relationship_map)
    
    # Check for relationship issues
    investigation["issues"] = detect_relationship_issues(client, relationship_map)
    
    # Generate recommendations
    if investigation["issues"]:
        investigation["recommendations"].append("Review and clean up relationship inconsistencies")
    
    if investigation["dependency_analysis"].get("circular_dependencies"):
        investigation["recommendations"].append("Resolve circular dependencies to prevent impact calculation issues")
    
    return investigation

def build_relationship_map(client: ServiceNowClient, ci_sys_id: str, max_depth: int, 
                          visited: set, relationship_types: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Recursively build relationship map
    """
    if max_depth <= 0 or ci_sys_id in visited:
        return {}
    
    visited.add(ci_sys_id)
    
    # Query relationships
    query = f"parent={ci_sys_id}^ORchild={ci_sys_id}"
    if relationship_types:
        type_query = "^".join([f"type.name={rt}" for rt in relationship_types])
        query += f"^{type_query}"
    
    try:
        relationships = client.query_table("cmdb_rel_ci",
                                         query=query,
                                         fields=["parent", "child", "type", "sys_id"],
                                         limit=200)
    except Exception:
        return {"error": "Failed to query relationships"}
    
    relationship_map = {
        "ci_sys_id": ci_sys_id,
        "relationships": relationships,
        "children": {},
        "parents": {}
    }
    
    # Recursively process related CIs
    for rel in relationships:
        if rel.get("parent") == ci_sys_id:
            child_id = rel.get("child")
            if child_id and child_id not in visited:
                relationship_map["children"][child_id] = build_relationship_map(
                    client, child_id, max_depth - 1, visited, relationship_types
                )
        elif rel.get("child") == ci_sys_id:
            parent_id = rel.get("parent")
            if parent_id and parent_id not in visited:
                relationship_map["parents"][parent_id] = build_relationship_map(
                    client, parent_id, max_depth - 1, visited, relationship_types
                )
    
    return relationship_map

def analyze_dependencies(relationship_map: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze dependency patterns in relationship map
    """
    analysis = {
        "total_relationships": 0,
        "dependency_depth": 0,
        "circular_dependencies": [],
        "critical_dependencies": []
    }
    
    # Count total relationships
    def count_relationships(node):
        count = len(node.get("relationships", []))
        for child in node.get("children", {}).values():
            count += count_relationships(child)
        for parent in node.get("parents", {}).values():
            count += count_relationships(parent)
        return count
    
    analysis["total_relationships"] = count_relationships(relationship_map)
    
    # Calculate dependency depth
    def calculate_depth(node, current_depth=0):
        max_depth = current_depth
        for child in node.get("children", {}).values():
            child_depth = calculate_depth(child, current_depth + 1)
            max_depth = max(max_depth, child_depth)
        return max_depth
    
    analysis["dependency_depth"] = calculate_depth(relationship_map)
    
    return analysis

def detect_relationship_issues(client: ServiceNowClient, relationship_map: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Detect issues in CI relationships
    """
    issues = []
    
    # Check for orphaned relationships (relationships pointing to non-existent CIs)
    def check_orphaned_relationships(node):
        for rel in node.get("relationships", []):
            parent_id = rel.get("parent")
            child_id = rel.get("child")
            
            # Check if referenced CIs exist
            for ci_id in [parent_id, child_id]:
                if ci_id:
                    try:
                        client.get_record("cmdb_ci", ci_id)
                    except Exception:
                        issues.append({
                            "type": "orphaned_relationship",
                            "relationship_id": rel.get("sys_id"),
                            "missing_ci": ci_id,
                            "severity": "medium"
                        })
        
        # Recursively check children and parents
        for child in node.get("children", {}).values():
            check_orphaned_relationships(child)
        for parent in node.get("parents", {}).values():
            check_orphaned_relationships(parent)
    
    check_orphaned_relationships(relationship_map)
    
    return issues