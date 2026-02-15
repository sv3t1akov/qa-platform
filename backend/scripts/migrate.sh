#!/bin/bash
# Скрипт для применения миграций к базе данных на Fly.io

set -e

echo "Applying database migrations..."

# Проверка наличия DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set"
    exit 1
fi

# Путь к файлам миграций
SCHEMA_FILE="app/db/schema.sql"
SEED_FILE="app/db/seed.sql"

# Применить schema.sql
if [ -f "$SCHEMA_FILE" ]; then
    echo "Applying schema.sql..."
    psql "$DATABASE_URL" -f "$SCHEMA_FILE"
    echo "Schema applied successfully!"
else
    echo "WARNING: $SCHEMA_FILE not found"
fi

# Применить seed.sql
if [ -f "$SEED_FILE" ]; then
    echo "Applying seed.sql..."
    psql "$DATABASE_URL" -f "$SEED_FILE"
    echo "Seed data applied successfully!"
else
    echo "WARNING: $SEED_FILE not found"
fi

echo "Migration completed!"
