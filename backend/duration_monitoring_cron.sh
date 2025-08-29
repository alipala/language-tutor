#!/bin/bash
# Duration Tracking Monitoring Cron Job
# Run daily at 2 AM to check for data anomalies

cd /app/backend
python3 duration_monitoring.py >> /var/log/duration_monitoring.log 2>&1
