#!/bin/bash
set -e

echo "Setting up development environment..."

# Use the workspace folder that Codespaces creates (matches GitHub repo name)
WORKSPACE_DIR="/workspaces/agentic-property-management"

# Fallback: detect workspace if name differs
if [ ! -d "$WORKSPACE_DIR" ]; then
  WORKSPACE_DIR="$(find /workspaces -maxdepth 1 -mindepth 1 -type d | head -1)"
  echo "Using detected workspace: $WORKSPACE_DIR"
fi

cd "$WORKSPACE_DIR"

# Install Python dependencies
pip install -r apps/api/requirements.txt

# Install Node dependencies for portal
cd apps/portal
npm install
cd "$WORKSPACE_DIR"

# Copy env example if no .env exists
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example - update with your credentials"
fi

# Wait for Postgres to be ready
echo "Waiting for PostgreSQL..."
until pg_isready -h db -p 5432 -U postgres 2>/dev/null; do
  sleep 1
done

# Run database migrations
echo "Running database migrations..."
cd apps/api
python -m app.db_migrate
cd "$WORKSPACE_DIR"

echo "Development environment ready!"
