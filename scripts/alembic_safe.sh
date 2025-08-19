#!/bin/bash

# =============================================================================
# SAFE ALEMBIC WRAPPER SCRIPT
# =============================================================================
# This script runs Alembic commands and automatically fixes permissions
# Use this instead of direct docker compose exec backend alembic commands

set -e

COMMAND="$*"

if [ -z "$COMMAND" ]; then
    echo "Usage: ./alembic_safe.sh <alembic_command>"
    echo "Examples:"
    echo "  ./alembic_safe.sh current"
    echo "  ./alembic_safe.sh revision --autogenerate -m 'description'"
    echo "  ./alembic_safe.sh upgrade head"
    echo "  ./alembic_safe.sh downgrade -1"
    exit 1
fi

echo "🚀 Running Alembic command: $COMMAND"
echo "=================================="

# Run the alembic command
cd /home/enabledrm
docker compose exec backend alembic $COMMAND

# Fix permissions automatically
echo ""
echo "🔧 Fixing permissions..."
sudo chown -R enabledrm:enabledrm /home/enabledrm/backend/alembic/
chmod -R 755 /home/enabledrm/backend/alembic/
chmod 644 /home/enabledrm/backend/alembic/versions/*.py 2>/dev/null || true

echo "✅ Command completed and permissions fixed!"
echo "📁 All Alembic files are now editable in VS Code"