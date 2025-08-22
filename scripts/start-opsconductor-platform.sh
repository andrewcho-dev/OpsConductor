#!/bin/bash

# =============================================================================
# 🚀 OpsConductor Platform - Complete Startup Script
# =============================================================================
# Initializes and starts the complete microservices architecture
#
# Usage: ./scripts/start-opsconductor-platform.sh [options]
# Options:
#   --fresh     Clean start (removes all containers and volumes)
#   --rebuild   Rebuild all images before starting
#   --workers   Start only distributed workers
#   --platform  Start only main platform (no workers)
#   --status    Show current status without starting
#   --help      Show this help message
# =============================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
WORKERS_COMPOSE="$ROOT_DIR/services/execution-service/docker-compose.workers.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${PURPLE}[STEP]${NC} $1"; }

# Help message
show_help() {
    cat << EOF
🚀 OpsConductor Platform - Complete Startup Script

USAGE:
    ./scripts/start-opsconductor-platform.sh [OPTIONS]

OPTIONS:
    --fresh     Clean start (removes all containers and volumes)
    --rebuild   Rebuild all images before starting  
    --workers   Start only distributed workers
    --platform  Start only main platform (no workers)
    --status    Show current status without starting
    --help      Show this help message

EXAMPLES:
    # Full platform startup
    ./scripts/start-opsconductor-platform.sh
    
    # Clean restart with rebuild
    ./scripts/start-opsconductor-platform.sh --fresh --rebuild
    
    # Start only workers
    ./scripts/start-opsconductor-platform.sh --workers
    
    # Check current status
    ./scripts/start-opsconductor-platform.sh --status

ARCHITECTURE:
    🌐 Frontend & Gateway Layer
    🔧 Core Microservices (9 services)
    🚀 Distributed Execution Layer (3 workers)
    🗄️ Database Layer (8 dedicated DBs)
    💾 Storage & Management Layer

EOF
}

# Status check function
show_status() {
    log_step "🔍 Checking OpsConductor Platform Status"
    
    echo -e "\n${CYAN}=== MAIN PLATFORM STATUS ===${NC}"
    cd "$ROOT_DIR"
    if docker compose ps --format "table {{.Name}}\t{{.Image}}\t{{.Status}}" 2>/dev/null | grep -q "opsconductor"; then
        docker compose ps --format "table {{.Name}}\t{{.Image}}\t{{.Status}}"
    else
        echo "❌ Main platform services not running"
    fi
    
    echo -e "\n${CYAN}=== DISTRIBUTED WORKERS STATUS ===${NC}"
    cd "$ROOT_DIR/services/execution-service"
    if docker compose -f docker-compose.workers.yml ps --format "table {{.Name}}\t{{.Image}}\t{{.Status}}" 2>/dev/null | grep -q "execution\|system\|node-red"; then
        docker compose -f docker-compose.workers.yml ps --format "table {{.Name}}\t{{.Image}}\t{{.Status}}"
    else
        echo "❌ Distributed workers not running"
    fi
    
    echo -e "\n${CYAN}=== NETWORK STATUS ===${NC}"
    if docker network ls | grep -q "opsconductor-network"; then
        echo "✅ OpsConductor network exists"
    else
        echo "❌ OpsConductor network not found"
    fi
    
    echo -e "\n${CYAN}=== VOLUME STATUS ===${NC}"
    echo "📦 Docker Volumes:"
    docker volume ls | grep -E "(postgres_data|redis_data|minio_data|execution)" || echo "❌ No OpsConductor volumes found"
}

# Clean shutdown function
clean_shutdown() {
    log_step "🧹 Performing Clean Shutdown"
    
    cd "$ROOT_DIR"
    log_info "Stopping main platform services..."
    docker compose down --remove-orphans 2>/dev/null || true
    
    cd "$ROOT_DIR/services/execution-service"  
    log_info "Stopping distributed workers..."
    docker compose -f docker-compose.workers.yml down --remove-orphans 2>/dev/null || true
    
    log_success "All services stopped"
}

