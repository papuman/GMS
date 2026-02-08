# 🚀 GMS Deployment - Execute Now

**Domain:** blanchedalmond-raccoon-234970.hostingersite.com
**VPS IP:** 168.231.71.94
**Status:** ✅ Firewall configured, ready to deploy

---

## ⚡ Quick Deployment (30 minutes)

### **Step 1: Upload Update Script** (1 minute)

Open terminal and run:

```bash
cd /Users/papuman/Documents/My\ Projects/GMS/deployment
scp update-vps.sh root@168.231.71.94:/root/
```

**Expected output:**
```
update-vps.sh                100%  2.1KB   2.1KB/s   00:00
```

---

### **Step 2: Update VPS System** (5-10 minutes)

SSH into VPS:

```bash
ssh root@168.231.71.94
```

Run update script:

```bash
bash /root/update-vps.sh
```

**What it does:**
- Removes n8n (frees 500MB RAM)
- Updates Ubuntu to latest version
- Updates all packages
- Updates Docker & Docker Compose
- Cleans up unused files

**Expected output:**
```
✓ n8n removed
✓ Packages updated
✓ System upgraded
✓ Docker updated
✓ Docker Compose is up to date
```

When complete, reboot:

```bash
reboot
```

Wait 2 minutes for VPS to restart.

---

### **Step 3: Configure Passwords** (2 minutes)

**IMPORTANT:** You only need to change 2 things in `.env`:

1. **Your email** (for SSL certificate notifications)
2. **Traefik dashboard password**

Open `.env`:

```bash
cd /Users/papuman/Documents/My\ Projects/GMS/deployment
nano .env
```

**Change line 8:**
```bash
# FROM:
ACME_EMAIL=your-email@example.com

# TO:
ACME_EMAIL=your-actual-email@gmail.com
```

**Change line 18 - Generate Traefik password:**

First, install htpasswd (if needed):
```bash
# On Mac:
brew install httpd

# On Linux:
sudo apt-get install apache2-utils
```

Generate password hash:
```bash
htpasswd -nb admin YourSecurePassword123
```

**Example output:**
```
admin:$apr1$xyz$abc123def
```

**IMPORTANT:** Replace `$` with `$$` (double dollar signs):
```
admin:$$apr1$$xyz$$abc123def
```

Copy this to line 18 in `.env`:
```bash
TRAEFIK_AUTH=admin:$$apr1$$xyz$$abc123def
```

**Save and exit:** Press `Ctrl+X`, then `Y`, then `Enter`

**Note:** Database passwords are already generated securely! Don't change them.

---

### **Step 4: Deploy GMS** (5 minutes)

Run deployment script:

```bash
./deploy.sh
```

**What it does:**
1. Creates directories on VPS
2. Uploads Docker configurations
3. Uploads Odoo custom modules (l10n_cr, l10n_cr_einvoice, payment_tilopay)
4. Starts 5 containers (Traefik, 2x PostgreSQL, 2x Odoo)
5. Configures SSL certificates
6. Sets up both staging and production

**Expected output:**
```
✓ Directories created
✓ Configurations uploaded
✓ Custom modules uploaded
✓ Containers starting...
✓ Deployment complete!

Staging: https://stage.blanchedalmond-raccoon-234970.hostingersite.com
Production: https://blanchedalmond-raccoon-234970.hostingersite.com
```

---

### **Step 5: Initialize Staging** (10 minutes)

Visit: **https://stage.blanchedalmond-raccoon-234970.hostingersite.com**

**If you see SSL warning:** This is normal! SSL certificate takes 2-3 minutes to generate. Wait and refresh.

**When you see "Create Database" page:**

1. **Master Password:** `javier5147` (change this later!)
2. **Database Name:** `gms_staging`
3. **Email:** `admin@yourdomain.com`
4. **Password:** `pZIMnLNi9Jv1cAnFVTptO6MGsTvL/Vhx` (from .env)
5. **Language:** English or Spanish
6. **Country:** Costa Rica
7. **Demo Data:** ✅ **Check this box** (for testing)

Click **"Create Database"** (takes ~60 seconds)

**Install Modules:**

1. Click **Apps** menu (top bar)
2. Click **"Update Apps List"** (may need to enable developer mode first)
3. Search and install:
   - ✅ **Costa Rica - Accounting** (l10n_cr)
   - ✅ **Costa Rica E-Invoicing** (l10n_cr_einvoice)
   - ✅ **Payment: TiloPay** (payment_tilopay)

Each module takes ~30 seconds to install.

---

### **Step 6: Test Staging** (5 minutes)

**Create Test Invoice:**

