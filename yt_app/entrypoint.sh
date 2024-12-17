#!/bin/sh

# Wait for PostgreSQL to become available
echo "Waiting for PostgreSQL to become available..."
while ! nc -z db 5432; do   
  sleep 1
done
echo "PostgreSQL is available now."

# Run Flask application
export FLASK_APP=main.py
flask run --host=0.0.0.0