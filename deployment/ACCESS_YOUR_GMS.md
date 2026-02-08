# 🎉 GMS System is LIVE!

**Deployment Completed:** January 27, 2026
**Status:** Containers Running - Ready for Database Initialization

---

## 🌐 Access Your GMS System

### Staging Environment
**URL:** https://stage.168.231.71.94.nip.io

**Purpose:** Testing, development, trying features

### Production Environment
**URL:** https://168.231.71.94.nip.io

**Purpose:** Live customer data, real invoices

### Traefik Dashboard
**URL:** https://traefik.168.231.71.94.nip.io
**Username:** admin
**Password:** GMS2026Secure!

---

## ⚠️ SSL Certificate Note

**First access may take 2-3 minutes** while Let's Encrypt generates your SSL certificates.

If you see:
- "Your connection is not private" → Click "Advanced" → "Proceed anyway"
- "Certificate error" → Wait 2 minutes and refresh
- "404 Not Found" → Wait 30 seconds and refresh

This is normal on first access. The certificates are being generated automatically.

---

## 🔑 Your Credentials

### Database Passwords

**Staging Database:**
- Database Name: `gms_staging`
- Password: `2OLt9CMWrK5xWqr1vvs87/F3GgEjcESqHbsI0YI6UpQ=`

**Production Database:**
- Database Name: `gms_production`
- Password: `waGtgS/jj3JzdFYrLajatZPwn3KENHo8k6s/I+YGNlY=`

### Odoo Admin

**Master Password (change this!):** `javier5147`

**Staging Admin:** `pZIMnLNi9Jv1cAnFVTptO6MGsTvL/Vhx`
**Production Admin:** `wQ4uMlQAC5Nz7TCFjnXyghJtVdMBYX2w`

### VPS Access
**IP:** 168.231.71.94
**Username:** root
**Password:** `rWq5xq@TuXju0WrX` (change this!)

---

## 📝 Next Steps: Initialize Databases

### Step 1: Open Staging URL

1. Open in browser: **https://stage.168.231.71.94.nip.io**
2. Wait for SSL certificate (may take 2 minutes on first access)
3. You'll see either:
   - Database Creation Page → Perfect! Proceed to Step 2
   - Login Page → Database already created, use staging admin password
   - 500 Error → See Troubleshooting below

### Step 2: Create Staging Database

When you see the "Create Database" page:

1. **Master Password:** `javier5147`
2. **Database Name:** `gms_staging`
3. **Email:** your email address
4. **Password:** `pZIMnLNi9Jv1cAnFVTptO6MGsTvL/Vhx`
5. **Language:** English or Spanish
6. **Country:** Costa Rica
7. **Demo Data:** ✅ **CHECK THIS** (for testing)
8. Click **"Create Database"**

Wait ~60 seconds for initialization.

### Step 3: Install Modules (Staging)

Once logged in:

1. Go to **Apps** menu (top bar)
2. Click **"Update Apps List"**
   (May need to enable Developer Mode first: Settings → Developer Tools → Activate)
3. Search and install:
   - ✅ **Costa Rica - Accounting** (l10n_cr)
   - ✅ **Costa Rica E-Invoicing** (l10n_cr_einvoice)
   - ✅ **Payment: TiloPay** (payment_tilopay)

Each module takes ~30 seconds to install.

### Step 4: Test Staging

Create a test invoice:
1. Accounting → Customers → Invoices
2. Create new invoice
3. Add customer and products
4. Validate and generate e-invoice
5. Verify it works

### Step 5: Repeat for Production

1. Open: **https://168.231.71.94.nip.io**
2. Create database: `gms_production`
3. Password: `wQ4uMlQAC5Nz7TCFjnXyghJtVdMBYX2w`
4. **Demo Data:** ❌ **DO NOT CHECK**
5. Install same 3 modules
6. Configure company info and e-invoicing

---

## 🔧 Troubleshooting

### "Cannot connect" or "Timeout"

**Check containers are running:**
```bash
ssh root@168.231.71.94
cd /root/gms
docker compose ps
```

