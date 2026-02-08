# GMS Deployment Files

This directory contains all files needed to deploy GMS to Hostinger VPS with both **staging** and **production** environments.

## Quick Start

### 1. Generate Free Subdomain

First, generate a free Hostinger subdomain:

```bash
# Use Hostinger MCP or API
# You'll get something like: gms-xxxxx.hostingersite.com
```

### 2. Configure Environment

```bash
# Copy template
cp .env.template .env

# Edit configuration
nano .env
```

**Required changes:**
- `DOMAIN_BASE` - Your generated subdomain (e.g., `gms-xxxxx.hostingersite.com`)
- `ACME_EMAIL` - Your email for SSL certificates
- `POSTGRES_PASSWORD_STAGE` - Strong password for staging DB
- `POSTGRES_PASSWORD_PROD` - Strong password for production DB
- `TRAEFIK_AUTH` - Generate with htpasswd

**Generate htpasswd:**
```bash
# Install htpasswd (if not installed)
brew install apache2  # macOS
# or
sudo apt-get install apache2-utils  # Linux

# Generate auth string
htpasswd -nb admin your_password
```

Copy the output to `TRAEFIK_AUTH` in `.env`, but replace `$` with `$$`.

### 3. Deploy to VPS

```bash
# Run deployment script
./deploy.sh
```

The script will:
1. Create directories on VPS
2. Upload all configuration files
3. Upload custom Odoo modules
4. Start Docker containers
5. Display access URLs

### 4. Initialize Databases

**Staging:**
1. Visit `https://stage.gms-xxxxx.hostingersite.com`
2. Create database: `gms_staging`
3. Set admin password
4. Install modules: `l10n_cr`, `l10n_cr_einvoice`, `payment_tilopay`

**Production:**
1. Visit `https://gms-xxxxx.hostingersite.com`
2. Create database: `gms_production`
3. Set admin password
4. Install modules
5. Configure company info
6. Upload production certificate

## File Structure

```
deployment/
├── README.md                           # This file
├── DEPLOYMENT_GUIDE.md                 # Detailed deployment guide
├── deploy.sh                           # Automated deployment script
├── docker-compose.production.yml       # Docker orchestration
├── .env.template                       # Environment variables template
├── .env                                # Your configuration (git-ignored)
├── staging/
│   ├── odoo.conf                       # Staging Odoo config
│   └── addons/                         # Staging modules (uploaded by script)
└── production/
    ├── odoo.conf                       # Production Odoo config
    └── addons/                         # Production modules (uploaded by script)
```

## Architecture

### Containers

| Container | Purpose | Port | RAM |
|-----------|---------|------|-----|
| `gms_traefik` | Reverse proxy + SSL | 80, 443 | 100MB |
| `gms_postgres_stage` | Staging database | 5433 | 1GB |
| `gms_odoo_stage` | Staging app | 8071 | 1.5GB |
| `gms_postgres_prod` | Production database | 5432 | 2GB |
| `gms_odoo_prod` | Production app | 8069 | 3GB |

**Total:** ~7.6GB / 8GB available

### Domains

- **Staging:** `stage.gms-xxxxx.hostingersite.com`
- **Production:** `gms-xxxxx.hostingersite.com`
- **Traefik Dashboard:** `traefik.gms-xxxxx.hostingersite.com`

### Data Persistence

All data is persisted in Docker volumes:
- `postgres-stage-data` - Staging database
- `odoo-stage-data` - Staging files/attachments
- `postgres-prod-data` - Production database
- `odoo-prod-data` - Production files/attachments
- `traefik-acme` - SSL certificates

## Common Operations

### View Logs

```bash
# SSH into VPS
ssh root@168.231.71.94

cd /root/gms

# All logs
docker-compose logs -f

# Specific service
docker-compose logs -f odoo-prod
docker-compose logs -f postgres-stage
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart odoo-prod
docker-compose restart postgres-stage
```

### Update Code (Staging)

