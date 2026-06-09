#!/bin/bash

# Railway deployment startup script
# Starts both backend API and Next.js frontend server
#
# Cron-service dispatch (news / scheduler / run_daily_digest):
# the root railway.toml pins this script as startCommand for EVERY
# service, so we branch on $RAILWAY_SERVICE_NAME up front. Recognised
# cron services exec their own entry script and exit — everything else
# (web and any unknown name) falls through to the unchanged uvicorn +
# Next.js boot below, byte-identical to the previous behaviour.

SERVICE_NAME="${RAILWAY_SERVICE_NAME:-web}"

start_healthcheck_listener() {
  # Tiny background HTTP server purely to satisfy Railway's healthcheck
  # (railway.toml sets healthcheckPath=/ for all services). Muted so it
  # doesn't pollute the cron log. Dies with the container when the main
  # cron script exits.
  local hp="${PORT:-8000}"
  python3 -m http.server "$hp" >/dev/null 2>&1 &
}

case "$SERVICE_NAME" in
  news)
    echo "[start.sh] Service=news — running news generator"
    start_healthcheck_listener
    cd /app/backend
    exec python run_news_generator.py
    ;;
  scheduler)
    echo "[start.sh] Service=scheduler — running background scheduler"
    start_healthcheck_listener
    cd /app/backend
    exec python run_scheduler.py
    ;;
  run_daily_digest)
    echo "[start.sh] Service=run_daily_digest — running daily digest job"
    start_healthcheck_listener
    cd /app/backend
    exec python cron_jobs/run_daily_digest.py
    ;;
esac

# --- web (default) path below — UNCHANGED from the previous version ---

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
PORT=$FRONTEND_PORT npm start &
FRONTEND_PID=$!

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
