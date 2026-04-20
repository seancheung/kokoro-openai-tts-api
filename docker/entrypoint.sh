#!/usr/bin/env bash
set -euo pipefail

: "${KOKORO_MODEL:=hexgrad/Kokoro-82M}"
: "${HOST:=0.0.0.0}"
: "${PORT:=8000}"
: "${LOG_LEVEL:=info}"

export KOKORO_MODEL HOST PORT LOG_LEVEL

if [ "$#" -eq 0 ]; then
  exec uvicorn app.server:app --host "$HOST" --port "$PORT" --log-level "$LOG_LEVEL"
fi
exec "$@"
