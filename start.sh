#!/bin/bash
# start.sh - Startup script that runs migration then starts the app

echo "🚀 Starting migration..."
python migrate_render.py

echo "🚀 Starting application..."
gunicorn app:app