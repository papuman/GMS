#!/bin/bash
# Health Check Script for Odoo E-Invoicing System
# Monitors all critical components and sends alerts on failures
# Usage: ./scripts/health_check.sh [--alert-email email@example.com]

set -u

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ALERT_EMAIL=""
SEND_ALERTS=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --alert-email)
            ALERT_EMAIL="$2"
            SEND_ALERTS=true
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--alert-email email@example.com]"
            exit 1
            ;;
    esac
done

# Load environment
if [ -f "${MODULE_DIR}/docker/.env" ]; then
    source "${MODULE_DIR}/docker/.env"
fi

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Status tracking
FAILURES=0
WARNINGS=0
ALERT_MESSAGE=""

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    WARNINGS=$((WARNINGS + 1))
    ALERT_MESSAGE="${ALERT_MESSAGE}\n[WARNING] $1"
}

log_failure() {
    echo -e "${RED}[FAIL]${NC} $1"
    FAILURES=$((FAILURES + 1))
    ALERT_MESSAGE="${ALERT_MESSAGE}\n[FAIL] $1"
}

# Send alert email
send_alert() {
    if [ "$SEND_ALERTS" = true ] && [ -n "$ALERT_EMAIL" ]; then
        echo -e "Health Check Alert - $(date)\n${ALERT_MESSAGE}" | \
            mail -s "[ALERT] GMS Odoo Health Check Failed" "$ALERT_EMAIL"
    fi
}

echo "========================================="
echo "Health Check - $(date)"
echo "========================================="
echo ""

# 1. Check Docker daemon
echo "1. Docker Daemon:"
if docker info >/dev/null 2>&1; then
    log_success "Docker daemon is running"
else
    log_failure "Docker daemon is not running"
fi

# 2. Check container status
echo ""
echo "2. Container Status:"
cd "${MODULE_DIR}/docker"

# Check if containers exist
if docker-compose ps >/dev/null 2>&1; then
    # Check Odoo
    if docker-compose ps odoo | grep -q "Up"; then
        log_success "Odoo container is running"
    else
        log_failure "Odoo container is not running"
    fi

    # Check PostgreSQL
    if docker-compose ps db | grep -q "Up"; then
        log_success "PostgreSQL container is running"
    else
        log_failure "PostgreSQL container is not running"
    fi

    # Check Nginx
    if docker-compose ps nginx | grep -q "Up"; then
        log_success "Nginx container is running"
    else
        log_failure "Nginx container is not running"
    fi

    # Check Redis (optional)
    if docker-compose ps redis | grep -q "Up"; then
        log_success "Redis container is running"
    else
        log_warning "Redis container is not running (optional)"
    fi
else
    log_failure "Cannot get container status"
fi

# 3. Check Odoo HTTP endpoint
echo ""
echo "3. Odoo HTTP Endpoint:"
if curl -sf http://localhost/web/health >/dev/null 2>&1; then
    log_success "Odoo HTTP endpoint is responding"
else
    log_failure "Odoo HTTP endpoint is not responding"
fi

# 4. Check database connectivity
echo ""
echo "4. Database Connectivity:"
if docker-compose exec -T db pg_isready -U "${POSTGRES_USER:-odoo}" >/dev/null 2>&1; then
    log_success "PostgreSQL is ready"

    # Check database size
    db_size=$(docker-compose exec -T db psql -U "${POSTGRES_USER:-odoo}" -d "${POSTGRES_DB:-odoo}" -t -c "SELECT pg_size_pretty(pg_database_size('${POSTGRES_DB:-odoo}'));" 2>/dev/null | xargs)
    if [ -n "$db_size" ]; then
        log_success "Database size: $db_size"
    fi
else
    log_failure "PostgreSQL is not ready"
fi

