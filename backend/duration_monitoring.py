#!/usr/bin/env python3
"""
Duration Tracking Monitoring System
Provides alerts and monitoring for duration tracking issues
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
import logging
import json

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import database
from duration_tracking_safeguards import DurationTrackingSafeguards
from monitoring.slack_notifier import slack_notifier, AlertSeverity, AlertContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DurationMonitoring:
    """Monitoring system for duration tracking health"""
    
    def __init__(self):
        self.db = database
        self.safeguards = DurationTrackingSafeguards()
        
    async def daily_health_check(self) -> Dict[str, Any]:
        """
        Perform daily health check on duration tracking system
        """
        health_report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": "healthy",
            "issues_found": [],
            "warnings": [],
            "stats": {},
            "recommendations": []
        }
        
        try:
            # 1. Check for data anomalies
            anomalies = await self.safeguards.detect_data_anomalies()
            if anomalies:
                health_report["issues_found"].extend([
                    f"Data anomaly for {a['email']}: {', '.join(a['issues'])}" 
                    for a in anomalies
                ])
                health_report["overall_status"] = "issues_detected"
            
            # 2. Check for recent suspicious changes
            recent_changes = await self.check_recent_suspicious_changes()
            if recent_changes:
                health_report["warnings"].extend([
                    f"Suspicious change for {c['email']}: {c['description']}"
                    for c in recent_changes
                ])
            
            # 3. Generate usage statistics
            stats = await self.generate_usage_statistics()
            health_report["stats"] = stats
            
            # 4. Check for users with missing period data
            missing_periods = await self.check_missing_period_data()
            if missing_periods:
                health_report["warnings"].extend([
                    f"Missing period data for {email}" for email in missing_periods
                ])
            
            # 5. Generate recommendations
            if anomalies:
                health_report["recommendations"].append(
                    "Review users with data anomalies and consider data restoration"
                )
            
            if len(health_report["issues_found"]) > 0:
                health_report["overall_status"] = "critical"
            elif len(health_report["warnings"]) > 0:
                health_report["overall_status"] = "warning"
            
            # Log the health check
            logger.info(f"Daily health check completed: {health_report['overall_status']}")
            if health_report["issues_found"]:
                logger.warning(f"Issues found: {len(health_report['issues_found'])}")
            
            # Store health report
            await self.db.duration_health_reports.insert_one(health_report)
            
            return health_report
            
        except Exception as e:
            logger.error(f"❌ Error during health check: {e}")
            health_report["overall_status"] = "error"
            health_report["issues_found"].append(f"Health check failed: {str(e)}")
            return health_report
    
    async def check_recent_suspicious_changes(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Check for suspicious changes in the last N hours
        """
        suspicious_changes = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        try:
            # Look for users with recent duration_fix_applied
            async for user in self.db.users.find({
                "duration_fix_date": {"$gte": cutoff_time.isoformat()}
            }):
                fix_details = user.get('duration_fix_details', {})
                old_minutes = fix_details.get('old_minutes', 0)
                new_minutes = fix_details.get('new_minutes', 0)
                
                # Flag suspicious resets
                if old_minutes > 10 and new_minutes == 0:
                    suspicious_changes.append({
                        "email": user.get('email', 'unknown'),
                        "description": f"Reset from {old_minutes} to 0 minutes",
                        "timestamp": user.get('duration_fix_date'),
                        "severity": "high"
                    })
                
                # Flag large changes
                minutes_diff = abs(new_minutes - old_minutes)
                if minutes_diff > 100:
                    suspicious_changes.append({
                        "email": user.get('email', 'unknown'),
                        "description": f"Large change: {old_minutes}→{new_minutes} minutes",
                        "timestamp": user.get('duration_fix_date'),
                        "severity": "medium"
                    })
                    
        except Exception as e:
            logger.error(f"❌ Error checking suspicious changes: {e}")
        
        return suspicious_changes
    
    async def generate_usage_statistics(self) -> Dict[str, Any]:
        """
        Generate usage statistics across all users
        """
        stats = {
            "total_users": 0,
            "active_users": 0,
            "total_minutes": 0,
            "total_sessions": 0,
            "avg_minutes_per_user": 0,
            "avg_sessions_per_user": 0,
            "users_by_plan": {},
            "anomaly_count": 0
        }
        
        try:
            total_minutes = 0
            total_sessions = 0
            active_users = 0
            plan_counts = {}
            
            async for user in self.db.users.find({}):
                stats["total_users"] += 1
                
                minutes = user.get('practice_minutes_used', 0)
                sessions = user.get('practice_sessions_used', 0)
                plan = user.get('subscription_plan', 'unknown')
                
                if minutes > 0 or sessions > 0:
                    active_users += 1
                
                total_minutes += minutes
                total_sessions += sessions
                
                # Count by plan
                plan_counts[plan] = plan_counts.get(plan, 0) + 1
            
            stats["active_users"] = active_users
            stats["total_minutes"] = total_minutes
            stats["total_sessions"] = total_sessions
            stats["users_by_plan"] = plan_counts
            
            if stats["total_users"] > 0:
                stats["avg_minutes_per_user"] = total_minutes / stats["total_users"]
                stats["avg_sessions_per_user"] = total_sessions / stats["total_users"]
            
            # Count anomalies
            anomalies = await self.safeguards.detect_data_anomalies()
            stats["anomaly_count"] = len(anomalies)
            
        except Exception as e:
            logger.error(f"❌ Error generating statistics: {e}")
        
        return stats
    
    async def check_missing_period_data(self) -> List[str]:
        """
        Check for users missing current_period_start/end data
        """
        missing_periods = []
        
        try:
            async for user in self.db.users.find({
                "$or": [
                    {"current_period_start": {"$exists": False}},
                    {"current_period_end": {"$exists": False}},
                    {"current_period_start": None},
                    {"current_period_end": None}
                ]
            }):
                email = user.get('email', 'unknown')
                # Only flag users with subscriptions
                if user.get('subscription_plan') and user.get('subscription_plan') != 'unknown':
                    missing_periods.append(email)
                    
        except Exception as e:
            logger.error(f"❌ Error checking missing periods: {e}")
        
        return missing_periods
    
    async def alert_on_critical_issues(self, health_report: Dict[str, Any]) -> bool:
        """
        Send alerts for critical issues using existing Slack notification system
        """
        if health_report["overall_status"] == "critical":
            logger.critical("🚨 CRITICAL DURATION TRACKING ISSUES DETECTED!")
            
            # Send Slack alert using existing notification system
            context = AlertContext(
                environment=os.getenv("ENVIRONMENT", "production"),
                endpoint="/duration-monitoring"
            )
            
            issues_text = "\n".join([f"• {issue}" for issue in health_report["issues_found"]])
            
            await slack_notifier.send_business_logic_alert(
                operation="Duration Tracking Health Check",
                issue=f"Critical issues detected in duration tracking system:\n{issues_text}",
                context=context,
                severity=AlertSeverity.CRITICAL,
                additional_data={
                    "total_issues": len(health_report["issues_found"]),
                    "total_warnings": len(health_report["warnings"]),
                    "anomaly_count": health_report["stats"].get("anomaly_count", 0),
                    "total_users": health_report["stats"].get("total_users", 0)
                }
            )
            
            for issue in health_report["issues_found"]:
                logger.critical(f"  - {issue}")
            
            # Store alert
            alert_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "critical_duration_issues",
                "issues": health_report["issues_found"],
                "health_report_id": health_report.get("_id"),
                "slack_alert_sent": True
            }
            
            await self.db.duration_alerts.insert_one(alert_data)
            return True
        
        elif health_report["overall_status"] == "warning":
            # Send warning-level Slack alert
            context = AlertContext(
                environment=os.getenv("ENVIRONMENT", "production"),
                endpoint="/duration-monitoring"
            )
            
            warnings_text = "\n".join([f"• {warning}" for warning in health_report["warnings"]])
            
            await slack_notifier.send_business_logic_alert(
                operation="Duration Tracking Health Check",
                issue=f"Warnings detected in duration tracking system:\n{warnings_text}",
                context=context,
                severity=AlertSeverity.MEDIUM,
                additional_data={
                    "total_warnings": len(health_report["warnings"]),
                    "anomaly_count": health_report["stats"].get("anomaly_count", 0),
                    "total_users": health_report["stats"].get("total_users", 0)
                }
            )
            
            return True
        
        return False

