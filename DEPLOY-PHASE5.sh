#!/bin/bash
#
# Deploy Phase 5 Files to Production
# This script synchronizes the l10n_cr_einvoice module from source to deployed directory
#
# Usage: bash DEPLOY-PHASE5.sh
#

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
SOURCE_DIR="/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/l10n_cr_einvoice"
DEPLOY_DIR="/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/odoo/addons/l10n_cr_einvoice"

echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}  Phase 5 Deployment Script${NC}"
echo -e "${BLUE}  l10n_cr_einvoice Module${NC}"
echo -e "${BLUE}=============================================${NC}"
echo ""

# Check if source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}ERROR: Source directory not found: $SOURCE_DIR${NC}"
    exit 1
fi

# Check if deploy directory exists
if [ ! -d "$DEPLOY_DIR" ]; then
    echo -e "${RED}ERROR: Deploy directory not found: $DEPLOY_DIR${NC}"
    exit 1
fi

echo -e "${YELLOW}Source: $SOURCE_DIR${NC}"
echo -e "${YELLOW}Deploy: $DEPLOY_DIR${NC}"
echo ""

# Backup current deployment
echo -e "${BLUE}Step 1: Creating backup...${NC}"
BACKUP_DIR="/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/backup_$(date +%Y%m%d_%H%M%S)"
cp -r "$DEPLOY_DIR" "$BACKUP_DIR"
echo -e "${GREEN}✓ Backup created: $BACKUP_DIR${NC}"
echo ""

# Copy missing Phase 5 files
echo -e "${BLUE}Step 2: Copying missing Phase 5 files...${NC}"

# QR Generator
if [ -f "$SOURCE_DIR/models/qr_generator.py" ]; then
    cp "$SOURCE_DIR/models/qr_generator.py" "$DEPLOY_DIR/models/"
    echo -e "${GREEN}✓ Copied: models/qr_generator.py${NC}"
else
    echo -e "${RED}✗ Missing: models/qr_generator.py${NC}"
fi

# Email Templates
if [ -f "$SOURCE_DIR/data/email_templates.xml" ]; then
    cp "$SOURCE_DIR/data/email_templates.xml" "$DEPLOY_DIR/data/"
    echo -e "${GREEN}✓ Copied: data/email_templates.xml${NC}"
else
    echo -e "${RED}✗ Missing: data/email_templates.xml${NC}"
fi

# Dashboard Views
if [ -f "$SOURCE_DIR/views/einvoice_dashboard_views.xml" ]; then
    cp "$SOURCE_DIR/views/einvoice_dashboard_views.xml" "$DEPLOY_DIR/views/"
    echo -e "${GREEN}✓ Copied: views/einvoice_dashboard_views.xml${NC}"
else
    echo -e "${RED}✗ Missing: views/einvoice_dashboard_views.xml${NC}"
fi

# Wizard Views
if [ -f "$SOURCE_DIR/views/einvoice_wizard_views.xml" ]; then
    cp "$SOURCE_DIR/views/einvoice_wizard_views.xml" "$DEPLOY_DIR/views/"
    echo -e "${GREEN}✓ Copied: views/einvoice_wizard_views.xml${NC}"
else
    echo -e "${RED}✗ Missing: views/einvoice_wizard_views.xml${NC}"
fi

# Company Views
if [ -f "$SOURCE_DIR/views/res_company_views.xml" ]; then
    cp "$SOURCE_DIR/views/res_company_views.xml" "$DEPLOY_DIR/views/"
    echo -e "${GREEN}✓ Copied: views/res_company_views.xml${NC}"
else
    echo -e "${RED}✗ Missing: views/res_company_views.xml${NC}"
fi

echo ""

# Update modified files
echo -e "${BLUE}Step 3: Updating modified files...${NC}"

# Hacienda API
cp "$SOURCE_DIR/models/hacienda_api.py" "$DEPLOY_DIR/models/"
echo -e "${GREEN}✓ Updated: models/hacienda_api.py${NC}"

# E-invoice Document
cp "$SOURCE_DIR/models/einvoice_document.py" "$DEPLOY_DIR/models/"
echo -e "${GREEN}✓ Updated: models/einvoice_document.py${NC}"

# Models Init
cp "$SOURCE_DIR/models/__init__.py" "$DEPLOY_DIR/models/"
echo -e "${GREEN}✓ Updated: models/__init__.py${NC}"

# Manifest
cp "$SOURCE_DIR/__manifest__.py" "$DEPLOY_DIR/"
echo -e "${GREEN}✓ Updated: __manifest__.py${NC}"

echo ""

# Verify file sizes
echo -e "${BLUE}Step 4: Verifying deployment...${NC}"

echo "File sizes after deployment:"
echo "  hacienda_api.py: $(wc -c < "$DEPLOY_DIR/models/hacienda_api.py") bytes"
echo "  einvoice_document.py: $(wc -c < "$DEPLOY_DIR/models/einvoice_document.py") bytes"
echo "  __init__.py: $(wc -c < "$DEPLOY_DIR/models/__init__.py") bytes"
echo "  __manifest__.py: $(wc -c < "$DEPLOY_DIR/__manifest__.py") bytes"

if [ -f "$DEPLOY_DIR/models/qr_generator.py" ]; then
    echo "  qr_generator.py: $(wc -c < "$DEPLOY_DIR/models/qr_generator.py") bytes"
fi

echo ""

# Restart Odoo
echo -e "${BLUE}Step 5: Restarting Odoo container...${NC}"
docker restart gms_odoo
echo -e "${GREEN}✓ Container restarted${NC}"
echo ""

# Wait for Odoo to start
echo -e "${YELLOW}Waiting 10 seconds for Odoo to start...${NC}"
sleep 10
echo ""

# Update module
echo -e "${BLUE}Step 6: Updating module in database...${NC}"
docker exec gms_odoo odoo -d gms_validation -u l10n_cr_einvoice --stop-after-init
echo -e "${GREEN}✓ Module updated${NC}"
echo ""

# Final restart
echo -e "${BLUE}Step 7: Final restart...${NC}"
docker restart gms_odoo
echo -e "${GREEN}✓ Container restarted${NC}"
echo ""

# Summary
echo -e "${BLUE}=============================================${NC}"
echo -e "${GREEN}  DEPLOYMENT COMPLETE!${NC}"
echo -e "${BLUE}=============================================${NC}"
echo ""
echo "Next steps:"
echo "1. Wait 10 seconds for Odoo to fully start"
echo "2. Run validation: python3 validate_installation.py"
echo "3. Check Odoo logs: docker logs gms_odoo --tail 50"
echo "4. Test Phase 5 features in Odoo UI"
echo ""
echo "Backup location: $BACKUP_DIR"
echo ""
echo -e "${YELLOW}To rollback if needed:${NC}"
echo "  rm -rf $DEPLOY_DIR"
echo "  cp -r $BACKUP_DIR $DEPLOY_DIR"
echo "  docker restart gms_odoo"
echo ""
