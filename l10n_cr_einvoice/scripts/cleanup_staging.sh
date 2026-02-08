#!/bin/bash

################################################################################
# GMS Staging Cleanup Script
# Version: 19.0.1.8.0
# Purpose: Clean up staging environment and optionally remove data
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/docker/docker-compose.staging.yml"
ENV_FILE="${PROJECT_ROOT}/docker/.env.staging"

echo -e "${YELLOW}"
echo "=========================================================================="
echo "  GMS Staging Environment Cleanup"
echo "=========================================================================="
echo -e "${NC}"

# Parse command line arguments
REMOVE_DATA=false
if [ "$1" = "--remove-data" ] || [ "$1" = "-d" ]; then
    REMOVE_DATA=true
    echo -e "${RED}WARNING: This will remove all staging data including databases!${NC}"
    echo -n "Are you sure you want to continue? (yes/no): "
    read -r response
    if [ "$response" != "yes" ]; then
        echo "Cleanup cancelled."
        exit 0
    fi
fi

echo ""
echo -e "${BLUE}Stopping staging services...${NC}"
docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" stop

echo -e "${BLUE}Removing staging containers...${NC}"
if [ "$REMOVE_DATA" = true ]; then
    echo -e "${YELLOW}Removing containers AND volumes (all data will be lost)...${NC}"
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" down -v
else
    echo -e "${GREEN}Removing containers only (data will be preserved)...${NC}"
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" down
fi

echo -e "${BLUE}Cleaning up dangling images and containers...${NC}"
docker system prune -f

if [ "$REMOVE_DATA" = true ]; then
    echo -e "${YELLOW}Removing staging volumes...${NC}"
    docker volume rm gms-postgres-staging-data 2>/dev/null || true
    docker volume rm gms-redis-staging-data 2>/dev/null || true
    docker volume rm gms-odoo-staging-data 2>/dev/null || true
    docker volume rm gms-odoo-staging-logs 2>/dev/null || true
    docker volume rm gms-nginx-staging-logs 2>/dev/null || true
    docker volume rm gms-prometheus-staging-data 2>/dev/null || true
    docker volume rm gms-grafana-staging-data 2>/dev/null || true
fi

echo ""
echo -e "${GREEN}=========================================================================="
echo "  Staging Environment Cleanup Complete!"
echo -e "==========================================================================${NC}"
echo ""

if [ "$REMOVE_DATA" = true ]; then
    echo -e "${GREEN}Status:${NC} All staging containers and data have been removed"
    echo ""
    echo "To redeploy staging environment:"
    echo "  ./scripts/deploy_staging.sh"
else
    echo -e "${GREEN}Status:${NC} Staging containers stopped and removed (data preserved)"
    echo ""
    echo "To restart staging environment with existing data:"
    echo "  cd ${PROJECT_ROOT}"
    echo "  docker-compose -f docker/docker-compose.staging.yml --env-file docker/.env.staging up -d"
    echo ""
    echo "To completely remove all data:"
    echo "  ./scripts/cleanup_staging.sh --remove-data"
fi

echo ""
echo -e "${BLUE}Current Docker status:${NC}"
echo ""
docker ps -a | grep gms || echo "No GMS containers running"
echo ""
docker volume ls | grep gms || echo "No GMS volumes remaining"
echo ""
