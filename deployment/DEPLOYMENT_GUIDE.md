# GMS Production Deployment Guide
# Hostinger VPS - Staging + Production Environments

**VPS ID:** 920223
**IP Address:** 168.231.71.94
**Last Updated:** 2026-01-27

---

## Architecture Overview

```
Internet → Traefik (SSL) → {
    stage.gms-XXXX.hostingersite.com → Staging Environment
    gms-XXXX.hostingersite.com       → Production Environment
}
```

### Environment Specifications

| Resource | Staging | Production | Total |
|----------|---------|------------|-------|
| Odoo RAM | 1.5GB | 3GB | 4.5GB |
| PostgreSQL RAM | 1GB | 2GB | 3GB |
| Workers | 0 (dev) | 2 | - |
| DB Max Conn | 64 | 128 | - |
| Purpose | Testing, dev branches | Live customers | - |

**VPS Total:** 8GB RAM, 2 CPU

---

## Pre-Deployment Steps

### Step 1: Generate Free Subdomain

```bash
# SSH into VPS
ssh root@168.231.71.94

# Install Hostinger CLI tools (if not present)
# Use Hostinger API to generate subdomain
curl -X POST https://api.hostinger.com/v1/hosting/subdomain/generate
```

Or use the Hostinger MCP tool to generate subdomain.

**Expected Output:** `gms-xxxxx.hostingersite.com`

Update `.env` file with this domain.

### Step 2: Create Deployment Directory

```bash
# On VPS
mkdir -p /root/gms
cd /root/gms
mkdir -p staging/addons production/addons traefik
```

### Step 3: Upload Files to VPS

**From your local machine:**

```bash
# Navigate to deployment folder
cd /Users/papuman/Documents/My\ Projects/GMS/deployment

# Upload docker-compose
scp docker-compose.production.yml root@168.231.71.94:/root/gms/docker-compose.yml

# Upload configs
scp staging/odoo.conf root@168.231.71.94:/root/gms/staging/
scp production/odoo.conf root@168.231.71.94:/root/gms/production/

# Upload custom addons (staging)
scp -r ../odoo/addons/l10n_cr root@168.231.71.94:/root/gms/staging/addons/
scp -r ../odoo/addons/l10n_cr_einvoice root@168.231.71.94:/root/gms/staging/addons/
scp -r ../payment_tilopay root@168.231.71.94:/root/gms/staging/addons/

# Upload custom addons (production) - same initially
scp -r ../odoo/addons/l10n_cr root@168.231.71.94:/root/gms/production/addons/
scp -r ../odoo/addons/l10n_cr_einvoice root@168.231.71.94:/root/gms/production/addons/
scp -r ../payment_tilopay root@168.231.71.94:/root/gms/production/addons/

# Upload .env file (after editing)
scp .env root@168.231.71.94:/root/gms/
```

### Step 4: Configure Environment Variables

```bash
# On VPS
cd /root/gms
cp .env.template .env
nano .env
```

**Update these values:**
- `DOMAIN_BASE` - Your generated subdomain
- `ACME_EMAIL` - Your email for SSL certificates
- `POSTGRES_PASSWORD_STAGE` - Strong password
- `POSTGRES_PASSWORD_PROD` - Strong password (different)
- `TRAEFIK_AUTH` - Generate with htpasswd

**Generate Traefik Auth:**
```bash
# Install htpasswd
apt-get install -y apache2-utils

# Generate password (replace 'your_password')
echo $(htpasswd -nb admin your_password) | sed -e s/\\$/\\$\\$/g
```

### Step 5: Configure Firewall (CRITICAL)

Use Hostinger MCP to create firewall or do it manually:

```bash
# Rules needed:
# - Allow SSH (22) from your IP
# - Allow HTTP (80) from anywhere
# - Allow HTTPS (443) from anywhere
# - Deny PostgreSQL (5432) from anywhere
# - Deny direct Odoo access (8069, 8071) from anywhere
```

---

## Deployment Process

### Step 1: Deploy Infrastructure

