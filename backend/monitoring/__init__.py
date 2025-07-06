"""
MyTaco AI Monitoring Package
Comprehensive application monitoring with Slack integration
"""

from .slack_notifier import (
    AlertSeverity,
    AlertContext,
    Alert,
    SlackNotifier,
    slack_notifier,
    send_error_alert,
    send_performance_alert,
    send_business_logic_alert,
    send_health_alert
)

from .middleware import (
    MonitoringMiddleware,
    RequestLoggingMiddleware,
    monitor_openai_operation,
    monitor_database_operation,
    monitor_payment_operation
)

__all__ = [
    # Slack Notifier
    "AlertSeverity",
    "AlertContext", 
    "Alert",
    "SlackNotifier",
    "slack_notifier",
    "send_error_alert",
    "send_performance_alert", 
    "send_business_logic_alert",
    "send_health_alert",
    
    # Middleware
    "MonitoringMiddleware",
    "RequestLoggingMiddleware",
    
    # Decorators
    "monitor_openai_operation",
    "monitor_database_operation",
    "monitor_payment_operation"
]
