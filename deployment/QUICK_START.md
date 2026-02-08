# GMS Quick Start Deployment

**Generated Domain:** `blanchedalmond-raccoon-234970.hostingersite.com`

## Your URLs

- **Staging:** https://stage.blanchedalmond-raccoon-234970.hostingersite.com
- **Production:** https://blanchedalmond-raccoon-234970.hostingersite.com
- **Traefik Dashboard:** https://traefik.blanchedalmond-raccoon-234970.hostingersite.com

---

## Deploy in 5 Minutes

### 1. Configure Passwords

```bash
cd deployment
nano .env
```

**Change these 4 values:**
- `ACME_EMAIL` - Your email (for SSL cert notifications)
- `POSTGRES_PASSWORD_STAGE` - Strong password for staging DB
- `POSTGRES_PASSWORD_PROD` - Different strong password for production DB
- `TRAEFIK_AUTH` - Dashboard password (see below)

**Generate Traefik password:**
```bash
# On Mac:
brew install apache2
htpasswd -nb admin YourPassword

# On Linux:
sudo apt-get install apache2-utils
htpasswd -nb admin YourPassword

# Copy the output to TRAEFIK_AUTH in .env
# Replace $ with $$ (double dollar signs)
```

### 2. Configure VPS Firewall (CRITICAL!)

**Before deploying, you MUST configure firewall!**

The VPS currently has NO firewall. We need to create one.

I can do this for you via Hostinger API. Should I proceed?

### 3. Deploy!

```bash
cd deployment
./deploy.sh
```

**What it does:**
- Creates directories on VPS
- Uploads all configs
- Uploads your custom modules
- Starts 5 containers
- Configures SSL

**Time:** ~5 minutes

### 4. Initialize Staging

**Visit:** https://stage.blanchedalmond-raccoon-234970.hostingersite.com

1. You'll see "Create Database" page
2. Fill in:
   - Master Password: (from odoo.conf, default: `javier5147` - CHANGE THIS!)
   - Database Name: `gms_staging`
   - Email: `admin@yourdomain.com`
   - Password: Strong password
   - Language: English or Spanish
   - Country: Costa Rica
   - Demo Data: ✅ Load (for testing)

3. Click "Create Database" (takes ~30 seconds)

4. Install modules:
   - Go to Apps menu
   - Click "Update Apps List"
   - Search and install:
     - Costa Rica - Accounting
     - Costa Rica E-Invoicing
     - Payment: TiloPay

### 5. Test Staging

**Create test invoice:**
1. Accounting → Customers → Invoices
2. Create new invoice
3. Add customer (with VAT)
4. Add line items
5. Validate
6. Click "Generate E-Invoice"
7. Click "Sign XML" (will use sandbox)
8. Click "Submit to Hacienda"
9. Check status

**If successful:** ✅ Ready to initialize production!

### 6. Initialize Production

**Visit:** https://blanchedalmond-raccoon-234970.hostingersite.com

1. Create database: `gms_production`
2. Demo Data: ❌ DO NOT LOAD
3. Install same modules
4. Configure company:
   - Settings → Companies
   - Legal name, Tax ID, address
   - Costa Rica location code
   - Upload production certificate (when ready)
5. Configure Hacienda:
   - Environment: **Production** (not sandbox!)
   - API username
   - API password
6. Configure SMTP email server

### 7. Test Production

**Before going live:**
- Create test invoice
- Verify e-invoice generation works
- Verify signature works
- Submit to Hacienda production
- Verify acceptance
- Check email delivery

---

## Monitoring

### Check Status

```bash
ssh root@168.231.71.94
cd /root/gms
docker-compose ps
```

**Expected:**
```
gms_traefik          running   80/tcp, 443/tcp
gms_postgres_stage   running   5432/tcp
gms_odoo_stage       running   8069/tcp
gms_postgres_prod    running   5432/tcp
gms_odoo_prod        running   8069/tcp
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f odoo-prod
docker-compose logs -f traefik
```

### Resource Usage

```bash
docker stats
```

**Watch for:**
- Memory: Should stay under 7.5GB
- If over 90%: Reduce workers in production/odoo.conf