```bash
# From your local machine
cd /Users/papuman/Documents/My\ Projects/GMS/deployment

# Upload updated module
scp -r ../odoo/addons/l10n_cr_einvoice root@168.231.71.94:/root/gms/staging/addons/

# Restart staging
ssh root@168.231.71.94 "cd /root/gms && docker-compose restart odoo-stage"

# Update module in database
ssh root@168.231.71.94 "docker exec -it gms_odoo_stage odoo -d gms_staging -u l10n_cr_einvoice --stop-after-init"
```

### Promote Staging to Production

```bash
# Only after thorough testing in staging!

# Backup production first
ssh root@168.231.71.94 "docker exec gms_postgres_prod pg_dump -U odoo gms_production > /root/backups/prod_$(date +%Y%m%d_%H%M%S).sql"

# Upload code
scp -r ../odoo/addons/l10n_cr_einvoice root@168.231.71.94:/root/gms/production/addons/

# Restart production
ssh root@168.231.71.94 "cd /root/gms && docker-compose restart odoo-prod"

# Update module
ssh root@168.231.71.94 "docker exec -it gms_odoo_prod odoo -d gms_production -u l10n_cr_einvoice --stop-after-init"
```

### Backup Database

```bash
# Automated backups (set up on VPS)
ssh root@168.231.71.94 "bash /root/backup_gms.sh"

# Manual backup
ssh root@168.231.71.94 "docker exec gms_postgres_prod pg_dump -U odoo gms_production | gzip > /root/backups/manual_$(date +%Y%m%d_%H%M%S).sql.gz"
```

### Restore Database

```bash
# List backups
ssh root@168.231.71.94 "ls -lh /root/backups/"

# Restore (CAUTION: Overwrites database!)
ssh root@168.231.71.94 "gunzip < /root/backups/prod_YYYYMMDD_HHMMSS.sql.gz | docker exec -i gms_postgres_prod psql -U odoo -d gms_production"
```

## Security

### Firewall Configuration

**Must be configured before deployment!**

Use Hostinger MCP or panel:
- ✅ Allow: SSH (22), HTTP (80), HTTPS (443)
- ❌ Block: PostgreSQL (5432, 5433), Direct Odoo (8069, 8071)

### Credentials

**Change these immediately after deployment:**

1. Odoo admin password (both environments)
2. Database passwords (in .env)
3. Traefik dashboard password (in .env)
4. Master password in odoo.conf files

### Certificate Management

- SSL certificates auto-renew via Let's Encrypt
- Production e-invoicing certificate must be uploaded manually
- Monitor certificate expiry

## Monitoring

### Resource Usage

```bash
ssh root@168.231.71.94 "docker stats"
```

### Disk Space

```bash
ssh root@168.231.71.94 "df -h"
```

### Container Health

```bash
ssh root@168.231.71.94 "cd /root/gms && docker-compose ps"
```

## Troubleshooting

### Container won't start

```bash
# Check logs
ssh root@168.231.71.94 "cd /root/gms && docker-compose logs odoo-prod"

# Common issues:
# - Wrong password in .env
# - Database not ready (wait 30s)
# - Port conflict
```

### Out of memory

```bash
# Check usage
ssh root@168.231.71.94 "free -h"

# Reduce workers in production/odoo.conf
# Change: workers = 2 to workers = 1
# Restart: docker-compose restart odoo-prod
```

### SSL certificate issues

```bash
# Check traefik logs
ssh root@168.231.71.94 "docker logs gms_traefik"

# Verify DNS
nslookup gms-xxxxx.hostingersite.com

# Force renewal
ssh root@168.231.71.94 "docker exec -it gms_traefik rm /acme.json && docker restart gms_traefik"
```

## Support

For detailed instructions, see:
- `DEPLOYMENT_GUIDE.md` - Complete deployment walkthrough
- Production deployment guide in project root
- Odoo documentation: https://www.odoo.com/documentation/19.0/

## License

See project LICENSE file.
