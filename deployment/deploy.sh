#!/bin/bash
# GMS Deployment Script
# Deploys staging + production to Hostinger VPS

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

VPS_HOST="168.231.71.94"
VPS_USER="root"
DEPLOY_DIR="/root/gms"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  GMS Deployment to Hostinger VPS${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}ERROR: .env file not found!${NC}"
    echo "Please copy .env.template to .env and configure it first."
    exit 1
fi

# Source environment variables
source .env

if [ -z "$DOMAIN_BASE" ]; then
    echo -e "${RED}ERROR: DOMAIN_BASE not set in .env${NC}"
    exit 1
fi

echo -e "${YELLOW}Configuration:${NC}"
echo "  VPS: $VPS_HOST"
echo "  Domain: $DOMAIN_BASE"
echo "  Staging: stage.$DOMAIN_BASE"
echo "  Production: $DOMAIN_BASE"
echo ""

read -p "Continue with deployment? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo -e "${GREEN}Step 1: Creating directories on VPS...${NC}"
ssh $VPS_USER@$VPS_HOST "mkdir -p $DEPLOY_DIR/{staging/addons,production/addons,traefik,backups}"

echo -e "${GREEN}Step 2: Uploading Docker Compose configuration...${NC}"
scp docker-compose.production.yml $VPS_USER@$VPS_HOST:$DEPLOY_DIR/docker-compose.yml
scp .env $VPS_USER@$VPS_HOST:$DEPLOY_DIR/.env

echo -e "${GREEN}Step 3: Uploading Odoo configurations...${NC}"
scp staging/odoo.conf $VPS_USER@$VPS_HOST:$DEPLOY_DIR/staging/odoo.conf
scp production/odoo.conf $VPS_USER@$VPS_HOST:$DEPLOY_DIR/production/odoo.conf

echo -e "${GREEN}Step 4: Uploading custom addons (staging)...${NC}"
scp -r ../odoo/addons/l10n_cr $VPS_USER@$VPS_HOST:$DEPLOY_DIR/staging/addons/
scp -r ../odoo/addons/l10n_cr_einvoice $VPS_USER@$VPS_HOST:$DEPLOY_DIR/staging/addons/

# Check if payment_tilopay exists
if [ -d "../payment_tilopay" ]; then
    scp -r ../payment_tilopay $VPS_USER@$VPS_HOST:$DEPLOY_DIR/staging/addons/
fi

echo -e "${GREEN}Step 5: Uploading custom addons (production)...${NC}"
scp -r ../odoo/addons/l10n_cr $VPS_USER@$VPS_HOST:$DEPLOY_DIR/production/addons/
scp -r ../odoo/addons/l10n_cr_einvoice $VPS_USER@$VPS_HOST:$DEPLOY_DIR/production/addons/

if [ -d "../payment_tilopay" ]; then
    scp -r ../payment_tilopay $VPS_USER@$VPS_HOST:$DEPLOY_DIR/production/addons/
fi

echo -e "${GREEN}Step 6: Starting Docker containers...${NC}"
ssh $VPS_USER@$VPS_HOST "cd $DEPLOY_DIR && docker-compose pull"
ssh $VPS_USER@$VPS_HOST "cd $DEPLOY_DIR && docker-compose up -d"

echo ""
echo -e "${GREEN}Step 7: Waiting for containers to start (30s)...${NC}"
sleep 30

echo ""
echo -e "${GREEN}Step 8: Checking container status...${NC}"
ssh $VPS_USER@$VPS_HOST "cd $DEPLOY_DIR && docker-compose ps"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Access Staging:"
echo "   https://stage.$DOMAIN_BASE"
echo "   - Create database: gms_staging"
echo "   - Install GMS modules"
echo ""
echo "2. Access Production:"
echo "   https://$DOMAIN_BASE"
echo "   - Create database: gms_production"
echo "   - Configure company & e-invoicing"
echo ""
echo "3. Monitor logs:"
echo "   ssh $VPS_USER@$VPS_HOST 'cd $DEPLOY_DIR && docker-compose logs -f'"
echo ""
echo "4. View container stats:"
echo "   ssh $VPS_USER@$VPS_HOST 'docker stats'"
echo ""
echo -e "${YELLOW}Troubleshooting:${NC}"
echo "   See deployment/DEPLOYMENT_GUIDE.md for detailed instructions"
echo ""
