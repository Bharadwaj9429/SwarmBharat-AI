"""
Comprehensive Error Handling Module for SwarmBharat AI
Production-ready error handling with logging, monitoring, and user-friendly responses
"""

import logging
import traceback
import sys
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import json
from functools import wraps
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    SYSTEM = "system"
    EXTERNAL_API = "external_api"
    DATABASE = "database"
    NETWORK = "network"
    BUSINESS_LOGIC = "business_logic"
    UNKNOWN = "unknown"

class SwarmBharatError(Exception):
    """Base exception for SwarmBharat AI system"""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, user_message: str = None,
                 error_code: str = None, context: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.user_message = user_message or "An error occurred. Please try again."
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.context = context or {}
        self.timestamp = datetime.now()
        self.traceback_str = traceback.format_exc()

class ValidationError(SwarmBharatError):
    """Validation errors"""
    
    def __init__(self, message: str, field: str = None, user_message: str = None):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            user_message=user_message or f"Invalid input: {field if field else 'data'}",
            error_code="VALIDATION_ERROR",
            context={"field": field}
        )

class AuthenticationError(SwarmBharatError):
    """Authentication errors"""
    
    def __init__(self, message: str, user_message: str = None):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            user_message=user_message or "Authentication failed. Please check your credentials.",
            error_code="AUTH_ERROR"
        )

class RateLimitError(SwarmBharatError):
    """Rate limiting errors"""
    
    def __init__(self, message: str, user_message: str = None):
        super().__init__(
            message=message,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            user_message=user_message or "Too many requests. Please try again later.",
            error_code="RATE_LIMIT_ERROR"
        )

class ExternalAPIError(SwarmBharatError):
    """External API errors"""
    
    def __init__(self, message: str, api_name: str = None, user_message: str = None):
        super().__init__(
            message=message,
            category=ErrorCategory.EXTERNAL_API,
            severity=ErrorSeverity.HIGH,
            user_message=user_message or "External service unavailable. Please try again later.",
            error_code="EXTERNAL_API_ERROR",
            context={"api_name": api_name}
        )

class DatabaseError(SwarmBharatError):
    """Database errors"""
    
    def __init__(self, message: str, user_message: str = None):
        super().__init__(
            message=message,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.CRITICAL,
            user_message=user_message or "Database error. Please try again later.",
            error_code="DATABASE_ERROR"
        )

class BusinessLogicError(SwarmBharatError):
    """Business logic errors"""
    
    def __init__(self, message: str, user_message: str = None):
        super().__init__(
            message=message,
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.MEDIUM,
            user_message=user_message or "Processing error. Please try again.",
            error_code="BUSINESS_LOGIC_ERROR"
        )

