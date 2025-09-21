#!/bin/bash
# Railway startup script with proper port handling

# Set default port if PORT environment variable is not set or empty
if [ -z "$PORT" ]; then
    PORT=8000
fi

echo "Starting application on port $PORT"
exec python -m uvicorn main:app --host 0.0.0.0 --port "$PORT"