---

## Daily Workflow

### Developing Features

1. **Work in staging:**
   - https://stage.blanchedalmond-raccoon-234970.hostingersite.com
   - Test all changes here first
   - Use sandbox e-invoicing

2. **Upload new code:**
   ```bash
   cd deployment
   scp -r ../your_module root@168.231.71.94:/root/gms/staging/addons/
   ssh root@168.231.71.94 "cd /root/gms && docker-compose restart odoo-stage"
   ```

3. **Test thoroughly**

4. **Promote to production:**
   ```bash
   # Backup first!
   ssh root@168.231.71.94 "docker exec gms_postgres_prod pg_dump -U odoo gms_production > /root/backups/prod_$(date +%Y%m%d).sql"

   # Deploy
   scp -r ../your_module root@168.231.71.94:/root/gms/production/addons/
   ssh root@168.231.71.94 "cd /root/gms && docker-compose restart odoo-prod"
   ```

### Backups

**Automated:**
```bash
# Setup on VPS (run once)
ssh root@168.231.71.94
cp /root/gms/deployment/backup_script.sh /root/backup_gms.sh
chmod +x /root/backup_gms.sh
crontab -e
# Add: 0 2 * * * /root/backup_gms.sh >> /var/log/gms_backup.log 2>&1
```

**Manual:**
```bash
ssh root@168.231.71.94 "docker exec gms_postgres_prod pg_dump -U odoo gms_production | gzip > /root/backups/manual_$(date +%Y%m%d_%H%M%S).sql.gz"
```

---

## Troubleshooting

### Can't access websites

**Check DNS:**
```bash
nslookup blanchedalmond-raccoon-234970.hostingersite.com
# Should return: 168.231.71.94
```

**Check Traefik:**
```bash
ssh root@168.231.71.94 "docker logs gms_traefik"
```

### Container keeps restarting

```bash
# Check logs
ssh root@168.231.71.94 "cd /root/gms && docker-compose logs odoo-prod"

# Common issues:
# - Wrong database password in .env
# - Database not ready (wait 30s and check again)
```

### Out of memory

```bash
# Check usage
ssh root@168.231.71.94 "docker stats"

# If Odoo over 90%:
# Edit production/odoo.conf
# Change: workers = 2 to workers = 1
# Then: docker-compose restart odoo-prod
```

### SSL certificate not working

```bash
# Takes ~2 minutes to generate on first access
# Check status:
ssh root@168.231.71.94 "docker logs gms_traefik | grep certificate"

# If stuck, verify DNS is pointing to VPS
```

---

## Next Steps After Deployment

1. **Security:**
   - Change all default passwords
   - Configure firewall (CRITICAL!)
   - Enable fail2ban
   - Disable database listing in production

2. **Configuration:**
   - Set up SMTP email server
   - Upload production e-invoice certificate
   - Configure payment gateways (TiloPay, SINPE)
   - Create user accounts

3. **Data Migration:**
   - If migrating from old system, export data
   - Import to staging first, test thoroughly
   - Then import to production

4. **Monitoring:**
   - Set up automated backups (cron job)
   - Monitor disk space weekly
   - Check logs daily for errors
   - Test backup restoration monthly

5. **Documentation:**
   - Document admin procedures
   - Train staff on system
   - Create user guides

---

## Support

**Files:**
- `README.md` - Quick reference
- `DEPLOYMENT_GUIDE.md` - Detailed walkthrough
- `../PRODUCTION_DEPLOYMENT_GUIDE.md` - E-invoicing setup

**Commands:**
- Deploy: `./deploy.sh`
- SSH: `ssh root@168.231.71.94`
- Logs: `docker-compose logs -f`
- Restart: `docker-compose restart`
- Stop: `docker-compose down`
- Start: `docker-compose up -d`

**URLs:**
- Staging: https://stage.blanchedalmond-raccoon-234970.hostingersite.com
- Production: https://blanchedalmond-raccoon-234970.hostingersite.com

---

**Ready to deploy?** Run `./deploy.sh` after configuring `.env`!
