"""
CSDM (Common Service Data Model) 5.0 Pack for ServiceNow MCP Server

This pack provides comprehensive support for ServiceNow's CSDM 5.0 framework,
including CI discovery, relationship mapping, service topology analysis,
and CSDM compliance validation.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..logging_config import get_logger
from ..error_handler import ServiceNowError, handle_errors
from ..constants import ServiceNowTables, DefaultValues


# Constants
class CSDMVersion:
    """CSDM version constants"""
    VERSION_5_0 = "5.0"

class CSDMDefaults:
    """Default values for CSDM operations"""
    MAX_DISCOVERY_DEPTH = 5
    DEFAULT_DISCOVERY_DEPTH = 3
    DEFAULT_RELATIONSHIP_LIMIT = 500
    DEFAULT_QUERY_LIMIT = 1000
    STALE_DATA_THRESHOLD_DAYS = 30
    MAX_CLOUD_QUERY_IDS = 50

class CloudProvider(Enum):
    """Supported cloud providers"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    VMWARE = "vmware"

@dataclass
class CSDMFoundationClasses:
    """CSDM 5.0 Foundation Classes mapping"""
    BUSINESS_APPLICATION = 'cmdb_ci_business_app'
    APPLICATION_SERVICE = 'cmdb_ci_app_server'
    COMPUTER = 'cmdb_ci_computer'
    STORAGE = 'cmdb_ci_storage_device'
    NETWORK_GEAR = 'cmdb_ci_netgear'
    DATABASE = 'cmdb_ci_database'
    
    @classmethod
    def get_all_classes(cls) -> Set[str]:
        """Get all foundation class names"""
        return {
            cls.BUSINESS_APPLICATION,
            cls.APPLICATION_SERVICE,
            cls.COMPUTER,
            cls.STORAGE,
            cls.NETWORK_GEAR,
            cls.DATABASE
        }

@dataclass
class CSDMRelationships:
    """CSDM relationship type mappings"""
    DEPENDS_ON = 'Depends on::Used by'
    HOSTED_ON = 'Hosted on::Hosts'
    MEMBER_OF = 'Member of::Members'
    CONNECTS_TO = 'Connects to::Connected by'
    RUNS_ON = 'Runs on::Runs'
    USES = 'Uses::Used by'
    
    @classmethod
    def get_all_relationships(cls) -> Set[str]:
        """Get all CSDM relationship types"""
        return {
            cls.DEPENDS_ON,
            cls.HOSTED_ON,
            cls.MEMBER_OF,
            cls.CONNECTS_TO,
            cls.RUNS_ON,
            cls.USES
        }

# Cloud provider CI class mappings
CLOUD_CI_CLASSES = {
    CloudProvider.AWS: [
        'cmdb_ci_aws_instance',
        'cmdb_ci_aws_rds_instance', 
        'cmdb_ci_aws_load_balancer',
        'cmdb_ci_aws_s3_bucket'
    ],
    CloudProvider.AZURE: [
        'cmdb_ci_azure_vm',
        'cmdb_ci_azure_sql_database',
        'cmdb_ci_azure_load_balancer'
    ],
    CloudProvider.GCP: [
        'cmdb_ci_gcp_instance',
        'cmdb_ci_gcp_sql_instance'
    ]
}

@dataclass
class TopologyDiscoveryResult:
    """Result of topology discovery operation"""
    root_ci: Dict[str, Any]
    layers: Dict[str, Any]
    relationships: List[Dict[str, Any]]
    csdm_compliance: Dict[str, Any]
    cloud_resources: Optional[List[Dict[str, Any]]]
    discovery_metadata: Dict[str, Any]


