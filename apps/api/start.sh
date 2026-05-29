#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "Running database migrations..."
alembic -c alembic.ini upgrade head
echo "Migrations complete. Starting server..."
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8080}"
