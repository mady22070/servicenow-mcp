
"""
Comprehensive audit system for AI operations with context tracking,
compliance reporting, and anomaly detection.
"""

import json
import time
import os
import sys
import hashlib
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from contextlib import contextmanager

# Configuration with safe defaults
def _get_safe_audit_path():
    """Get a safe path for audit files with fallback options"""
    # Try user-specified path first
    if os.getenv("MCP_AUDIT_FILE"):
        return Path(os.getenv("MCP_AUDIT_FILE")).expanduser()
    
    # Try common writable locations
    for base_path in [Path.home(), Path("/tmp"), Path(".")]:
        try:
            audit_path = base_path / "servicenow_mcp_audit.log"
            # Test if we can write to this location
            audit_path.touch(exist_ok=True)
            return audit_path
        except (PermissionError, OSError):
            continue
    
    # Fallback to None (disable file logging)
    return None

def _get_safe_db_path():
    """Get a safe path for audit database with fallback options"""
    # Try user-specified path first
    if os.getenv("MCP_AUDIT_DB"):
        return Path(os.getenv("MCP_AUDIT_DB")).expanduser()
    
    # Try common writable locations
    for base_path in [Path.home(), Path("/tmp"), Path(".")]:
        try:
            db_path = base_path / "servicenow_mcp_audit.db"
            # Test if we can create/access the database
            db_path.parent.mkdir(parents=True, exist_ok=True)
            # Test database creation
            with sqlite3.connect(str(db_path)) as conn:
                conn.execute("SELECT 1")
            return db_path
        except (PermissionError, OSError, sqlite3.Error):
            continue
    
    # Fallback to None (disable database logging)
    return None

AUDIT_PATH = _get_safe_audit_path()
AUDIT_DB_PATH = _get_safe_db_path()
RETENTION_DAYS = int(os.getenv("MCP_AUDIT_RETENTION_DAYS", "90"))

