"""
Slack Notification Service for MyTaco AI Monitoring
Sends real-time alerts to Slack when errors occur
"""

import os
import json
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import httpx
from enum import Enum

class AlertSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class AlertContext:
    """Context information for alerts"""
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    request_id: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    environment: Optional[str] = None

@dataclass
class Alert:
    """Alert data structure"""
    title: str
    message: str
    severity: AlertSeverity
    error_type: str
    timestamp: datetime
    context: AlertContext
    stack_trace: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

class SlackNotifier:
    """Handles sending alerts to Slack with deduplication and formatting"""
    
    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.is_production = self.environment == "production"
        self.alert_cache = {}  # For deduplication
        self.cache_duration = timedelta(minutes=5)  # Dedupe window
        
        # Alert thresholds
        self.performance_threshold = float(os.getenv("PERFORMANCE_THRESHOLD", "10.0"))  # seconds
        self.error_rate_threshold = float(os.getenv("ERROR_RATE_THRESHOLD", "10.0"))  # percentage
        
        print(f"[SLACK_NOTIFIER] Initialized for {self.environment} environment")
        print(f"[SLACK_NOTIFIER] Webhook configured: {bool(self.webhook_url)}")
        print(f"[SLACK_NOTIFIER] Performance threshold: {self.performance_threshold}s")
    
    def is_enabled(self) -> bool:
        """Check if Slack notifications are enabled"""
        return bool(self.webhook_url)
    
    def _generate_alert_key(self, alert: Alert) -> str:
        """Generate a unique key for alert deduplication"""
        key_data = f"{alert.error_type}:{alert.context.endpoint}:{alert.title}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _should_send_alert(self, alert: Alert) -> bool:
        """Check if alert should be sent (deduplication logic)"""
        if not self.is_enabled():
            return False
        
        alert_key = self._generate_alert_key(alert)
        now = datetime.now()
        
        # Check if we've sent this alert recently
        if alert_key in self.alert_cache:
            last_sent = self.alert_cache[alert_key]
            if now - last_sent < self.cache_duration:
                print(f"[SLACK_NOTIFIER] Skipping duplicate alert: {alert_key}")
                return False
        
        # Update cache
        self.alert_cache[alert_key] = now
        
        # Clean old entries from cache
        self._cleanup_cache()
        
        return True
    
    def _cleanup_cache(self):
        """Remove old entries from alert cache"""
        now = datetime.now()
        expired_keys = [
            key for key, timestamp in self.alert_cache.items()
            if now - timestamp > self.cache_duration
        ]
        for key in expired_keys:
            del self.alert_cache[key]
    
    def _format_slack_message(self, alert: Alert) -> Dict[str, Any]:
        """Format alert as Slack message with rich formatting"""
        
        # Color coding based on severity
        color_map = {
            AlertSeverity.CRITICAL: "#FF0000",  # Red
            AlertSeverity.HIGH: "#FF8C00",      # Orange
            AlertSeverity.MEDIUM: "#FFD700",    # Yellow
            AlertSeverity.LOW: "#87CEEB"        # Light Blue
        }
        
        # Emoji mapping
        emoji_map = {
            AlertSeverity.CRITICAL: "🚨",
            AlertSeverity.HIGH: "⚠️",
            AlertSeverity.MEDIUM: "⚡",
            AlertSeverity.LOW: "ℹ️"
        }
        
        # Build context fields
        fields = []
        
        if alert.context.endpoint:
            fields.append({
                "title": "Endpoint",
                "value": f"`{alert.context.method or 'GET'} {alert.context.endpoint}`",
                "short": True
            })
        
        if alert.context.user_email:
            fields.append({
                "title": "User",
                "value": alert.context.user_email,
                "short": True
            })
        
        if alert.context.environment:
            fields.append({
                "title": "Environment",
                "value": alert.context.environment.upper(),
                "short": True
            })
        
        fields.append({
            "title": "Time",
            "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "short": True
        })
        
        # Add additional data if present
        if alert.additional_data:
            for key, value in alert.additional_data.items():
                if len(fields) < 8:  # Slack limit
                    fields.append({
                        "title": key.replace("_", " ").title(),
                        "value": str(value),
                        "short": True
                    })
        
        # Build attachment
        attachment = {
            "color": color_map[alert.severity],
            "title": f"{emoji_map[alert.severity]} {alert.title}",
            "text": alert.message,
            "fields": fields,
            "footer": "MyTaco AI Monitoring",
            "ts": int(alert.timestamp.timestamp())
        }
        
        # Add stack trace if present (for critical errors)
        if alert.stack_trace and alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            # Truncate stack trace to avoid Slack message limits
            truncated_trace = alert.stack_trace[:1000]
            if len(alert.stack_trace) > 1000:
                truncated_trace += "\n... (truncated)"
            
            attachment["fields"].append({
                "title": "Stack Trace",
                "value": f"```{truncated_trace}```",
                "short": False
            })
        
        # Build main message
        message = {
            "text": f"{emoji_map[alert.severity]} *{alert.severity.value.upper()}* Alert from MyTaco AI",
            "attachments": [attachment]
        }
        
        return message
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to Slack"""
        try:
            if not self._should_send_alert(alert):
                return False
            
            message = self._format_slack_message(alert)
            
            print(f"[SLACK_NOTIFIER] Sending {alert.severity.value} alert: {alert.title}")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=message,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    print(f"[SLACK_NOTIFIER] ✅ Alert sent successfully")
                    return True
                else:
                    print(f"[SLACK_NOTIFIER] ❌ Failed to send alert: {response.status_code}")
                    print(f"[SLACK_NOTIFIER] Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"[SLACK_NOTIFIER] ❌ Error sending alert: {str(e)}")
            return False
    
    async def send_error_alert(
        self,
        error: Exception,
        context: AlertContext,
        severity: AlertSeverity = AlertSeverity.HIGH,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send an error alert"""
        
        # Determine error type and severity
        error_type = type(error).__name__
        
        # Auto-adjust severity based on error type
        if "OpenAI" in str(error) or "openai" in str(error).lower():
            severity = AlertSeverity.CRITICAL
            error_type = "OpenAI_API_Error"
        elif "Database" in str(error) or "mongo" in str(error).lower():
            severity = AlertSeverity.CRITICAL
            error_type = "Database_Error"
        elif "Stripe" in str(error) or "stripe" in str(error).lower():
            severity = AlertSeverity.HIGH
            error_type = "Payment_Error"
        elif "Authentication" in str(error) or "auth" in str(error).lower():
            severity = AlertSeverity.HIGH
            error_type = "Authentication_Error"
        
        alert = Alert(
            title=f"{error_type}: {str(error)[:100]}",
            message=str(error),
            severity=severity,
            error_type=error_type,
            timestamp=datetime.now(),
            context=context,
            stack_trace=self._get_stack_trace(),
            additional_data=additional_data
        )
        
        return await self.send_alert(alert)
    
    async def send_performance_alert(
        self,
        endpoint: str,
        response_time: float,
        context: AlertContext,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send a performance alert for slow responses"""
        
        if response_time < self.performance_threshold:
            return False  # No alert needed
        
        severity = AlertSeverity.MEDIUM
        if response_time > self.performance_threshold * 2:
            severity = AlertSeverity.HIGH
        if response_time > self.performance_threshold * 3:
            severity = AlertSeverity.CRITICAL
        
        alert = Alert(
            title=f"Slow Response: {endpoint}",
            message=f"Endpoint took {response_time:.2f}s to respond (threshold: {self.performance_threshold}s)",
            severity=severity,
            error_type="Performance_Issue",
            timestamp=datetime.now(),
            context=context,
            additional_data={
                "response_time": f"{response_time:.2f}s",
                "threshold": f"{self.performance_threshold}s",
                **(additional_data or {})
            }
        )
        
        return await self.send_alert(alert)
    
    async def send_business_logic_alert(
        self,
        operation: str,
        issue: str,
        context: AlertContext,
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send a business logic alert"""
        
        alert = Alert(
            title=f"Business Logic Issue: {operation}",
            message=issue,
            severity=severity,
            error_type="Business_Logic_Error",
            timestamp=datetime.now(),
            context=context,
            additional_data=additional_data
        )
        
        return await self.send_alert(alert)
    
    async def send_health_alert(
        self,
        service: str,
        status: str,
        details: str,
        severity: AlertSeverity = AlertSeverity.HIGH
    ) -> bool:
        """Send a system health alert"""
        
        context = AlertContext(
            environment=self.environment,
            endpoint="/health"
        )
        
        alert = Alert(
            title=f"Health Check Failed: {service}",
            message=f"Service '{service}' is {status}. {details}",
            severity=severity,
            error_type="Health_Check_Failure",
            timestamp=datetime.now(),
            context=context,
            additional_data={
                "service": service,
                "status": status
            }
        )
        
        return await self.send_alert(alert)
    
    def _get_stack_trace(self) -> Optional[str]:
        """Get current stack trace"""
        try:
            import traceback
            return traceback.format_exc()
        except:
            return None

# Global instance
slack_notifier = SlackNotifier()

# Convenience functions
async def send_error_alert(error: Exception, context: AlertContext, **kwargs) -> bool:
    """Convenience function to send error alert"""
    return await slack_notifier.send_error_alert(error, context, **kwargs)

async def send_performance_alert(endpoint: str, response_time: float, context: AlertContext, **kwargs) -> bool:
    """Convenience function to send performance alert"""
    return await slack_notifier.send_performance_alert(endpoint, response_time, context, **kwargs)

async def send_business_logic_alert(operation: str, issue: str, context: AlertContext, **kwargs) -> bool:
    """Convenience function to send business logic alert"""
    return await slack_notifier.send_business_logic_alert(operation, issue, context, **kwargs)

async def send_health_alert(service: str, status: str, details: str, **kwargs) -> bool:
    """Convenience function to send health alert"""
    return await slack_notifier.send_health_alert(service, status, details, **kwargs)