async def run_daily_monitoring():
    """
    Run the daily monitoring check
    """
    print("🔍 Running Daily Duration Tracking Monitoring")
    print("=" * 50)
    
    monitoring = DurationMonitoring()
    
    # Run health check
    health_report = await monitoring.daily_health_check()
    
    # Print summary
    print(f"Overall Status: {health_report['overall_status'].upper()}")
    print(f"Issues Found: {len(health_report['issues_found'])}")
    print(f"Warnings: {len(health_report['warnings'])}")
    
    if health_report["issues_found"]:
        print("\n🚨 ISSUES:")
        for issue in health_report["issues_found"]:
            print(f"  - {issue}")
    
    if health_report["warnings"]:
        print("\n⚠️ WARNINGS:")
        for warning in health_report["warnings"]:
            print(f"  - {warning}")
    
    # Print stats
    stats = health_report["stats"]
    print(f"\n📊 STATISTICS:")
    print(f"  Total Users: {stats.get('total_users', 0)}")
    print(f"  Active Users: {stats.get('active_users', 0)}")
    print(f"  Total Minutes: {stats.get('total_minutes', 0):.1f}")
    print(f"  Total Sessions: {stats.get('total_sessions', 0)}")
    print(f"  Anomalies: {stats.get('anomaly_count', 0)}")
    
    # Send alerts if critical
    await monitoring.alert_on_critical_issues(health_report)
    
    return health_report

if __name__ == "__main__":
    asyncio.run(run_daily_monitoring())
