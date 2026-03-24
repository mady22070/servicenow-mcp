# ServiceNow CSDM 5.0 Support Guide

## 🏗️ Overview

Our ServiceNow MCP server provides comprehensive support for **ServiceNow's Common Service Data Model (CSDM) 5.0**, the latest framework for organizing and standardizing Configuration Management Database (CMDB) data.

## 🎯 What is CSDM 5.0?

**CSDM (Common Service Data Model) 5.0** is ServiceNow's standardized framework that provides:

- **Consistent data structure** across ServiceNow instances
- **Standardized CI classes** for infrastructure and applications
- **Predefined relationships** between configuration items
- **Cloud-native support** for modern infrastructure
- **Service mapping integration** for automated discovery
- **Business service alignment** with technical infrastructure

## 🔧 CSDM 5.0 Components

### Foundation Classes
```
Business Layer:
├── Business Application (cmdb_ci_business_app)
├── Application Service (cmdb_ci_app_server)
└── Business Service (cmdb_ci_service)

Infrastructure Layer:
├── Computer (cmdb_ci_computer)
├── Storage (cmdb_ci_storage_device)
├── Network Gear (cmdb_ci_netgear)
└── Database (cmdb_ci_database)

Cloud Layer:
├── AWS Resources (cmdb_ci_aws_*)
├── Azure Resources (cmdb_ci_azure_*)
├── GCP Resources (cmdb_ci_gcp_*)
└── Container Resources (cmdb_ci_container_*)
```

### Relationship Types
- **Depends on / Used by** - Service dependencies
- **Hosted on / Hosts** - Infrastructure hosting
- **Member of / Members** - Cluster and group memberships
- **Connects to / Connected by** - Network connections
- **Runs on / Runs** - Application hosting
- **Uses / Used by** - Resource utilization

## 🛠️ MCP Tools for CSDM 5.0

### 1. Topology Discovery
```python
# Discover complete service topology
discover_csdm_topology(
    root_ci_id="abc123",
    depth=3,
    include_cloud=True,
    env="prod"
)
```

**Returns:**
- Complete service topology map
- Layer-by-layer CI discovery
- Relationship mapping
- CSDM compliance analysis
- Cloud resource integration

### 2. Health Analysis
```python
# Analyze CSDM health and compliance
analyze_csdm_health(
    ci_class="cmdb_ci_business_app",
    environment="production",
    env="prod"
)
```

**Returns:**
- CI statistics by class and status
- Discovery coverage analysis
- Orphaned CI detection
- Data freshness assessment
- Compliance score and recommendations

### 3. Structure Validation
```python
# Validate CSDM structure for a service
validate_csdm_structure(
    business_service_id="service123",
    env="prod"
)
```

**Returns:**
- Business application mapping
- Application service connections
- Infrastructure component links
- Dependency validation
- Structure completeness score

### 4. Cloud Resource Discovery
```python
# Discover cloud resources
discover_cloud_resources(
    cloud_provider="aws",
    region="us-east-1",
    env="prod"
)
```

**Returns:**
- Cloud resource inventory
- Regional distribution
- Resource relationships
- Cost analysis data
- Compliance issues

## 📊 CSDM Analysis Examples

### Service Topology Discovery
```json
{
  "root_ci": {
    "name": "Customer Portal",
    "sys_class_name": "cmdb_ci_business_app",
    "operational_status": "Operational"
  },
  "layers": {
    "layer_1": {
      "cis": [
        {
          "name": "Portal Web Service",
          "sys_class_name": "cmdb_ci_app_server"
        }
      ],
      "csdm_classes": ["cmdb_ci_app_server"]
    },
    "layer_2": {
      "cis": [
        {
          "name": "Web Server 01",
          "sys_class_name": "cmdb_ci_computer"
        },
        {
          "name": "Customer Database",
          "sys_class_name": "cmdb_ci_database"
        }
      ],
      "csdm_classes": ["cmdb_ci_computer", "cmdb_ci_database"]
    }
  },
  "csdm_compliance": {
    "foundation_classes_present": [
      "cmdb_ci_business_app",
      "cmdb_ci_app_server", 
      "cmdb_ci_computer",
      "cmdb_ci_database"
    ],
    "compliance_score": 85.5
  }
}
```

### Health Analysis Results
```json
{
  "csdm_compliance_score": 78,
  "ci_statistics": {
    "total_cis": 1250,
    "by_class": {
      "cmdb_ci_computer": 450,
      "cmdb_ci_database": 125,
      "cmdb_ci_business_app": 85
    }
  },
  "discovery_coverage": {
    "automated_discovery": 85,
    "manual_entry": 15
  },
  "orphaned_cis": {
    "count": 23,
    "percentage": 1.8
  },
  "recommendations": [
    "Implement Service Mapping for automated discovery",
    "Address 23 orphaned CIs by establishing relationships",
    "Update 45 stale CIs to improve data freshness"
  ]
}
```

## 🎯 Use Cases

### 1. Service Impact Analysis
```python
# Discover what depends on a critical database
topology = discover_csdm_topology(
    root_ci_id="critical_db_123",
    depth=2,
    include_cloud=True
)

# Analyze impact scope
impact_scope = len(topology["layers"]["layer_1"]["cis"])
print(f"Database impacts {impact_scope} services")
```

