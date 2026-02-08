# Phase 7: Quick Reference Guide
## Production Deployment Infrastructure

**Version**: 19.0.1.8.0 | **Status**: PRODUCTION READY

---

## One-Command Operations

### Deploy
```bash
cd /Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/l10n_cr_einvoice
./scripts/deploy_production.sh
```

### Backup
```bash
./scripts/backup_database.sh --encrypt --upload
```

### Restore
```bash
./scripts/restore_database.sh /path/to/backup.dump
```

### Health Check
```bash
./scripts/health_check.sh --alert-email admin@gms-cr.com
```

### Rollback
```bash
./scripts/deploy_production.sh --rollback
```

---

## Quick Start (30 Minutes)

```bash
# 1. Setup (5 min)
cd l10n_cr_einvoice/docker
cp .env.example .env
nano .env  # Configure

# 2. Build (10 min)
docker-compose build

# 3. Deploy (10 min)
docker-compose up -d

# 4. Initialize (3 min)
docker-compose exec odoo odoo -d odoo -i l10n_cr_einvoice --stop-after-init
docker-compose restart odoo

# 5. Test (2 min)
cd ..
python3 deployment/smoke_tests.py
```

---

## File Locations

### Scripts
- **Deploy**: `/scripts/deploy_production.sh`
- **Backup**: `/scripts/backup_database.sh`
- **Restore**: `/scripts/restore_database.sh`
- **Health**: `/scripts/health_check.sh`
- **Migrate**: `/scripts/migrate_data.sh`

### Docker
- **Compose**: `/docker/docker-compose.yml`
- **Dockerfile**: `/docker/Dockerfile`
- **Nginx**: `/docker/nginx.conf`
- **Odoo**: `/docker/odoo.conf`
- **Environment**: `/docker/.env.example`

### Documentation
- **Admin Guide**: `/docs/ADMIN_GUIDE.md`
- **Pre-Deployment**: `/deployment/PRE_DEPLOYMENT_CHECKLIST.md`
- **Deployment**: `/deployment/DEPLOYMENT_CHECKLIST.md`
- **Rollback**: `/deployment/ROLLBACK_PLAN.md`
- **Quick Start**: `/deployment/QUICK_START.md`

### Monitoring
- **Prometheus**: `/monitoring/prometheus.yml`
- **Alerts**: `/monitoring/alerts.yml`
- **Dashboard**: `/monitoring/grafana_dashboard.json`

### Security
- **Hacienda Cert**: `/security/HACIENDA_CERTIFICATE_SETUP.md`
- **SSL Setup**: `/security/SSL_SETUP.md`
- **Firewall**: `/security/firewall_rules.sh`

---

## Common Tasks

### Service Management
```bash
cd docker

# Start all
docker-compose up -d

# Stop all
docker-compose down

# Restart Odoo
docker-compose restart odoo

# View logs
docker-compose logs -f odoo

# Check status
docker-compose ps
```

### Database Operations
```bash
# Backup now
./scripts/backup_database.sh

# Restore from backup
./scripts/restore_database.sh backup_file.dump

# Connect to database
docker-compose exec db psql -U odoo -d odoo

# Vacuum & analyze
docker-compose exec db psql -U odoo -d odoo -c "VACUUM ANALYZE;"
```

### Monitoring
```bash
# Health check
./scripts/health_check.sh

# Smoke tests
python3 deployment/smoke_tests.py

# View metrics
open http://localhost:9090  # Prometheus
open http://localhost:3000  # Grafana
```

### Logs
```bash
# Odoo logs
docker-compose logs -f odoo

# Nginx logs
docker-compose logs -f nginx

# Database logs
docker-compose logs -f db

# All logs
docker-compose logs -f

# Deployment logs
cat docker/logs/deployment_*.log
```

---

## Emergency Procedures

### System Down
```bash
# 1. Check status
./scripts/health_check.sh

# 2. Check logs
docker-compose logs --tail=100 odoo

# 3. Restart services
docker-compose restart

# 4. If still down, rollback
./scripts/deploy_production.sh --rollback
```

### Database Issues
```bash
# 1. Check connectivity
docker-compose exec db pg_isready

# 2. Check connections
docker-compose exec db psql -U odoo -c "SELECT count(*) FROM pg_stat_activity;"

# 3. Kill connections if needed
docker-compose restart db

# 4. Restore from backup if corrupted
./scripts/restore_database.sh latest_backup.dump
```

### SSL Certificate Expired
```bash
# 1. Check expiry
openssl x509 -in docker/ssl/fullchain.pem -noout -dates

# 2. Renew Let's Encrypt
sudo certbot renew

# 3. Copy new certificate
sudo cp /etc/letsencrypt/live/domain/fullchain.pem docker/ssl/
sudo cp /etc/letsencrypt/live/domain/privkey.pem docker/ssl/

# 4. Restart Nginx
docker-compose restart nginx
```

---

## Deployment Timeline

