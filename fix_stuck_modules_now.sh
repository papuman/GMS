#!/bin/bash
# Quick fix for stuck Odoo modules

set -e

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║           FIXING STUCK MODULE INSTALLATION                         ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Check for database name from PostgreSQL
echo "🔍 Looking for Odoo databases..."
echo ""

# Try to list databases (works if PostgreSQL is accessible)
DB_LIST=$(psql -U odoo -h localhost -l 2>/dev/null | grep odoo | awk '{print $1}' || echo "")

if [ -n "$DB_LIST" ]; then
    echo "Found databases:"
    echo "$DB_LIST"
    echo ""
    echo "Enter your database name (or press Enter to try first one):"
    read DB_NAME

    if [ -z "$DB_NAME" ]; then
        DB_NAME=$(echo "$DB_LIST" | head -1)
        echo "Using: $DB_NAME"
    fi
else
    echo "Could not auto-detect databases."
    echo "What is your database name? (Common names: odoo, gms_db, postgres)"
    read DB_NAME
fi

echo ""
echo "💾 Database: $DB_NAME"
echo "⚙️  Running fix..."
echo ""

# Run Odoo shell to fix stuck modules
cd "/Users/papuman/Documents/My Projects/GMS"

python3 odoo/odoo-bin shell -c odoo.conf -d "$DB_NAME" << 'EOF'
# Find stuck modules
stuck = env['ir.module.module'].search([('state', 'in', ['to install', 'to upgrade', 'to remove'])])

if stuck:
    print(f"\n🔍 Found {len(stuck)} stuck module(s):")
    for m in stuck:
        print(f"  - {m.name}: {m.state}")

    # Fix them
    for m in stuck:
        old_state = m.state
        if m.state in ['to install', 'to remove']:
            m.state = 'uninstalled'
        elif m.state == 'to upgrade':
            m.state = 'installed'
        print(f"  ✓ Fixed {m.name}: {old_state} → {m.state}")

    env.cr.commit()
    print("\n✅ FIXED! Modules have been reset.")
    print("   You can now install/upgrade modules again.")
else:
    print("\n✅ No stuck modules found.")
    print("   The issue might be something else.")
    print("\nTry these:")
    print("  1. Refresh your browser")
    print("  2. Clear browser cache")
    print("  3. Restart Odoo server")

EOF

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                          DONE!                                     ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Refresh your browser (Cmd+R or Ctrl+R)"
echo "  2. Try installing the module again"
echo ""
