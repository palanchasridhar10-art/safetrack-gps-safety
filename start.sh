#!/usr/bin/env bash
set -e

echo "=== Starting SafeTrack Server ==="
if [ -f "requirements.txt" ]; then
    pip install --no-cache-dir -r requirements.txt
elif [ -f "backend/requirements.txt" ]; then
    pip install --no-cache-dir -r backend/requirements.txt
fi

if [ -d "backend" ]; then
    cd backend
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
