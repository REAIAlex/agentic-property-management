#!/bin/bash
set -e

echo "Setting up development environment..."

# Install Python dependencies
cd /workspaces/AgenticPropertyManager
pip install -r apps/api/requirements.txt

# Install Node dependencies for portal
cd apps/portal
npm install
cd ../..

# Copy env example if no .env exists
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example - update with your credentials"
fi

# Wait for Postgres to be ready
echo "Waiting for PostgreSQL..."
until pg_isready -h db -p 5432 -U postgres; do
  sleep 1
done

# Run database migrations
echo "Running database migrations..."
cd apps/api
python -m app.db_migrate
cd ../..

echo "Development environment ready!"
