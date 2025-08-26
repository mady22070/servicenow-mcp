"""
Constants for ServiceNow MCP server
"""

from enum import Enum


class ServiceNowAPI:
    """ServiceNow API endpoint constants"""
    
    # Base API paths
    TABLE_API = "/api/now/table"
    STATS_API = "/api/now/stats"
    ATTACHMENT_API = "/api/now/attachment"
    ATTACHMENT_FILE_API = "/api/now/attachment/file"
    
    # Common parameters
    PARAM_LIMIT = "sysparm_limit"
    PARAM_QUERY = "sysparm_query"
    PARAM_FIELDS = "sysparm_fields"
    PARAM_DISPLAY_VALUE = "sysparm_display_value"
    PARAM_GROUP_BY = "sysparm_group_by"
    PARAM_COUNT = "sysparm_count"
    PARAM_SUM_FIELDS = "sysparm_sum_fields"
    PARAM_AVG_FIELDS = "sysparm_avg_fields"
    PARAM_MIN_FIELDS = "sysparm_min_fields"
    PARAM_MAX_FIELDS = "sysparm_max_fields"


class HTTPStatus:
    """HTTP status code constants"""
    
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503


class ServiceNowTables:
    """Common ServiceNow table names"""
    
    # Core tables
    INCIDENT = "incident"
    PROBLEM = "problem"
    CHANGE_REQUEST = "change_request"
    
    # System tables
    SYS_USER = "sys_user"
    SYS_SCRIPT = "sys_script"
    SYS_SCRIPT_INCLUDE = "sys_script_include"
    SYS_DICTIONARY = "sys_dictionary"
    SYS_CHOICE = "sys_choice"
    SYS_DB_OBJECT = "sys_db_object"
    SYS_ATTACHMENT = "sys_attachment"
    
    # CMDB tables
    CMDB_CI = "cmdb_ci"
    CMDB_REL_CI = "cmdb_rel_ci"
    
    # Monitoring tables
    SYSLOG_TRANSACTION = "syslog_transaction"
    SYS_EXECUTION_TRACKER = "sys_execution_tracker"
    ECC_QUEUE = "ecc_queue"
    EM_EVENT = "em_event"
    
    # Service Catalog
    ITEM_OPTION_NEW = "item_option_new"
    QUESTION_CHOICE = "question_choice"
    SC_CAT_ITEM_CLIENT_SCRIPT = "sc_cat_item_client_script"


class DefaultValues:
    """Default values for various operations"""
    
    # Environment
    ENVIRONMENT = "dev"
    SCOPE = "x_cloudorch_aiops"
    
    # Query limits
    DEFAULT_QUERY_LIMIT = 100
    MAX_QUERY_LIMIT = 10000
    DEFAULT_ATTACHMENT_LIMIT = 50
    
    # Timeouts
    DEFAULT_TIMEOUT = 30
    DEFAULT_SINCE_MINUTES = 60
    
    # Performance
    DEFAULT_CHUNK_SIZE = 8192
    DEFAULT_BATCH_SIZE = 100
    
    # CI Graph
    DEFAULT_CI_GRAPH_DEPTH = 2
    DEFAULT_CI_GRAPH_LIMIT = 200


class ErrorCodes:
    """Error code constants"""
    
    # MCP errors
    MCP_ERROR = "mcp_error"
    VALIDATION_ERROR = "validation_error"
    AUTH_ERROR = "auth_error"
    SERVICENOW_ERROR = "servicenow_error"
    CONFIG_ERROR = "config_error"
    GUARD_ERROR = "guard_error"
    TIMEOUT_ERROR = "timeout_error"
    NOT_FOUND_ERROR = "not_found_error"
    INTERNAL_ERROR = "internal_error"
    GENERAL_ERROR = "general_error"
    
    # ServiceNow specific
    NON_JSON_RESPONSE = "non_json_response"
    TABLE_NOT_FOUND = "table_not_found"
    RECORD_NOT_FOUND = "record_not_found"
    FIELD_NOT_FOUND = "field_not_found"
    PERMISSION_DENIED = "permission_denied"


class LogLevels:
    """Logging level constants"""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class BusinessRuleWhen(str, Enum):
    """Business rule execution timing"""
    BEFORE = "before"
    AFTER = "after"
    ASYNC = "async"
    DISPLAY = "display"


class ScriptTypes(str, Enum):
    """ServiceNow script types"""
    BUSINESS_RULE = "business_rule"
    SCRIPT_INCLUDE = "script_include"
    UI_SCRIPT = "ui_script"
    CLIENT_SCRIPT = "client_script"


class FieldTypes:
    """ServiceNow field types"""
    
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "glide_date"
    DATETIME = "glide_date_time"
    REFERENCE = "reference"
    CHOICE = "choice"
    EMAIL = "email"
    URL = "url"
    PHONE = "phone_number"
    CURRENCY = "currency"
    PERCENT = "percent_complete"
    DURATION = "glide_duration"
    JOURNAL = "journal"
    JOURNAL_INPUT = "journal_input"
    HTML = "html"
    SCRIPT = "script"
    CONDITIONS = "conditions"
    WORKFLOW = "workflow"


class Environments(str, Enum):
    """Supported environments"""
    DEV = "dev"
    TEST = "test"
    PROD = "prod"


class HealthStatus(str, Enum):
    """Health check status values"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class CIRelationshipDirections:
    """CI relationship direction constants"""
    UP = "up"
    DOWN = "down"
    BOTH = "both"


class Headers:
    """HTTP header constants"""
    
    ACCEPT = "Accept"
    CONTENT_TYPE = "Content-Type"
    USER_AGENT = "User-Agent"
    AUTHORIZATION = "Authorization"
    
    # Values
    APPLICATION_JSON = "application/json"
    MULTIPART_FORM_DATA = "multipart/form-data"
    APPLICATION_OCTET_STREAM = "application/octet-stream"
    
    # User agent
    MCP_USER_AGENT = "ServiceNow-MCP-Client/0.8.0"


class CacheKeys:
    """Cache key prefixes"""
    
    TABLE_SCHEMA = "schema"
    TABLE_FIELDS = "fields"
    USER_INFO = "user"
    SYSTEM_PROPERTIES = "sysprop"
    CHOICE_LIST = "choices"


class ValidationMessages:
    """Validation error messages"""
    
    EMPTY_TABLE_NAME = "Table name cannot be empty"
    EMPTY_SYS_ID = "sys_id cannot be empty"
    EMPTY_DATA = "Data cannot be empty"
    EMPTY_FILE_PATH = "file_path cannot be empty"
    EMPTY_OUT_PATH = "out_path cannot be empty"
    EMPTY_ATTACHMENT_ID = "attachment_sys_id cannot be empty"
    
    INVALID_DATA_TYPE = "Data must be a dictionary"
    INVALID_LIMIT = "Limit must be greater than 0"
    LIMIT_EXCEEDED = "Limit cannot exceed 10000"
    
    INVALID_TABLE_NAME = "Table name must be alphanumeric with underscores/hyphens"
    INVALID_FIELD_NAME = "Field name must be alphanumeric with underscores"