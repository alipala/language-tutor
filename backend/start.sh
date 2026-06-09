#!/bin/bash
# Railway startup script — service-aware dispatch.
#
# The root railway.toml pins `startCommand = /app/start.sh` for every
# service, so this single script has to route each Railway service to
# the right entry point. We branch on $RAILWAY_SERVICE_NAME (auto-set
# by Railway) and fall back to the legacy uvicorn path for the `web`
# service so its behaviour is byte-identical to the previous version.
#
# Cron services (news / scheduler / run_daily_digest) ship a silent
# minimal HTTP listener on $PORT alongside their actual workload so
# Railway's healthcheck (GET /) doesn't time out and fail the deploy
# while the cron job is doing its real work.

set -e

SERVICE="${RAILWAY_SERVICE_NAME:-web}"
HEALTH_PORT="${PORT:-8000}"

start_healthcheck_listener() {
  # Tiny background HTTP server purely to satisfy Railway's healthcheck.
  # Output is muted so it doesn't drown the real log. The container
  # exits as soon as the main cron script returns, killing this child.
  python3 -m http.server "$HEALTH_PORT" >/dev/null 2>&1 &
}

case "$SERVICE" in
  news)
    echo "[start.sh] Service=news — running news generator"
    start_healthcheck_listener
    exec python run_news_generator.py
    ;;
  scheduler)
    echo "[start.sh] Service=scheduler — running background scheduler"
    start_healthcheck_listener
    exec python run_scheduler.py
    ;;
  run_daily_digest)
    echo "[start.sh] Service=run_daily_digest — running daily digest job"
    start_healthcheck_listener
    exec /opt/venv/bin/python cron_jobs/run_daily_digest.py
    ;;
  *)
    # web (default) — UNCHANGED legacy behaviour. Anything that isn't a
    # recognised cron service falls here, so an accidentally-renamed
    # web instance still boots correctly.
    if [ -z "$PORT" ]; then
      PORT=8000
    fi
    echo "Starting application on port $PORT"
    echo "Workers: ${UVICORN_WORKERS:-1}"
    exec python -m uvicorn main:app \
      --host 0.0.0.0 \
      --port "$PORT" \
      --workers "${UVICORN_WORKERS:-1}"
    ;;
esac
