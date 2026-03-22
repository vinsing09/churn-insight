#!/bin/bash
echo "=== STARTING ===" >&2
alembic upgrade head >&2 2>&1 || echo "Alembic done" >&2
echo "=== STARTING UVICORN ===" >&2
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port ${PORT:-8000} \
  --log-level debug \
  2>&1