1. Go to **Accounting → Customers → Invoices**
2. Click **Create**
3. Select customer (or create new one with VAT)
4. Add product line
5. Click **Confirm**
6. Click **"Generate E-Invoice"**
7. Click **"Sign XML"** (uses sandbox certificate)
8. Click **"Submit to Hacienda"**
9. Check status → Should show "Submitted" or "Accepted"

**If successful:** ✅ Staging is working!

---

### **Step 7: Initialize Production** (10 minutes)

Visit: **https://blanchedalmond-raccoon-234970.hostingersite.com**

**Create Database:**

1. **Master Password:** `javier5147` (change this later!)
2. **Database Name:** `gms_production`
3. **Email:** `admin@yourdomain.com`
4. **Password:** `wQ4uMlQAC5Nz7TCFjnXyghJtVdMBYX2w` (from .env)
5. **Language:** Spanish
6. **Country:** Costa Rica
7. **Demo Data:** ❌ **DO NOT CHECK** (no demo data in production!)

Install same 3 modules as staging.

**Configure Company:**

1. Go to **Settings → Companies → Update Company**
2. Fill in:
   - Legal Name
   - Tax ID (Cédula Jurídica)
   - Address
   - Phone
   - Email

**Configure E-Invoicing:**

1. **Emisor Location Code:** 8-digit code (e.g., 01010100)
2. **Hacienda Environment:** **Sandbox** (test first!)
3. **Auto-generate E-Invoice:** ✅ Enable
4. **Auto-submit to Hacienda:** ❌ Disable (submit manually until tested)

**Upload Certificate:**
- When you have production certificate, upload it here
- For now, keep using sandbox

---

## ✅ Deployment Complete Checklist

After completing all steps, verify:

- [ ] Staging accessible at stage.blanchedalmond-raccoon-234970.hostingersite.com
- [ ] Production accessible at blanchedalmond-raccoon-234970.hostingersite.com
- [ ] SSL certificates working (HTTPS with green lock)
- [ ] Can log into both environments
- [ ] Modules installed successfully
- [ ] Can create invoice in staging
- [ ] E-invoice generation works
- [ ] Firewall active (verify: `ssh root@168.231.71.94 "iptables -L"`)

---

## 📊 Monitor Deployment

**Check container status:**
```bash
ssh root@168.231.71.94 "cd /root/gms && docker-compose ps"
```

**Expected output:**
```
gms_traefik          running   80/tcp, 443/tcp
gms_postgres_stage   running   5432/tcp
gms_odoo_stage       running   8069/tcp
gms_postgres_prod    running   5432/tcp
gms_odoo_prod        running   8069/tcp
```

**Check logs:**
```bash
ssh root@168.231.71.94 "cd /root/gms && docker-compose logs -f odoo-prod"
```

**Check resource usage:**
```bash
ssh root@168.231.71.94 "docker stats --no-stream"
```

**Expected RAM usage:**
- Traefik: ~100MB
- Postgres Stage: ~500MB
- Odoo Stage: ~1.5GB
- Postgres Prod: ~1GB
- Odoo Prod: ~3GB
- **Total: ~6GB / 8GB available** ✅

---

## 🔧 Troubleshooting

### Can't access website

**Check DNS:**
```bash
nslookup blanchedalmond-raccoon-234970.hostingersite.com
# Should return: 168.231.71.94
```

**Check Traefik:**
```bash
ssh root@168.231.71.94 "docker logs gms_traefik"
```

### SSL certificate not working

Wait 2-3 minutes and refresh. Check:
```bash
ssh root@168.231.71.94 "docker logs gms_traefik | grep certificate"
```

### Container keeps restarting

```bash
ssh root@168.231.71.94 "cd /root/gms && docker-compose logs odoo-prod"
```

Common issues:
- Wrong database password in .env
- Database not ready (wait 30s)

### Out of memory

```bash
ssh root@168.231.71.94 "free -h"
```

If over 90%, reduce workers in `production/odoo.conf` from 4 to 2.

---

## 🎯 What's Next

After successful deployment:

1. **Change master passwords** (both environments)
2. **Set up SMTP email** (for invoice delivery)
3. **Upload production certificate** (when ready)
4. **Configure Hacienda production credentials**
5. **Set up automated backups**
6. **Create user accounts**
7. **Import data** (if migrating from old system)

---

## 📞 Support

**Files:**
- `QUICK_START.md` - Quick reference
- `DEPLOYMENT_GUIDE.md` - Detailed guide
- `VPS_SETUP_COMMANDS.md` - VPS commands

**URLs:**
- Staging: https://stage.blanchedalmond-raccoon-234970.hostingersite.com
- Production: https://blanchedalmond-raccoon-234970.hostingersite.com
- Traefik: https://traefik.blanchedalmond-raccoon-234970.hostingersite.com

---

**Ready? Start with Step 1!** 🚀
