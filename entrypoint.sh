#!/bin/bash
set -e

echo "Waiting for MySQL..."
while ! python -c "
import MySQLdb
try:
    MySQLdb.connect(
        host='${DB_HOST:-db}',
        port=int('${DB_PORT:-3306}'),
        user='${DB_USER:-root}',
        passwd='${DB_PASSWORD:-}',
    )
    print('MySQL is ready')
except Exception as e:
    print(f'MySQL not ready: {e}')
    exit(1)
" 2>/dev/null; do
    echo "MySQL is unavailable - sleeping 2s"
    sleep 2
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput 2>/dev/null || true

echo "Starting Gunicorn..."
exec gunicorn root_directory.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
