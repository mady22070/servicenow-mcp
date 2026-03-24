"""
Pydantic models for request/response validation and MCP resources
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum


# Constants for field validation
class FieldLimits:
    """Constants for field length limits and validation"""
    SHORT_DESCRIPTION_MAX = 160
    DESCRIPTION_MAX = 4000
    FIELD_NAME_MAX = 80
    TABLE_NAME_MAX = 80
    QUERY_LIMIT_MIN = 1
    QUERY_LIMIT_MAX = 10000
    CHUNK_SIZE_MIN = 1
    CHUNK_SIZE_MAX = 1000
    BATCH_SIZE_MIN = 1
    BATCH_SIZE_MAX = 100


class Environment(str, Enum):
    """Supported ServiceNow environments"""
    DEV = "dev"
    TEST = "test"
    PROD = "prod"


class BusinessRuleWhen(str, Enum):
    """Business rule execution timing"""
    BEFORE = "before"
    AFTER = "after"
    ASYNC = "async"
    DISPLAY = "display"


class ScriptType(str, Enum):
    """ServiceNow script types"""
    BUSINESS_RULE = "business_rule"
    SCRIPT_INCLUDE = "script_include"
    UI_SCRIPT = "ui_script"
    CLIENT_SCRIPT = "client_script"


class HealthStatus(str, Enum):
    """Health check status values"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


# Validation mixins
class TableNameValidationMixin:
    """Mixin for table name validation"""
    
    @field_validator('table_name')
    @classmethod
    def validate_table_name(cls, v: str) -> str:
        """Validate ServiceNow table name format"""
        if not v or not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Table name must be alphanumeric with underscores or hyphens")
        return v.lower()


class ScopeValidationMixin:
    """Mixin for scope validation"""
    
    @field_validator('scope')
    @classmethod
    def validate_scope(cls, v: str) -> str:
        """Validate ServiceNow scope format"""
        if v and not v.startswith('x_'):
            raise ValueError("Custom scope must start with 'x_'")
        return v


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
    limit: int = Field(
        100, 
        ge=FieldLimits.QUERY_LIMIT_MIN, 
        le=FieldLimits.QUERY_LIMIT_MAX, 
        description="Maximum records to return"
    )
    display: bool = Field(False, description="Return display values")
    env: Environment = Field(Environment.DEV, description="Environment (dev/test/prod)")

    @field_validator('table')
    @classmethod
    def validate_table(cls, v: str) -> str:
        """Validate table name format"""
        if not v or not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Table name must be alphanumeric with underscores/hyphens")
        return v.lower()


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
    short_description: str = Field(
        ..., 
        min_length=1, 
        max_length=FieldLimits.SHORT_DESCRIPTION_MAX,
        description="Brief description of the incident"
    )
    description: Optional[str] = Field(
        None, 
        max_length=FieldLimits.DESCRIPTION_MAX,
        description="Detailed description of the incident"
    )
    additional_fields: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional fields to set on the incident"
    )
    env: Environment = Field(Environment.DEV, description="Environment")


class CreateTableParams(BaseModel, TableNameValidationMixin, ScopeValidationMixin):
    """Parameters for create_table tool"""
    table_label: str = Field(
        ..., 
        min_length=1, 
        max_length=FieldLimits.FIELD_NAME_MAX,
        description="Display label for the table"
    )
    table_name: str = Field(
        ..., 
        min_length=1, 
        max_length=FieldLimits.TABLE_NAME_MAX,
        description="Technical table name"
    )
    extends: Optional[str] = Field(None, description="Parent table to extend")
    scope: Optional[str] = Field("x_cloudorch_aiops", description="Application scope")
    dry_run: bool = Field(False, description="Preview changes without executing")
    env: Environment = Field(Environment.DEV, description="Environment")


