#!/bin/bash

# Install database dependencies and run migration

echo "Installing database dependencies..."

cd apps/backend

# Install new dependencies
pip install sqlalchemy alembic psycopg2-binary

# Run database initialization
python scripts/init_database.py

echo "Database setup completed!"