# Fresh start function
fresh_start() {
    log_step "🔄 Performing Fresh Start (Removing all data)"
    
    read -p "⚠️  This will DELETE ALL DATA. Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Fresh start cancelled"
        return 1
    fi
    
    clean_shutdown
    
    log_info "Removing containers and volumes..."
    docker system prune -f --volumes 2>/dev/null || true
    
    # Remove specific volumes
    docker volume rm $(docker volume ls -q | grep -E "(opsconductor|postgres_data|redis_data|minio_data|execution)") 2>/dev/null || true
    
    log_success "Fresh start completed"
}

# Environment setup
setup_environment() {
    log_step "🔧 Setting up Environment"
    
    cd "$ROOT_DIR"
    
    # Check for .env file
    if [[ ! -f .env ]]; then
        if [[ -f .env.production ]]; then
            log_info "Copying .env.production to .env"
            cp .env.production .env
        else
            log_error ".env file not found. Please create one from .env.example"
            exit 1
        fi
    fi
    
    # Load environment variables
    source .env
    
    # Create logs directory
    mkdir -p logs
    chmod 755 logs
    
    # Create SSL directory and certificates if not exist
    mkdir -p nginx/ssl
    if [[ ! -f nginx/ssl/cert.pem ]] || [[ ! -f nginx/ssl/key.pem ]]; then
        log_info "Generating self-signed SSL certificates..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/key.pem \
            -out nginx/ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=OpsConductor/CN=localhost" 2>/dev/null || true
    fi
    
    log_success "Environment setup completed"
}

# Build services
build_services() {
    local rebuild_flag="$1"
    
    log_step "🏗️ Building Services"
    
    cd "$ROOT_DIR"
    
    if [[ "$rebuild_flag" == "true" ]]; then
        log_info "Building main platform services (with rebuild)..."
        docker compose build --no-cache --parallel
    else
        log_info "Building main platform services..."
        docker compose build --parallel
    fi
    
    cd "$ROOT_DIR/services/execution-service"
    if [[ "$rebuild_flag" == "true" ]]; then
        log_info "Building distributed workers (with rebuild)..."
        docker compose -f docker-compose.workers.yml build --no-cache --parallel
    else
        log_info "Building distributed workers..."
        docker compose -f docker-compose.workers.yml build --parallel
    fi
    
    log_success "All services built successfully"
}

# Start infrastructure (databases, cache, storage)
start_infrastructure() {
    log_step "🗄️ Starting Infrastructure Layer"
    
    cd "$ROOT_DIR"
    
    log_info "Starting databases and cache..."
    docker compose up -d \
        postgres redis \
        auth-postgres user-postgres targets-postgres jobs-postgres \
        execution-postgres audit-postgres notification-postgres \
        minio portainer
    
    log_info "Waiting for infrastructure to be healthy..."
    local retries=0
    local max_retries=30
    
    while [[ $retries -lt $max_retries ]]; do
        if docker compose ps --filter "status=running" --filter "health=healthy" | grep -q "postgres\|redis"; then
            log_success "Infrastructure services are healthy"
            break
        fi
        
        retries=$((retries + 1))
        log_info "Waiting for infrastructure... ($retries/$max_retries)"
        sleep 10
    done
    
    if [[ $retries -eq $max_retries ]]; then
        log_error "Infrastructure failed to start within timeout"
        return 1
    fi
}

# Start microservices
start_microservices() {
    log_step "🔧 Starting Core Microservices"
    
    cd "$ROOT_DIR"
    
    log_info "Starting auth and user services first..."
    docker compose up -d auth-service user-service
    sleep 15
    
    log_info "Starting remaining microservices..."
    docker compose up -d \
        targets-service jobs-service execution-service \
        audit-events-service target-discovery-service notification-service
    
    log_info "Waiting for microservices to be healthy..."
    sleep 30
    
    log_success "Core microservices started"
}

# Start workers
start_workers() {
    log_step "🚀 Starting Distributed Workers"
    
    cd "$ROOT_DIR/services/execution-service"
    
    log_info "Starting distributed workers and Node-RED..."
    docker compose -f docker-compose.workers.yml up -d
    
    log_info "Waiting for workers to be healthy..."
    sleep 20
    
    log_success "Distributed workers started"
}

# Start frontend and gateway
start_frontend_gateway() {
    log_step "🌐 Starting Frontend & Gateway"
    
    cd "$ROOT_DIR"
    
    log_info "Starting frontend..."
    docker compose up -d frontend
    sleep 10
    
    log_info "Starting API gateway..."
    docker compose up -d nginx
    
    log_success "Frontend and gateway started"
}