class AuditLevel(Enum):
    """Audit severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SECURITY = "security"

class ComplianceStatus(Enum):
    """Compliance check status"""
    COMPLIANT = "compliant"
    VIOLATION = "violation"
    WARNING = "warning"
    UNKNOWN = "unknown"

@dataclass
class AuditContext:
    """Enhanced context for audit entries"""
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    ai_agent_id: Optional[str] = None
    operation_type: Optional[str] = None
    resource_accessed: Optional[str] = None
    risk_level: Optional[str] = None
    compliance_tags: Optional[List[str]] = None
    parent_operation_id: Optional[str] = None

@dataclass
class AuditEntry:
    """Structured audit entry"""
    timestamp: float
    action: str
    level: AuditLevel
    details: Dict[str, Any]
    context: AuditContext
    operation_id: str
    checksum: str
    compliance_status: ComplianceStatus = ComplianceStatus.UNKNOWN

class ComprehensiveAuditor:
    """Enhanced audit system for AI operations"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._db_available = False
        self._init_database()
        self._compliance_rules = self._load_compliance_rules()
        self._anomaly_patterns = set()
        
    def _init_database(self):
        """Initialize SQLite database for structured audit storage"""
        if AUDIT_DB_PATH is None:
            print("Warning: Audit database disabled due to permission issues", file=sys.stderr)
            return
            
        try:
            AUDIT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(str(AUDIT_DB_PATH)) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS audit_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL NOT NULL,
                        action TEXT NOT NULL,
                        level TEXT NOT NULL,
                        operation_id TEXT NOT NULL,
                        session_id TEXT,
                        user_id TEXT,
                        ai_agent_id TEXT,
                        operation_type TEXT,
                        resource_accessed TEXT,
                        risk_level TEXT,
                        compliance_status TEXT,
                        details TEXT,
                        checksum TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_entries(timestamp)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_operation_id ON audit_entries(operation_id)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_session_id ON audit_entries(session_id)
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS compliance_violations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        audit_entry_id INTEGER,
                        rule_id TEXT NOT NULL,
                        violation_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        description TEXT,
                        remediation_suggested TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (audit_entry_id) REFERENCES audit_entries (id)
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS anomaly_detections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pattern_hash TEXT NOT NULL,
                        pattern_description TEXT,
                        confidence_score REAL,
                        first_detected DATETIME,
                        last_detected DATETIME,
                        occurrence_count INTEGER DEFAULT 1,
                        risk_assessment TEXT
                    )
                """)
                
            self._db_available = True
            print(f"Audit database initialized at: {AUDIT_DB_PATH}", file=sys.stderr)
            
        except (PermissionError, OSError, sqlite3.Error) as e:
            print(f"Warning: Could not initialize audit database: {e}", file=sys.stderr)
            print("Audit logging will continue to file only", file=sys.stderr)
            self._db_available = False
    
    def _load_compliance_rules(self) -> Dict[str, Any]:
        """Load compliance rules from configuration"""
        return {
            "sensitive_operations": [
                "delete_record", "bulk_delete", "modify_acl", 
                "create_user", "modify_user_roles", "system_property_change"
            ],
            "high_risk_tables": [
                "sys_user", "sys_user_role", "sys_security_acl", 
                "sys_properties", "sys_script"
            ],
            "required_approvals": [
                "production_deployment", "security_config_change",
                "bulk_data_modification"
            ],
            "data_classification": {
                "pii_fields": ["email", "phone", "address", "ssn"],
                "sensitive_tables": ["hr_", "finance_", "legal_"]
            }
        }
    
    def log_ai_operation(
        self,
        action: str,
        details: Dict[str, Any],
        context: Optional[AuditContext] = None,
        level: AuditLevel = AuditLevel.INFO
    ) -> str:
        """Log AI operation with enhanced context tracking"""
        
        operation_id = self._generate_operation_id(action, details)
        
        if context is None:
            context = AuditContext()
        
        # Enhance context with risk assessment
        context.risk_level = self._assess_risk_level(action, details)
        
        # Create audit entry
        entry = AuditEntry(
            timestamp=time.time(),
            action=action,
            level=level,
            details=details,
            context=context,
            operation_id=operation_id,
            checksum=self._generate_checksum(action, details, operation_id),
            compliance_status=self._check_compliance(action, details, context)
        )
        
        # Store in database and log file
        with self._lock:
            self._store_audit_entry(entry)
            self._write_to_log_file(entry)
            
        # Check for anomalies
        self._detect_anomalies(entry)
        
        # Handle compliance violations
        if entry.compliance_status == ComplianceStatus.VIOLATION:
            self._handle_compliance_violation(entry)
            
        return operation_id
    
    def _generate_operation_id(self, action: str, details: Dict[str, Any]) -> str:
        """Generate unique operation ID"""
        content = f"{action}_{time.time()}_{hash(str(details))}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _generate_checksum(self, action: str, details: Dict[str, Any], operation_id: str) -> str:
        """Generate integrity checksum for audit entry"""
        content = f"{action}_{operation_id}_{json.dumps(details, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _assess_risk_level(self, action: str, details: Dict[str, Any]) -> str:
        """Assess risk level of operation"""
        if action in self._compliance_rules["sensitive_operations"]:
            return "HIGH"
        
        if details.get("table") in self._compliance_rules["high_risk_tables"]:
            return "HIGH"
        
        if details.get("bulk_operation", False):
            return "MEDIUM"
        
        return "LOW"
    
    def _check_compliance(
        self, 
        action: str, 
        details: Dict[str, Any], 
        context: AuditContext
    ) -> ComplianceStatus:
        """Check operation against compliance rules"""
        
        # Check for sensitive operations
        if action in self._compliance_rules["sensitive_operations"]:
            if not context.user_id:
                return ComplianceStatus.VIOLATION
        
        # Check for high-risk table access
        table = details.get("table", "")
        if any(table.startswith(prefix) for prefix in self._compliance_rules["high_risk_tables"]):
            if context.risk_level != "HIGH":
                return ComplianceStatus.WARNING
        
        # Check for PII access
        if self._contains_pii(details):
            if not details.get("pii_handling_approved", False):
                return ComplianceStatus.VIOLATION
        
        return ComplianceStatus.COMPLIANT
    
    def _contains_pii(self, details: Dict[str, Any]) -> bool:
        """Check if operation involves PII data"""
        pii_fields = self._compliance_rules["data_classification"]["pii_fields"]
        
        # Check field names
        fields = details.get("fields", [])
        if isinstance(fields, list):
            if any(field.lower() in pii_fields for field in fields):
                return True
        
        # Check table names
        table = details.get("table", "")
        sensitive_prefixes = self._compliance_rules["data_classification"]["sensitive_tables"]
        return any(table.startswith(prefix) for prefix in sensitive_prefixes)
    
    def _store_audit_entry(self, entry: AuditEntry):
        """Store audit entry in database"""
        if not self._db_available or AUDIT_DB_PATH is None:
            return
            
        try:
            with sqlite3.connect(str(AUDIT_DB_PATH)) as conn:
                conn.execute("""
                    INSERT INTO audit_entries (
                        timestamp, action, level, operation_id, session_id,
                        user_id, ai_agent_id, operation_type, resource_accessed,
                        risk_level, compliance_status, details, checksum
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.timestamp,
                    entry.action,
                    entry.level.value,
                    entry.operation_id,
                    entry.context.session_id,
                    entry.context.user_id,
                    entry.context.ai_agent_id,
                    entry.context.operation_type,
                    entry.context.resource_accessed,
                    entry.context.risk_level,
                    entry.compliance_status.value,
                    json.dumps(entry.details),
                    entry.checksum
                ))
        except (sqlite3.Error, OSError) as e:
            # Database operation failed, but continue with file logging
            pass
    
    def _write_to_log_file(self, entry: AuditEntry):
        """Write audit entry to log file for backward compatibility"""
        try:
            AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(AUDIT_PATH, "a", encoding="utf-8") as f:
                log_entry = {
                    "ts": entry.timestamp,
                    "action": entry.action,
                    "level": entry.level.value,
                    "operation_id": entry.operation_id,
                    "details": entry.details,
                    "context": asdict(entry.context),
                    "compliance_status": entry.compliance_status.value,
                    "checksum": entry.checksum
                }
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass  # Fail silently to maintain system stability
    
    def _detect_anomalies(self, entry: AuditEntry):
        """Detect anomalous patterns in audit data"""
        # Pattern: Rapid successive operations
        if self._is_rapid_operation_pattern(entry):
            self._record_anomaly("rapid_operations", entry, 0.8)
        
        # Pattern: Unusual time access
        if self._is_unusual_time_access(entry):
            self._record_anomaly("unusual_time_access", entry, 0.6)
        
        # Pattern: Privilege escalation attempt
        if self._is_privilege_escalation_pattern(entry):
            self._record_anomaly("privilege_escalation", entry, 0.9)
    
    def _is_rapid_operation_pattern(self, entry: AuditEntry) -> bool:
        """Check for rapid successive operations"""
        if not entry.context.session_id or not self._db_available or AUDIT_DB_PATH is None:
            return False
        
        try:
            # Check last 5 minutes for same session
            cutoff_time = entry.timestamp - 300  # 5 minutes
            
            with sqlite3.connect(str(AUDIT_DB_PATH)) as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM audit_entries 
                    WHERE session_id = ? AND timestamp > ?
                """, (entry.context.session_id, cutoff_time))
                
                count = cursor.fetchone()[0]
                return count > 50  # More than 50 operations in 5 minutes
        except (sqlite3.Error, OSError):
            return False
    
    def _is_unusual_time_access(self, entry: AuditEntry) -> bool:
        """Check for access during unusual hours"""
        dt = datetime.fromtimestamp(entry.timestamp)
        # Consider 10 PM to 6 AM as unusual hours
        return dt.hour >= 22 or dt.hour <= 6
    
    def _is_privilege_escalation_pattern(self, entry: AuditEntry) -> bool:
        """Check for potential privilege escalation"""
        sensitive_actions = ["modify_user_roles", "create_user", "modify_acl"]
        return (entry.action in sensitive_actions and 
                entry.context.risk_level == "HIGH")
    
    def _record_anomaly(self, pattern_type: str, entry: AuditEntry, confidence: float):
        """Record detected anomaly"""
        if not self._db_available or AUDIT_DB_PATH is None:
            return
            
        try:
            pattern_hash = hashlib.md5(f"{pattern_type}_{entry.context.session_id}".encode()).hexdigest()
            
            with sqlite3.connect(str(AUDIT_DB_PATH)) as conn:
            # Check if pattern already exists
            cursor = conn.execute("""
                SELECT id, occurrence_count FROM anomaly_detections 
                WHERE pattern_hash = ?
            """, (pattern_hash,))
            
            result = cursor.fetchone()
            
            if result:
                # Update existing pattern
                conn.execute("""
                    UPDATE anomaly_detections 
                    SET last_detected = CURRENT_TIMESTAMP,
                        occurrence_count = occurrence_count + 1
                    WHERE id = ?
                """, (result[0],))
            else:
                # Create new pattern
                conn.execute("""
                    INSERT INTO anomaly_detections (
                        pattern_hash, pattern_description, confidence_score,
                        first_detected, last_detected, risk_assessment
                    ) VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?)
                """, (
                    pattern_hash,
                    f"{pattern_type} detected for session {entry.context.session_id}",
                    confidence,
                    "HIGH" if confidence > 0.8 else "MEDIUM"
                ))
    
    def _handle_compliance_violation(self, entry: AuditEntry):
        """Handle compliance violations"""
        violation_id = self._record_compliance_violation(entry)
        
        # Log security event
        self.log_ai_operation(
            "compliance_violation_detected",
            {
                "original_operation": entry.operation_id,
                "violation_id": violation_id,
                "severity": "HIGH" if entry.level == AuditLevel.CRITICAL else "MEDIUM"
            },
            AuditContext(
                session_id=entry.context.session_id,
                operation_type="security_event"
            ),
            AuditLevel.SECURITY
        )
    
    def _record_compliance_violation(self, entry: AuditEntry) -> int:
        """Record compliance violation in database"""
        with sqlite3.connect(AUDIT_DB_PATH) as conn:
            cursor = conn.execute("""
                INSERT INTO compliance_violations (
                    rule_id, violation_type, severity, description, remediation_suggested
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                "general_compliance",
                entry.action,
                entry.level.value,
                f"Compliance violation in {entry.action}",
                "Review operation parameters and ensure proper authorization"
            ))
            
            return cursor.lastrowid
    
    def get_audit_trail(
        self,
        session_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve audit trail with filtering"""
        
        query = "SELECT * FROM audit_entries WHERE 1=1"
        params = []
        
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        
        if operation_id:
            query += " AND operation_id = ?"
            params.append(operation_id)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(AUDIT_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_compliance_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate compliance report"""
        cutoff_time = time.time() - (days * 24 * 3600)
        
        with sqlite3.connect(AUDIT_DB_PATH) as conn:
            # Total operations
            cursor = conn.execute("""
                SELECT COUNT(*) FROM audit_entries WHERE timestamp > ?
            """, (cutoff_time,))
            total_operations = cursor.fetchone()[0]
            
            # Compliance violations
            cursor = conn.execute("""
                SELECT COUNT(*) FROM audit_entries 
                WHERE timestamp > ? AND compliance_status = 'violation'
            """, (cutoff_time,))
            violations = cursor.fetchone()[0]
            
            # High-risk operations
            cursor = conn.execute("""
                SELECT COUNT(*) FROM audit_entries 
                WHERE timestamp > ? AND risk_level = 'HIGH'
            """, (cutoff_time,))
            high_risk_ops = cursor.fetchone()[0]
            
            # Anomalies detected
            cursor = conn.execute("""
                SELECT COUNT(*) FROM anomaly_detections 
                WHERE first_detected > datetime(?, 'unixepoch')
            """, (cutoff_time,))
            anomalies = cursor.fetchone()[0]
            
            return {
                "period_days": days,
                "total_operations": total_operations,
                "compliance_violations": violations,
                "high_risk_operations": high_risk_ops,
                "anomalies_detected": anomalies,
                "compliance_rate": (total_operations - violations) / max(total_operations, 1) * 100,
                "generated_at": datetime.now().isoformat()
            }
    
    def cleanup_old_entries(self, retention_days: int = None):
        """Clean up old audit entries based on retention policy"""
        if retention_days is None:
            retention_days = RETENTION_DAYS
        
        cutoff_time = time.time() - (retention_days * 24 * 3600)
        
        with sqlite3.connect(AUDIT_DB_PATH) as conn:
            # Delete old audit entries
            cursor = conn.execute("""
                DELETE FROM audit_entries WHERE timestamp < ?
            """, (cutoff_time,))
            
            deleted_count = cursor.rowcount
            
            # Clean up orphaned compliance violations
            conn.execute("""
                DELETE FROM compliance_violations 
                WHERE audit_entry_id NOT IN (SELECT id FROM audit_entries)
            """)
            
            return deleted_count

# Global auditor instance
_auditor = ComprehensiveAuditor()

# Backward compatibility functions
def log(action: str, details: dict):
    """Legacy log function for backward compatibility"""
    _auditor.log_ai_operation(action, details)

# Enhanced API functions
def log_ai_operation(
    action: str,
    details: Dict[str, Any],
    context: Optional[AuditContext] = None,
    level: AuditLevel = AuditLevel.INFO
) -> str:
    """Log AI operation with enhanced context"""
    return _auditor.log_ai_operation(action, details, context, level)

def get_audit_trail(**kwargs) -> List[Dict[str, Any]]:
    """Get audit trail with filtering"""
    return _auditor.get_audit_trail(**kwargs)

def get_compliance_report(days: int = 7) -> Dict[str, Any]:
    """Generate compliance report"""
    return _auditor.get_compliance_report(days)

def cleanup_old_entries(retention_days: int = None) -> int:
    """Clean up old audit entries"""
    return _auditor.cleanup_old_entries(retention_days)
