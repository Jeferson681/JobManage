#!/bin/sh
set -e

# wait for Postgres to be ready
python /app/docker/wait_for_pg.py --timeout 60

# If a DATABASE_URL is provided, set DSN for the script
exec python /app/scripts/load_demo_pg.py "$@"
