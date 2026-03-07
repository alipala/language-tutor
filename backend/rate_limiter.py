"""
Rate Limiting Middleware for FastAPI
Prevents abuse, protects budget, and improves stability

Integrated with Slack notifications for monitoring
"""

import time
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from collections import defaultdict
from datetime import datetime
import asyncio

# Import Slack notification system
from monitoring.slack_notifier import slack_notifier, AlertContext, AlertSeverity

class RateLimiter:
    """
    In-memory rate limiter with sliding window algorithm

    Limits:
    - General API: 100 requests/minute per user
    - Realtime sessions: 10 sessions/hour per user
    - GPT-4o requests: 50 requests/hour per user
    - Challenge requests: 100 requests/hour per user
    """

    def __init__(self):
        # Store request timestamps: {user_id: {endpoint_category: [timestamps]}}
        self.requests: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))

        # Rate limit configurations
        self.limits = {
            "general": {"max_requests": 100, "window_seconds": 60},  # 100/min (mid-session activities)
            "realtime": {"max_requests": 10, "window_seconds": 3600},  # 10/hour (NEW conversation sessions)
            "auth": {"max_requests": 10, "window_seconds": 300},  # 10/5min (prevent brute force)
        }

        # Cleanup old entries every 5 minutes
        self._start_cleanup_task()

    def _start_cleanup_task(self):
        """Start background task to cleanup old request timestamps"""
        async def cleanup():
            while True:
                await asyncio.sleep(300)  # 5 minutes
                self._cleanup_old_requests()

        asyncio.create_task(cleanup())

    def _cleanup_old_requests(self):
        """Remove request timestamps older than 1 hour"""
        cutoff_time = time.time() - 3600

        for user_id in list(self.requests.keys()):
            for category in list(self.requests[user_id].keys()):
                # Filter out old timestamps
                self.requests[user_id][category] = [
                    ts for ts in self.requests[user_id][category]
                    if ts > cutoff_time
                ]

                # Remove empty categories
                if not self.requests[user_id][category]:
                    del self.requests[user_id][category]

            # Remove empty user entries
            if not self.requests[user_id]:
                del self.requests[user_id]

    def _get_category(self, path: str) -> str:
        """Determine rate limit category from request path

        CRITICAL RULE: ONLY rate limit NEW conversation session starts.
        NEVER interrupt active conversations with rate limits.

        Rate limited:
        - /api/realtime/token - Starting new practice/learning plan session (10/hour)
        - /api/auth/* - Login/register attempts (10/5min)

        NOT rate limited (use general 100/min):
        - All mid-conversation activities
        - All challenge endpoints
        - All other requests
        """
        # Exclude mid-session activities from strict rate limiting
        # These MUST have very lenient limits to avoid interrupting conversations
        mid_session_patterns = [
            "/conversation-help",           # Mid-conversation AI help
            "/realtime/usage-log",          # Session activity logging
            "/realtime/semantic-feedback",  # Mid-session feedback
            "/realtime/session-summary",    # End of session summary
            "/sentence-assessment",         # Mid-conversation assessments
            "/chat",                        # Contextual chat during practice
            "/contextual-chat",             # Alternate chat endpoint
        ]

        for pattern in mid_session_patterns:
            if pattern in path:
                return "general"  # Use very lenient general limit (100/min)

        # ONLY rate limit NEW conversation session starts
        if "/realtime/token" in path:
            return "realtime"  # 10 new sessions per hour
        # Only rate limit auth attempts (prevent brute force)
        elif "/auth/" in path or "/login" in path or "/register" in path:
            return "auth"  # 10 attempts per 5 minutes
        # Everything else uses general limit (100/min) - includes challenges, etc.
        else:
            return "general"

    def _get_user_friendly_message(self, category: str, retry_after: int) -> str:
        """Get user-friendly message based on category"""
        minutes = max(1, int(retry_after / 60))

        messages = {
            "realtime": f"You've practiced a lot! Take a {minutes}-minute break to let your learning sink in. 🧘",
            "auth": f"For your account security, please wait {minutes} minute(s) before trying again. 🔒",
            "general": f"Please wait {retry_after if retry_after < 60 else f'{minutes} minute(s)'} and try again."
        }

        return messages.get(category, messages["general"])

    def _is_rate_limited(self, user_id: str, category: str) -> tuple[bool, Optional[int]]:
        """
        Check if user is rate limited for a category

        Returns:
            (is_limited, retry_after_seconds)
        """
        now = time.time()
        config = self.limits[category]
        window = config["window_seconds"]
        max_requests = config["max_requests"]

        # Get timestamps for this user and category
        timestamps = self.requests[user_id][category]

        # Remove timestamps outside the window
        cutoff = now - window
        valid_timestamps = [ts for ts in timestamps if ts > cutoff]
        self.requests[user_id][category] = valid_timestamps

        # Check if limit exceeded
        if len(valid_timestamps) >= max_requests:
            # Calculate retry-after time (when oldest request expires)
            oldest_timestamp = min(valid_timestamps)
            retry_after = int(oldest_timestamp + window - now)
            return True, max(retry_after, 1)

        return False, None

    def add_request(self, user_id: str, category: str):
        """Record a new request for rate limiting"""
        self.requests[user_id][category].append(time.time())

    async def check_rate_limit(self, request: Request, user_id: Optional[str] = None):
        """
        Check rate limit for a request

        Args:
            request: FastAPI Request object
            user_id: User ID (if authenticated), otherwise uses IP

        Raises:
            HTTPException: If rate limit exceeded
        """
        # Use user_id if authenticated, otherwise use IP address
        identifier = user_id or request.client.host
        is_authenticated = bool(user_id)

        # Determine category
        category = self._get_category(request.url.path)

        # Check rate limit
        is_limited, retry_after = self._is_rate_limited(identifier, category)

        if is_limited:
            # Send Slack notification for rate limit violations
            await self._send_rate_limit_alert(
                identifier=identifier,
                user_id=user_id,
                category=category,
                request=request,
                retry_after=retry_after,
                is_authenticated=is_authenticated
            )

            # Get user-friendly message
            user_message = self._get_user_friendly_message(category, retry_after)

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": user_message,
                    "retry_after": retry_after,
                    "category": category,
                    "limit": self.limits[category]["max_requests"],
                    "window": self.limits[category]["window_seconds"]
                },
                headers={"Retry-After": str(retry_after)}
            )

        # Record this request
        self.add_request(identifier, category)

    async def _send_rate_limit_alert(
        self,
        identifier: str,
        user_id: Optional[str],
        category: str,
        request: Request,
        retry_after: int,
        is_authenticated: bool
    ):
        """
        Send detailed Slack notification when rate limit is exceeded
        """
        try:
            # Determine severity based on category and authentication
            severity = AlertSeverity.MEDIUM

            # Critical categories get higher severity
            if category in ["realtime", "gpt4o"]:
                severity = AlertSeverity.HIGH

            # Repeated violations from same user
            request_count = len(self.requests[identifier][category])
            if request_count > self.limits[category]["max_requests"] * 1.5:
                severity = AlertSeverity.CRITICAL

            # Build alert context
            context = AlertContext(
                user_id=user_id if is_authenticated else None,
                endpoint=str(request.url.path),
                method=request.method,
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                environment="production" if slack_notifier.is_production else "development"
            )

            # Additional data for the alert
            additional_data = {
                "Category": category.upper(),
                "Limit": f"{self.limits[category]['max_requests']} requests/{self.limits[category]['window_seconds']}s",
                "Request Count": request_count,
                "Retry After": f"{retry_after}s",
                "Authentication": "Authenticated User" if is_authenticated else "Anonymous (IP-based)",
                "Identifier": user_id if is_authenticated else f"IP: {request.client.host}"
            }

            # Prepare alert message
            if is_authenticated:
                title = f"Rate Limit Exceeded: User {user_id[:8]}..."
                message = (
                    f"🚫 **Authenticated user** has exceeded rate limits.\n\n"
                    f"**Category:** `{category.upper()}`\n"
                    f"**Endpoint:** `{request.method} {request.url.path}`\n"
                    f"**Limit:** {self.limits[category]['max_requests']} requests per "
                    f"{self.limits[category]['window_seconds']}s\n"
                    f"**Current Count:** {request_count} requests\n\n"
                    f"⏱️ User must wait **{retry_after} seconds** before retrying."
                )
            else:
                title = f"Rate Limit Exceeded: Anonymous IP {request.client.host}"
                message = (
                    f"🚫 **Anonymous user** (IP-based) has exceeded rate limits.\n\n"
                    f"**Category:** `{category.upper()}`\n"
                    f"**IP Address:** `{request.client.host}`\n"
                    f"**Endpoint:** `{request.method} {request.url.path}`\n"
                    f"**Limit:** {self.limits[category]['max_requests']} requests per "
                    f"{ self.limits[category]['window_seconds']}s\n"
                    f"**Current Count:** {request_count} requests\n\n"
                    f"⏱️ IP must wait **{retry_after} seconds** before retrying.\n\n"
                    f"⚠️ *Possible abuse from this IP address*"
                )

            # Send alert to Slack
            await slack_notifier.send_alert(
                slack_notifier.Alert(
                    title=title,
                    message=message,
                    severity=severity,
                    error_type="Rate_Limit_Exceeded",
                    timestamp=datetime.now(),
                    context=context,
                    additional_data=additional_data
                )
            )

            print(f"[RATE_LIMITER] 🔔 Slack alert sent for rate limit violation: {identifier} ({category})")

        except Exception as e:
            print(f"[RATE_LIMITER] ⚠️  Failed to send Slack alert: {str(e)}")


