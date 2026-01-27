#!/bin/bash

################################################################################
# GMS Staging Deployment Script
# Version: 19.0.1.8.0
# Purpose: Deploy l10n_cr_einvoice module to local staging environment
# Environment: Staging (Docker-based)
################################################################################

set -e  # Exit on any error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DOCKER_DIR="${PROJECT_ROOT}/docker"
COMPOSE_FILE="${DOCKER_DIR}/docker-compose.staging.yml"
ENV_FILE="${DOCKER_DIR}/.env.staging"
LOG_FILE="${PROJECT_ROOT}/staging_deployment_$(date +%Y%m%d_%H%M%S).log"
MODULE_VERSION="19.0.1.8.0"

# Required ports
REQUIRED_PORTS=(8070 8080 5433 9091 3001)
# Required disk space in GB
REQUIRED_DISK_GB=10

################################################################################
# Functions
################################################################################

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "${LOG_FILE}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "${LOG_FILE}"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "${LOG_FILE}"
}

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1" | tee -a "${LOG_FILE}"
}

print_header() {
    echo -e "${CYAN}"
    echo "=========================================================================="
    echo "  GMS Staging Deployment - Costa Rica E-Invoicing Module"
    echo "  Version: ${MODULE_VERSION}"
    echo "  Environment: Staging (Local Docker)"
    echo "=========================================================================="
    echo -e "${NC}"
}

check_docker() {
    log_info "Checking Docker installation..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker Desktop."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker Desktop."
        exit 1
    fi

    local docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    log "Docker version: ${docker_version}"

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed."
        exit 1
    fi

    local compose_version=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    log "Docker Compose version: ${compose_version}"
}

