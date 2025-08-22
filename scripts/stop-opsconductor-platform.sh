#!/bin/bash

# =============================================================================
# 🛑 OpsConductor Platform - Complete Shutdown Script
# =============================================================================
# Safely stops all OpsConductor services and workers
#
# Usage: ./scripts/stop-opsconductor-platform.sh [options]
# Options:
#   --clean     Remove containers and networks (keeps volumes)
#   --purge     Remove everything including volumes (DATA LOSS!)
#   --workers   Stop only distributed workers
#   --platform  Stop only main platform (keep workers)
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
🛑 OpsConductor Platform - Complete Shutdown Script

USAGE:
    ./scripts/stop-opsconductor-platform.sh [OPTIONS]

OPTIONS:
    --clean     Remove containers and networks (keeps volumes)
    --purge     Remove everything including volumes (⚠️  DATA LOSS!)
    --workers   Stop only distributed workers
    --platform  Stop only main platform (keep workers)
    --help      Show this help message

EXAMPLES:
    # Standard shutdown (keeps everything for restart)
    ./scripts/stop-opsconductor-platform.sh
    
    # Clean shutdown (removes containers, keeps data)
    ./scripts/stop-opsconductor-platform.sh --clean
    
    # Complete purge (⚠️  DELETES ALL DATA)
    ./scripts/stop-opsconductor-platform.sh --purge
    
    # Stop only workers
    ./scripts/stop-opsconductor-platform.sh --workers

SHUTDOWN ORDER:
    1. 🌐 API Gateway & Frontend
    2. 🔧 Microservices
    3. 🚀 Distributed Workers
    4. 🗄️ Databases & Storage
    5. 🌐 Networks (if --clean or --purge)
    6. 💾 Volumes (if --purge only)

EOF
}

# Stop main platform
stop_main_platform() {
    log_step "🛑 Stopping Main Platform Services"
    
    cd "$ROOT_DIR"
    
    # Stop in reverse order of startup
    log_info "Stopping API gateway and frontend..."
    docker compose stop nginx frontend 2>/dev/null || true
    
    log_info "Stopping microservices..."
    docker compose stop \
        auth-service user-service targets-service jobs-service \
        execution-service audit-events-service target-discovery-service \
        notification-service 2>/dev/null || true
    
    log_info "Stopping infrastructure..."
    docker compose stop \
        postgres redis auth-postgres user-postgres targets-postgres \
        jobs-postgres execution-postgres audit-postgres notification-postgres \
        minio portainer 2>/dev/null || true
    
    log_success "Main platform stopped"
}

# Stop workers
stop_workers() {
    log_step "🛑 Stopping Distributed Workers"
    
    cd "$ROOT_DIR/services/execution-service"
    
    log_info "Stopping workers and Node-RED..."
    docker compose -f docker-compose.workers.yml stop 2>/dev/null || true
    
    log_success "Distributed workers stopped"
}

# Clean containers and networks
clean_containers() {
    log_step "🧹 Cleaning Containers and Networks"
    
    cd "$ROOT_DIR"
    
    log_info "Removing main platform containers..."
    docker compose down --remove-orphans 2>/dev/null || true
    
    cd "$ROOT_DIR/services/execution-service"
    log_info "Removing worker containers..."
    docker compose -f docker-compose.workers.yml down --remove-orphans 2>/dev/null || true
    
    # Clean up any orphaned containers
    log_info "Cleaning orphaned containers..."
    docker container prune -f 2>/dev/null || true
    
    # Clean up networks
    log_info "Cleaning networks..."
    docker network prune -f 2>/dev/null || true
    
    log_success "Containers and networks cleaned"
}

# Purge everything including volumes
purge_everything() {
    log_step "🗑️  Purging All Data (INCLUDING VOLUMES)"
    
    read -p "⚠️  This will DELETE ALL DATA including databases. Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Purge cancelled"
        return 1
    fi
    
    clean_containers
    
    log_info "Removing volumes..."
    
    # Remove OpsConductor specific volumes
    docker volume ls -q | grep -E "(opsconductor|postgres_data|redis_data|minio_data|execution|portainer)" | xargs -r docker volume rm 2>/dev/null || true
    
    # Clean up any remaining unused volumes
    log_warning "Cleaning all unused volumes..."
    docker volume prune -f 2>/dev/null || true
    
    # Clean up images if requested
    read -p "Also remove OpsConductor images? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Removing OpsConductor images..."
        docker image ls --format "{{.Repository}}:{{.Tag}}" | grep -E "(opsconductor|execution-service)" | xargs -r docker image rm -f 2>/dev/null || true
    fi
    
    log_success "Complete purge completed"
}

# Show final status
show_final_status() {
    log_step "📊 Final Status Check"
    
    local running_containers
    running_containers=$(docker ps --format "{{.Names}}" | grep -E "(opsconductor|execution|system|node-red)" | wc -l)
    
    if [[ $running_containers -eq 0 ]]; then
        log_success "✅ All OpsConductor services stopped"
    else
        log_warning "⚠️  $running_containers OpsConductor containers still running:"
        docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(opsconductor|execution|system|node-red)" || true
    fi
    
    # Check volumes
    local volumes
    volumes=$(docker volume ls -q | grep -E "(opsconductor|postgres_data|redis_data|minio_data|execution)" | wc -l)
    
    if [[ $volumes -gt 0 ]]; then
        log_info "📦 $volumes data volumes preserved"
    else
        log_warning "💾 No data volumes found (may have been purged)"
    fi
}

# Main shutdown function
shutdown_platform() {
    local stop_workers_flag="$1"
    local stop_platform_flag="$2"
    local clean_flag="$3"
    local purge_flag="$4"
    
    log_step "🛑 Shutting Down OpsConductor Platform"
    
    if [[ "$stop_platform_flag" == "true" ]]; then
        stop_main_platform
    fi
    
    if [[ "$stop_workers_flag" == "true" ]]; then
        stop_workers
    fi
    
    if [[ "$purge_flag" == "true" ]]; then
        purge_everything
    elif [[ "$clean_flag" == "true" ]]; then
        clean_containers
    fi
    
    show_final_status
    
    if [[ "$purge_flag" == "true" ]]; then
        log_success "🗑️  OpsConductor Platform completely purged"
        log_info "💡 Use './scripts/start-opsconductor-platform.sh --fresh' to restart from scratch"
    elif [[ "$clean_flag" == "true" ]]; then
        log_success "🧹 OpsConductor Platform cleaned"  
        log_info "💡 Use './scripts/start-opsconductor-platform.sh' to restart"
    else
        log_success "🛑 OpsConductor Platform stopped"
        log_info "💡 Use './scripts/start-opsconductor-platform.sh' to restart"
        log_info "💡 Use --clean to remove containers or --purge to remove all data"
    fi
}

# Main script logic
main() {
    local clean_flag="false"
    local purge_flag="false"
    local workers_only="false"
    local platform_only="false"
    local stop_workers_flag="true"
    local stop_platform_flag="true"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --clean)
                clean_flag="true"
                shift
                ;;
            --purge)
                purge_flag="true"
                shift
                ;;
            --workers)
                workers_only="true"
                stop_platform_flag="false"
                shift
                ;;
            --platform)
                platform_only="true"
                stop_workers_flag="false"
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
    
    # Shutdown services
    shutdown_platform "$stop_workers_flag" "$stop_platform_flag" "$clean_flag" "$purge_flag"
}

# Run main function with all arguments
main "$@"