# Global rate limiter instance
rate_limiter = RateLimiter()


# Dependency for FastAPI routes
async def check_rate_limit(request: Request, user_id: Optional[str] = None):
    """
    FastAPI dependency to check rate limits

    Usage in routes:
        @router.post("/api/endpoint")
        async def endpoint(
            request: Request,
            current_user = Depends(get_current_user),
            _rate_limit = Depends(check_rate_limit)
        ):
            ...
    """
    await rate_limiter.check_rate_limit(request, user_id)


# Middleware version (applies to all requests)
async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware to apply rate limiting to all requests

    Add to FastAPI app:
        app.add_middleware(RateLimitMiddleware)
    """
    # Try to extract user_id from JWT token in Authorization header
    user_id = None
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

            # Decode JWT to get user_id (without full validation for performance)
            import os
            from jose import jwt

            SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_key")
            ALGORITHM = "HS256"

            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")
            except:
                # Invalid token, will use IP address for rate limiting
                user_id = None
    except:
        # No token or error decoding, will use IP address
        user_id = None

    # Check rate limit
    try:
        await rate_limiter.check_rate_limit(request, user_id)
    except HTTPException as e:
        # Return 429 response
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail,
            headers=e.headers
        )

    # Continue processing request
    response = await call_next(request)
    return response


# Custom middleware class
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI"""

    async def dispatch(self, request: Request, call_next):
        return await rate_limit_middleware(request, call_next)
