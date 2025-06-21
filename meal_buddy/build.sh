#!/usr/bin/env bash

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Load data
python manage.py loaddata initial_data.json
