#!/bin/sh
set -e

echo "⏳ Waiting for PostgreSQL..."
while ! python -c "import socket; socket.create_connection(('db', 5432), timeout=1)" 2>/dev/null; do
  sleep 1
done

echo "🚀 Running Alembic migrations..."
alembic upgrade head

echo "🟢 Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