class ErrorHandler:
    """Centralized error handling and logging"""
    
    def __init__(self):
        self.error_stats = {
            "total_errors": 0,
            "by_category": {},
            "by_severity": {},
            "by_error_code": {}
        }
    
    def handle_exception(self, exception: Exception, context: Dict[str, Any] = None) -> SwarmBharatError:
        """Convert any exception to SwarmBharatError with proper categorization"""
        
        if isinstance(exception, SwarmBharatError):
            # Already our custom exception
            error = exception
        elif isinstance(exception, ValueError):
            error = ValidationError(
                message=str(exception),
                user_message="Invalid input provided. Please check your data and try again."
            )
        elif isinstance(exception, PermissionError):
            error = AuthenticationError(
                message=str(exception),
                user_message="Permission denied. Please check your access rights."
            )
        elif isinstance(exception, ConnectionError):
            error = ExternalAPIError(
                message=str(exception),
                user_message="Connection error. Please check your internet connection."
            )
        elif isinstance(exception, TimeoutError):
            error = ExternalAPIError(
                message=str(exception),
                user_message="Service timeout. Please try again later."
            )
        else:
            # Unknown exception
            error = SwarmBharatError(
                message=str(exception),
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH,
                user_message="An unexpected error occurred. Please try again later.",
                error_code="SYSTEM_ERROR",
                context={"original_exception": type(exception).__name__}
            )
        
        # Add additional context
        if context:
            error.context.update(context)
        
        # Log the error
        self.log_error(error)
        
        # Update statistics
        self.update_stats(error)
        
        return error
    
    def log_error(self, error: SwarmBharatError):
        """Log error with appropriate level"""
        
        log_data = {
            "error_code": error.error_code,
            "category": error.category.value,
            "severity": error.severity.value,
            # Avoid reserved LogRecord keys like "message".
            "error_message": error.message,
            "user_message": error.user_message,
            "context": error.context,
            "timestamp": error.timestamp.isoformat()
        }
        
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"CRITICAL ERROR: {error.error_code} - {error.message}", extra=log_data)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(f"HIGH SEVERITY ERROR: {error.error_code} - {error.message}", extra=log_data)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"MEDIUM SEVERITY ERROR: {error.error_code} - {error.message}", extra=log_data)
        else:
            logger.info(f"LOW SEVERITY ERROR: {error.error_code} - {error.message}", extra=log_data)
    
    def update_stats(self, error: SwarmBharatError):
        """Update error statistics"""
        self.error_stats["total_errors"] += 1
        
        # Update by category
        category = error.category.value
        self.error_stats["by_category"][category] = self.error_stats["by_category"].get(category, 0) + 1
        
        # Update by severity
        severity = error.severity.value
        self.error_stats["by_severity"][severity] = self.error_stats["by_severity"].get(severity, 0) + 1
        
        # Update by error code
        error_code = error.error_code
        self.error_stats["by_error_code"][error_code] = self.error_stats["by_error_code"].get(error_code, 0) + 1
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get current error statistics"""
        return self.error_stats.copy()
    
    def create_http_response(self, error: SwarmBharatError) -> Tuple[Dict[str, Any], int]:
        """Create appropriate HTTP response for error"""
        
        status_code = self.get_http_status_code(error)
        
        response_data = {
            "error": True,
            "error_code": error.error_code,
            "message": error.user_message,
            "category": error.category.value,
            "severity": error.severity.value,
            "timestamp": error.timestamp.isoformat()
        }
        
        # Add context information in development mode
        if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            response_data["debug_info"] = {
                "technical_message": error.message,
                "context": error.context
            }
        
        return response_data, status_code
    
    def get_http_status_code(self, error: SwarmBharatError) -> int:
        """Get appropriate HTTP status code for error"""
        
        status_mapping = {
            ErrorCategory.VALIDATION: 400,
            ErrorCategory.AUTHENTICATION: 401,
            ErrorCategory.AUTHORIZATION: 403,
            ErrorCategory.RATE_LIMIT: 429,
            ErrorCategory.EXTERNAL_API: 502,
            ErrorCategory.DATABASE: 500,
            ErrorCategory.NETWORK: 503,
            ErrorCategory.SYSTEM: 500,
            ErrorCategory.BUSINESS_LOGIC: 422,
            ErrorCategory.UNKNOWN: 500
        }
        
        return status_mapping.get(error.category, 500)

# Global error handler instance
error_handler = ErrorHandler()

def safe_execute(func):
    """Decorator for safe execution with error handling"""
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except SwarmBharatError as e:
            # Already our custom exception
            raise e
        except Exception as e:
            # Convert to our custom exception
            context = {
                "function": func.__name__,
                "args_count": len(args),
                "kwargs_count": len(kwargs)
            }
            error = error_handler.handle_exception(e, context)
            raise error
    
    return wrapper

def handle_api_error(func):
    """Decorator for API endpoints with proper error handling"""
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except SwarmBharatError as e:
            # Convert to HTTP response
            response_data, status_code = error_handler.create_http_response(e)
            raise HTTPException(status_code=status_code, detail=response_data)
        except Exception as e:
            # Convert to our custom exception first
            context = {
                "endpoint": func.__name__,
                "method": "API"
            }
            error = error_handler.handle_exception(e, context)
            response_data, status_code = error_handler.create_http_response(error)
            raise HTTPException(status_code=status_code, detail=response_data)
    
    return wrapper

def log_performance(func):
    """Decorator for performance logging"""
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = datetime.now()
        try:
            result = await func(*args, **kwargs)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Performance: {func.__name__} completed in {duration:.3f}s")
            
            # Log slow operations
            if duration > 5.0:
                logger.warning(f"Slow operation detected: {func.__name__} took {duration:.3f}s")
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.error(f"Performance: {func.__name__} failed after {duration:.3f}s - {str(e)}")
            raise
    
    return wrapper

# Utility functions for common error scenarios
def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """Validate required fields in data"""
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing_fields:
        raise ValidationError(
            message=f"Missing required fields: {', '.join(missing_fields)}",
            field=", ".join(missing_fields),
            user_message=f"Please provide: {', '.join(missing_fields)}"
        )

def validate_field_length(data: str, field_name: str, min_length: int = 0, max_length: int = None) -> None:
    """Validate field length"""
    if len(data) < min_length:
        raise ValidationError(
            message=f"Field {field_name} too short. Minimum length: {min_length}",
            field=field_name,
            user_message=f"{field_name} must be at least {min_length} characters long."
        )
    
    if max_length and len(data) > max_length:
        raise ValidationError(
            message=f"Field {field_name} too long. Maximum length: {max_length}",
            field=field_name,
            user_message=f"{field_name} must be no more than {max_length} characters long."
        )

def validate_field_type(data: Any, field_name: str, expected_type: type) -> None:
    """Validate field type"""
    if not isinstance(data, expected_type):
        raise ValidationError(
            message=f"Field {field_name} must be of type {expected_type.__name__}",
            field=field_name,
            user_message=f"Invalid {field_name} format."
        )

def create_error_response(error_code: str, message: str, user_message: str = None, 
                         category: ErrorCategory = ErrorCategory.UNKNOWN, 
                         severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> SwarmBharatError:
    """Create standardized error response"""
    return SwarmBharatError(
        message=message,
        category=category,
        severity=severity,
        user_message=user_message or message,
        error_code=error_code
    )
