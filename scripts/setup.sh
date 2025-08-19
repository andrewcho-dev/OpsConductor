#!/bin/bash

# =============================================================================
# OPSCONDUCTOR - SETUP SCRIPT
# =============================================================================
# Automated setup for OpsConductor Docker infrastructure

set -e

echo "🚀 OpsConductor Setup Script"
echo "============================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ .env file created. Please edit it with your configuration."
else
    echo "✅ .env file already exists."
fi

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p logs/nginx

# Create uploads directory
echo "📁 Creating uploads directory..."
mkdir -p backend/uploads

# Generate SSL certificates if they don't exist
if [ ! -f nginx/ssl/cert.pem ] || [ ! -f nginx/ssl/key.pem ]; then
    echo "🔐 Generating self-signed SSL certificates..."
    mkdir -p nginx/ssl
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=OpsConductor/CN=localhost"
    echo "✅ SSL certificates generated."
else
    echo "✅ SSL certificates already exist."
fi

# Set proper permissions
echo "🔧 Setting proper permissions..."
chmod 600 nginx/ssl/key.pem
chmod 644 nginx/ssl/cert.pem

# Validate Docker Compose configuration
echo "🔍 Validating Docker Compose configuration..."
if docker compose config --quiet; then
    echo "✅ Docker Compose configuration is valid."
else
    echo "❌ Docker Compose configuration has errors."
    exit 1
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Run: docker compose up -d"
echo "3. Access OpsConductor at: https://localhost"
echo ""
echo "For production deployment:"
echo "1. Copy .env.production to .env"
echo "2. Edit production values"
echo "3. Run: docker compose -f docker-compose.prod.yml up -d"
echo ""