class CreateTableWithNavigationParams(BaseModel, TableNameValidationMixin, ScopeValidationMixin):
    """Parameters for create_table_with_navigation_enhanced tool"""
    table_label: str = Field(
        ..., 
        min_length=1, 
        max_length=FieldLimits.FIELD_NAME_MAX, 
        description="Display label for the table"
    )
    table_name: str = Field(
        ..., 
        min_length=1, 
        max_length=FieldLimits.TABLE_NAME_MAX, 
        description="Technical table name"
    )
    extends: Optional[str] = Field(None, description="Parent table to extend")
    scope: str = Field("x_cloudorch_aiops", description="Application scope")
    create_navigation: bool = Field(True, description="Create navigation module for the table")
    dry_run: bool = Field(False, description="Preview changes without executing")
    env: Environment = Field(Environment.DEV, description="Environment (dev/test/prod)")


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
    type: ScriptType
    table: Optional[str] = None
    active: bool = True
    script: str
    api_name: Optional[str] = None
    when: Optional[BusinessRuleWhen] = None


# Enhanced MCP Protocol Models
class ClientCapabilities(BaseModel):
    """Client capabilities for protocol negotiation"""
    streaming: bool = Field(False, description="Supports streaming responses")
    batch_operations: bool = Field(False, description="Supports batch operations")
    subscriptions: bool = Field(False, description="Supports real-time subscriptions")
    compression: bool = Field(False, description="Supports response compression")
    max_batch_size: Optional[int] = Field(None, description="Maximum batch operation size")
    protocol_version: str = Field("1.0", description="MCP protocol version")


class StreamingRequest(BaseModel):
    """Request for streaming response"""
    tool_name: str = Field(..., description="Tool to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    chunk_size: int = Field(
        100, 
        ge=FieldLimits.CHUNK_SIZE_MIN, 
        le=FieldLimits.CHUNK_SIZE_MAX, 
        description="Records per chunk"
    )
    stream_id: Optional[str] = Field(None, description="Stream identifier")


class StreamingChunk(BaseModel):
    """Individual chunk in streaming response"""
    stream_id: str = Field(..., description="Stream identifier")
    chunk_index: int = Field(..., description="Chunk sequence number")
    total_chunks: Optional[int] = Field(None, description="Total expected chunks")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Chunk data")
    is_final: bool = Field(False, description="Is this the final chunk")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Chunk metadata")


class BatchRequest(BaseModel):
    """Request for batch operations"""
    operations: List[Dict[str, Any]] = Field(
        ..., 
        min_items=FieldLimits.BATCH_SIZE_MIN, 
        max_items=FieldLimits.BATCH_SIZE_MAX, 
        description="Batch operations"
    )
    batch_id: Optional[str] = Field(None, description="Batch identifier")
    fail_fast: bool = Field(True, description="Stop on first error")
    parallel: bool = Field(False, description="Execute operations in parallel")


class BatchResponse(BaseModel):
    """Response for batch operations"""
    batch_id: str = Field(..., description="Batch identifier")
    total_operations: int = Field(..., description="Total operations in batch")
    successful_operations: int = Field(..., description="Number of successful operations")
    failed_operations: int = Field(..., description="Number of failed operations")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Operation results")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Operation errors")
    execution_time_ms: float = Field(..., description="Total execution time")


# Server Info Models
class ServerCapabilities(BaseModel):
    """MCP server capabilities"""
    tools: Dict[str, Any] = Field(default_factory=dict)
    resources: Dict[str, Any] = Field(default_factory=dict)
    prompts: Dict[str, Any] = Field(default_factory=dict)
    # Enhanced capabilities
    streaming: bool = Field(True, description="Supports streaming responses")
    batch_operations: bool = Field(True, description="Supports batch operations")
    subscriptions: bool = Field(False, description="Supports real-time subscriptions")
    compression: bool = Field(False, description="Supports response compression")
    max_batch_size: int = Field(100, description="Maximum batch operation size")
    max_stream_chunk_size: int = Field(1000, description="Maximum streaming chunk size")
    protocol_extensions: List[str] = Field(default_factory=lambda: ["streaming", "batch", "capability_negotiation"])


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
    status: HealthStatus
    timestamp: datetime
    environment: Environment
    connection_status: Dict[str, bool]
    response_time_ms: Optional[float] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)