```bash
# SSH into VPS
ssh root@168.231.71.94
cd /root/gms

# Stop existing n8n (temporarily)
cd /docker/n8n
docker-compose down

# Start GMS stack
cd /root/gms
docker-compose up -d

# Verify containers started
docker ps

# Check logs
docker logs gms_traefik
docker logs gms_odoo_stage
docker logs gms_odoo_prod
```

**Expected containers:**
- gms_traefik
- gms_postgres_stage
- gms_odoo_stage
- gms_postgres_prod
- gms_odoo_prod

### Step 2: Initialize Staging Database

```bash
# Wait for containers to be healthy (30 seconds)
sleep 30

# Access staging Odoo
# Visit: https://stage.gms-XXXX.hostingersite.com

# You'll see database creation screen
# Create database:
#   - Database Name: gms_staging
#   - Email: admin@example.com
#   - Password: (use STAGE_ODOO_ADMIN_PASSWORD from .env)
#   - Language: English or Spanish
#   - Country: Costa Rica
#   - Demo data: Load (for testing)
```

### Step 3: Install GMS Modules (Staging)

```bash
# Option A: Via Web UI
# 1. Go to Apps menu
# 2. Update Apps List
# 3. Search for: l10n_cr, l10n_cr_einvoice, payment_tilopay
# 4. Install each module

# Option B: Via command line
docker exec -it gms_odoo_stage odoo shell -d gms_staging --no-http
```

In Odoo shell:
```python
# Install modules
env['ir.module.module'].search([('name', 'in', ['l10n_cr', 'l10n_cr_einvoice', 'payment_tilopay'])]).button_install()
env.cr.commit()
exit()
```

### Step 4: Test Staging Environment

```bash
# Run test script
docker exec -it gms_odoo_stage bash
cd /mnt/extra-addons/l10n_cr_einvoice
python3 -m pytest tests/
```

**Verify:**
- [ ] Can log in to staging
- [ ] Modules installed successfully
- [ ] Can create company
- [ ] Can create invoice
- [ ] E-invoice generation works (sandbox)

### Step 5: Initialize Production Database

**Only proceed if staging tests pass!**

```bash
# Visit: https://gms-XXXX.hostingersite.com

# Create database:
#   - Database Name: gms_production
#   - Email: admin@yourdomain.com
#   - Password: (use PROD_ODOO_ADMIN_PASSWORD from .env)
#   - Language: Spanish
#   - Country: Costa Rica
#   - Demo data: DO NOT LOAD

# Install GMS modules (same as staging)
```

### Step 6: Configure Production

**Critical production settings:**

1. **Company Setup:**
   - Settings → Companies → Update Company
   - Legal Name
   - Tax ID (Cédula Jurídica)
   - Costa Rica location code
   - Upload production certificate

2. **E-Invoice Configuration:**
   - Hacienda Environment: **Production**
   - API Credentials: Production credentials
   - Auto-submit: Disabled initially

3. **Email Configuration:**
   - Settings → Technical → Outgoing Mail Servers
   - Configure SMTP server

4. **Security:**
   - Change admin password
   - Create user accounts
   - Configure access rights

### Step 7: Data Migration (if needed)

```bash
# Export from local/old system
docker exec gms_postgres pg_dump -U odoo gms_validation > backup_for_migration.sql

# Upload to VPS
scp backup_for_migration.sql root@168.231.71.94:/root/

# Import to production
docker exec -i gms_postgres_prod psql -U odoo -d gms_production < /root/backup_for_migration.sql
```

---

## Workflow: Deploying Updates

### Staging Workflow

```bash
# 1. Upload new code to staging
scp -r ./new_module root@168.231.71.94:/root/gms/staging/addons/

# 2. Restart staging Odoo
docker restart gms_odoo_stage

# 3. Update module
docker exec -it gms_odoo_stage odoo -d gms_staging -u module_name --stop-after-init

# 4. Test changes
# Visit: https://stage.gms-XXXX.hostingersite.com

# 5. Verify functionality
```

### Production Deployment

