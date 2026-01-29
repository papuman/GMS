#!/bin/bash
# -*- coding: utf-8 -*-
#
# File Synchronization Script for l10n_cr_einvoice Module
# Synchronizes files from main location to odoo/addons location
#
# Author: GMS Development Team
# Date: 2025-12-28
#
# Usage: ./sync_files.sh [--dry-run] [--phase=N]
#

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Paths
BASE_PATH="/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS"
MAIN_LOC="$BASE_PATH/l10n_cr_einvoice"
ODOO_LOC="$BASE_PATH/odoo/addons/l10n_cr_einvoice"

# Parse arguments
DRY_RUN=false
PHASE="all"

for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --phase=*)
            PHASE="${arg#*=}"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--dry-run] [--phase=N]"
            echo ""
            echo "Options:"
            echo "  --dry-run       Show what would be copied without actually copying"
            echo "  --phase=N       Sync only Phase N files (1, 2, 3, 5, or 'all')"
            echo "  -h, --help      Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Sync all files"
            echo "  $0 --dry-run          # Show what would be synced"
            echo "  $0 --phase=5          # Sync only Phase 5 files"
            exit 0
            ;;
    esac
done

# Print header
echo -e "${BOLD}${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║          l10n_cr_einvoice File Synchronization                        ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN MODE - No files will be modified${NC}\n"
fi

# Backup function
backup_file() {
    local file=$1
    local backup_dir="$BASE_PATH/odoo_backups/$(date +%Y%m%d_%H%M%S)"

    if [ -f "$file" ]; then
        mkdir -p "$backup_dir"
        cp "$file" "$backup_dir/"
        echo -e "${BLUE}  Backed up to: $backup_dir/$(basename $file)${NC}"
    fi
}

