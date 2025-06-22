#!/usr/bin/env bash

# Exit on any error
set -e

echo "Starting build process..."

# Print Python version for debugging
echo "Python version:"
python --version

echo "Installing dependencies..."
# Install dependencies
pip install -r requirements.txt

echo "Collecting static files..."
# Collect static files
python manage.py collectstatic --noinput

echo "Running migrations..."
# Run migrations
python manage.py migrate --noinput

echo "Build completed successfully!"