# 5. Check disk space
echo ""
echo "5. Disk Space:"
available_space=$(df -BG "${MODULE_DIR}" | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$available_space" -gt 10 ]; then
    log_success "Disk space: ${available_space}GB available"
elif [ "$available_space" -gt 5 ]; then
    log_warning "Disk space: ${available_space}GB available (running low)"
else
    log_failure "Disk space: ${available_space}GB available (critical)"
fi

# 6. Check SSL certificate expiry
echo ""
echo "6. SSL Certificate:"
ssl_cert="${MODULE_DIR}/docker/ssl/fullchain.pem"
if [ -f "$ssl_cert" ]; then
    expiry_date=$(openssl x509 -enddate -noout -in "$ssl_cert" 2>/dev/null | cut -d= -f2)
    if [ -n "$expiry_date" ]; then
        expiry_epoch=$(date -d "$expiry_date" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$expiry_date" +%s 2>/dev/null)
        current_epoch=$(date +%s)
        days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))

        if [ "$days_until_expiry" -gt 30 ]; then
            log_success "SSL certificate valid for $days_until_expiry days"
        elif [ "$days_until_expiry" -gt 7 ]; then
            log_warning "SSL certificate expires in $days_until_expiry days"
        else
            log_failure "SSL certificate expires in $days_until_expiry days (urgent renewal needed)"
        fi
    else
        log_warning "Cannot determine SSL certificate expiry"
    fi
else
    log_warning "SSL certificate not found at $ssl_cert"
fi

# 7. Check Hacienda API connectivity
echo ""
echo "7. Hacienda API Connectivity:"
if [ -n "${HACIENDA_API_URL:-}" ]; then
    if curl -sf "${HACIENDA_API_URL}/health" >/dev/null 2>&1 || \
       curl -sf "${HACIENDA_API_URL}" >/dev/null 2>&1; then
        log_success "Hacienda API is reachable"
    else
        log_warning "Hacienda API is not reachable (check credentials or network)"
    fi
else
    log_warning "HACIENDA_API_URL not configured"
fi

# 8. Check memory usage
echo ""
echo "8. Memory Usage:"
# Odoo container memory
odoo_mem=$(docker stats --no-stream --format "{{.MemUsage}}" gms_odoo 2>/dev/null | awk '{print $1}')
if [ -n "$odoo_mem" ]; then
    log_success "Odoo memory usage: $odoo_mem"
fi

# Database container memory
db_mem=$(docker stats --no-stream --format "{{.MemUsage}}" gms_postgres 2>/dev/null | awk '{print $1}')
if [ -n "$db_mem" ]; then
    log_success "PostgreSQL memory usage: $db_mem"
fi

# 9. Check logs for errors
echo ""
echo "9. Recent Errors in Logs:"
error_count=$(docker-compose logs --tail=100 odoo 2>/dev/null | grep -i "error" | grep -v "ERROR:werkzeug" | wc -l)
if [ "$error_count" -eq 0 ]; then
    log_success "No recent errors in Odoo logs"
elif [ "$error_count" -lt 10 ]; then
    log_warning "$error_count errors found in recent logs"
else
    log_failure "$error_count errors found in recent logs"
fi

# 10. Check backup status
echo ""
echo "10. Backup Status:"
backup_dir="${MODULE_DIR}/docker/backups"
if [ -d "$backup_dir" ]; then
    latest_backup=$(ls -t "$backup_dir"/odoo_backup_*.dump 2>/dev/null | head -1)
    if [ -n "$latest_backup" ]; then
        backup_age=$(( ($(date +%s) - $(stat -f %m "$latest_backup" 2>/dev/null || stat -c %Y "$latest_backup" 2>/dev/null)) / 86400 ))
        if [ "$backup_age" -le 1 ]; then
            log_success "Latest backup is $backup_age days old"
        elif [ "$backup_age" -le 7 ]; then
            log_warning "Latest backup is $backup_age days old"
        else
            log_failure "Latest backup is $backup_age days old (backups may be failing)"
        fi
    else
        log_warning "No backups found"
    fi
else
    log_warning "Backup directory not found"
fi

# Summary
echo ""
echo "========================================="
echo "Health Check Summary"
echo "========================================="

if [ $FAILURES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}Status: HEALTHY${NC}"
    echo "All checks passed successfully"
    exit 0
elif [ $FAILURES -eq 0 ]; then
    echo -e "${YELLOW}Status: HEALTHY (with warnings)${NC}"
    echo "Warnings: $WARNINGS"
    exit 0
else
    echo -e "${RED}Status: UNHEALTHY${NC}"
    echo "Failures: $FAILURES"
    echo "Warnings: $WARNINGS"

    # Send alert
    send_alert

    exit 1
fi
