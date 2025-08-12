#!/bin/sh
set -e

# Run Gunicorn with the correct port from the environment variable
exec gunicorn --bind "0.0.0.0:$PORT" \
  --worker-class eventlet \
  --workers 1 \
  --threads 8 \
  --timeout 0 \
  "api.api:app"