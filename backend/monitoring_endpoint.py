#!/usr/bin/env python3
"""
HTTP Endpoint for Duration Monitoring
Can be called via HTTP requests for Railway-compatible monitoring
"""

from flask import Flask, jsonify, request
import asyncio
import logging
from datetime import datetime, timezone
import os
import sys

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from duration_monitoring import run_daily_monitoring

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/health-check', methods=['GET', 'POST'])
async def duration_health_check():
    """
    HTTP endpoint to trigger duration tracking health check
    Can be called by external cron services or Railway scheduled tasks
    """
    try:
        # Verify authorization (simple token check)
        auth_token = request.headers.get('Authorization') or request.args.get('token')
        expected_token = os.getenv('MONITORING_TOKEN', 'default-monitoring-token')
        
        if auth_token != f"Bearer {expected_token}" and auth_token != expected_token:
            return jsonify({
                "error": "Unauthorized",
                "message": "Valid monitoring token required"
            }), 401
        
        logger.info("🔍 HTTP-triggered duration monitoring started...")
        
        # Run the monitoring
        health_report = await run_daily_monitoring()
        
        # Return the health report
        response = {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": health_report.get('overall_status', 'unknown'),
            "issues_count": len(health_report.get('issues_found', [])),
            "warnings_count": len(health_report.get('warnings', [])),
            "stats": health_report.get('stats', {}),
            "message": "Duration monitoring completed successfully"
        }
        
        # Include issues and warnings if present
        if health_report.get('issues_found'):
            response["issues"] = health_report['issues_found']
        if health_report.get('warnings'):
            response["warnings"] = health_report['warnings']
        
        logger.info(f"✅ HTTP monitoring completed - Status: {response['status']}")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ HTTP monitoring failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/monitoring-status', methods=['GET'])
def monitoring_status():
    """
    Simple status endpoint to verify monitoring system is available
    """
    return jsonify({
        "service": "Duration Tracking Monitoring",
        "status": "active",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoints": {
            "health_check": "/health-check",
            "status": "/monitoring-status"
        },
        "usage": {
            "health_check": "POST/GET /health-check?token=YOUR_TOKEN",
            "external_cron": "curl -X POST https://your-railway-app.com/health-check -H 'Authorization: Bearer YOUR_TOKEN'"
        }
    })

if __name__ == '__main__':
    # For development/testing
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
