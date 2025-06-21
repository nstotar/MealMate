#!/usr/bin/env bash

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Load data
python manage.py loaddata initial_data.json
