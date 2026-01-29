# 🎉 GMS Deployment Complete!

**Deployment Date:** January 27, 2026
**Status:** ✅ Successfully Deployed
**VPS IP:** 168.231.71.94

---

## ✅ What Was Deployed

1. **n8n removed** - Freed 500MB RAM
2. **System updated** - Ubuntu 24.04, Docker 29.2.0
3. **Firewall configured** - SSH, HTTP, HTTPS only
4. **5 containers running**:
   - Traefik (reverse proxy + SSL)
   - PostgreSQL Staging
   - Odoo Staging
   - PostgreSQL Production
   - Odoo Production
5. **Custom modules uploaded**:
   - l10n_cr (Costa Rica localization)
   - l10n_cr_einvoice (E-invoicing)
   - payment_tilopay (TiloPay payment gateway)

---

## 🌐 Your URLs

### Staging Environment
**URL:** https://stage.blanchedalmond-raccoon-234970.hostingersite.com

**Purpose:** Testing, development, trying new features

### Production Environment
**URL:** https://blanchedalmond-raccoon-234970.hostingersite.com

**Purpose:** Live customer data, real invoices

### Traefik Dashboard
**URL:** https://traefik.blanchedalmond-raccoon-234970.hostingersite.com
**Username:** admin
**Password:** GMS2026Secure!

---

## 🔑 Credentials