| Time | Task | Command |
|------|------|---------|
| T-0 | Backup | `./scripts/backup_database.sh` |
| T+5 | Stop | `docker-compose down` |
| T+10 | Build | `docker-compose build` |
| T+20 | Start | `docker-compose up -d` |
| T+25 | Migrate | `docker-compose exec odoo odoo --update=l10n_cr_einvoice` |
| T+30 | Test | `python3 deployment/smoke_tests.py` |

**Total**: 30 minutes

---

## Health Checks

### Manual Checks
```bash
# 1. Services running
docker-compose ps

# 2. HTTP endpoint
curl http://localhost/web/health

# 3. Database
docker-compose exec db pg_isready

# 4. Disk space
df -h

# 5. Memory
free -h

# 6. Logs for errors
docker-compose logs --tail=100 odoo | grep -i error
```

### Automated Checks
```bash
# Run all checks
./scripts/health_check.sh

# With email alerts
./scripts/health_check.sh --alert-email admin@gms-cr.com

# Add to cron (every 30 min)
*/30 * * * * /path/to/health_check.sh --alert-email admin@gms-cr.com
```

---

## Performance Tuning

### Odoo Workers
Edit `docker/odoo.conf`:
```ini
workers = 8  # CPU cores * 2 + 1
```

### Database Connections
```ini
db_maxconn = 128
```

### Memory Limits
```ini
limit_memory_hard = 4294967296  # 4GB
limit_memory_soft = 3221225472  # 3GB
```

### Apply Changes
```bash
docker-compose restart odoo
```

---

## Monitoring Dashboards

### Access
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090

### Key Metrics
- Invoice submission rate
- Acceptance rate
- API response time
- Error rate
- Queue sizes
- System resources

### Alerts
- Critical: Service down, database issues
- Warning: High CPU/memory, slow queries
- Business: Invoice rejections, API errors

---

## Backup Strategy

### Automated Daily Backup
```bash
# Add to crontab
0 2 * * * /path/to/backup_database.sh --encrypt --upload
```

### Manual Backup
```bash
./scripts/backup_database.sh --encrypt
```

### Verify Backup
```bash
# List backups
ls -lh docker/backups/

# Test restore
./scripts/restore_database.sh --target test_db backup.dump
```

### Retention
- **Local**: 30 days
- **Cloud**: 90 days
- **Critical**: Keep indefinitely

---

## Security Checklist

- [ ] SSL certificate valid (>30 days)
- [ ] Firewall enabled (UFW)
- [ ] fail2ban active
- [ ] Strong passwords set
- [ ] Hacienda certificates secured
- [ ] Backups encrypted
- [ ] Security updates applied
- [ ] Audit logging enabled

### Quick Security Check
```bash
# SSL certificate
openssl x509 -in docker/ssl/fullchain.pem -noout -dates

# Firewall status
sudo ufw status

# fail2ban status
sudo fail2ban-client status

# Security updates
sudo apt update && sudo apt list --upgradable
```

---

## Troubleshooting

### Issue: Can't access website
```bash
# Check firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check Nginx
docker-compose logs nginx

# Test locally
curl http://localhost
```

### Issue: Slow performance
```bash
# Check resource usage
docker stats

# Database vacuum
docker-compose exec db psql -U odoo -d odoo -c "VACUUM ANALYZE;"

# Increase workers
nano docker/odoo.conf  # workers = 8
docker-compose restart odoo
```

### Issue: Database connection failed
```bash
# Check database status
docker-compose exec db pg_isready

# Check credentials
cat docker/.env | grep POSTGRES

# Restart database
docker-compose restart db
```

---

## Support Contacts

**Email**: support@gms-cr.com
**Hours**: Mon-Fri 8AM-6PM CST
**Emergency**: 24/7 hotline

**Escalation**:
1. Technical Lead (0-30 min)
2. DevOps Manager (30-60 min)
3. CTO (>60 min)

---

## Success Criteria

- [ ] All services healthy
- [ ] All tests passing (200+)
- [ ] Response time <2s
- [ ] Error rate <0.1%
- [ ] Uptime >99.9%
- [ ] Backups working
- [ ] Monitoring active
- [ ] Documentation complete

---

## Version Information

**Module**: l10n_cr_einvoice
**Version**: 19.0.1.8.0
**Status**: PRODUCTION READY
**Odoo**: 19.0
**PostgreSQL**: 15
**Python**: 3.11

---

## Quick Commands Reference

```bash
# Deploy
./scripts/deploy_production.sh

# Rollback
./scripts/deploy_production.sh --rollback

# Backup
./scripts/backup_database.sh --encrypt

# Restore
./scripts/restore_database.sh backup.dump

# Health Check
./scripts/health_check.sh

# Start Services
docker-compose up -d

# Stop Services
docker-compose down

# Logs
docker-compose logs -f odoo

# Test
python3 deployment/smoke_tests.py
```

---

**PRODUCTION READY - Version 19.0.1.8.0**