### 2. Cloud Migration Planning
```python
# Discover current cloud footprint
aws_resources = discover_cloud_resources("aws", "us-east-1")
azure_resources = discover_cloud_resources("azure", "eastus")

# Compare cloud usage
print(f"AWS: {aws_resources['total_resources']} resources")
print(f"Azure: {azure_resources['total_resources']} resources")
```

### 3. CSDM Compliance Audit
```python
# Analyze overall CSDM health
health = analyze_csdm_health()
compliance_score = health["csdm_compliance_score"]

if compliance_score < 70:
    print("CSDM compliance needs improvement")
    for rec in health["recommendations"]:
        print(f"- {rec}")
```

### 4. Service Validation
```python
# Validate critical business service structure
validation = validate_csdm_structure("customer_portal_service")

if validation["validation_score"] < 80:
    print("Service structure incomplete:")
    for missing in validation["missing_components"]:
        print(f"- Missing: {missing}")
```

## 🔍 Advanced CSDM Features

### Multi-Cloud Support
- **AWS Integration**: EC2, RDS, S3, Lambda, EKS
- **Azure Integration**: VMs, SQL Database, Storage, AKS
- **GCP Integration**: Compute Engine, Cloud SQL, GKE
- **Hybrid Cloud**: On-premises and cloud resource mapping

### Container and Kubernetes Support
- **Container Discovery**: Docker containers and images
- **Kubernetes Integration**: Pods, services, deployments
- **Microservices Mapping**: Service mesh topology
- **Container Orchestration**: Cluster and node relationships

### Service Mapping Integration
- **Automated Discovery**: Real-time topology discovery
- **Pattern Recognition**: Application pattern identification
- **Dependency Mapping**: Automatic relationship creation
- **Change Detection**: Topology change monitoring

## 📈 CSDM Metrics and KPIs

### Compliance Metrics
- **Foundation Class Coverage**: Percentage of CSDM classes used
- **Relationship Density**: Average relationships per CI
- **Discovery Coverage**: Automated vs manual CI creation
- **Data Freshness**: Percentage of recently updated CIs

### Quality Metrics
- **Orphaned CIs**: CIs without relationships
- **Duplicate Detection**: Potential duplicate CIs
- **Incomplete Records**: CIs missing required attributes
- **Stale Data**: CIs not updated recently

### Business Metrics
- **Service Coverage**: Business services with complete topology
- **Impact Analysis Readiness**: Services ready for impact analysis
- **Change Risk Assessment**: Services with dependency mapping
- **Incident Response**: Services with complete runbooks

## 🚀 Best Practices

### 1. Start with Business Services
```python
# Begin CSDM implementation with business services
business_services = query_table(
    "cmdb_ci_service",
    query="business_criticality=1 - Most Critical"
)

for service in business_services["result"]:
    validation = validate_csdm_structure(service["sys_id"])
    print(f"Service: {service['name']}, Score: {validation['validation_score']}")
```

### 2. Implement Automated Discovery
- Use ServiceNow Discovery for infrastructure
- Implement Service Mapping for applications
- Configure cloud discovery connectors
- Set up container discovery

### 3. Establish Data Governance
- Define CI naming conventions
- Implement data quality rules
- Set up automated validation
- Create data stewardship processes

### 4. Monitor CSDM Health
```python
# Regular CSDM health monitoring
def monitor_csdm_health():
    health = analyze_csdm_health()
    
    if health["csdm_compliance_score"] < 75:
        # Alert operations team
        send_alert(f"CSDM compliance dropped to {health['csdm_compliance_score']}")
    
    return health
```

## 🔧 Integration with ServiceNow Modules

### IT Service Management (ITSM)
- **Incident Management**: Impact analysis using CSDM topology
- **Problem Management**: Root cause analysis with service maps
- **Change Management**: Risk assessment using dependencies

### IT Operations Management (ITOM)
- **Event Management**: Correlation using CSDM relationships
- **Service Mapping**: Automated topology discovery
- **Discovery**: Infrastructure and application discovery

### IT Business Management (ITBM)
- **Portfolio Management**: Application portfolio mapping
- **Financial Management**: Cost allocation using CSDM
- **Risk Management**: Business impact assessment

## 📚 Additional Resources

### ServiceNow Documentation
- [CSDM 5.0 Implementation Guide](https://docs.servicenow.com/csdm)
- [Service Mapping Best Practices](https://docs.servicenow.com/service-mapping)
- [Discovery Configuration](https://docs.servicenow.com/discovery)

### Training and Certification
- ServiceNow CSDM Implementation Specialist
- ServiceNow Discovery Implementation
- ServiceNow Service Mapping Implementation

---

## 🎉 Summary

Our ServiceNow MCP server provides comprehensive CSDM 5.0 support with:

- ✅ **Complete topology discovery** with multi-layer analysis
- ✅ **Health and compliance monitoring** with scoring
- ✅ **Structure validation** for business services
- ✅ **Cloud resource discovery** across major providers
- ✅ **Automated recommendations** for improvement
- ✅ **Integration ready** with ServiceNow modules

This makes it easy to implement, monitor, and maintain CSDM 5.0 compliance across your ServiceNow environment while providing powerful automation capabilities for service management and operations.