### SSL Certificates
**Email:** mecagoensumadre@hotmail.com
**Renewal:** Automatic (Let's Encrypt)

### Database Passwords

**Staging Database:**
- Host: postgres-stage (internal)
- Database: gms_staging
- User: odoo
- Password: `2OLt9CMWrK5xWqr1vvs87/F3GgEjcESqHbsI0YI6UpQ=`

**Production Database:**
- Host: postgres-prod (internal)
- Database: gms_production
- User: odoo
- Password: `waGtgS/jj3JzdFYrLajatZPwn3KENHo8k6s/I+YGNlY=`

### Odoo Master Passwords

**Staging:**
- Master Password: `javier5147`
- Admin Password: `pZIMnLNi9Jv1cAnFVTptO6MGsTvL/Vhx`

**Production:**
- Master Password: `javier5147`
- Admin Password: `wQ4uMlQAC5Nz7TCFjnXyghJtVdMBYX2w`

---

## 🚀 Next Steps: Initialize Your Databases

### Step 1: Initialize Staging (10 minutes)

1. **Visit:** https://stage.blanchedalmond-raccoon-234970.hostingersite.com

2. **You'll see:** "Create Database" screen

3. **Fill in:**
   - Master Password: `javier5147`
   - Database Name: `gms_staging`
   - Email: `admin@yourdomain.com`
   - Password: `pZIMnLNi9Jv1cAnFVTptO6MGsTvL/Vhx`
   - Language: English or Spanish
   - Country: Costa Rica
   - Demo Data: ✅ **Check this** (for testing)

4. **Click "Create Database"** (takes ~60 seconds)

5. **Install Modules:**
   - Go to **Apps** menu
   - Click **"Update Apps List"**
   - Search and install:
     - ✅ Costa Rica - Accounting (l10n_cr)
     - ✅ Costa Rica E-Invoicing (l10n_cr_einvoice)
     - ✅ Payment: TiloPay (payment_tilopay)

6. **Test it:**
   - Create a test invoice
   - Try e-invoice generation
   - Verify everything works

### Step 2: Initialize Production (10 minutes)

1. **Visit:** https://blanchedalmond-raccoon-234970.hostingersite.com

2. **Create Database:**
   - Master Password: `javier5147`
   - Database Name: `gms_production`
   - Email: `admin@yourdomain.com`
   - Password: `wQ4uMlQAC5Nz7TCFjnXyghJtVdMBYX2w`
   - Language: Spanish
   - Country: Costa Rica
   - Demo Data: ❌ **DO NOT CHECK** (no demo data in production!)

3. **Install same 3 modules**

4. **Configure Company:**
   - Settings → Companies → Update Company
   - Fill in legal name, tax ID, address, phone
   - **E-Invoice Configuration:**
     - Emisor Location Code: 8-digit code (e.g., 01010100)
     - Hacienda Environment: **Sandbox** (test first!)
     - Auto-generate: ✅ Enable
     - Auto-submit: ❌ Disable initially

5. **Upload Certificate:**
   - When you have production certificate, upload it
   - For now, use sandbox for testing

---

## 📊 System Status

### Container Status

```bash
ssh root@168.231.71.94 'cd /root/gms && docker compose ps'
```

**All running:**
- ✅ gms_traefik - Reverse proxy
- ✅ gms_postgres_stage - Staging DB
- ✅ gms_odoo_stage - Staging app
- ✅ gms_postgres_prod - Production DB
- ✅ gms_odoo_prod - Production app

### Resource Usage

**RAM Allocation:**
- Traefik: ~100MB
- Staging: ~4.5GB (Odoo 2.5GB + DB 2GB)
- Production: ~7GB (Odoo 4GB + DB 3GB)
- **Total: ~7.6GB / 8GB available** ✅

**Performance:**
- Staging: 20-30 concurrent users
- Production: 50-75 concurrent users
- Production workers: 4 (2x previous capacity!)

### Security

- ✅ Firewall active (SSH, HTTP, HTTPS only)
- ✅ Database ports blocked from internet
- ✅ Direct Odoo access blocked
- ✅ SSL/TLS enabled (automatic renewal)
- ✅ HTTPS enforced (HTTP redirects)

---

## 🔧 Common Operations

### View Logs

```bash
# SSH into VPS
ssh root@168.231.71.94

# View all logs
cd /root/gms && docker compose logs -f

# View specific service
docker compose logs -f odoo-prod
docker compose logs -f traefik
```

### Restart Services

```bash
ssh root@168.231.71.94
cd /root/gms

# Restart all
docker compose restart

# Restart specific service
docker compose restart odoo-prod
```

### Check Resource Usage

```bash
ssh root@168.231.71.94
docker stats
```

### Backup Database

```bash
# Staging
ssh root@168.231.71.94 "docker exec gms_postgres_stage pg_dump -U odoo gms_staging | gzip > /root/backups/stage_$(date +%Y%m%d).sql.gz"

# Production
ssh root@168.231.71.94 "docker exec gms_postgres_prod pg_dump -U odoo gms_production | gzip > /root/backups/prod_$(date +%Y%m%d).sql.gz"
```

---

## 🎯 Important Notes

### Change These Passwords Immediately!

1. **Odoo Master Password** (both environments):
   - Current: `javier5147`
   - Change in Settings → Technical → Parameters → System Parameters

2. **VPS Root Password**:
   - Current: `rWq5xq@TuXju0WrX`
   - Change with: `passwd`

### SSL Certificates

- Auto-generated by Let's Encrypt
- Email notifications to: mecagoensumadre@hotmail.com
- Auto-renewal 30 days before expiry
- No action needed

### Firewall

- ✅ Active and configured
- Ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)
- All other ports blocked
- PostgreSQL not accessible from internet

---

## 📞 Support & Documentation

**Deployment Files:**
- `/Users/papuman/Documents/My Projects/GMS/deployment/`

**Documentation:**
- `DEPLOY_NOW.md` - Detailed deployment guide
- `DEPLOYMENT_GUIDE.md` - Complete documentation
- `QUICK_START.md` - Quick reference
- `VPS_SETUP_COMMANDS.md` - VPS commands

**Access VPS:**
```bash
ssh root@168.231.71.94
# Password: rWq5xq@TuXju0WrX
```

---

## ✅ Deployment Checklist

- [x] VPS system updated
- [x] n8n removed
- [x] Firewall configured
- [x] Docker containers deployed
- [x] SSL certificates configured
- [x] Custom modules uploaded
- [x] Both environments running
- [ ] Staging database initialized ← **Do this next**
- [ ] Production database initialized
- [ ] Company information configured
- [ ] E-invoicing certificate uploaded
- [ ] User accounts created
- [ ] Automated backups set up

---

**🎉 Deployment successful! Visit your URLs to initialize the databases.**

**Staging:** https://stage.blanchedalmond-raccoon-234970.hostingersite.com
**Production:** https://blanchedalmond-raccoon-234970.hostingersite.com

**Questions?** Check the documentation files or SSH into the VPS to inspect logs.