@handle_errors("discover_csdm_topology")
def discover_csdm_topology(
    client, 
    root_ci_id: str, 
    depth: int = CSDMDefaults.DEFAULT_DISCOVERY_DEPTH, 
    include_cloud: bool = True
) -> Dict[str, Any]:
    """
    Discover complete CSDM topology from a root CI
    
    Args:
        client: ServiceNow client
        root_ci_id: Root CI sys_id to start discovery
        depth: Discovery depth (1-5)
        include_cloud: Include cloud resources in discovery
        
    Returns:
        Complete CSDM topology with relationships and metadata
        
    Raises:
        ServiceNowError: If root CI not found or discovery fails
    """
    logger = get_logger()
    
    # Validate input parameters
    if not root_ci_id or not root_ci_id.strip():
        raise ServiceNowError("Root CI ID cannot be empty")
    
    if depth < 1 or depth > CSDMDefaults.MAX_DISCOVERY_DEPTH:
        raise ServiceNowError(f"Discovery depth must be between 1 and {CSDMDefaults.MAX_DISCOVERY_DEPTH}")
    
    logger.info(f"Starting CSDM topology discovery for CI {root_ci_id}, depth={depth}")
    
    # Get root CI details
    root_ci = _get_root_ci(client, root_ci_id)
    
    # Initialize topology structure
    topology = _initialize_topology_structure(root_ci, depth, include_cloud)
    
    # Discover topology layers
    current_cis = [root_ci_id]
    discovered_cis = {root_ci_id}  # Track discovered CIs to avoid duplicates
    
    for layer_num in range(depth):
        if not current_cis:
            logger.info(f"No more CIs to explore at layer {layer_num + 1}")
            break
            
        layer_name = f"layer_{layer_num + 1}"
        next_cis = _discover_layer(
            client, current_cis, layer_name, layer_num + 1, 
            topology, discovered_cis
        )
        
        current_cis = next_cis
        logger.info(f"Discovered {len(next_cis)} new CIs in {layer_name}")
    
    # Analyze CSDM compliance
    topology["csdm_compliance"] = _analyze_csdm_compliance(topology)
    
    # Discover cloud resources if requested
    if include_cloud:
        topology["cloud_resources"] = _discover_cloud_resources(client, topology)
    
    logger.info(f"CSDM topology discovery completed. Found {len(topology['relationships'])} relationships")
    return topology


def _get_root_ci(client, root_ci_id: str) -> Dict[str, Any]:
    """Get root CI details with error handling"""
    root_ci = client.get_record(ServiceNowTables.CMDB_CI, root_ci_id, fields=[
        "name", "sys_class_name", "operational_status", "environment",
        "business_criticality", "discovery_source", "last_discovered"
    ])
    
    if not root_ci or root_ci.get("error"):
        raise ServiceNowError(f"Root CI not found: {root_ci_id}")
    
    return root_ci


def _initialize_topology_structure(
    root_ci: Dict[str, Any], 
    depth: int, 
    include_cloud: bool
) -> Dict[str, Any]:
    """Initialize the topology data structure"""
    return {
        "root_ci": root_ci,
        "discovery_metadata": {
            "discovered_at": datetime.utcnow().isoformat(),
            "depth": depth,
            "include_cloud": include_cloud,
            "csdm_version": CSDMVersion.VERSION_5_0
        },
        "layers": {},
        "relationships": [],
        "csdm_compliance": {},
        "cloud_resources": [] if include_cloud else None
    }


def _discover_layer(
    client, 
    current_cis: List[str], 
    layer_name: str, 
    layer_num: int,
    topology: Dict[str, Any],
    discovered_cis: Set[str]
) -> List[str]:
    """Discover a single layer of the topology"""
    logger = get_logger()
    
    topology["layers"][layer_name] = {
        "cis": [],
        "relationships": [],
        "csdm_classes": set()
    }
    
    next_cis = []
    
    for ci_id in current_cis:
        try:
            # Get relationships for this CI
            relationships = client.get_relationships(
                ci_id, 
                direction="both", 
                limit=CSDMDefaults.DEFAULT_RELATIONSHIP_LIMIT
            )
            
            for rel in relationships:
                connected_ci_id = _extract_connected_ci_id(rel, ci_id)
                
                # Skip if already discovered
                if connected_ci_id in discovered_cis:
                    continue
                
                # Get connected CI details
                connected_ci = _get_connected_ci(client, connected_ci_id)
                
                if connected_ci:
                    _add_ci_to_layer(
                        connected_ci, layer_name, topology, 
                        next_cis, discovered_cis
                    )
                    
                    # Add relationship
                    relationship = _create_relationship_record(
                        rel, ci_id, connected_ci_id, layer_num
                    )
                    topology["relationships"].append(relationship)
                    topology["layers"][layer_name]["relationships"].append(relationship)
                    
        except Exception as e:
            logger.warning(f"Error discovering relationships for CI {ci_id}: {e}")
            continue
    
    # Convert sets to lists for JSON serialization
    topology["layers"][layer_name]["csdm_classes"] = list(
        topology["layers"][layer_name]["csdm_classes"]
    )
    
    return next_cis


