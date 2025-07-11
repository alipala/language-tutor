"""
Production-safe logging configuration for the backend
Prevents sensitive information from appearing in production logs
"""

import os
import logging
import sys
from typing import Optional

class ProductionSafeFormatter(logging.Formatter):
    """Custom formatter that sanitizes sensitive information in production"""
    
    SENSITIVE_PATTERNS = [
        'password', 'token', 'key', 'secret', 'auth', 'credential',
        'bearer', 'jwt', 'api_key', 'openai', 'stripe'
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_production = os.getenv('NODE_ENV') == 'production' or os.getenv('ENVIRONMENT') == 'production'
    
    def format(self, record):
        # Get the original formatted message
        formatted = super().format(record)
        
        # In production, sanitize sensitive information
        if self.is_production:
            formatted = self._sanitize_message(formatted)
        
        return formatted
    
    def _sanitize_message(self, message: str) -> str:
        """Remove or mask sensitive information from log messages"""
        # Convert to lowercase for pattern matching
        message_lower = message.lower()
        
        # Check if message contains sensitive patterns
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message_lower:
                # If it contains sensitive info, return a generic message
                return "[SENSITIVE DATA REMOVED FOR SECURITY]"
        
        # Remove potential API keys, tokens, etc. (basic pattern matching)
        import re
        
        # Remove anything that looks like an API key or token
        message = re.sub(r'sk-[a-zA-Z0-9-_]{20,}', '[API_KEY_REMOVED]', message)
        message = re.sub(r'ek-[a-zA-Z0-9-_]{20,}', '[EPHEMERAL_KEY_REMOVED]', message)
        message = re.sub(r'Bearer [a-zA-Z0-9-_\.]{20,}', 'Bearer [TOKEN_REMOVED]', message)
        message = re.sub(r'token["\s]*[:=]["\s]*[a-zA-Z0-9-_\.]{20,}', 'token: [TOKEN_REMOVED]', message, flags=re.IGNORECASE)
        
        return message

class ProductionLogger:
    """Production-safe logger that adapts behavior based on environment"""
    
    def __init__(self, name: str = __name__):
        self.logger = logging.getLogger(name)
        self.is_production = os.getenv('NODE_ENV') == 'production' or os.getenv('ENVIRONMENT') == 'production'
        self.is_railway = os.getenv('RAILWAY_ENVIRONMENT') is not None
        
        # Configure logger if not already configured
        if not self.logger.handlers:
            self._configure_logger()
    
    def _configure_logger(self):
        """Configure the logger based on environment"""
        
        # Set log level based on environment
        if self.is_production:
            # In production, only log warnings and errors
            self.logger.setLevel(logging.WARNING)
        else:
            # In development, log everything
            self.logger.setLevel(logging.DEBUG)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Set formatter
        if self.is_production:
            # Production formatter with sanitization
            formatter = ProductionSafeFormatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            # Development formatter with more detail
            formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Prevent duplicate logs
        self.logger.propagate = False
    
    def debug(self, message: str, *args, **kwargs):
        """Debug level logging - only shows in development"""
        if not self.is_production:
            self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Info level logging - only shows in development"""
        if not self.is_production:
            self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Warning level logging - shows in both environments"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Error level logging - shows in both environments"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Critical level logging - shows in both environments"""
        self.logger.critical(message, *args, **kwargs)
    
    # Convenience methods for common logging patterns
    def api_request(self, method: str, endpoint: str, user_id: Optional[str] = None):
        """Log API requests (development only)"""
        if not self.is_production:
            self.info(f"API {method} {endpoint} - User: {user_id or 'Anonymous'}")
    
    def api_response(self, method: str, endpoint: str, status_code: int, duration_ms: float):
        """Log API responses (development only)"""
        if not self.is_production:
            self.info(f"API {method} {endpoint} - {status_code} - {duration_ms:.2f}ms")
    
    def api_error(self, method: str, endpoint: str, error: str, user_id: Optional[str] = None):
        """Log API errors (production safe)"""
        if self.is_production:
            # In production, log minimal error info
            self.error(f"API Error {method} {endpoint} - Status: Error")
        else:
            # In development, log full error details
            self.error(f"API Error {method} {endpoint} - User: {user_id or 'Anonymous'} - Error: {error}")
    
    def database_operation(self, operation: str, collection: str, success: bool):
        """Log database operations (development only)"""
        if not self.is_production:
            status = "SUCCESS" if success else "FAILED"
            self.info(f"DB {operation} on {collection} - {status}")
    
    def auth_event(self, event: str, user_id: Optional[str] = None, success: bool = True):
        """Log authentication events (production safe)"""
        if self.is_production:
            # In production, log minimal auth info
            status = "SUCCESS" if success else "FAILED"
            self.info(f"Auth {event} - {status}")
        else:
            # In development, include user ID
            status = "SUCCESS" if success else "FAILED"
            self.info(f"Auth {event} - User: {user_id or 'Unknown'} - {status}")
    
    def business_logic(self, operation: str, details: str):
        """Log business logic events (development only)"""
        if not self.is_production:
            self.info(f"Business Logic: {operation} - {details}")

# Create a default logger instance
logger = ProductionLogger("language_tutor")

# Export convenience functions
def get_logger(name: str) -> ProductionLogger:
    """Get a logger instance for a specific module"""
    return ProductionLogger(name)

# Replace print statements with proper logging
def safe_print(*args, **kwargs):
    """Safe replacement for print statements that respects production environment"""
    message = " ".join(str(arg) for arg in args)
    logger.info(message)

# Export the main logger and functions
__all__ = ['logger', 'get_logger', 'safe_print', 'ProductionLogger']
