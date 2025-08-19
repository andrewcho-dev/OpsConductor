#!/bin/bash

# =============================================================================
# ALEMBIC PERMISSIONS FIX SCRIPT
# =============================================================================
# This script fixes the root permission issue that causes Alembic problems
# Run this after ANY alembic operation to prevent permission issues

echo "🔧 Fixing Alembic permissions..."

# Fix ownership of all alembic files
sudo chown -R enabledrm:enabledrm /home/enabledrm/backend/alembic/

# Fix permissions
chmod -R 755 /home/enabledrm/backend/alembic/
chmod 644 /home/enabledrm/backend/alembic/versions/*.py 2>/dev/null || true

echo "✅ Alembic permissions fixed!"
echo "📁 All files in /home/enabledrm/backend/alembic/ are now owned by enabledrm:enabledrm"

# Show current permissions
echo "📋 Current permissions:"
ls -la /home/enabledrm/backend/alembic/versions/ | head -5