def _extract_connected_ci_id(rel: Dict[str, Any], source_ci_id: str) -> str:
    """Extract the connected CI ID from a relationship"""
    parent_id = rel.get("parent")
    child_id = rel.get("child")
    return child_id if parent_id == source_ci_id else parent_id


def _get_connected_ci(client, ci_id: str) -> Optional[Dict[str, Any]]:
    """Get connected CI details with error handling"""
    try:
        connected_ci = client.get_record(ServiceNowTables.CMDB_CI, ci_id, fields=[
            "name", "sys_class_name", "operational_status", "environment"
        ])
        
        if connected_ci and not connected_ci.get("error"):
            return connected_ci
    except Exception as e:
        logger = get_logger()
        logger.warning(f"Error retrieving CI {ci_id}: {e}")
    
    return None


def _add_ci_to_layer(
    connected_ci: Dict[str, Any],
    layer_name: str,
    topology: Dict[str, Any],
    next_cis: List[str],
    discovered_cis: Set[str]
):
    """Add CI to the current layer"""
    topology["layers"][layer_name]["cis"].append(connected_ci)
    topology["layers"][layer_name]["csdm_classes"].add(
        connected_ci.get("sys_class_name", "unknown")
    )
    
    ci_id = connected_ci.get("sys_id")
    if ci_id:
        next_cis.append(ci_id)
        discovered_cis.add(ci_id)


def _create_relationship_record(
    rel: Dict[str, Any], 
    source_ci_id: str, 
    target_ci_id: str, 
    layer: int
) -> Dict[str, Any]:
    """Create a relationship record"""
    parent_id = rel.get("parent")
    rel_type = rel.get("type", {}).get("display_value", "Unknown")
    
    return {
        "source_ci": source_ci_id,
        "target_ci": target_ci_id,
        "relationship_type": rel_type,
        "direction": "outbound" if parent_id == source_ci_id else "inbound",
        "layer": layer
    }