# Health check
perform_health_check() {
    log_step "🩺 Performing Health Check"
    
    cd "$ROOT_DIR"
    
    local services=(
        "https://localhost/health:Gateway"
        "https://localhost:Frontend" 
        "http://localhost:9000:Portainer"
        "http://localhost:9090:MinIO Console"
    )
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r url name <<< "$service_info"
        if curl -k -s --max-time 10 "$url" > /dev/null 2>&1; then
            log_success "$name is accessible"
        else
            log_warning "$name is not accessible at $url"
        fi
    done
    
    # Check service health
    log_info "Checking service health status..."
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
}

# Initialize databases
initialize_databases() {
    log_step "💾 Initializing Databases"
    
    cd "$ROOT_DIR"
    
    log_info "Running database initialization scripts..."
    
    # Main database initialization
    if docker compose exec -T postgres psql -U ${POSTGRES_USER:-opsconductor} -d ${POSTGRES_DB:-opsconductor} -c "SELECT 1;" > /dev/null 2>&1; then
        log_success "Main database is accessible"
    else
        log_warning "Main database is not ready"
    fi
    
    # Service databases initialization
    local db_services=("auth-postgres" "user-postgres" "targets-postgres" "jobs-postgres" "audit-postgres" "notification-postgres")
    
    for db_service in "${db_services[@]}"; do
        if docker compose ps "$db_service" | grep -q "healthy"; then
            log_success "$db_service is healthy"
        else
            log_warning "$db_service is not healthy"
        fi
    done
}

# Create admin user
create_admin_user() {
    log_step "👤 Creating Admin User"
    
    cd "$ROOT_DIR"
    
    if [[ -f create_admin_user.py ]]; then
        log_info "Running admin user creation script..."
        python3 create_admin_user.py || log_warning "Admin user creation failed or user already exists"
    else
        log_warning "Admin user creation script not found"
    fi
}

# Main startup function
start_platform() {
    local start_workers_flag="$1"
    local start_platform_flag="$2"
    local rebuild_flag="$3"
    
    log_step "🚀 Starting OpsConductor Platform"
    
    setup_environment
    
    if [[ "$rebuild_flag" == "true" ]] || [[ "$start_platform_flag" == "true" ]]; then
        build_services "$rebuild_flag"
    fi
    
    if [[ "$start_platform_flag" == "true" ]]; then
        start_infrastructure
        initialize_databases
        start_microservices
        start_frontend_gateway
        create_admin_user
    fi
    
    if [[ "$start_workers_flag" == "true" ]]; then
        start_workers
    fi
    
    if [[ "$start_platform_flag" == "true" ]] && [[ "$start_workers_flag" == "true" ]]; then
        perform_health_check
        
        log_success "🎉 OpsConductor Platform Started Successfully!"
        echo -e "\n${GREEN}=== ACCESS POINTS ===${NC}"
        echo -e "🌐 Main Application: ${CYAN}https://localhost${NC}"
        echo -e "🐳 Portainer: ${CYAN}http://localhost:9000${NC}"
        echo -e "📦 MinIO Console: ${CYAN}http://localhost:9090${NC}"
        echo -e "🔴 Node-RED: ${CYAN}http://localhost:1880${NC}"
        echo -e "\n${YELLOW}Note: Use --status to check service health${NC}"
    fi
}

# Main script logic
main() {
    local fresh_flag="false"
    local rebuild_flag="false"
    local workers_only="false"
    local platform_only="false"
    local status_only="false"
    local start_workers_flag="true"
    local start_platform_flag="true"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --fresh)
                fresh_flag="true"
                shift
                ;;
            --rebuild)
                rebuild_flag="true"
                shift
                ;;
            --workers)
                workers_only="true"
                start_platform_flag="false"
                shift
                ;;
            --platform)
                platform_only="true"
                start_workers_flag="false"
                shift
                ;;
            --status)
                status_only="true"
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Handle status-only request
    if [[ "$status_only" == "true" ]]; then
        show_status
        exit 0
    fi
    
    # Handle fresh start
    if [[ "$fresh_flag" == "true" ]]; then
        fresh_start
    fi
    
    # Start services
    start_platform "$start_workers_flag" "$start_platform_flag" "$rebuild_flag"
}

# Run main function with all arguments
main "$@"