#!/usr/bin/env python3
"""
Daily Slack webhook health check monitoring script
"""

import requests
import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import time
import logging

# Configuration
WEBHOOK_URL = "https://hooks.slack.com/services/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"
RAILWAY_HEALTH_URL = "https://taco.up.railway.app/health"  # Your Railway app health endpoint
ALERT_EMAIL = "ali@mytaco.ai"  # Replace with your email
SMTP_SERVER = "smtp.gmail.com"  # Configure for your email provider
SMTP_PORT = 587

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webhook_monitor.log'),
        logging.StreamHandler()
    ]
)

class WebhookMonitor:
    def __init__(self):
        self.webhook_url = WEBHOOK_URL
        self.railway_url = RAILWAY_HEALTH_URL
        self.alert_email = ALERT_EMAIL
        self.last_check_file = "last_webhook_check.json"
        
    def check_webhook_health(self):
        """Test Slack webhook health"""
        try:
            test_message = {
                "text": f"🔍 Daily health check - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "username": "Webhook Monitor",
                "icon_emoji": ":white_check_mark:"
            }
            
            logging.info("Testing Slack webhook...")
            response = requests.post(
                self.webhook_url,
                json=test_message,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                logging.info("✅ Slack webhook is healthy")
                return True, "Webhook working correctly"
            else:
                error_msg = f"Webhook failed: HTTP {response.status_code} - {response.text}"
                logging.error(f"❌ {error_msg}")
                return False, error_msg
                
        except requests.exceptions.Timeout:
            error_msg = "Webhook timeout - Slack may be experiencing issues"
            logging.error(f"❌ {error_msg}")
            return False, error_msg
        except requests.exceptions.ConnectionError:
            error_msg = "Connection error - Check internet connectivity"
            logging.error(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Webhook error: {str(e)}"
            logging.error(f"❌ {error_msg}")
            return False, error_msg

    def check_railway_health(self):
        """Check Railway app health"""
        try:
            logging.info("Checking Railway app health...")
            response = requests.get(self.railway_url, timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                logging.info("✅ Railway app is healthy")
                return True, health_data
            else:
                error_msg = f"Railway app unhealthy: HTTP {response.status_code}"
                logging.error(f"❌ {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Railway health check error: {str(e)}"
            logging.error(f"❌ {error_msg}")
            return False, error_msg

    def send_alert_email(self, subject, message):
        """Send email alert (configure with your email settings)"""
        try:
            # For now, just log the alert
            # You can configure actual email sending later
            logging.warning(f"EMAIL ALERT: {subject}")
            logging.warning(f"Message: {message}")
            
            # Uncomment and configure below for actual email sending:
            """
            msg = MIMEMultipart()
            msg['From'] = "your-email@gmail.com"  # Configure sender
            msg['To'] = self.alert_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login("your-email@gmail.com", "your-app-password")  # Configure credentials
            text = msg.as_string()
            server.sendmail("your-email@gmail.com", self.alert_email, text)
            server.quit()
            
            logging.info(f"Alert email sent to {self.alert_email}")
            """
            
        except Exception as e:
            logging.error(f"Failed to send email alert: {str(e)}")

    def send_slack_alert(self, message):
        """Send alert to Slack (if webhook is working)"""
        try:
            alert_message = {
                "text": f"🚨 WEBHOOK MONITOR ALERT\n{message}",
                "username": "Webhook Monitor",
                "icon_emoji": ":warning:"
            }
            
            response = requests.post(
                self.webhook_url,
                json=alert_message,
                timeout=5
            )
            
            if response.status_code == 200:
                logging.info("Alert sent to Slack")
            else:
                logging.error("Failed to send Slack alert")
                
        except Exception as e:
            logging.error(f"Error sending Slack alert: {str(e)}")

    def save_check_result(self, webhook_healthy, railway_healthy, details):
        """Save check results to file"""
        try:
            result = {
                "timestamp": datetime.now().isoformat(),
                "webhook_healthy": webhook_healthy,
                "railway_healthy": railway_healthy,
                "details": details
            }
            
            with open(self.last_check_file, 'w') as f:
                json.dump(result, f, indent=2)
                
        except Exception as e:
            logging.error(f"Failed to save check result: {str(e)}")

    def load_last_check(self):
        """Load last check results"""
        try:
            if os.path.exists(self.last_check_file):
                with open(self.last_check_file, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logging.error(f"Failed to load last check: {str(e)}")
            return None

    def run_health_check(self):
        """Run complete health check"""
        logging.info("="*60)
        logging.info("🔍 STARTING WEBHOOK HEALTH CHECK")
        logging.info("="*60)
        
        # Check webhook health
        webhook_healthy, webhook_details = self.check_webhook_health()
        
        # Check Railway app health
        railway_healthy, railway_details = self.check_railway_health()
        
        # Load previous check results
        last_check = self.load_last_check()
        
        # Determine if we need to send alerts
        send_alert = False
        alert_messages = []
        
        # Check for webhook issues
        if not webhook_healthy:
            send_alert = True
            alert_messages.append(f"🚨 Slack Webhook Failed: {webhook_details}")
            
            # Check if this is a new failure
            if last_check and last_check.get("webhook_healthy", True):
                alert_messages.append("This is a NEW webhook failure!")
        
        # Check for Railway issues
        if not railway_healthy:
            send_alert = True
            alert_messages.append(f"🚨 Railway App Failed: {railway_details}")
            
            if last_check and last_check.get("railway_healthy", True):
                alert_messages.append("This is a NEW Railway failure!")
        
        # Send alerts if needed
        if send_alert:
            alert_message = "\n".join(alert_messages)
            
            # Send email alert
            self.send_alert_email(
                "🚨 My Taco AI - Webhook/App Health Alert",
                alert_message
            )
            
            # Try to send Slack alert (if webhook is working)
            if webhook_healthy:
                self.send_slack_alert(alert_message)
        
        # Log summary
        logging.info("="*60)
        logging.info("📊 HEALTH CHECK SUMMARY")
        logging.info(f"Slack Webhook: {'✅ Healthy' if webhook_healthy else '❌ Failed'}")
        logging.info(f"Railway App: {'✅ Healthy' if railway_healthy else '❌ Failed'}")
        
        if webhook_healthy and railway_healthy:
            logging.info("🎉 All systems healthy!")
        else:
            logging.warning("⚠️ Issues detected - alerts sent")
        
        logging.info("="*60)
        
        # Save results
        self.save_check_result(
            webhook_healthy, 
            railway_healthy, 
            {
                "webhook": webhook_details,
                "railway": railway_details
            }
        )
        
        return webhook_healthy and railway_healthy

def main():
    """Main function"""
    monitor = WebhookMonitor()
    
    # Run single health check
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "--continuous":
        # Continuous monitoring mode
        logging.info("🔄 Starting continuous monitoring mode...")
        logging.info("Checking every 30 minutes. Press Ctrl+C to stop.")
        
        try:
            while True:
                monitor.run_health_check()
                logging.info("😴 Sleeping for 30 minutes...")
                time.sleep(1800)  # 30 minutes
        except KeyboardInterrupt:
            logging.info("🛑 Monitoring stopped by user")
    else:
        # Single check mode
        monitor.run_health_check()

if __name__ == "__main__":
    main()