```bash
# ONLY after staging validation passes!

# 1. Backup production database
docker exec gms_postgres_prod pg_dump -U odoo gms_production > /root/backups/prod_$(date +%Y%m%d_%H%M%S).sql

# 2. Upload code to production
scp -r ./new_module root@168.231.71.94:/root/gms/production/addons/

# 3. Restart production Odoo
docker restart gms_odoo_prod

# 4. Update module (minimal downtime)
docker exec -it gms_odoo_prod odoo -d gms_production -u module_name --stop-after-init

# 5. Smoke test
# Visit: https://gms-XXXX.hostingersite.com
```

### Rolling Back

```bash
# If production deployment fails:

# 1. Stop production
docker stop gms_odoo_prod

# 2. Restore database
docker exec -i gms_postgres_prod psql -U odoo -d gms_production < /root/backups/prod_YYYYMMDD_HHMMSS.sql

# 3. Revert code
# Remove new files or restore old version

# 4. Start production
docker start gms_odoo_prod
```

---

## Monitoring

### Health Checks

```bash
# Check all containers
docker ps -a

# Check resource usage
docker stats

# Check logs
docker logs gms_odoo_prod --tail=100 -f
docker logs gms_postgres_prod --tail=100 -f

# Check disk space
df -h

# Check memory
free -h
```

### Automated Backups

Create backup script:

```bash
cat > /root/backup_gms.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup staging database
docker exec gms_postgres_stage pg_dump -U odoo gms_staging | gzip > $BACKUP_DIR/stage_$DATE.sql.gz

# Backup production database
docker exec gms_postgres_prod pg_dump -U odoo gms_production | gzip > $BACKUP_DIR/prod_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /root/backup_gms.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /root/backup_gms.sh >> /var/log/gms_backup.log 2>&1
```

### SSL Certificate Renewal

Traefik handles this automatically via Let's Encrypt. Certificates renew 30 days before expiry.

**Monitor certificate status:**
```bash
docker logs gms_traefik | grep -i "certificate"
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs gms_odoo_prod

# Common issues:
# - Wrong password in .env
# - Database not ready (wait 30s)
# - Port conflict (check with: netstat -tulpn)
```

### Out of Memory

```bash
# Check memory usage
docker stats

# If OOM, reduce workers:
# Edit production/odoo.conf
workers = 1  # Reduce from 2 to 1

# Restart
docker restart gms_odoo_prod
```

### Database Connection Error

```bash
# Check postgres is running
docker ps | grep postgres

# Check connection from odoo container
docker exec -it gms_odoo_prod bash
psql -h postgres-prod -U odoo -d gms_production

# If fails, check .env passwords match
```

### SSL Certificate Issues

```bash
# Check traefik logs
docker logs gms_traefik

# Verify domain DNS
nslookup gms-XXXX.hostingersite.com

# Force certificate renewal
docker exec -it gms_traefik rm /acme.json
docker restart gms_traefik
```

---

## Security Checklist

- [ ] Firewall configured (SSH, HTTP, HTTPS only)
- [ ] Postgres not exposed to internet
- [ ] Strong passwords set for all databases
- [ ] Odoo master password changed from default
- [ ] list_db disabled in production
- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] Regular backups configured
- [ ] User access rights configured properly
- [ ] Production certificate secured
- [ ] API credentials secured

---

## URLs Reference

| Service | Staging | Production |
|---------|---------|------------|
| **Odoo** | https://stage.gms-XXXX.hostingersite.com | https://gms-XXXX.hostingersite.com |
| **Traefik Dashboard** | https://traefik.gms-XXXX.hostingersite.com | Same |
| **Database (internal)** | postgres-stage:5432 | postgres-prod:5432 |

---

## Support & Maintenance

**Regular Tasks:**
- Daily: Check docker stats
- Daily: Review logs for errors
- Weekly: Verify backups completed
- Monthly: Review disk space
- Monthly: Security updates (docker pull latest images)
- Quarterly: Test backup restoration

**Upgrade Path:**
When VPS resources are insufficient:
- Upgrade to KVM 4 (4 CPU, 16GB RAM)
- Cost: ~$30-40/month additional
