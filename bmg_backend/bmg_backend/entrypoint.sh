#!/bin/sh
set -e

echo "=== BMG startup ==="

echo "--- makemigrations ---"
python manage.py makemigrations tenants        --noinput 2>/dev/null || true
python manage.py makemigrations multi_language --noinput 2>/dev/null || true
python manage.py makemigrations audit          --noinput 2>/dev/null || true
python manage.py makemigrations users          --noinput 2>/dev/null || true
python manage.py makemigrations social_accounts --noinput 2>/dev/null || true

echo "--- migrate_schemas --shared ---"
python manage.py migrate_schemas --shared --noinput

echo "--- collectstatic ---"
python manage.py collectstatic --noinput 2>&1 | tail -5

echo "=== Ready: $@ ==="
exec "$@"