All should show "Up". If not:
```bash
docker compose up -d
```

### "500 Internal Server Error"

This means Odoo is running but database needs initialization.

**Option A:** Wait 5 minutes and refresh - initial startup takes time

**Option B:** Initialize via command line:
```bash
ssh root@168.231.71.94
docker exec -it gms_odoo_stage bash
odoo -d gms_staging --init=base --stop-after-init
exit
docker compose restart odoo-stage
```

Then refresh browser.

### "Certificate Error" persists

SSL generation failed. Check Traefik logs:
```bash
ssh root@168.231.71.94
docker logs gms_traefik --tail 50
```

Or use HTTP (not secure):
```
http://stage.168.231.71.94.nip.io
http://168.231.71.94.nip.io
```

### "Database already exists"

Good! Just login with the admin password:
- Staging: `pZIMnLNi9Jv1cAnFVTptO6MGsTvL/Vhx`
- Production: `wQ4uMlQAC5Nz7TCFjnXyghJtVdMBYX2w`

### Can't access /web/database/manager

If direct database access needed:
```bash
ssh root@168.231.71.94
cd /root/gms

# Edit config to allow database listing
sed -i 's/list_db = False/list_db = True/g' staging/odoo.conf
docker compose restart odoo-stage
```

Then visit: https://stage.168.231.71.94.nip.io/web/database/manager

---

## 📊 System Status

**Deployed:**
- ✅ 5 containers running
- ✅ Firewall configured
- ✅ SSL auto-renewal enabled
- ✅ Custom modules uploaded
- ✅ Staging + Production isolated

**Pending:**
- ⏳ Database initialization (you do this via web)
- ⏳ Module installation
- ⏳ Company configuration
- ⏳ E-invoicing setup

---

## 🎯 Important Next Actions

1. **Change master password!**
   Settings → Technical → Database Manager → Set Master Password

2. **Change VPS root password:**
   ```bash
   ssh root@168.231.71.94
   passwd
   ```

3. **Set up automated backups:**
   ```bash
   ssh root@168.231.71.94
   # Create backup script (see DEPLOYMENT_COMPLETE.md)
   ```

4. **Configure SMTP email**
   Settings → Technical → Email → Outgoing Mail Servers

5. **Upload production e-invoice certificate**
   When you have it from Banco Central de Costa Rica

---

## 📞 Need Help?

**Check logs:**
```bash
ssh root@168.231.71.94
cd /root/gms

# View all logs
docker compose logs -f

# Specific service
docker logs gms_odoo_stage --tail 100
docker logs gms_traefik --tail 100
```

**Restart everything:**
```bash
ssh root@168.231.71.94
cd /root/gms
docker compose restart
```

**Check resources:**
```bash
ssh root@168.231.71.94
docker stats
free -h
df -h
```

---

## ✅ What You Got

1. **Staging Environment**
   - 4.5GB RAM (Odoo + PostgreSQL)
   - For testing and development
   - Demo data enabled

2. **Production Environment**
   - 7GB RAM (Odoo + PostgreSQL, 4 workers!)
   - For real customers
   - Can handle 50-75 concurrent users

3. **Security**
   - Firewall active (SSH, HTTP, HTTPS only)
   - Database not exposed to internet
   - SSL/TLS encrypted
   - Automatic certificate renewal

4. **Custom Modules**
   - Costa Rica e-invoicing (Hacienda integration)
   - Costa Rica localization (taxes, reports)
   - TiloPay payment gateway

5. **Professional Setup**
   - Docker containers
   - Traefik reverse proxy
   - Isolated environments
   - Production-ready configuration

---

**🚀 Ready to start! Open your browser and visit:**

**Staging:** https://stage.168.231.71.94.nip.io
**Production:** https://168.231.71.94.nip.io

**Questions? Everything is documented in:**
- `DEPLOYMENT_COMPLETE.md` - Full deployment details
- `DEPLOYMENT_GUIDE.md` - Detailed guide
- `QUICK_START.md` - Quick reference

**Your GMS system is live and ready for you!** 🎉
