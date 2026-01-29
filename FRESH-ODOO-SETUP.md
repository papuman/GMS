# Fresh Odoo Installation - Setup Guide

## Status: ✅ Fresh Installation Complete

Your Odoo instance has been completely reset to a clean state.

---

## Access Information

**Odoo Web Interface:**
- URL: http://localhost:8070
- Status: ✅ Running

**Database Manager:**
- URL: http://localhost:8070/web/database/manager
- Master Password: `admin123`

---

## First Time Setup

### Step 1: Create Your First Database

1. Go to: http://localhost:8070
2. You'll see the "Database Manager" page
3. Click "Create Database"
4. Fill in the form:
   - **Master Password:** `admin123`
   - **Database Name:** Choose a name (e.g., `odoo19`, `gms`, etc.)
   - **Email:** Your email
   - **Password:** Your admin password (e.g., `admin`)
   - **Language:** English (or your preference)
   - **Country:** Costa Rica
   - **Demo data:** Choose "Without demo data" for production

5. Click "Create Database"

### Step 2: Wait for Setup

The initial database creation takes 2-5 minutes. You'll see a loading screen.

### Step 3: Login

After creation, you'll be automatically logged in to your new Odoo instance.

---

## Install Your Custom Module

Once you have a database created:

1. Go to **Apps** (top menu)
2. Click "Update Apps List"
3. Search for "Costa Rica Electronic Invoicing"
4. Click "Install"

**Module Details:**
- Name: `l10n_cr_einvoice`
- Version: 19.0.1.11.0
- Location: `/mnt/extra-addons/l10n_cr_einvoice`

---

## Database Configuration

**PostgreSQL:**
- Host: `localhost` (or `db` from inside Docker)
- Port: `5432`
- Username: `odoo`
- Password: `odoo`

**Connect to Database:**
```bash
docker exec -it gms_postgres psql -U odoo -d postgres
```

---

## What Was Reset

✅ **All databases deleted:**
   - odoo19
   - gms
   - gms_validation

✅ **All data removed:**
   - Database data
   - File attachments
   - Sessions
   - User data

✅ **Fresh volumes created:**
   - gms_odoo-db-data (PostgreSQL data)
   - gms_odoo-web-data (Odoo file storage)

---

## Your Custom Module Is Still Available

Your `l10n_cr_einvoice` module is still in the `/mnt/extra-addons` directory and ready to install after you create a database.

**Module Files Location:**
- Source: `./odoo/addons/l10n_cr_einvoice/`
- Mounted: `/mnt/extra-addons/l10n_cr_einvoice/`

---

## Quick Start Commands

**Check Odoo logs:**
```bash
docker logs gms_odoo --tail 50
```

**Restart Odoo:**
```bash
docker restart gms_odoo
```

**Stop all services:**
```bash
docker-compose down
```

**Start all services:**
```bash
docker-compose up -d
```

---

## Recommended First Database Setup

For testing your tax reports module:

**Database Settings:**
- Name: `odoo19`
- Admin email: `admin@example.com`
- Admin password: `admin`
- Language: English
- Country: Costa Rica
- Demo data: **Without demo data**

**After database creation:**
1. Install `l10n_cr_einvoice` module
2. Go to: Accounting > Hacienda (CR) > Tax Reports
3. Test Phase 9B UI views

---

## Need Help?

**Check if services are running:**
```bash
docker ps | grep gms
```

**View Odoo logs:**
```bash
docker logs gms_odoo -f
```

**Access database directly:**
```bash
docker exec -it gms_postgres psql -U odoo -d <database_name>
```

---

**Setup Date:** December 31, 2025
**Odoo Version:** 19.0
**PostgreSQL Version:** 13
**Status:** ✅ Ready for first-time setup
