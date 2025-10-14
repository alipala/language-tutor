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

# Wait for backend to be ready with health check loop
echo "Waiting for backend to be ready..."
MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -f http://localhost:$BACKEND_PORT/api/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo "Backend not ready yet (attempt $ATTEMPT/$MAX_ATTEMPTS)..."
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "❌ Backend failed to start after $MAX_ATTEMPTS attempts"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend (Next.js server)
cd /app/frontend
echo "Starting Frontend Server on port $FRONTEND_PORT..."
# Next.js needs to listen on 0.0.0.0 to be accessible from outside the container
PORT=$FRONTEND_PORT npm start -- -H 0.0.0.0 &
FRONTEND_PID=$!

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