@handle_errors("analyze_csdm_health")
def analyze_csdm_health(
    client, 
    ci_class: Optional[str] = None, 
    environment: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze CSDM health and compliance across the environment
    
    Args:
        client: ServiceNow client
        ci_class: Specific CI class to analyze (optional)
        environment: Environment filter (prod, test, dev)
        
    Returns:
        Comprehensive CSDM health analysis
    """
    logger = get_logger()
    logger.info(f"Starting CSDM health analysis for class={ci_class}, env={environment}")
    
    # Build query filter
    query = _build_health_analysis_query(ci_class, environment)
    
    # Gather health metrics
    health_metrics = _gather_health_metrics(client, query)
    
    # Build health analysis result
    health_analysis = {
        "analysis_metadata": {
            "analyzed_at": datetime.utcnow().isoformat(),
            "ci_class_filter": ci_class,
            "environment_filter": environment,
            "csdm_version": CSDMVersion.VERSION_5_0
        },
        **health_metrics,
        "csdm_compliance_score": 0,
        "recommendations": []
    }
    
    # Calculate compliance score and recommendations
    compliance_data = _calculate_csdm_compliance_score(health_analysis)
    health_analysis.update(compliance_data)
    
    logger.info(f"CSDM health analysis completed. Compliance score: {health_analysis['csdm_compliance_score']}")
    return health_analysis


def _build_health_analysis_query(ci_class: Optional[str], environment: Optional[str]) -> str:
    """Build query filter for health analysis"""
    query_parts = []
    
    if ci_class:
        query_parts.append(f"sys_class_name={ci_class}")
    if environment:
        query_parts.append(f"environment={environment}")
    
    return "^".join(query_parts) if query_parts else ""


def _gather_health_metrics(client, base_query: str) -> Dict[str, Any]:
    """Gather all health metrics for CSDM analysis"""
    logger = get_logger()
    
    try:
        # Get CI statistics
        ci_stats = client.stats(
            ServiceNowTables.CMDB_CI,
            query=base_query,
            group_by=["sys_class_name", "operational_status", "environment"],
            count=True
        )
        
        # Analyze discovery coverage
        discovery_query = _append_to_query(base_query, "discovery_sourceISNOTEMPTY")
        discovery_stats = client.stats(
            ServiceNowTables.CMDB_CI,
            query=discovery_query,
            group_by=["discovery_source"],
            count=True
        )
        
        # Check for orphaned CIs
        orphaned_metrics = _analyze_orphaned_cis(client, base_query)
        
        # Analyze relationship health
        rel_stats = client.stats(
            "cmdb_rel_ci",
            group_by=["type"],
            count=True
        )
        
        # Check for stale data
        stale_metrics = _analyze_stale_data(client, base_query)
        
        return {
            "ci_statistics": ci_stats,
            "discovery_coverage": discovery_stats,
            "orphaned_cis": orphaned_metrics,
            "relationship_statistics": rel_stats,
            "data_freshness": stale_metrics
        }
        
    except Exception as e:
        logger.error(f"Error gathering health metrics: {e}")
        raise ServiceNowError(f"Failed to gather CSDM health metrics: {e}")


def _append_to_query(base_query: str, additional_filter: str) -> str:
    """Append additional filter to existing query"""
    if base_query:
        return f"{base_query}^{additional_filter}"
    return additional_filter


def _analyze_orphaned_cis(client, base_query: str) -> Dict[str, Any]:
    """Analyze orphaned CIs (CIs with no relationships)"""
    orphaned_query = _append_to_query(
        base_query, 
        "cmdb_rel_ci.parentISEMPTY^cmdb_rel_ci.childISEMPTY"
    )
    
    orphaned_cis = client.query_table(
        ServiceNowTables.CMDB_CI, 
        query=orphaned_query, 
        limit=DefaultValues.DEFAULT_QUERY_LIMIT
    )
    
    return {
        "count": len(orphaned_cis.get("result", [])),
        "examples": orphaned_cis.get("result", [])[:10]
    }


def _analyze_stale_data(client, base_query: str) -> Dict[str, Any]:
    """Analyze stale CI data"""
    stale_date = (
        datetime.utcnow() - timedelta(days=CSDMDefaults.STALE_DATA_THRESHOLD_DAYS)
    ).strftime("%Y-%m-%d")
    
    stale_query = _append_to_query(base_query, f"sys_updated_on<{stale_date}")
    stale_cis = client.query_table(
        ServiceNowTables.CMDB_CI, 
        query=stale_query, 
        limit=DefaultValues.DEFAULT_QUERY_LIMIT
    )
    
    return {
        "stale_cis_count": len(stale_cis.get("result", [])),
        "stale_threshold_days": CSDMDefaults.STALE_DATA_THRESHOLD_DAYS,
        "examples": stale_cis.get("result", [])[:10]
    }


def validate_csdm_structure(client, business_service_id: str) -> Dict[str, Any]:
    """
    Validate CSDM structure for a business service
    
    Args:
        client: ServiceNow client
        business_service_id: Business service sys_id
        
    Returns:
        CSDM structure validation results
    """
    
    # Get business service details
    business_service = client.get_record("cmdb_ci_service", business_service_id)
    
    if not business_service or business_service.get("error"):
        return {"error": "Business service not found", "service_id": business_service_id}
    
    validation = {
        "business_service": business_service,
        "validation_metadata": {
            "validated_at": datetime.utcnow().isoformat(),
            "csdm_version": "5.0"
        },
        "structure_validation": {
            "has_business_applications": False,
            "has_application_services": False,
            "has_infrastructure": False,
            "has_dependencies": False
        },
        "missing_components": [],
        "validation_score": 0,
        "recommendations": []
    }
    
    # Check for business applications
    bus_apps = client.query_table(
        "cmdb_rel_ci",
        query=f"parent={business_service_id}^child.sys_class_nameSTARTSWITHcmdb_ci_business_app",
        limit=100
    )
    
    if bus_apps.get("result"):
        validation["structure_validation"]["has_business_applications"] = True
        validation["business_applications"] = bus_apps["result"]
    else:
        validation["missing_components"].append("business_applications")
    
    # Check for application services
    app_services = client.query_table(
        "cmdb_rel_ci", 
        query=f"parent={business_service_id}^child.sys_class_nameSTARTSWITHcmdb_ci_app_server",
        limit=100
    )
    
    if app_services.get("result"):
        validation["structure_validation"]["has_application_services"] = True
        validation["application_services"] = app_services["result"]
    else:
        validation["missing_components"].append("application_services")
    
    # Check for infrastructure components
    infra_query = f"parent={business_service_id}^child.sys_class_nameIN" + \
                 "cmdb_ci_computer,cmdb_ci_storage_device,cmdb_ci_netgear,cmdb_ci_database"
    
    infrastructure = client.query_table("cmdb_rel_ci", query=infra_query, limit=100)
    
    if infrastructure.get("result"):
        validation["structure_validation"]["has_infrastructure"] = True
        validation["infrastructure_components"] = infrastructure["result"]
    else:
        validation["missing_components"].append("infrastructure_components")
    
    # Check for external dependencies
    dependencies = client.query_table(
        "cmdb_rel_ci",
        query=f"child={business_service_id}^type.nameSTARTSWITHDepends",
        limit=100
    )
    
    if dependencies.get("result"):
        validation["structure_validation"]["has_dependencies"] = True
        validation["dependencies"] = dependencies["result"]
    else:
        validation["missing_components"].append("external_dependencies")
    
    # Calculate validation score
    total_checks = len(validation["structure_validation"])
    passed_checks = sum(validation["structure_validation"].values())
    validation["validation_score"] = round((passed_checks / total_checks) * 100, 2)
    
    # Generate recommendations
    validation["recommendations"] = _generate_csdm_recommendations(validation)
    
    return validation


@handle_errors("discover_cloud_resources")
def discover_cloud_resources(
    client, 
    cloud_provider: str = CloudProvider.AWS.value, 
    region: Optional[str] = None
) -> Dict[str, Any]:
    """
    Discover and analyze cloud resources in CSDM
    
    Args:
        client: ServiceNow client
        cloud_provider: Cloud provider (aws, azure, gcp, vmware)
        region: Cloud region filter
        
    Returns:
        Cloud resource discovery results
        
    Raises:
        ServiceNowError: If unsupported cloud provider or discovery fails
    """
    logger = get_logger()
    logger.info(f"Starting cloud resource discovery for {cloud_provider}, region={region}")
    
    # Validate cloud provider
    try:
        provider_enum = CloudProvider(cloud_provider.lower())
    except ValueError:
        raise ServiceNowError(f"Unsupported cloud provider: {cloud_provider}")
    
    provider_classes = CLOUD_CI_CLASSES.get(provider_enum, [])
    if not provider_classes:
        raise ServiceNowError(f"No CI classes defined for provider: {cloud_provider}")
    
    # Initialize discovery results
    discovery_results = _initialize_cloud_discovery_results(cloud_provider, region)
    
    # Discover resources for each CI class
    for ci_class in provider_classes:
        try:
            _discover_cloud_ci_class(client, ci_class, region, discovery_results)
        except Exception as e:
            logger.warning(f"Error discovering {ci_class}: {e}")
            continue
    
    # Analyze cloud resource relationships
    discovery_results["cloud_relationships"] = _analyze_cloud_relationships(
        client, discovery_results
    )
    
    logger.info(f"Cloud discovery completed. Found {discovery_results['total_resources']} resources")
    return discovery_results


def _initialize_cloud_discovery_results(cloud_provider: str, region: Optional[str]) -> Dict[str, Any]:
    """Initialize cloud discovery results structure"""
    return {
        "cloud_provider": cloud_provider,
        "region_filter": region,
        "discovery_metadata": {
            "discovered_at": datetime.utcnow().isoformat(),
            "csdm_version": CSDMVersion.VERSION_5_0
        },
        "resource_types": {},
        "total_resources": 0,
        "regional_distribution": {},
        "cost_analysis": {},
        "compliance_issues": []
    }


def _discover_cloud_ci_class(
    client, 
    ci_class: str, 
    region: Optional[str], 
    discovery_results: Dict[str, Any]
):
    """Discover resources for a specific cloud CI class"""
    query = f"region={region}" if region else ""
    
    resources = client.query_table(
        ci_class, 
        query=query, 
        limit=CSDMDefaults.DEFAULT_QUERY_LIMIT
    )
    
    if not resources.get("result"):
        return
    
    resource_count = len(resources["result"])
    discovery_results["resource_types"][ci_class] = {
        "count": resource_count,
        "resources": resources["result"]
    }
    discovery_results["total_resources"] += resource_count
    
    # Analyze regional distribution
    _analyze_regional_distribution(resources["result"], discovery_results)


def _analyze_regional_distribution(resources: List[Dict[str, Any]], discovery_results: Dict[str, Any]):
    """Analyze regional distribution of cloud resources"""
    for resource in resources:
        resource_region = resource.get("region", "unknown")
        if resource_region not in discovery_results["regional_distribution"]:
            discovery_results["regional_distribution"][resource_region] = 0
        discovery_results["regional_distribution"][resource_region] += 1


# Helper functions
def _analyze_csdm_compliance(topology: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze CSDM compliance for discovered topology"""
    
    # Gather all CI classes from topology
    all_classes = set()
    for layer in topology["layers"].values():
        all_classes.update(layer["csdm_classes"])
    
    # Get foundation classes
    foundation_classes = CSDMFoundationClasses.get_all_classes()
    
    # Calculate class compliance
    present_classes = list(all_classes.intersection(foundation_classes))
    missing_classes = list(foundation_classes - all_classes)
    
    # Calculate relationship compliance
    relationship_coverage = _calculate_relationship_coverage(topology["relationships"])
    
    # Calculate overall compliance score
    class_score = (len(present_classes) / len(foundation_classes)) * 50 if foundation_classes else 0
    relationship_score = (relationship_coverage / 100) * 50
    overall_score = round(class_score + relationship_score, 2)
    
    return {
        "foundation_classes_present": present_classes,
        "missing_foundation_classes": missing_classes,
        "relationship_coverage": relationship_coverage,
        "compliance_score": overall_score
    }


def _calculate_relationship_coverage(relationships: List[Dict[str, Any]]) -> float:
    """Calculate CSDM relationship coverage percentage"""
    if not relationships:
        return 0.0
    
    csdm_relationship_types = CSDMRelationships.get_all_relationships()
    
    csdm_relationships = sum(
        1 for rel in relationships 
        if any(csdm_rel in rel["relationship_type"] for csdm_rel in csdm_relationship_types)
    )
    
    return round((csdm_relationships / len(relationships)) * 100, 2)


def _discover_cloud_resources(client, topology: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Discover cloud resources related to the topology"""
    cloud_resources = []
    
    # Look for cloud CIs in the topology
    for layer in topology["layers"].values():
        for ci in layer["cis"]:
            ci_class = ci.get("sys_class_name", "")
            cloud_provider = _detect_cloud_provider(ci_class)
            
            if cloud_provider != CloudProvider.VMWARE.value:  # Include all cloud providers except unknown
                cloud_resources.append({
                    "ci": ci,
                    "cloud_provider": cloud_provider,
                    "resource_type": ci_class
                })
    
    return cloud_resources


def _detect_cloud_provider(ci_class: str) -> str:
    """Detect cloud provider from CI class name"""
    if not ci_class:
        return "unknown"
        
    ci_class_lower = ci_class.lower()
    
    # Check for each cloud provider
    for provider in CloudProvider:
        if provider.value in ci_class_lower:
            return provider.value
    
    # Special cases
    if "google" in ci_class_lower:
        return CloudProvider.GCP.value
    elif "cloud" in ci_class_lower:
        return "generic_cloud"
    
    return "unknown"


def _calculate_csdm_compliance_score(health_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate CSDM compliance score and generate recommendations"""
    
    score = 0
    recommendations = []
    
    # Discovery coverage score (30%)
    discovery_results = health_analysis.get("discovery_coverage", {}).get("result", [])
    if discovery_results:
        score += 30
    else:
        recommendations.append("Implement automated discovery to improve CSDM coverage")
    
    # Relationship health score (25%)
    rel_results = health_analysis.get("relationship_statistics", {}).get("result", [])
    if rel_results and len(rel_results) > 5:  # Good relationship diversity
        score += 25
    else:
        recommendations.append("Improve CI relationship mapping for better service topology")
    
    # Data freshness score (25%)
    stale_count = health_analysis.get("data_freshness", {}).get("stale_cis_count", 0)
    total_cis = sum(int(stat.get("stats", {}).get("count", 0)) 
                   for stat in health_analysis.get("ci_statistics", {}).get("result", []))
    
    if total_cis > 0:
        freshness_ratio = 1 - (stale_count / total_cis)
        score += int(freshness_ratio * 25)
    
    if stale_count > 0:
        recommendations.append(f"Update {stale_count} stale CIs to improve data freshness")
    
    # Orphaned CIs score (20%)
    orphaned_count = health_analysis.get("orphaned_cis", {}).get("count", 0)
    if orphaned_count == 0:
        score += 20
    else:
        recommendations.append(f"Address {orphaned_count} orphaned CIs by establishing relationships")
    
    return {
        "csdm_compliance_score": score,
        "recommendations": recommendations
    }


def _generate_csdm_recommendations(validation: Dict[str, Any]) -> List[str]:
    """Generate CSDM structure recommendations"""
    
    recommendations = []
    missing = validation.get("missing_components", [])
    
    if "business_applications" in missing:
        recommendations.append(
            "Add business applications to provide clear business context for the service"
        )
    
    if "application_services" in missing:
        recommendations.append(
            "Map application services to show technical service components"
        )
    
    if "infrastructure_components" in missing:
        recommendations.append(
            "Connect infrastructure components (servers, databases, storage) to show hosting relationships"
        )
    
    if "external_dependencies" in missing:
        recommendations.append(
            "Document external service dependencies for complete service mapping"
        )
    
    score = validation.get("validation_score", 0)
    if score < 50:
        recommendations.append(
            "CSDM structure is incomplete. Consider implementing Service Mapping for automated discovery"
        )
    elif score < 80:
        recommendations.append(
            "Good CSDM foundation. Focus on completing missing components for full compliance"
        )
    
    return recommendations


def _analyze_cloud_relationships(client, discovery_results: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze relationships between cloud resources"""
    logger = get_logger()
    
    relationships = {
        "total_relationships": 0,
        "relationship_types": {},
        "cross_service_dependencies": [],
        "orphaned_resources": []
    }
    
    # Get all cloud resource sys_ids
    cloud_sys_ids = _extract_cloud_sys_ids(discovery_results)
    
    if not cloud_sys_ids:
        logger.info("No cloud resources found for relationship analysis")
        return relationships
    
    try:
        # Query relationships for cloud resources (limit to avoid query size issues)
        limited_sys_ids = cloud_sys_ids[:CSDMDefaults.MAX_CLOUD_QUERY_IDS]
        sys_ids_query = "^OR".join([
            f"parent={sys_id}^child={sys_id}" for sys_id in limited_sys_ids
        ])
        
        cloud_relationships = client.query_table(
            "cmdb_rel_ci",
            query=sys_ids_query,
            limit=CSDMDefaults.DEFAULT_QUERY_LIMIT
        )
        
        if cloud_relationships.get("result"):
            relationships["total_relationships"] = len(cloud_relationships["result"])
            
            # Analyze relationship types
            _analyze_relationship_types(cloud_relationships["result"], relationships)
            
        logger.info(f"Analyzed {relationships['total_relationships']} cloud relationships")
        
    except Exception as e:
        logger.error(f"Error analyzing cloud relationships: {e}")
    
    return relationships


def _extract_cloud_sys_ids(discovery_results: Dict[str, Any]) -> List[str]:
    """Extract sys_ids from cloud discovery results"""
    cloud_sys_ids = []
    
    for resource_type in discovery_results.get("resource_types", {}).values():
        for resource in resource_type.get("resources", []):
            sys_id = resource.get("sys_id")
            if sys_id:
                cloud_sys_ids.append(sys_id)
    
    return cloud_sys_ids


def _analyze_relationship_types(
    relationship_results: List[Dict[str, Any]], 
    relationships: Dict[str, Any]
):
    """Analyze and categorize relationship types"""
    for rel in relationship_results:
        rel_type = rel.get("type", {}).get("display_value", "Unknown")
        if rel_type not in relationships["relationship_types"]:
            relationships["relationship_types"][rel_type] = 0
        relationships["relationship_types"][rel_type] += 1