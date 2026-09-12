#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "=== Installing dependencies ==="
pip install -r requirements.txt

echo "=== Collecting static files ==="
python manage.py collectstatic --no-input --upload-unhashed-files

echo "=== Running migrations ==="
python manage.py migrate --no-input

echo "=== Build complete ==="
