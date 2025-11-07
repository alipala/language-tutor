"""
Enhanced Monitoring Middleware for MyTaco AI
Replaces basic error handling with comprehensive monitoring and alerting
"""

import time
import traceback
import uuid
from typing import Optional, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .slack_notifier import (
    AlertContext, 
    AlertSeverity,
    send_error_alert,
    send_performance_alert,
    send_business_logic_alert
)

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Enhanced middleware for monitoring, error handling, and alerting"""
    
    def __init__(self, app, performance_threshold: float = 5.0):
        super().__init__(app)
        self.performance_threshold = performance_threshold
        
        # Endpoints to exclude from monitoring (to avoid spam)
        # 🔇 SILENT MODE: Health checks are excluded to prevent log clutter
        self.excluded_endpoints = {
            "/health",
            "/api/health",
            "/api/health/ping",
            "/api/health/status",
            "/favicon.ico",
            "/robots.txt"
        }
        
        # Critical endpoints that need special attention
        self.critical_endpoints = {
            "/api/realtime/token",
            "/auth/login",
            "/auth/register",
            "/stripe/webhook",
            "/api/sentence/assess",
            "/api/speaking/assess"
        }
        
        print("[MONITORING_MIDDLEWARE] Initialized with enhanced error handling and alerting")
    
    def _extract_user_info(self, request: Request) -> tuple[Optional[str], Optional[str]]:
        """Extract user information from request"""
        try:
            # Try to get user from authorization header
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                # In a real implementation, you'd decode the JWT token
                # For now, we'll try to get user info from request state if available
                pass
            
            # Check if user info is available in request state (set by auth middleware)
            user_id = getattr(request.state, "user_id", None)
            user_email = getattr(request.state, "user_email", None)
            
            return user_id, user_email
        except:
            return None, None
    
    def _create_alert_context(self, request: Request, user_id: Optional[str] = None, user_email: Optional[str] = None) -> AlertContext:
        """Create alert context from request"""
        return AlertContext(
            user_id=user_id,
            user_email=user_email,
            endpoint=request.url.path,
            method=request.method,
            request_id=str(uuid.uuid4()),
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
            environment=request.headers.get("x-environment", "unknown")
        )
    
    def _should_monitor_endpoint(self, path: str) -> bool:
        """Check if endpoint should be monitored"""
        return path not in self.excluded_endpoints
    
    def _is_critical_endpoint(self, path: str) -> bool:
        """Check if endpoint is critical"""
        return path in self.critical_endpoints
    
    def _get_error_severity(self, error: Exception, endpoint: str) -> AlertSeverity:
        """Determine error severity based on error type and endpoint"""
        error_str = str(error).lower()
        
        # Critical errors
        if any(keyword in error_str for keyword in ["openai", "database", "mongo", "connection"]):
            return AlertSeverity.CRITICAL
        
        # High priority for critical endpoints
        if self._is_critical_endpoint(endpoint):
            return AlertSeverity.HIGH
        
        # Authentication and payment errors
        if any(keyword in error_str for keyword in ["auth", "stripe", "payment", "subscription"]):
            return AlertSeverity.HIGH
        
        # Default to medium
        return AlertSeverity.MEDIUM
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Main middleware logic"""
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Extract user info
        user_id, user_email = self._extract_user_info(request)
        
        # Create alert context
        context = self._create_alert_context(request, user_id, user_email)
        
        # Log request (only for monitored endpoints)
        if self._should_monitor_endpoint(request.url.path):
            print(f"[MONITORING] {request.method} {request.url.path} - User: {user_email or 'Anonymous'} - ID: {request_id}")
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Monitor performance for critical endpoints
            if self._should_monitor_endpoint(request.url.path) and response_time > self.performance_threshold:
                await send_performance_alert(
                    endpoint=request.url.path,
                    response_time=response_time,
                    context=context,
                    additional_data={
                        "method": request.method,
                        "status_code": response.status_code,
                        "is_critical": self._is_critical_endpoint(request.url.path)
                    }
                )
            
            # Monitor for 5xx errors
            if response.status_code >= 500 and self._should_monitor_endpoint(request.url.path):
                await send_business_logic_alert(
                    operation=f"{request.method} {request.url.path}",
                    issue=f"Server returned {response.status_code} status code",
                    context=context,
                    severity=AlertSeverity.HIGH,
                    additional_data={
                        "status_code": response.status_code,
                        "response_time": f"{response_time:.2f}s"
                    }
                )
            
            # Log successful requests for critical endpoints
            if self._is_critical_endpoint(request.url.path):
                print(f"[MONITORING] ✅ {request.method} {request.url.path} - {response.status_code} - {response_time:.2f}s")
            
            return response
            
        except Exception as e:
            # Calculate response time for failed requests
            response_time = time.time() - start_time
            
            # Log the error with full traceback
            error_detail = f"Error processing request: {str(e)}\n{traceback.format_exc()}"
            print(f"[MONITORING] ❌ {request.method} {request.url.path} - Error: {str(e)}")
            print(error_detail)
            
            # Send alert for monitored endpoints
            if self._should_monitor_endpoint(request.url.path):
                severity = self._get_error_severity(e, request.url.path)
                
                await send_error_alert(
                    error=e,
                    context=context,
                    severity=severity,
                    additional_data={
                        "response_time": f"{response_time:.2f}s",
                        "is_critical_endpoint": self._is_critical_endpoint(request.url.path),
                        "request_id": request_id
                    }
                )
            
            # Return appropriate error response
            status_code = 500
            error_type = "Internal Server Error"
            
            # Customize response based on error type
            if "HTTPException" in str(type(e)):
                # FastAPI HTTPException - extract status code if possible
                try:
                    status_code = getattr(e, 'status_code', 500)
                    error_type = getattr(e, 'detail', str(e))
                except:
                    pass
            elif "ValidationError" in str(type(e)):
                status_code = 422
                error_type = "Validation Error"
            elif "ConnectionError" in str(type(e)) or "TimeoutError" in str(type(e)):
                status_code = 503
                error_type = "Service Unavailable"
            
            return JSONResponse(
                status_code=status_code,
                content={
                    "error": error_type,
                    "detail": str(e),
                    "path": request.url.path,
                    "method": request.method,
                    "request_id": request_id,
                    "timestamp": time.time()
                }
            )

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Lightweight request logging middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.excluded_paths = {"/health", "/api/health", "/favicon.ico"}
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Log requests with timing"""
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        start_time = time.time()
        
        # Log incoming request
        print(f"[REQUEST] {request.method} {request.url.path} - {request.client.host if request.client else 'unknown'}")
        
        try:
            response = await call_next(request)
            response_time = time.time() - start_time
            
            # Log response
            print(f"[RESPONSE] {request.method} {request.url.path} - {response.status_code} - {response_time:.3f}s")
            
            return response
        except Exception as e:
            response_time = time.time() - start_time
            print(f"[ERROR] {request.method} {request.url.path} - {str(e)} - {response_time:.3f}s")
            raise

# Business Logic Monitoring Decorators
def monitor_openai_operation(operation_name: str):
    """Decorator to monitor OpenAI API operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                return result
            except Exception as e:
                # Create context for OpenAI operations
                context = AlertContext(
                    endpoint=f"/openai/{operation_name}",
                    environment="production"  # Adjust as needed
                )
                
                await send_error_alert(
                    error=e,
                    context=context,
                    severity=AlertSeverity.CRITICAL,
                    additional_data={
                        "operation": operation_name,
                        "function": func.__name__
                    }
                )
                raise
        return wrapper
    return decorator

def monitor_database_operation(operation_name: str):
    """Decorator to monitor database operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                return result
            except Exception as e:
                # Create context for database operations
                context = AlertContext(
                    endpoint=f"/database/{operation_name}",
                    environment="production"  # Adjust as needed
                )
                
                await send_error_alert(
                    error=e,
                    context=context,
                    severity=AlertSeverity.CRITICAL,
                    additional_data={
                        "operation": operation_name,
                        "function": func.__name__
                    }
                )
                raise
        return wrapper
    return decorator

def monitor_payment_operation(operation_name: str):
    """Decorator to monitor payment operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                return result
            except Exception as e:
                # Create context for payment operations
                context = AlertContext(
                    endpoint=f"/payments/{operation_name}",
                    environment="production"  # Adjust as needed
                )
                
                await send_error_alert(
                    error=e,
                    context=context,
                    severity=AlertSeverity.HIGH,
                    additional_data={
                        "operation": operation_name,
                        "function": func.__name__
                    }
                )
                raise
        return wrapper
    return decorator

# Import asyncio for decorator functions
import asyncio
