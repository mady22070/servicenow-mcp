"""
Pack Registry for ServiceNow MCP Server

This module provides a centralized registry for all available packs,
making it easier to manage, discover, and organize functionality.
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum


class PackCategory(Enum):
    """Categories for organizing packs"""
    CORE_DEVELOPMENT = "core_development"
    DATA_CONFIGURATION = "data_configuration"
    ITSM_SERVICE_MGMT = "itsm_service_management"
    CMDB_DISCOVERY = "cmdb_discovery"
    WORKFLOW_AUTOMATION = "workflow_automation"
    INTEGRATION_API = "integration_api"
    USER_INTERFACE = "user_interface"
    APPLICATION_DEV = "application_development"
    TESTING_QUALITY = "testing_quality"
    DOCUMENTATION = "documentation"
    SECURITY_GOVERNANCE = "security_governance"


@dataclass
class PackInfo:
    """Information about a pack"""
    name: str
    category: PackCategory
    description: str
    dependencies: List[str] = None
    experimental: bool = False
    deprecated: bool = False
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class PackRegistry:
    """Registry for managing ServiceNow MCP packs"""
    
    def __init__(self):
        self._packs: Dict[str, PackInfo] = {}
        self._initialize_packs()
    
    def _initialize_packs(self):
        """Initialize the pack registry with all available packs"""
        
        # Core Development Packs
        self.register(PackInfo(
            "senior_dev_pack",
            PackCategory.CORE_DEVELOPMENT,
            "Advanced development capabilities and troubleshooting"
        ))
        
        self.register(PackInfo(
            "story_driven_pack",
            PackCategory.CORE_DEVELOPMENT,
            "Story-to-implementation pipeline for development"
        ))
        
        self.register(PackInfo(
            "dev_pack",
            PackCategory.CORE_DEVELOPMENT,
            "General development tools and utilities"
        ))
        
        self.register(PackInfo(
            "scripts_pack",
            PackCategory.CORE_DEVELOPMENT,
            "Business rules, script includes, and client scripts"
        ))
        
        # Enhanced Development Packs - COMPLETE ATTRIBUTE COVERAGE
        self.register(PackInfo(
            "enhanced_scripts_pack",
            PackCategory.CORE_DEVELOPMENT,
            "Enhanced scripts with ALL ServiceNow attributes - Business Rules, Script Includes, Client Scripts, UI Policies, UI Actions"
        ))
        
        self.register(PackInfo(
            "enhanced_table_pack",
            PackCategory.DATA_CONFIGURATION,
            "Enhanced table management with ALL ServiceNow attributes - Tables, Fields, Complete Configuration"
        ))
        
        self.register(PackInfo(
            "enhanced_flow_pack",
            PackCategory.WORKFLOW_AUTOMATION,
            "Enhanced Flow Designer with ALL ServiceNow attributes - Flows, Triggers, Actions, Complete Configuration"
        ))
        
        self.register(PackInfo(
            "enhanced_acl_pack",
            PackCategory.SECURITY_GOVERNANCE,
            "Enhanced Access Control Lists with ALL ServiceNow attributes - Table ACLs, Field ACLs, Security Management"
        ))
        
        self.register(PackInfo(
            "enhanced_choice_pack",
            PackCategory.DATA_CONFIGURATION,
            "Enhanced Choice Lists with ALL ServiceNow attributes - Choices, Choice Lists, Dependent Choices"
        ))
        
        self.register(PackInfo(
            "interactive_input_pack",
            PackCategory.USER_INTERFACE,
            "Interactive User Input Collection - Dynamic forms, validation, user prompts instead of assumptions"
        ))
        
        self.register(PackInfo(
            "background_script_pack",
            PackCategory.CORE_DEVELOPMENT,
            "Background script execution and management"
        ))
        
        # Data and Configuration Packs
        self.register(PackInfo(
            "table_pack",
            PackCategory.DATA_CONFIGURATION,
            "Table creation, modification, and management"
        ))
        
        self.register(PackInfo(
            "data_pack",
            PackCategory.DATA_CONFIGURATION,
            "Data import, export, and transformation"
        ))
        

        
        self.register(PackInfo(
            "update_set_pack",
            PackCategory.DATA_CONFIGURATION,
            "Update set management and deployment"
        ))
        
        self.register(PackInfo(
            "attachment_pack",
            PackCategory.DATA_CONFIGURATION,
            "File attachment operations"
        ))
        
        self.register(PackInfo(
            "props_pack",
            PackCategory.DATA_CONFIGURATION,
            "System properties management"
        ))
        
        # ITSM and Service Management Packs
        self.register(PackInfo(
            "change_pack",
            PackCategory.ITSM_SERVICE_MGMT,
            "Change management operations"
        ))
        
        self.register(PackInfo(
            "problem_pack",
            PackCategory.ITSM_SERVICE_MGMT,
            "Problem management operations"
        ))
        
        self.register(PackInfo(
            "request_pack",
            PackCategory.ITSM_SERVICE_MGMT,
            "Service request management"
        ))
        
        self.register(PackInfo(
            "irm_pack",
            PackCategory.ITSM_SERVICE_MGMT,
            "Incident Response Management"
        ))
        
        self.register(PackInfo(
            "approvals_pack",
            PackCategory.ITSM_SERVICE_MGMT,
            "Approval workflow management"
        ))
        
        self.register(PackInfo(
            "notify_pack",
            PackCategory.ITSM_SERVICE_MGMT,
            "Notification management"
        ))
        
        # CMDB and Discovery Packs
        self.register(PackInfo(
            "cmdb_pack",
            PackCategory.CMDB_DISCOVERY,
            "Configuration Management Database operations"
        ))
        
        self.register(PackInfo(
            "advanced_cmdb_pack",
            PackCategory.CMDB_DISCOVERY,
            "Advanced CMDB analysis and troubleshooting"
        ))
        
        self.register(PackInfo(
            "csdm_pack",
            PackCategory.CMDB_DISCOVERY,
            "Common Service Data Model (CSDM) 5.0 support"
        ))
        
        self.register(PackInfo(
            "discovery_pack",
            PackCategory.CMDB_DISCOVERY,
            "Discovery operations and management"
        ))
        
        self.register(PackInfo(
            "itam_pack",
            PackCategory.CMDB_DISCOVERY,
            "IT Asset Management operations"
        ))
        
        # Workflow and Automation Packs
        self.register(PackInfo(
            "flow_pack",
            PackCategory.WORKFLOW_AUTOMATION,
            "Flow Designer operations"
        ))
        
        self.register(PackInfo(
            "pipeline_pack",
            PackCategory.WORKFLOW_AUTOMATION,
            "CI/CD pipeline management"
        ))
        
        self.register(PackInfo(
            "planner_pack",
            PackCategory.WORKFLOW_AUTOMATION,
            "Planning and orchestration tools"
        ))
        
        self.register(PackInfo(
            "operate_pack",
            PackCategory.WORKFLOW_AUTOMATION,
            "Operations and monitoring tools"
        ))
        
        # Integration and API Packs
        self.register(PackInfo(
            "scripted_rest_api_pack",
            PackCategory.INTEGRATION_API,
            "Scripted REST API development with best practices"
        ))
        
        self.register(PackInfo(
            "scripted_rest_pack",
            PackCategory.INTEGRATION_API,
            "Basic scripted REST operations"
        ))
        
        self.register(PackInfo(
            "integrations_pack",
            PackCategory.INTEGRATION_API,
            "Integration management and monitoring"
        ))
        
        # User Interface and Experience Packs
        self.register(PackInfo(
            "ui_builder_pack",
            PackCategory.USER_INTERFACE,
            "UI Builder page creation and management"
        ))
        
        self.register(PackInfo(
            "catalog_pack",
            PackCategory.USER_INTERFACE,
            "Service catalog management"
        ))
        
        self.register(PackInfo(
            "ux_pack",
            PackCategory.USER_INTERFACE,
            "User experience optimization"
        ))
        
        self.register(PackInfo(
            "user_pack",
            PackCategory.USER_INTERFACE,
            "User management operations"
        ))
        
        # Application Development Packs
        self.register(PackInfo(
            "scoped_app_pack",
            PackCategory.APPLICATION_DEV,
            "Scoped application management"
        ))
        
        self.register(PackInfo(
            "scoped_development_pack",
            PackCategory.APPLICATION_DEV,
            "Scoped development enforcement and best practices"
        ))
        
        self.register(PackInfo(
            "best_practices_pack",
            PackCategory.APPLICATION_DEV,
            "ServiceNow development best practices validation"
        ))
        
        # Testing and Quality Packs
        self.register(PackInfo(
            "atf_pack",
            PackCategory.TESTING_QUALITY,
            "Automated Test Framework operations"
        ))
        
        self.register(PackInfo(
            "troubleshoot_pack",
            PackCategory.TESTING_QUALITY,
            "Troubleshooting and diagnostic tools"
        ))
        
        # Documentation and Knowledge Packs
        self.register(PackInfo(
            "servicenow_docs_pack",
            PackCategory.DOCUMENTATION,
            "ServiceNow documentation search and access"
        ))
        
        self.register(PackInfo(
            "docs_pack",
            PackCategory.DOCUMENTATION,
            "Documentation generation and management"
        ))
        
        self.register(PackInfo(
            "knowledge_pack",
            PackCategory.DOCUMENTATION,
            "Knowledge base management"
        ))
        
        # Security and Governance Packs
        self.register(PackInfo(
            "governance_pack",
            PackCategory.SECURITY_GOVERNANCE,
            "Governance and compliance tools"
        ))
        
        self.register(PackInfo(
            "impersonation_pack",
            PackCategory.SECURITY_GOVERNANCE,
            "User impersonation management"
        ))
        
        self.register(PackInfo(
            "event_pack",
            PackCategory.SECURITY_GOVERNANCE,
            "Event management and monitoring"
        ))
        
        # Enhanced Packs (New Capabilities)
        self.register(PackInfo(
            "naming_conventions_pack",
            PackCategory.APPLICATION_DEV,
            "ServiceNow naming conventions validation and suggestions"
        ))
        
        self.register(PackInfo(
            "catalog_management_pack",
            PackCategory.USER_INTERFACE,
            "Comprehensive catalog item creation with variables and UI policies"
        ))
        
        self.register(PackInfo(
            "ui_management_pack",
            PackCategory.USER_INTERFACE,
            "Complete UI component management (policies, actions, layouts)"
        ))
    
    def register(self, pack_info: PackInfo):
        """Register a pack in the registry"""
        self._packs[pack_info.name] = pack_info
    
    def get_pack(self, name: str) -> Optional[PackInfo]:
        """Get pack information by name"""
        return self._packs.get(name)
    
    def get_packs_by_category(self, category: PackCategory) -> List[PackInfo]:
        """Get all packs in a specific category"""
        return [pack for pack in self._packs.values() if pack.category == category]
    
    def get_all_packs(self) -> List[PackInfo]:
        """Get all registered packs"""
        return list(self._packs.values())
    
    def get_pack_names(self) -> List[str]:
        """Get all pack names"""
        return list(self._packs.keys())
    
    def get_pack_names_by_category(self, category: PackCategory) -> List[str]:
        """Get pack names by category"""
        return [pack.name for pack in self.get_packs_by_category(category)]
    
    def validate_dependencies(self) -> Dict[str, List[str]]:
        """Validate pack dependencies and return any missing dependencies"""
        missing_deps = {}
        
        for pack_name, pack_info in self._packs.items():
            missing = []
            for dep in pack_info.dependencies:
                if dep not in self._packs:
                    missing.append(dep)
            
            if missing:
                missing_deps[pack_name] = missing
        
        return missing_deps
    
    def get_categories(self) -> List[PackCategory]:
        """Get all available categories"""
        return list(PackCategory)
    
    def get_category_summary(self) -> Dict[str, int]:
        """Get summary of packs per category"""
        summary = {}
        for category in PackCategory:
            summary[category.value] = len(self.get_packs_by_category(category))
        return summary


# Global registry instance
_registry = PackRegistry()

def get_pack_registry() -> PackRegistry:
    """Get the global pack registry instance"""
    return _registry