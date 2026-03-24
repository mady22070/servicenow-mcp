"""
Comprehensive error handling for ServiceNow MCP server with pattern analysis
"""

from __future__ import annotations
from typing import Any, Dict, Optional, Type, Union, List, Tuple
from functools import wraps
import traceback
import sys
import json
import hashlib
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from pathlib import Path

from .models import MCPError, MCPResponse
from .logging_config import get_logger


class MCPException(Exception):
    """Base exception for MCP operations"""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "mcp_error",
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.utcnow()


class ValidationError(MCPException):
    """Validation error for input parameters"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
            
        super().__init__(message, "validation_error", details)


class AuthenticationError(MCPException):
    """Authentication/authorization error"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "auth_error")


class ServiceNowError(MCPException):
    """ServiceNow API error"""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        details = {}
        if status_code:
            details["status_code"] = status_code
        if response_data:
            details["response_data"] = response_data
            
        super().__init__(message, "servicenow_error", details)


class ConfigurationError(MCPException):
    """Configuration error"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        details = {}
        if config_key:
            details["config_key"] = config_key
            
        super().__init__(message, "config_error", details)


class GuardError(MCPException):
    """Security guard error"""
    
    def __init__(self, message: str, table: Optional[str] = None, operation: Optional[str] = None):
        details = {}
        if table:
            details["table"] = table
        if operation:
            details["operation"] = operation
            
        super().__init__(message, "guard_error", details)


class TimeoutError(MCPException):
    """Operation timeout error"""
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None):
        details = {}
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
            
        super().__init__(message, "timeout_error", details)


@dataclass
class ErrorPattern:
    """Represents a recognized error pattern"""
    pattern_id: str
    error_type: str
    message_patterns: List[str]
    frequency: int
    first_seen: datetime
    last_seen: datetime
    resolution_success_rate: float
    common_contexts: Dict[str, Any]
    resolution_strategies: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ErrorOccurrence:
    """Represents a single error occurrence"""
    occurrence_id: str
    error_type: str
    message: str
    operation: str
    table: Optional[str]
    context: Dict[str, Any]
    timestamp: datetime
    resolution_attempted: bool
    resolution_successful: bool
    resolution_strategy: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ErrorPatternRecognizer:
    """Recognizes and classifies error patterns"""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.logger = get_logger()
        self.storage_path = Path(storage_path or "error_patterns.json")
        self.patterns: Dict[str, ErrorPattern] = {}
        self.occurrences: List[ErrorOccurrence] = []
        self.similarity_threshold = 0.8
        self._load_patterns()
    
    def analyze_error(self, error: Exception, operation: str, table: Optional[str] = None,
                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze error and classify it into patterns"""
        
        error_message = str(error)
        error_type = type(error).__name__
        
        # Create occurrence record
        occurrence = ErrorOccurrence(
            occurrence_id=self._generate_occurrence_id(error_message, operation),
            error_type=error_type,
            message=error_message,
            operation=operation,
            table=table,
            context=context or {},
            timestamp=datetime.utcnow(),
            resolution_attempted=False,
            resolution_successful=False,
            resolution_strategy=None
        )
        
        # Find matching pattern or create new one
        pattern_id = self._find_or_create_pattern(occurrence)
        
        # Update pattern statistics
        self._update_pattern_stats(pattern_id, occurrence)
        
        # Store occurrence
        self.occurrences.append(occurrence)
        
        # Generate analysis
        analysis = self._generate_error_analysis(pattern_id, occurrence)
        
        # Save patterns periodically
        if len(self.occurrences) % 10 == 0:
            self._save_patterns()
        
        return analysis
    
    def get_similar_errors(self, error_message: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar errors from history"""
        
        similarities = []
        
        for occurrence in self.occurrences[-100:]:  # Check recent occurrences
            similarity = self._calculate_similarity(error_message, occurrence.message)
            if similarity > self.similarity_threshold:
                similarities.append({
                    'occurrence': occurrence.to_dict(),
                    'similarity': similarity,
                    'pattern_id': self._find_pattern_for_occurrence(occurrence)
                })
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:limit]
    
    def get_pattern_trends(self, days: int = 7) -> Dict[str, Any]:
        """Analyze error pattern trends over time"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_occurrences = [
            occ for occ in self.occurrences 
            if occ.timestamp > cutoff_date
        ]
        
        # Count occurrences by pattern
        pattern_counts = Counter()
        for occurrence in recent_occurrences:
            pattern_id = self._find_pattern_for_occurrence(occurrence)
            if pattern_id:
                pattern_counts[pattern_id] += 1
        
        # Calculate trends
        trends = {}
        for pattern_id, count in pattern_counts.items():
            pattern = self.patterns.get(pattern_id)
            if pattern:
                trends[pattern_id] = {
                    'pattern': pattern.to_dict(),
                    'recent_count': count,
                    'trend': 'increasing' if count > pattern.frequency / 7 else 'stable'
                }
        
        return {
            'period_days': days,
            'total_errors': len(recent_occurrences),
            'unique_patterns': len(trends),
            'trends': trends
        }
    
    def predict_error_likelihood(self, operation: str, table: Optional[str] = None,
                               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Predict likelihood of errors for given operation"""
        
        # Find similar historical operations
        similar_ops = [
            occ for occ in self.occurrences
            if occ.operation == operation and (not table or occ.table == table)
        ]
        
        if not similar_ops:
            return {
                'error_likelihood': 0.0,
                'confidence': 0.0,
                'predicted_errors': [],
                'recommendations': ['No historical data available for this operation']
            }
        
        # Calculate error rate
        total_ops = len(similar_ops)
        error_rate = total_ops / max(total_ops * 10, 100)  # Assume 10x more successful ops
        
        # Find most common error patterns
        pattern_counts = Counter()
        for occurrence in similar_ops:
            pattern_id = self._find_pattern_for_occurrence(occurrence)
            if pattern_id:
                pattern_counts[pattern_id] += 1
        
        predicted_errors = []
        for pattern_id, count in pattern_counts.most_common(3):
            pattern = self.patterns.get(pattern_id)
            if pattern:
                predicted_errors.append({
                    'pattern_id': pattern_id,
                    'error_type': pattern.error_type,
                    'likelihood': count / total_ops,
                    'resolution_success_rate': pattern.resolution_success_rate,
                    'common_strategies': pattern.resolution_strategies
                })
        
        return {
            'error_likelihood': min(error_rate, 1.0),
            'confidence': min(total_ops / 50, 1.0),  # Higher confidence with more data
            'predicted_errors': predicted_errors,
            'recommendations': self._generate_prevention_recommendations(predicted_errors)
        }
    
    def learn_from_resolution(self, occurrence_id: str, strategy: str, successful: bool):
        """Learn from error resolution attempts"""
        
        # Find the occurrence
        occurrence = None
        for occ in self.occurrences:
            if occ.occurrence_id == occurrence_id:
                occurrence = occ
                break
        
        if not occurrence:
            self.logger.warning(f"Occurrence {occurrence_id} not found for learning")
            return
        
        # Update occurrence
        occurrence.resolution_attempted = True
        occurrence.resolution_successful = successful
        occurrence.resolution_strategy = strategy
        
        # Update pattern statistics
        pattern_id = self._find_pattern_for_occurrence(occurrence)
        if pattern_id and pattern_id in self.patterns:
            pattern = self.patterns[pattern_id]
            
            # Update resolution strategies
            if strategy not in pattern.resolution_strategies:
                pattern.resolution_strategies.append(strategy)
            
            # Update success rate (simple moving average)
            if successful:
                pattern.resolution_success_rate = (
                    pattern.resolution_success_rate * 0.9 + 0.1
                )
            else:
                pattern.resolution_success_rate = (
                    pattern.resolution_success_rate * 0.9
                )
        
        self._save_patterns()
    
    def _generate_occurrence_id(self, message: str, operation: str) -> str:
        """Generate unique ID for error occurrence"""
        content = f"{message}:{operation}:{datetime.utcnow().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _find_or_create_pattern(self, occurrence: ErrorOccurrence) -> str:
        """Find existing pattern or create new one"""
        
        # Look for similar patterns
        for pattern_id, pattern in self.patterns.items():
            if self._matches_pattern(occurrence, pattern):
                return pattern_id
        
        # Create new pattern
        pattern_id = self._generate_pattern_id(occurrence)
        self.patterns[pattern_id] = ErrorPattern(
            pattern_id=pattern_id,
            error_type=occurrence.error_type,
            message_patterns=[occurrence.message],
            frequency=0,
            first_seen=occurrence.timestamp,
            last_seen=occurrence.timestamp,
            resolution_success_rate=0.5,  # Start with neutral success rate
            common_contexts={},
            resolution_strategies=[]
        )
        
        return pattern_id
    
    def _generate_pattern_id(self, occurrence: ErrorOccurrence) -> str:
        """Generate unique pattern ID"""
        content = f"{occurrence.error_type}:{occurrence.operation}:{occurrence.message[:50]}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _matches_pattern(self, occurrence: ErrorOccurrence, pattern: ErrorPattern) -> bool:
        """Check if occurrence matches existing pattern"""
        
        # Must be same error type
        if occurrence.error_type != pattern.error_type:
            return False
        
        # Check message similarity
        for pattern_msg in pattern.message_patterns:
            if self._calculate_similarity(occurrence.message, pattern_msg) > self.similarity_threshold:
                return True
        
        return False
    
    def _calculate_similarity(self, msg1: str, msg2: str) -> float:
        """Calculate similarity between two error messages"""
        
        # Simple token-based similarity
        tokens1 = set(re.findall(r'\w+', msg1.lower()))
        tokens2 = set(re.findall(r'\w+', msg2.lower()))
        
        if not tokens1 and not tokens2:
            return 1.0
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        return len(intersection) / len(union)
    
    def _update_pattern_stats(self, pattern_id: str, occurrence: ErrorOccurrence):
        """Update pattern statistics with new occurrence"""
        
        pattern = self.patterns[pattern_id]
        pattern.frequency += 1
        pattern.last_seen = occurrence.timestamp
        
        # Add message pattern if significantly different
        is_new_pattern = True
        for existing_msg in pattern.message_patterns:
            if self._calculate_similarity(occurrence.message, existing_msg) > 0.9:
                is_new_pattern = False
                break
        
        if is_new_pattern and len(pattern.message_patterns) < 5:
            pattern.message_patterns.append(occurrence.message)
        
        # Update common contexts
        for key, value in occurrence.context.items():
            if key not in pattern.common_contexts:
                pattern.common_contexts[key] = {}
            
            str_value = str(value)
            if str_value not in pattern.common_contexts[key]:
                pattern.common_contexts[key][str_value] = 0
            pattern.common_contexts[key][str_value] += 1
    
    def _find_pattern_for_occurrence(self, occurrence: ErrorOccurrence) -> Optional[str]:
        """Find pattern ID for given occurrence"""
        
        for pattern_id, pattern in self.patterns.items():
            if self._matches_pattern(occurrence, pattern):
                return pattern_id
        return None
    
    def _generate_error_analysis(self, pattern_id: str, occurrence: ErrorOccurrence) -> Dict[str, Any]:
        """Generate comprehensive error analysis"""
        
        pattern = self.patterns[pattern_id]
        
        # Get similar errors
        similar_errors = self.get_similar_errors(occurrence.message, limit=3)
        
        # Generate recommendations
        recommendations = []
        if pattern.resolution_strategies:
            recommendations.extend([
                f"Try resolution strategy: {strategy}" 
                for strategy in pattern.resolution_strategies[:3]
            ])
        
        if pattern.resolution_success_rate > 0.7:
            recommendations.append("This error pattern has high resolution success rate")
        elif pattern.resolution_success_rate < 0.3:
            recommendations.append("This error pattern is difficult to resolve - consider alternative approaches")
        
        return {
            'pattern_id': pattern_id,
            'error_classification': {
                'type': occurrence.error_type,
                'frequency': pattern.frequency,
                'first_seen': pattern.first_seen.isoformat(),
                'last_seen': pattern.last_seen.isoformat(),
                'resolution_success_rate': pattern.resolution_success_rate
            },
            'similar_errors': similar_errors,
            'recommendations': recommendations,
            'resolution_strategies': pattern.resolution_strategies,
            'common_contexts': pattern.common_contexts,
            'occurrence_id': occurrence.occurrence_id
        }
    
    def _generate_prevention_recommendations(self, predicted_errors: List[Dict]) -> List[str]:
        """Generate prevention recommendations based on predicted errors"""
        
        recommendations = []
        
        for error in predicted_errors:
            if error['likelihood'] > 0.3:
                recommendations.append(
                    f"High risk of {error['error_type']} - consider preventive measures"
                )
            
            if error['resolution_success_rate'] < 0.5:
                recommendations.append(
                    f"Difficult to resolve {error['error_type']} - validate inputs carefully"
                )
        
        if not recommendations:
            recommendations.append("Low error risk for this operation")
        
        return recommendations
    
    def _load_patterns(self):
        """Load patterns from storage"""
        
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # Load patterns
            for pattern_data in data.get('patterns', []):
                pattern = ErrorPattern(
                    pattern_id=pattern_data['pattern_id'],
                    error_type=pattern_data['error_type'],
                    message_patterns=pattern_data['message_patterns'],
                    frequency=pattern_data['frequency'],
                    first_seen=datetime.fromisoformat(pattern_data['first_seen']),
                    last_seen=datetime.fromisoformat(pattern_data['last_seen']),
                    resolution_success_rate=pattern_data['resolution_success_rate'],
                    common_contexts=pattern_data['common_contexts'],
                    resolution_strategies=pattern_data['resolution_strategies']
                )
                self.patterns[pattern.pattern_id] = pattern
            
            # Load recent occurrences (last 1000)
            for occ_data in data.get('occurrences', [])[-1000:]:
                occurrence = ErrorOccurrence(
                    occurrence_id=occ_data['occurrence_id'],
                    error_type=occ_data['error_type'],
                    message=occ_data['message'],
                    operation=occ_data['operation'],
                    table=occ_data.get('table'),
                    context=occ_data['context'],
                    timestamp=datetime.fromisoformat(occ_data['timestamp']),
                    resolution_attempted=occ_data['resolution_attempted'],
                    resolution_successful=occ_data['resolution_successful'],
                    resolution_strategy=occ_data.get('resolution_strategy')
                )
                self.occurrences.append(occurrence)
            
            self.logger.info(f"Loaded {len(self.patterns)} error patterns and {len(self.occurrences)} occurrences")
            
        except Exception as e:
            self.logger.error(f"Failed to load error patterns: {e}")
    
    def _save_patterns(self):
        """Save patterns to storage"""
        
        try:
            # Prepare data for serialization
            data = {
                'patterns': [pattern.to_dict() for pattern in self.patterns.values()],
                'occurrences': [occ.to_dict() for occ in self.occurrences[-1000:]]  # Keep last 1000
            }
            
            # Convert datetime objects to ISO strings
            for pattern_data in data['patterns']:
                pattern_data['first_seen'] = pattern_data['first_seen'].isoformat()
                pattern_data['last_seen'] = pattern_data['last_seen'].isoformat()
            
            for occ_data in data['occurrences']:
                occ_data['timestamp'] = occ_data['timestamp'].isoformat()
            
            # Save to file
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.debug(f"Saved {len(self.patterns)} error patterns")
            
        except Exception as e:
            self.logger.error(f"Failed to save error patterns: {e}")


# Global pattern recognizer instance
_pattern_recognizer = ErrorPatternRecognizer()


class ResourceNotFoundError(MCPException):
    """Resource not found error"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
            
        super().__init__(message, "not_found_error", details)


def create_error_response(
    error: Union[Exception, MCPException, str],
    operation: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    table: Optional[str] = None
) -> MCPResponse:
    """
    Create a standardized error response with pattern analysis
    
    Args:
        error: Exception or error message
        operation: Operation that failed
        context: Additional context information
        table: Table involved in the operation
        
    Returns:
        MCPResponse with error details and pattern analysis
    """
    logger = get_logger()
    
    # Analyze error pattern if it's an actual exception
    pattern_analysis = None
    if isinstance(error, Exception) and operation:
        try:
            pattern_analysis = _pattern_recognizer.analyze_error(
                error, operation, table, context
            )
        except Exception as e:
            logger.warning(f"Failed to analyze error pattern: {e}")
    
    if isinstance(error, MCPException):
        mcp_error = MCPError(
            error=error.error_code,
            message=error.message,
            details=error.details
        )
        
        # Add context if provided
        if context:
            mcp_error.details.update(context)
            
        # Add operation if provided
        if operation:
            mcp_error.details["operation"] = operation
            
        # Add pattern analysis
        if pattern_analysis:
            mcp_error.details["pattern_analysis"] = pattern_analysis
            
        # Log the error
        logger.error(f"MCP Error in {operation or 'unknown'}: {error.message}", extra={
            "operation": operation,
            "error_code": error.error_code,
            "details": error.details,
            "pattern_analysis": pattern_analysis
        })
        
    elif isinstance(error, Exception):
        # Convert generic exception to MCP error
        error_details = {
            "exception_type": type(error).__name__,
            "traceback": traceback.format_exc()
        }
        
        if context:
            error_details.update(context)
            
        if operation:
            error_details["operation"] = operation
            
        # Add pattern analysis
        if pattern_analysis:
            error_details["pattern_analysis"] = pattern_analysis
            
        mcp_error = MCPError(
            error="internal_error",
            message=str(error),
            details=error_details
        )
        
        # Log the error
        logger.error(f"Unexpected error in {operation or 'unknown'}: {str(error)}", extra={
            "operation": operation,
            "exception_type": type(error).__name__,
            "traceback": traceback.format_exc(),
            "pattern_analysis": pattern_analysis
        })
        
    else:
        # String error message
        error_details = {}
        if context:
            error_details.update(context)
        if operation:
            error_details["operation"] = operation
            
        mcp_error = MCPError(
            error="general_error",
            message=str(error),
            details=error_details
        )
        
        # Log the error
        logger.error(f"Error in {operation or 'unknown'}: {str(error)}", extra={
            "operation": operation,
            "message": str(error)
        })
    
    return MCPResponse(
        success=False,
        error=mcp_error,
        metadata={
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "operation": operation,
            "pattern_analysis": pattern_analysis
        }
    )


def handle_errors(operation: Optional[str] = None):
    """
    Decorator for comprehensive error handling
    
    Args:
        operation: Name of the operation for logging
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # If result is already an MCPResponse with error, return as-is
                if isinstance(result, dict) and result.get("error"):
                    return result
                    
                # Wrap successful result in MCPResponse if not already wrapped
                if not isinstance(result, dict) or "success" not in result:
                    return MCPResponse(
                        success=True,
                        data=result if isinstance(result, dict) else {"result": result},
                        metadata={
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "operation": operation or func.__name__
                        }
                    ).dict()
                
                return result
                
            except MCPException as e:
                return create_error_response(e, operation or func.__name__).dict()
                
            except Exception as e:
                return create_error_response(e, operation or func.__name__).dict()
                
        return wrapper
    return decorator


def validate_parameters(model_class: Type):
    """
    Decorator for parameter validation using Pydantic models
    
    Args:
        model_class: Pydantic model class for validation
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Validate parameters using the model
                validated_params = model_class(**kwargs)
                
                # Replace kwargs with validated parameters
                return func(*args, **validated_params.dict())
                
            except Exception as e:
                if "validation error" in str(e).lower():
                    raise ValidationError(f"Parameter validation failed: {str(e)}")
                raise
                
        return wrapper
    return decorator


def safe_execute(func, *args, **kwargs) -> Dict[str, Any]:
    """
    Safely execute a function with error handling
    
    Args:
        func: Function to execute
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Dictionary with success/error information
    """
    try:
        result = func(*args, **kwargs)
        return {
            "success": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger = get_logger()
        logger.error(f"Safe execution failed: {str(e)}", extra={
            "function": func.__name__ if hasattr(func, '__name__') else str(func),
            "args": str(args)[:200],  # Truncate long args
            "kwargs": str(kwargs)[:200]  # Truncate long kwargs
        })
        
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


def log_and_raise(
    exception_class: Type[MCPException],
    message: str,
    operation: Optional[str] = None,
    **kwargs
):
    """
    Log an error and raise an exception
    
    Args:
        exception_class: Exception class to raise
        message: Error message
        operation: Operation name for logging
        **kwargs: Additional arguments for the exception
    """
    logger = get_logger()
    
    logger.error(f"Raising {exception_class.__name__}: {message}", extra={
        "operation": operation,
        "exception_class": exception_class.__name__,
        "message": message
    })
    
    raise exception_class(message, **kwargs)


# Pattern Recognition Functions

def analyze_error_pattern(error: Exception, operation: str, table: Optional[str] = None,
                         context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Analyze error and return pattern information
    
    Args:
        error: Exception to analyze
        operation: Operation that failed
        table: Table involved in operation
        context: Additional context
        
    Returns:
        Dictionary with pattern analysis
    """
    return _pattern_recognizer.analyze_error(error, operation, table, context)


def get_similar_errors(error_message: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Find similar errors from history
    
    Args:
        error_message: Error message to find similarities for
        limit: Maximum number of similar errors to return
        
    Returns:
        List of similar error occurrences
    """
    return _pattern_recognizer.get_similar_errors(error_message, limit)


def get_error_trends(days: int = 7) -> Dict[str, Any]:
    """
    Get error pattern trends over specified period
    
    Args:
        days: Number of days to analyze
        
    Returns:
        Dictionary with trend analysis
    """
    return _pattern_recognizer.get_pattern_trends(days)


def predict_error_likelihood(operation: str, table: Optional[str] = None,
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Predict likelihood of errors for given operation
    
    Args:
        operation: Operation to predict errors for
        table: Table involved in operation
        context: Additional context
        
    Returns:
        Dictionary with error predictions
    """
    return _pattern_recognizer.predict_error_likelihood(operation, table, context)


def learn_from_resolution(occurrence_id: str, strategy: str, successful: bool):
    """
    Learn from error resolution attempts
    
    Args:
        occurrence_id: ID of the error occurrence
        strategy: Resolution strategy used
        successful: Whether the resolution was successful
    """
    _pattern_recognizer.learn_from_resolution(occurrence_id, strategy, successful)


def get_error_statistics() -> Dict[str, Any]:
    """
    Get comprehensive error statistics
    
    Returns:
        Dictionary with error statistics
    """
    patterns = _pattern_recognizer.patterns
    occurrences = _pattern_recognizer.occurrences
    
    # Calculate statistics
    total_patterns = len(patterns)
    total_occurrences = len(occurrences)
    
    # Most common error types
    error_type_counts = Counter()
    for pattern in patterns.values():
        error_type_counts[pattern.error_type] += pattern.frequency
    
    # Resolution success rates by error type
    success_rates = {}
    for error_type in error_type_counts.keys():
        type_patterns = [p for p in patterns.values() if p.error_type == error_type]
        if type_patterns:
            avg_success_rate = sum(p.resolution_success_rate for p in type_patterns) / len(type_patterns)
            success_rates[error_type] = avg_success_rate
    
    # Recent activity (last 24 hours)
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_occurrences = [occ for occ in occurrences if occ.timestamp > recent_cutoff]
    
    return {
        'total_patterns': total_patterns,
        'total_occurrences': total_occurrences,
        'most_common_errors': dict(error_type_counts.most_common(5)),
        'resolution_success_rates': success_rates,
        'recent_activity': {
            'last_24h_occurrences': len(recent_occurrences),
            'active_patterns': len(set(
                _pattern_recognizer._find_pattern_for_occurrence(occ) 
                for occ in recent_occurrences
            ))
        }
    }