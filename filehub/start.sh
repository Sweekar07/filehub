#!/bin/sh

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate || {
    echo "Migration failed"
    exit 1
}

# Start the Django development server
echo "Starting Django server..."
python manage.py runserver 0.0.0.0:8000 || {
    echo "Failed to start Django server"
    exit 1
}
