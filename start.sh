#!/bin/sh

# Wait until Postgres is ready
POSTGRES_PORT=5432
PG_ADDR=$POSTGRES_ADDRESS

while ! nc -z "$PG_ADDR" "$POSTGRES_PORT"; do sleep 1; done

# Run migrations
alembic upgrade head

# Run the app
exec python3 main.py