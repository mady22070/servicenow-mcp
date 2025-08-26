"""
Pydantic models for request/response validation and MCP resources
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


# Base Models
class MCPError(BaseModel):
    """Standard MCP error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    """Standard MCP response wrapper"""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    error: Optional[MCPError] = None
    metadata: Optional[Dict[str, Any]] = None


# Tool Parameter Models
class QueryTableParams(BaseModel):
    """Parameters for query_table tool"""
    table: str = Field(..., description="ServiceNow table name")
    query: str = Field("", description="Encoded query string")
    fields: Optional[List[str]] = Field(None, description="Fields to return")
    limit: int = Field(100, ge=1, le=10000, description="Maximum records to return")
    display: bool = Field(False, description="Return display values")
    env: str = Field("dev", description="Environment (dev/test/prod)")

    @field_validator('table')
    @classmethod
    def validate_table(cls, v):
        if not v or not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Table name must be alphanumeric with underscores/hyphens")
        return v


class StatsParams(BaseModel):
    """Parameters for stats tool"""
    table: str = Field(..., description="ServiceNow table name")
    query: str = Field("", description="Encoded query string")
    group_by: Optional[List[str]] = Field(None, description="Fields to group by")
    count: bool = Field(True, description="Include count")
    sum: Optional[List[str]] = Field(None, description="Fields to sum")
    avg: Optional[List[str]] = Field(None, description="Fields to average")
    minv: Optional[List[str]] = Field(None, description="Fields to find minimum")
    maxv: Optional[List[str]] = Field(None, description="Fields to find maximum")
    env: str = Field("dev", description="Environment")


class CreateIncidentParams(BaseModel):
    """Parameters for create_incident tool"""
    short_description: str = Field(..., min_length=1, max_length=160)
    description: Optional[str] = Field(None, max_length=4000)
    additional_fields: Optional[Dict[str, Any]] = Field(None)
    env: str = Field("dev", description="Environment")


class CreateTableParams(BaseModel):
    """Parameters for create_table tool"""
    table_label: str = Field(..., min_length=1, max_length=80)
    table_name: str = Field(..., min_length=1, max_length=80)
    extends: Optional[str] = Field(None, description="Parent table to extend")
    scope: Optional[str] = Field("x_cloudorch_aiops", description="Application scope")
    dry_run: bool = Field(False, description="Preview changes without executing")
    env: str = Field("dev", description="Environment")

    @field_validator('table_name')
    @classmethod
    def validate_table_name(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError("Table name must be alphanumeric with underscores")
        return v


class AddFieldParams(BaseModel):
    """Parameters for add_field tool"""
    table_name: str = Field(..., description="Target table name")
    name: str = Field(..., min_length=1, max_length=80, description="Field name")
    ftype: str = Field(..., description="Field type")
    label: str = Field(..., min_length=1, max_length=80, description="Field label")
    mandatory: bool = Field(False, description="Is field mandatory")
    default: Optional[str] = Field(None, description="Default value")
    choices: Optional[List[str]] = Field(None, description="Choice list values")
    scope: Optional[str] = Field("x_cloudorch_aiops", description="Application scope")
    dry_run: bool = Field(False, description="Preview changes without executing")
    env: str = Field("dev", description="Environment")


class CreateScriptIncludeParams(BaseModel):
    """Parameters for create_script_include tool"""
    name: str = Field(..., min_length=1, max_length=80)
    script: str = Field(..., min_length=1)
    api_name: str = Field("", description="API name for the script include")
    active: bool = Field(True, description="Is script include active")
    scope: str = Field("x_cloudorch_aiops", description="Application scope")
    table: str = Field("sys_script_include", description="Target table")
    dry_run: bool = Field(False, description="Preview changes without executing")
    env: str = Field("dev", description="Environment")


class CreateBusinessRuleParams(BaseModel):
    """Parameters for create_business_rule tool"""
    table_name: str = Field(..., description="Target table name")
    name: str = Field(..., min_length=1, max_length=80)
    when: str = Field(..., description="When to execute (before/after/async/display)")
    actions: Dict[str, Any] = Field(..., description="Actions configuration")
    condition: str = Field("", description="Condition script")
    script: str = Field("", description="Business rule script")
    active: bool = Field(True, description="Is business rule active")
    table: str = Field("sys_script", description="Target table")
    dry_run: bool = Field(False, description="Preview changes without executing")
    env: str = Field("dev", description="Environment")


class ExecutePlanParams(BaseModel):
    """Parameters for execute_plan tool"""
    plan: List[Dict[str, Any]] = Field(..., min_length=1, description="Execution plan steps")
    confirm: bool = Field(False, description="Require confirmation for each step")
    continue_on_error: bool = Field(False, description="Continue execution on errors")
    env: str = Field("dev", description="Environment")


class WorkspaceParams(BaseModel):
    """Parameters for workspace operations"""
    name: str = Field("default", description="Workspace name")
    env: str = Field("", description="Environment setting")
    scope: str = Field("", description="Scope setting")
    confirm: bool = Field(False, description="Confirmation setting")


# Resource Models
class TableResource(BaseModel):
    """ServiceNow table resource"""
    name: str
    label: str
    sys_id: str
    super_class: Optional[str] = None
    number_ref: Optional[str] = None
    is_extendable: bool = False
    access: str = "public"
    read_access: bool = True
    create_access: bool = True
    update_access: bool = True
    delete_access: bool = True


class FieldResource(BaseModel):
    """ServiceNow field resource"""
    name: str
    label: str
    table: str
    type: str
    max_length: Optional[int] = None
    mandatory: bool = False
    read_only: bool = False
    default_value: Optional[str] = None
    reference: Optional[str] = None
    choices: Optional[List[str]] = None


class RecordResource(BaseModel):
    """ServiceNow record resource"""
    sys_id: str
    table: str
    number: Optional[str] = None
    display_value: str
    sys_created_on: datetime
    sys_updated_on: datetime
    fields: Dict[str, Any]


class ScriptResource(BaseModel):
    """ServiceNow script resource"""
    sys_id: str
    name: str
    type: Literal["business_rule", "script_include", "ui_script", "client_script"]
    table: Optional[str] = None
    active: bool = True
    script: str
    api_name: Optional[str] = None
    when: Optional[str] = None


# Server Info Models
class ServerCapabilities(BaseModel):
    """MCP server capabilities"""
    tools: Dict[str, Any] = Field(default_factory=dict)
    resources: Dict[str, Any] = Field(default_factory=dict)
    prompts: Dict[str, Any] = Field(default_factory=dict)


class ServerInfo(BaseModel):
    """MCP server information"""
    name: str = "servicenow-mcp"
    version: str = "0.8.0-full"
    description: str = "ServiceNow MCP Server with comprehensive automation capabilities"
    capabilities: ServerCapabilities = Field(default_factory=ServerCapabilities)
    environments: List[str] = Field(default_factory=lambda: ["dev", "test", "prod"])
    supported_tables: Optional[List[str]] = None
    features: List[str] = Field(default_factory=lambda: [
        "multi-environment",
        "senior-developer-capabilities", 
        "story-driven-development",
        "advanced-cmdb-analysis",
        "plan-execution",
        "workspace-management"
    ])


# Validation Models
class ValidationResult(BaseModel):
    """Validation result for operations"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class HealthCheck(BaseModel):
    """Health check response"""
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime
    environment: str
    connection_status: Dict[str, bool]
    response_time_ms: Optional[float] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)