check_ports() {
    log_info "Checking required ports availability..."

    local ports_in_use=()

    for port in "${REQUIRED_PORTS[@]}"; do
        if lsof -Pi :${port} -sTCP:LISTEN -t >/dev/null 2>&1; then
            ports_in_use+=("${port}")
            log_warning "Port ${port} is already in use"
        else
            log "Port ${port} is available"
        fi
    done

    if [ ${#ports_in_use[@]} -gt 0 ]; then
        log_error "The following ports are in use: ${ports_in_use[*]}"
        log_error "Please stop services using these ports or modify the configuration."
        exit 1
    fi
}

check_disk_space() {
    log_info "Checking available disk space..."

    local available_gb=$(df -g "${PROJECT_ROOT}" | awk 'NR==2 {print $4}')

    if [ "${available_gb}" -lt "${REQUIRED_DISK_GB}" ]; then
        log_error "Insufficient disk space. Required: ${REQUIRED_DISK_GB}GB, Available: ${available_gb}GB"
        exit 1
    fi

    log "Available disk space: ${available_gb}GB"
}

check_required_files() {
    log_info "Checking required files..."

    local required_files=(
        "${COMPOSE_FILE}"
        "${ENV_FILE}"
        "${PROJECT_ROOT}/__manifest__.py"
        "${PROJECT_ROOT}/models/__init__.py"
    )

    for file in "${required_files[@]}"; do
        if [ ! -f "${file}" ]; then
            log_error "Required file not found: ${file}"
            exit 1
        fi
    done

    log "All required files present"
}

preflight_checks() {
    log_info "Running pre-flight checks..."

    check_docker
    check_ports
    check_disk_space
    check_required_files

    log "Pre-flight checks completed successfully"
}

build_images() {
    log_info "Building Docker images..."

    cd "${PROJECT_ROOT}"

    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" build --no-cache 2>&1 | tee -a "${LOG_FILE}"

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log "Docker images built successfully"
    else
        log_error "Failed to build Docker images"
        exit 1
    fi
}

start_services() {
    log_info "Starting staging services..."

    cd "${PROJECT_ROOT}"

    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d 2>&1 | tee -a "${LOG_FILE}"

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log "Services started successfully"
    else
        log_error "Failed to start services"
        exit 1
    fi
}

wait_for_services() {
    log_info "Waiting for services to be ready..."

    local max_attempts=30
    local attempt=0

    # Wait for PostgreSQL
    log "Waiting for PostgreSQL..."
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T postgres-staging pg_isready -U odoo_staging >/dev/null 2>&1; then
            log "PostgreSQL is ready"
            break
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    if [ $attempt -eq $max_attempts ]; then
        log_error "PostgreSQL failed to start"
        exit 1
    fi

    # Wait for Redis
    log "Waiting for Redis..."
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T redis-staging redis-cli ping >/dev/null 2>&1; then
            log "Redis is ready"
            break
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    if [ $attempt -eq $max_attempts ]; then
        log_error "Redis failed to start"
        exit 1
    fi

    # Wait for Odoo
    log "Waiting for Odoo (this may take 60-90 seconds)..."
    attempt=0
    max_attempts=60
    while [ $attempt -lt $max_attempts ]; do
        if curl -sf http://localhost:8070/web/health >/dev/null 2>&1; then
            log "Odoo is ready"
            break
        fi
        attempt=$((attempt + 1))
        sleep 3
    done

    if [ $attempt -eq $max_attempts ]; then
        log_error "Odoo failed to start"
        log_info "Checking Odoo logs:"
        docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" logs --tail=50 odoo-staging
        exit 1
    fi

    log "All services are ready"
}

initialize_database() {
    log_info "Initializing database and installing module..."

    # Create database and install module
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T odoo-staging \
        odoo -d staging_gms \
        --init=l10n_cr_einvoice \
        --without-demo=all \
        --stop-after-init 2>&1 | tee -a "${LOG_FILE}"

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log "Module installed successfully"
    else
        log_error "Failed to install module"
        exit 1
    fi

    # Restart Odoo to apply changes
    log_info "Restarting Odoo..."
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" restart odoo-staging

    # Wait for Odoo to be ready again
    sleep 10
    wait_for_services
}

run_smoke_tests() {
    log_info "Running smoke tests..."

    if [ -f "${PROJECT_ROOT}/deployment/staging_tests.py" ]; then
        python3 "${PROJECT_ROOT}/deployment/staging_tests.py" 2>&1 | tee -a "${LOG_FILE}"

        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            log "Smoke tests passed"
        else
            log_warning "Some smoke tests failed. Check logs for details."
        fi
    else
        log_warning "Smoke tests script not found. Skipping."
    fi
}

display_access_info() {
    echo ""
    echo -e "${CYAN}=========================================================================="
    echo "  Staging Environment Deployed Successfully!"
    echo -e "==========================================================================${NC}"
    echo ""
    echo -e "${GREEN}Access Information:${NC}"
    echo -e "  Odoo Web Interface:    ${BLUE}http://localhost:8070${NC}"
    echo -e "  Nginx Proxy:           ${BLUE}http://localhost:8080${NC}"
    echo -e "  Grafana Dashboard:     ${BLUE}http://localhost:3001${NC}"
    echo -e "  Prometheus Metrics:    ${BLUE}http://localhost:9091${NC}"
    echo ""
    echo -e "${GREEN}Credentials:${NC}"
    echo -e "  Odoo Admin:            ${BLUE}admin${NC}"
    echo -e "  Odoo Password:         ${BLUE}StagingAdmin2024!SecurePass${NC}"
    echo -e "  Database:              ${BLUE}staging_gms${NC}"
    echo -e "  Grafana User:          ${BLUE}admin${NC}"
    echo -e "  Grafana Password:      ${BLUE}StagingGrafana2024!${NC}"
    echo ""
    echo -e "${GREEN}Services Status:${NC}"
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps
    echo ""
    echo -e "${GREEN}Next Steps:${NC}"
    echo "  1. Access Odoo at http://localhost:8070"
    echo "  2. Login with admin credentials"
    echo "  3. Go to Settings > Activate Developer Mode"
    echo "  4. Navigate to Hacienda > Configuration"
    echo "  5. Configure Hacienda sandbox credentials"
    echo "  6. Upload test certificate"
    echo "  7. Run test scenarios from deployment/STAGING_USER_GUIDE.md"
    echo ""
    echo -e "${YELLOW}Useful Commands:${NC}"
    echo "  View logs:             ${BLUE}docker-compose -f docker/docker-compose.staging.yml logs -f${NC}"
    echo "  Stop services:         ${BLUE}docker-compose -f docker/docker-compose.staging.yml stop${NC}"
    echo "  Start services:        ${BLUE}docker-compose -f docker/docker-compose.staging.yml start${NC}"
    echo "  Restart services:      ${BLUE}docker-compose -f docker/docker-compose.staging.yml restart${NC}"
    echo "  Clean up:              ${BLUE}./scripts/cleanup_staging.sh${NC}"
    echo ""
    echo -e "${GREEN}Log File:${NC} ${LOG_FILE}"
    echo ""
}

display_errors() {
    echo -e "${RED}=========================================================================="
    echo "  Deployment Failed!"
    echo -e "==========================================================================${NC}"
    echo ""
    echo "Check the log file for details: ${LOG_FILE}"
    echo ""
    echo "Common issues:"
    echo "  - Docker not running: Start Docker Desktop"
    echo "  - Ports in use: Stop conflicting services"
    echo "  - Insufficient disk space: Free up at least 10GB"
    echo ""
    echo "To view recent logs:"
    echo "  docker-compose -f ${COMPOSE_FILE} logs --tail=100"
    echo ""
}

cleanup_on_error() {
    log_error "Deployment failed. Cleaning up..."
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" down 2>&1 | tee -a "${LOG_FILE}"
}

################################################################################
# Main Execution
################################################################################

main() {
    print_header

    log "Starting staging deployment at $(date)"
    log "Project root: ${PROJECT_ROOT}"
    log "Log file: ${LOG_FILE}"

    # Run pre-flight checks
    preflight_checks

    # Build and deploy
    build_images
    start_services
    wait_for_services
    initialize_database

    # Validation
    run_smoke_tests

    # Success
    display_access_info

    log "Staging deployment completed successfully at $(date)"

    exit 0
}

# Error handling
trap 'log_error "Script interrupted"; cleanup_on_error; display_errors; exit 1' INT TERM
trap 'if [ $? -ne 0 ]; then display_errors; fi' EXIT

# Run main function
main "$@"
