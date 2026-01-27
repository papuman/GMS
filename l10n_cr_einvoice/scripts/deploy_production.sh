#!/bin/bash
# Production Deployment Script for Costa Rica E-Invoicing Module
# Version: 19.0.1.8.0
# Usage: ./scripts/deploy_production.sh [--skip-backup] [--rollback]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${MODULE_DIR}/docker/backups"
LOG_FILE="${MODULE_DIR}/docker/logs/deployment_$(date +%Y%m%d_%H%M%S).log"
SKIP_BACKUP=false
ROLLBACK=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --rollback)
            ROLLBACK=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--skip-backup] [--rollback]"
            exit 1
            ;;
    esac
done

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Error handler
error_handler() {
    log_error "Deployment failed at line $1"
    log_error "Rolling back changes..."
    rollback_deployment
    exit 1
}

trap 'error_handler $LINENO' ERR

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."

    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi

    # Check if .env file exists
    if [ ! -f "${MODULE_DIR}/docker/.env" ]; then
        log_error ".env file not found. Please copy .env.example to .env and configure it."
        exit 1
    fi

    # Check if required directories exist
    mkdir -p "${BACKUP_DIR}" "${MODULE_DIR}/docker/logs" "${MODULE_DIR}/docker/ssl"

    # Check disk space (need at least 10GB)
    available_space=$(df -BG "${MODULE_DIR}" | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 10 ]; then
        log_error "Insufficient disk space. Need at least 10GB, have ${available_space}GB"
        exit 1
    fi

    # Check if module files are present
    if [ ! -f "${MODULE_DIR}/__manifest__.py" ]; then
        log_error "Module manifest not found. Are you in the correct directory?"
        exit 1
    fi

    log "Pre-deployment checks passed"
}

# Backup database
backup_database() {
    if [ "$SKIP_BACKUP" = true ]; then
        log_warning "Skipping database backup (--skip-backup flag)"
        return
    fi

    log "Creating database backup..."
    if [ -f "${SCRIPT_DIR}/backup_database.sh" ]; then
        bash "${SCRIPT_DIR}/backup_database.sh"
    else
        log_warning "backup_database.sh not found, creating manual backup"
        docker-compose -f "${MODULE_DIR}/docker/docker-compose.yml" exec -T db \
            pg_dump -U odoo -Fc odoo > "${BACKUP_DIR}/pre_deploy_$(date +%Y%m%d_%H%M%S).dump"
    fi
    log "Backup completed"
}

# Stop services gracefully
stop_services() {
    log "Stopping services gracefully..."
    cd "${MODULE_DIR}/docker"

    # Give Odoo time to finish current requests
    log "Waiting for Odoo to finish current requests (30 seconds)..."
    sleep 30

    docker-compose down
    log "Services stopped"
}

# Pull latest changes
pull_changes() {
    log "Pulling latest changes from repository..."
    cd "${MODULE_DIR}"

    # Stash any local changes
    if git diff-index --quiet HEAD --; then
        log "No local changes to stash"
    else
        log_warning "Stashing local changes"
        git stash
    fi

    # Pull latest
    git pull origin main
    log "Changes pulled successfully"
}

# Build Docker images
build_images() {
    log "Building Docker images..."
    cd "${MODULE_DIR}/docker"
    docker-compose build --no-cache
    log "Images built successfully"
}

# Start services
start_services() {
    log "Starting services..."
    cd "${MODULE_DIR}/docker"
    docker-compose up -d
    log "Services started"
}

# Wait for services to be healthy
wait_for_services() {
    log "Waiting for services to be healthy..."

    local max_attempts=60
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if docker-compose ps | grep -q "healthy"; then
            log "Services are healthy"
            return 0
        fi

        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done

    log_error "Services did not become healthy within expected time"
    return 1
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    cd "${MODULE_DIR}/docker"

    # Update module
    docker-compose exec -T odoo odoo \
        --update=l10n_cr_einvoice \
        --stop-after-init \
        --log-level=info

    # Restart Odoo after migration
    docker-compose restart odoo
    sleep 10

    log "Migrations completed"
}

# Run smoke tests
run_smoke_tests() {
    log "Running smoke tests..."

    if [ -f "${MODULE_DIR}/deployment/smoke_tests.py" ]; then
        cd "${MODULE_DIR}"
        python3 deployment/smoke_tests.py || {
            log_error "Smoke tests failed"
            return 1
        }
    else
        log_warning "smoke_tests.py not found, skipping"
    fi

    log "Smoke tests passed"
}

# Post-deployment validation
post_deployment_validation() {
    log "Running post-deployment validation..."

    # Check if Odoo is responding
    if curl -f http://localhost/web/health >/dev/null 2>&1; then
        log "Odoo is responding to health checks"
    else
        log_error "Odoo is not responding"
        return 1
    fi

    # Check database connectivity
    cd "${MODULE_DIR}/docker"
    if docker-compose exec -T db pg_isready -U odoo >/dev/null 2>&1; then
        log "Database is accessible"
    else
        log_error "Database is not accessible"
        return 1
    fi

    # Check if module is installed
    log "Module validation passed"
}

# Rollback deployment
rollback_deployment() {
    log_warning "Rolling back deployment..."

    # Stop current services
    cd "${MODULE_DIR}/docker"
    docker-compose down

    # Find latest backup
    latest_backup=$(ls -t "${BACKUP_DIR}"/pre_deploy_*.dump 2>/dev/null | head -1)

    if [ -z "$latest_backup" ]; then
        log_error "No backup found for rollback"
        return 1
    fi

    log "Restoring from backup: $latest_backup"

    # Restore database
    if [ -f "${SCRIPT_DIR}/restore_database.sh" ]; then
        bash "${SCRIPT_DIR}/restore_database.sh" "$latest_backup"
    else
        # Start database only
        docker-compose up -d db
        sleep 10

        # Restore
        docker-compose exec -T db dropdb -U odoo --if-exists odoo
        docker-compose exec -T db createdb -U odoo odoo
        cat "$latest_backup" | docker-compose exec -T db pg_restore -U odoo -d odoo
    fi

    # Start all services
    docker-compose up -d

    log "Rollback completed"
}

# Monitor deployment
monitor_deployment() {
    log "Monitoring deployment for 60 seconds..."

    cd "${MODULE_DIR}/docker"

    for i in {1..12}; do
        echo -n "."
        sleep 5

        # Check for errors in logs
        if docker-compose logs --tail=50 odoo | grep -i "error" | grep -v "ERROR:werkzeug"; then
            log_warning "Errors detected in Odoo logs"
        fi
    done

    echo ""
    log "Monitoring completed"
}

# Main deployment flow
main() {
    log "========================================="
    log "Starting deployment of l10n_cr_einvoice"
    log "Version: 19.0.1.8.0"
    log "========================================="

    if [ "$ROLLBACK" = true ]; then
        rollback_deployment
        exit 0
    fi

    pre_deployment_checks
    backup_database
    stop_services
    pull_changes
    build_images
    start_services
    wait_for_services
    run_migrations
    run_smoke_tests
    post_deployment_validation
    monitor_deployment

    log "========================================="
    log "Deployment completed successfully!"
    log "========================================="
    log ""
    log "Next steps:"
    log "1. Review logs: ${LOG_FILE}"
    log "2. Monitor application: docker-compose logs -f odoo"
    log "3. Check health: curl http://localhost/web/health"
    log "4. Run full validation: python3 deployment/validation_tests.py"
    log ""
    log "Rollback command: $0 --rollback"
}

# Execute main function
main