# Copy function
copy_file() {
    local src=$1
    local dest=$2
    local label=$3

    if [ ! -f "$src" ]; then
        echo -e "${RED}✗ Source not found: $label${NC}"
        return 1
    fi

    if [ "$DRY_RUN" = true ]; then
        echo -e "${CYAN}[DRY RUN] Would copy: $label${NC}"
        echo -e "  From: $src"
        echo -e "  To:   $dest"
        return 0
    fi

    # Backup existing file if it exists
    if [ -f "$dest" ]; then
        backup_file "$dest"
    fi

    # Create directory if needed
    mkdir -p "$(dirname "$dest")"

    # Copy file
    cp -v "$src" "$dest"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Copied: $label${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed: $label${NC}"
        return 1
    fi
}

# Main synchronization
echo -e "${BOLD}Starting synchronization...${NC}\n"

FILES_COPIED=0
FILES_FAILED=0

# Phase 5 Critical Files
if [ "$PHASE" = "all" ] || [ "$PHASE" = "5" ]; then
    echo -e "${BOLD}${YELLOW}Phase 5 Files (CRITICAL)${NC}"
    echo "───────────────────────────────────────────────────────────────────────"

    copy_file \
        "$MAIN_LOC/models/qr_generator.py" \
        "$ODOO_LOC/models/qr_generator.py" \
        "models/qr_generator.py"
    [ $? -eq 0 ] && ((FILES_COPIED++)) || ((FILES_FAILED++))

    copy_file \
        "$MAIN_LOC/reports/einvoice_report_templates.xml" \
        "$ODOO_LOC/reports/einvoice_report_templates.xml" \
        "reports/einvoice_report_templates.xml"
    [ $? -eq 0 ] && ((FILES_COPIED++)) || ((FILES_FAILED++))

    echo ""
fi

# Phase 1 & 2 Files
if [ "$PHASE" = "all" ] || [ "$PHASE" = "1" ] || [ "$PHASE" = "2" ]; then
    echo -e "${BOLD}${YELLOW}Phase 1 & 2 Files (REVIEW FIRST)${NC}"
    echo "───────────────────────────────────────────────────────────────────────"
    echo -e "${YELLOW}Note: These files have differences. Review before copying!${NC}\n"

    # Only show what would be copied in dry-run or if user confirms
    if [ "$DRY_RUN" = false ]; then
        echo -e "${YELLOW}These files will overwrite existing Odoo files:${NC}"
        echo "  - models/einvoice_document.py (Main: 23KB, Odoo: 15KB)"
        echo "  - models/__init__.py (Main: 312B, Odoo: 285B)"
        echo "  - __manifest__.py (Main: 2KB, Odoo: 2KB)"
        echo ""
        read -p "Continue? (y/N) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Skipping Phase 1 & 2 files${NC}\n"
        else
            copy_file \
                "$MAIN_LOC/models/einvoice_document.py" \
                "$ODOO_LOC/models/einvoice_document.py" \
                "models/einvoice_document.py"
            [ $? -eq 0 ] && ((FILES_COPIED++)) || ((FILES_FAILED++))

            copy_file \
                "$MAIN_LOC/models/__init__.py" \
                "$ODOO_LOC/models/__init__.py" \
                "models/__init__.py"
            [ $? -eq 0 ] && ((FILES_COPIED++)) || ((FILES_FAILED++))
        fi
    else
        echo -e "${CYAN}[DRY RUN] Would ask to copy Phase 1 & 2 files${NC}"
    fi

    echo ""
fi

# Phase 3 Files
if [ "$PHASE" = "all" ] || [ "$PHASE" = "3" ]; then
    echo -e "${BOLD}${YELLOW}Phase 3 Files (INVESTIGATE FIRST)${NC}"
    echo "───────────────────────────────────────────────────────────────────────"
    echo -e "${RED}WARNING: hacienda_api.py has MAJOR differences${NC}"
    echo "  Main: 19KB | Odoo: 7KB (11KB difference)"
    echo -e "${YELLOW}Run diff before copying!${NC}\n"

    if [ "$DRY_RUN" = false ]; then
        read -p "Show diff now? (y/N) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            diff -u "$ODOO_LOC/models/hacienda_api.py" \
                    "$MAIN_LOC/models/hacienda_api.py" | less
        fi

        read -p "Copy hacienda_api.py from main to odoo? (y/N) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            copy_file \
                "$MAIN_LOC/models/hacienda_api.py" \
                "$ODOO_LOC/models/hacienda_api.py" \
                "models/hacienda_api.py"
            [ $? -eq 0 ] && ((FILES_COPIED++)) || ((FILES_FAILED++))
        fi
    else
        echo -e "${CYAN}[DRY RUN] Would ask about hacienda_api.py${NC}"
    fi

    echo ""
fi

# Module Core Files
if [ "$PHASE" = "all" ]; then
    echo -e "${BOLD}${YELLOW}Module Core Files${NC}"
    echo "───────────────────────────────────────────────────────────────────────"

    copy_file \
        "$MAIN_LOC/__manifest__.py" \
        "$ODOO_LOC/__manifest__.py" \
        "__manifest__.py"
    [ $? -eq 0 ] && ((FILES_COPIED++)) || ((FILES_FAILED++))

    echo ""
fi

# Summary
echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${CYAN}SYNCHRONIZATION SUMMARY${NC}"
echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════════════${NC}\n"

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN completed - No files were modified${NC}"
    echo "Run without --dry-run to perform actual synchronization"
else
    echo -e "Files copied: ${GREEN}$FILES_COPIED${NC}"
    echo -e "Files failed: ${RED}$FILES_FAILED${NC}"

    if [ $FILES_COPIED -gt 0 ]; then
        echo -e "\n${GREEN}Synchronization completed!${NC}"
        echo -e "\n${BOLD}Next steps:${NC}"
        echo "  1. Restart Odoo to load updated module:"
        echo "     odoo-bin -c odoo.conf -u l10n_cr_einvoice -d tribu_sandbox"
        echo ""
        echo "  2. Run integration tests:"
        echo "     python3 check_file_sync.py"
        echo "     odoo-bin shell -c odoo.conf -d tribu_sandbox < test_e2e_integration_odoo.py"
        echo ""
        echo "  3. Verify QR generation works:"
        echo "     (in Odoo shell) env['l10n_cr.qr.generator'].generate_qr_code('12345678901234567890123456789012345678901234567890')"
    fi

    if [ $FILES_FAILED -gt 0 ]; then
        echo -e "\n${RED}Some files failed to copy. Check errors above.${NC}"
        exit 1
    fi
fi

echo -e "\n${BOLD}${CYAN}═══════════════════════════════════════════════════════════════════════${NC}\n"

exit 0
