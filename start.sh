#!/bin/bash

# Railway deployment startup script
# This script handles the PORT environment variable properly for uvicorn

# Set default port if PORT is not set
PORT=${PORT:-3001}

echo "Starting Language Tutor Backend on port $PORT"
echo "Environment: ${ENVIRONMENT:-production}"
echo "Railway: ${RAILWAY_ENVIRONMENT:-false}"

# Change to backend directory
cd /app/backend

# Start the application with the correct port
exec python -m uvicorn main:app --host 0.0.0.0 --port $PORT
