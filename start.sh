#!/bin/bash
echo "Starting migration..."
python migrate_render.py
echo "Starting application..."
gunicorn app:app