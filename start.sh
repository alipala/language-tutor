#!/bin/bash

# Railway deployment startup script
# Starts both backend API and Next.js frontend server

# Set default port if PORT is not set
PORT=${PORT:-3001}
BACKEND_PORT=8000
FRONTEND_PORT=$PORT

echo "Starting Language Tutor Application"
echo "Environment: ${ENVIRONMENT:-production}"
echo "Backend Port: $BACKEND_PORT"
echo "Frontend Port: $FRONTEND_PORT"
echo "Railway: ${RAILWAY_ENVIRONMENT:-false}"

# Start backend in background
cd /app/backend
echo "Starting Backend API on port $BACKEND_PORT..."
python -m uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend (Next.js server)
cd /app/frontend
echo "Starting Frontend Server on port $FRONTEND_PORT..."
PORT=$FRONTEND_PORT npm start &
FRONTEND_PID=$!

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
