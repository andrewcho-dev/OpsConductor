#!/bin/bash

# =============================================================================
# RabbitMQ Setup Script for OpsConductor Microservices
# =============================================================================
# This script sets up RabbitMQ exchanges, queues, and bindings for the
# OpsConductor microservices architecture

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
RABBITMQ_URL=${RABBITMQ_URL:-"amqp://guest:guest@localhost:5672/"}
RABBITMQ_HOST=${RABBITMQ_HOST:-"localhost"}
RABBITMQ_PORT=${RABBITMQ_PORT:-"5672"}
RABBITMQ_USER=${RABBITMQ_USER:-"guest"}
RABBITMQ_PASS=${RABBITMQ_PASS:-"guest"}

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}OpsConductor Microservices - RabbitMQ Setup${NC}"
echo -e "${BLUE}==============================================================================${NC}"

# Function to check if RabbitMQ is running
check_rabbitmq() {
    echo -e "${YELLOW}Checking RabbitMQ connection...${NC}"
    
    # Try to connect using Python
    python3 -c "
import pika
import sys
try:
    connection = pika.BlockingConnection(pika.URLParameters('$RABBITMQ_URL'))
    connection.close()
    print('✅ RabbitMQ is accessible')
except Exception as e:
    print(f'❌ Cannot connect to RabbitMQ: {e}')
    sys.exit(1)
"
}

# Function to install Python dependencies
install_dependencies() {
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    
    # Check if pika is installed
    if ! python3 -c "import pika" 2>/dev/null; then
        echo -e "${YELLOW}Installing pika...${NC}"
        pip3 install pika
    else
        echo -e "${GREEN}✅ pika is already installed${NC}"
    fi
}

# Function to run RabbitMQ setup
run_setup() {
    echo -e "${YELLOW}Running RabbitMQ setup...${NC}"
    
    cd "$(dirname "$0")/.."
    
    # Run the Python setup script
    RABBITMQ_URL="$RABBITMQ_URL" python3 infrastructure/rabbitmq-setup.py
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ RabbitMQ setup completed successfully!${NC}"
    else
        echo -e "${RED}❌ RabbitMQ setup failed!${NC}"
        exit 1
    fi
}

# Function to verify setup
verify_setup() {
    echo -e "${YELLOW}Verifying RabbitMQ setup...${NC}"
    
    # Check if exchanges exist
    python3 -c "
import pika
import sys

try:
    connection = pika.BlockingConnection(pika.URLParameters('$RABBITMQ_URL'))
    channel = connection.channel()
    
    # Try to declare exchanges (passive=True means check if exists)
    exchanges = [
        'opsconductor.events',
        'opsconductor.auth', 
        'opsconductor.jobs',
        'opsconductor.system',
        'opsconductor.dlx'
    ]
    
    for exchange in exchanges:
        try:
            channel.exchange_declare(exchange=exchange, passive=True)
            print(f'✅ Exchange {exchange} exists')
        except Exception as e:
            print(f'❌ Exchange {exchange} not found: {e}')
    
    connection.close()
    print('✅ RabbitMQ setup verification completed')
    
except Exception as e:
    print(f'❌ Verification failed: {e}')
    sys.exit(1)
"
}

# Function to show RabbitMQ management info
show_management_info() {
    echo -e "${BLUE}==============================================================================${NC}"
    echo -e "${BLUE}RabbitMQ Management Information${NC}"
    echo -e "${BLUE}==============================================================================${NC}"
    echo -e "${GREEN}Management UI:${NC} http://$RABBITMQ_HOST:15672"
    echo -e "${GREEN}Username:${NC} $RABBITMQ_USER"
    echo -e "${GREEN}Password:${NC} $RABBITMQ_PASS"
    echo ""
    echo -e "${YELLOW}Key Exchanges Created:${NC}"
    echo "  • opsconductor.events - Main events exchange"
    echo "  • opsconductor.auth   - Authentication events"
    echo "  • opsconductor.jobs   - Job-related events"
    echo "  • opsconductor.system - System monitoring events"
    echo "  • opsconductor.dlx    - Dead letter exchange"
    echo ""
    echo -e "${YELLOW}Service Queues Created:${NC}"
    echo "  • auth-service.events"
    echo "  • user-service.events"
    echo "  • universal-targets.events"
    echo "  • job-management.events"
    echo "  • job-execution.events"
    echo "  • job-scheduling.events"
    echo "  • audit-events.events"
    echo "  • system.health-checks"
    echo "  • system.alerts"
    echo -e "${BLUE}==============================================================================${NC}"
}

# Main execution
main() {
    echo -e "${GREEN}Starting RabbitMQ setup for OpsConductor microservices...${NC}"
    echo ""
    
    # Check prerequisites
    install_dependencies
    check_rabbitmq
    
    # Run setup
    run_setup
    
    # Verify setup
    verify_setup
    
    # Show management info
    show_management_info
    
    echo ""
    echo -e "${GREEN}🎉 RabbitMQ setup completed successfully!${NC}"
    echo -e "${GREEN}You can now start the OpsConductor microservices.${NC}"
}

# Handle script arguments
case "${1:-}" in
    "check")
        check_rabbitmq
        ;;
    "verify")
        verify_setup
        ;;
    "info")
        show_management_info
        ;;
    *)
        main
        ;;
esac