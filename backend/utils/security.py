"""
Comprehensive Security Module for SwarmBharat AI
Production-ready security measures including input validation, sanitization, and protection
"""

import re
import html
import hashlib
import hmac
import secrets
import time
import unicodedata
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityConfig:
    max_query_length: int = 5000
    max_document_size: int = 10000000  # 10MB
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    enable_input_validation: bool = True
    enable_output_sanitization: bool = True
    enable_rate_limiting: bool = True
    enable_audit_logging: bool = True

class SecurityValidator:
    """Comprehensive security validation and sanitization"""
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        self.rate_limit_cache = {}
        self.blocked_ips = set()
        self.suspicious_patterns = self._load_suspicious_patterns()
        
    def _load_suspicious_patterns(self) -> List[str]:
        """Load patterns for detecting malicious input"""
        return [
            # SQL Injection patterns
            r"(?i)(union|select|insert|update|delete|drop|create|alter|exec|script)",
            r"(?i)(or\s+1\s*=\s*1|and\s+1\s*=\s*1|'.*or.*'|\".*or.*\")",
            r"(?i)(--|#|/\*|\*/|;)",
            
            # XSS patterns
            r"(?i)(<script|</script|javascript:|vbscript:|onload|onerror|onclick)",
            r"(?i)(<iframe|<object|<embed|<link|<meta)",
            
            # Command injection
            r"(?i)(system|exec|eval|shell_exec|passthru|proc_open|popen)",
            r"(?i)(rm\s+-rf|&&|\|\||;|`|\$\(|\$\{)",
            
            # Path traversal
            r"(?i)(\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c)",
            
            # LDAP injection
            r"(?i)(\(\|\()|(\)\|))",
            
            # NoSQL injection
            r"(?i)(\$where|\$ne|\$gt|\$lt|\$in|\$nin)",
            
            # XXE injection
            r"(?i)(<!DOCTYPE.*\[|<!ENTITY.*SYSTEM)",
            
            # Buffer overflow attempts
            r"(A{1000,})",
            
            # Unicode attacks
            r"(?i)(%u[0-9a-f]{4}|%[0-9a-f]{2})",
        ]
    
    def validate_input(self, input_data: str, input_type: str = "query") -> Tuple[bool, str, str]:
        """
        Validate and sanitize input data
        
        Returns:
            Tuple of (is_valid, sanitized_data, error_message)
        """
        if not input_data:
            return True, "", ""
        
        # Check length limits
        if len(input_data) > self.config.max_query_length:
            return False, "", f"Input too long. Maximum {self.config.max_query_length} characters allowed."

        # Reject low-signal Unicode/emoji spam (common abuse pattern).
        # Keep it permissive for Indian scripts, but block inputs that are mostly symbols.
        if len(input_data) >= 200:
            meaningful = 0
            total = 0
            for ch in input_data:
                if ch.isspace():
                    meaningful += 1
                    total += 1
                    continue
                cat = unicodedata.category(ch)
                total += 1
                # Letters/marks/numbers/punctuation are generally meaningful.
                if cat[0] in {"L", "M", "N", "P"}:
                    meaningful += 1
            if total > 0:
                ratio = meaningful / total
                if ratio < 0.55:
                    return False, "", "Input looks like spam or contains too many symbols. Please rephrase your question."
        
        # Check for truly malicious patterns (more specific)
        dangerous_patterns = [
            r"(?i)(union\s+select\s+.*\s+from\s+.*\s+where|drop\s+table\s+.*|delete\s+from\s+.*\s+where)",
            r"(?i)(exec\s*\(|execute\s*\(|xp_cmdshell|sp_executesql)",
            r"(?i)(insert\s+into\s+.*\s+values\s*\(|update\s+.*\s+set\s+.*\s+where)",
            r"(?i)(<script[^>]*>.*?</script>|<iframe[^>]*>.*?</iframe>)",
            r"(?i)(javascript:[^a-zA-Z]|on\w+\s*=\s*['\"])",
            r"(?i)(rm\s+-rf|&&|\|\||;\s*rm|\$\(|\$\{)",
            r"(?i)(\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c)",
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, input_data):
                logger.warning(f"Dangerous pattern detected: {pattern[:50]}...")
                return False, "", "Input contains potentially malicious content."
        
        # Sanitize the input
        sanitized_data = self._sanitize_input(input_data)
        
        return True, sanitized_data, ""
    
    def _sanitize_input(self, input_data: str) -> str:
        """Sanitize input data to prevent attacks"""
        if not input_data:
            return ""
        
        # HTML encode to prevent XSS
        sanitized = html.escape(input_data)
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', sanitized)
        
        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        # Remove control characters except newlines and tabs
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', sanitized)
        
        return sanitized
    
    def validate_document(self, document_content: bytes, filename: str) -> Tuple[bool, str, str]:
        """
        Validate uploaded documents
        
        Returns:
            Tuple of (is_valid, error_message, safe_content)
        """
        if not document_content:
            return False, "Empty document", ""
        
        # Check file size
        if len(document_content) > self.config.max_document_size:
            return False, f"Document too large. Maximum {self.config.max_document_size // 1000000}MB allowed.", ""
        
        # Check file type (more permissive)
        allowed_extensions = [
            '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt',  # Documents
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff',  # Images
            '.xls', '.xlsx', '.csv', '.ods',  # Spreadsheets
            '.ppt', '.pptx', '.odp',  # Presentations
            '.html', '.htm', '.md', '.json', '.xml'  # Web/Code files
        ]
        file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        # Allow all common file types for testing
        if f'.{file_extension}' not in allowed_extensions and file_extension not in ['html', 'txt', 'pdf']:
            return False, f"File type .{file_extension} not allowed. Allowed types: {', '.join(allowed_extensions)}", ""
        
        # Check for truly malicious content in document (less aggressive)
        try:
            content_str = document_content.decode('utf-8', errors='ignore')
            
            # Only check for extremely dangerous patterns
            dangerous_patterns = [
                r"(?i)(<script[^>]*>.*?</script>|<iframe[^>]*>.*?</iframe>)",
                r"(?i)(javascript:[^a-zA-Z])",
                r"(?i)(rm\s+-rf|&&|\|\||;\s*rm)",
                r"(?i)(exec\s*\(|execute\s*\(|xp_cmdshell)",
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, content_str):
                    return False, f"Document contains potentially malicious content: {pattern[:50]}...", ""
            
            return True, "", content_str
            
        except Exception as e:
            logger.error(f"Document validation error: {e}")
            return False, f"Document processing error: {str(e)}", ""
    
    def check_rate_limit(self, user_id: str, ip_address: str = None) -> Tuple[bool, str]:
        """
        Check if user/IP is rate limited
        
        Returns:
            Tuple of (is_allowed, error_message)
        """
        if not self.config.enable_rate_limiting:
            return True, ""
        
        current_time = int(time.time())
        window_start = current_time - self.config.rate_limit_window
        
        # Use user_id or IP for rate limiting
        key = user_id if user_id else (ip_address or "unknown")
        
        # Initialize or clean old entries
        if key not in self.rate_limit_cache:
            self.rate_limit_cache[key] = []
        
        # Remove old requests outside the window
        self.rate_limit_cache[key] = [
            req_time for req_time in self.rate_limit_cache[key] 
            if req_time > window_start
        ]
        
        # Check if limit exceeded
        if len(self.rate_limit_cache[key]) >= self.config.rate_limit_requests:
            logger.warning(f"Rate limit exceeded for {key}: {len(self.rate_limit_cache[key])} requests")
            return False, f"Rate limit exceeded. Maximum {self.config.rate_limit_requests} requests per hour."
        
        # Add current request
        self.rate_limit_cache[key].append(current_time)
        
        return True, ""
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token for session protection"""
        return secrets.token_urlsafe(32)
    
    def verify_csrf_token(self, token: str, session_token: str) -> bool:
        """Verify CSRF token"""
        return hmac.compare_digest(token, session_token)
    
    def hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data for storage"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def mask_sensitive_data(self, data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
        """Mask sensitive data for logging"""
        if len(data) <= visible_chars:
            return mask_char * len(data)
        
        return data[:visible_chars] + mask_char * (len(data) - visible_chars)
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key format"""
        if not api_key:
            return False
        
        # Basic API key validation (customize based on your requirements)
        return len(api_key) >= 32 and re.match(r'^[a-zA-Z0-9_-]+$', api_key)
    
    def sanitize_output(self, output_data: str) -> str:
        """Sanitize output data to prevent information leakage"""
        if not output_data:
            return ""
        
        # Remove potential system information
        sanitized = re.sub(r'(?i)(error|exception|traceback|stack trace)', '[SYSTEM]', output_data)
        
        # Remove file paths
        sanitized = re.sub(r'[A-Za-z]:\\[^\\]*\\[^\\]*', '[PATH]', sanitized)
        sanitized = re.sub(r'/[^/]*/[^/]*', '[PATH]', sanitized)
        
        # Remove IP addresses
        sanitized = re.sub(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', '[IP]', sanitized)
        
        # Mask potential sensitive data patterns
        sanitized = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]', sanitized)  # Credit card
        sanitized = re.sub(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b', '[SSN]', sanitized)  # SSN
        
        return sanitized
    
    def audit_log(self, event_type: str, user_id: str, details: Dict[str, Any]):
        """Log security events for audit trail"""
        if not self.config.enable_audit_logging:
            return
        
        audit_data = {
            "timestamp": time.time(),
            "event_type": event_type,
            "user_id": self.hash_sensitive_data(user_id),
            "details": details
        }
        
        logger.info(f"AUDIT: {event_type} - User: {self.mask_sensitive_data(user_id)} - Details: {details}")
    
    def check_sql_injection(self, query: str) -> bool:
        """Specific check for SQL injection attempts"""
        # Only flag if it contains actual SQL keywords with dangerous patterns
        dangerous_patterns = [
            r"(?i)(union\s+select\s+\w+\s+from\s+\w+\s+where)",
            r"(?i)(;\s*select\s+.+\s+from\s+.+)",  # stacked queries / probing
            r"(?i)(\bselect\b\s+.+\s+\bfrom\b\s+.+\s*(--|#|/\*))",  # SELECT with comment tail
            r"(?i)(drop\s+table\s+\w+|delete\s+from\s+\w+\s+where)",
            r"(?i)(exec\s*\(|execute\s*\(|xp_cmdshell|sp_executesql)",
            r"(?i)(insert\s+into\s+\w+\s+values\s*\(|update\s+\w+\s+set\s+\w+\s*=\s*['\"])",
            r"(?i)('?\s+or\s+'?1'?\s*=\s*'?\s*1)",  # classic tautology
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query):
                return True
        
        return False
    
    def check_xss(self, input_data: str) -> bool:
        """Specific check for XSS attempts"""
        # Only flag actual XSS patterns, not just mentions
        dangerous_xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"<iframe[^>]*>.*?</iframe>",
            r"(?i)javascript:",
            r"on\w+\s*=\s*['\"]",          # quoted handlers
            r"on\w+\s*=\s*[^\\s>]+",       # unquoted handlers (e.g., onerror=alert(1))
        ]
        
        for pattern in dangerous_xss_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                return True
        
        return False
    
    def get_security_score(self, input_data: str) -> Dict[str, Any]:
        """Get security assessment score for input"""
        score = 100
        issues = []
        
        # Check length
        if len(input_data) > self.config.max_query_length * 0.8:
            score -= 10
            issues.append("Long input")
        
        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, input_data):
                score -= 20
                issues.append("Suspicious pattern detected")
                break
        
        # Check for special characters
        special_chars = len(re.findall(r'[<>"\'&]', input_data))
        if special_chars > 5:
            score -= 10
            issues.append("Many special characters")
        
        # Determine risk level
        if score >= 80:
            risk_level = SecurityLevel.LOW
        elif score >= 60:
            risk_level = SecurityLevel.MEDIUM
        elif score >= 40:
            risk_level = SecurityLevel.HIGH
        else:
            risk_level = SecurityLevel.CRITICAL
        
        return {
            "score": max(0, score),
            "risk_level": risk_level.value,
            "issues": issues
        }

# Global security instance
security_validator = SecurityValidator()

def validate_user_input(input_data: str, input_type: str = "query") -> Tuple[bool, str, str]:
    """Convenience function for input validation"""
    return security_validator.validate_input(input_data, input_type)

def sanitize_output(output_data: str) -> str:
    """Convenience function for output sanitization"""
    return security_validator.sanitize_output(output_data)

def check_rate_limit(user_id: str, ip_address: str = None) -> Tuple[bool, str]:
    """Convenience function for rate limiting"""
    return security_validator.check_rate_limit(user_id, ip_address)
