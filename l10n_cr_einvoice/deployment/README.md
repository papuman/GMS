# Deployment Guide
## Costa Rica E-Invoicing Module v19.0.1.8.0

Complete deployment infrastructure for production-ready Costa Rica electronic invoicing.

---

## Quick Links

- **30-Minute Deployment**: [QUICK_START.md](QUICK_START.md)
- **Pre-Deployment Checklist**: [PRE_DEPLOYMENT_CHECKLIST.md](PRE_DEPLOYMENT_CHECKLIST.md)
- **Deployment Execution**: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
- **Rollback Procedures**: [ROLLBACK_PLAN.md](ROLLBACK_PLAN.md)
- **Admin Guide**: [../docs/ADMIN_GUIDE.md](../docs/ADMIN_GUIDE.md)

---

## Deployment Options

### Option 1: Quick Start (30 minutes)

For experienced administrators who want to deploy quickly:

```bash
# Follow the quick start guide
cat QUICK_START.md

# Execute deployment
cd ../docker
docker-compose up -d
```

**Best for**: Development, staging, proof-of-concept

### Option 2: Full Production Deployment (60 minutes)

For production environments with complete validation:

```bash
# 1. Complete pre-deployment checklist
cat PRE_DEPLOYMENT_CHECKLIST.md

# 2. Execute deployment with checklist
cat DEPLOYMENT_CHECKLIST.md

# 3. Run automated deployment
cd ..
./scripts/deploy_production.sh
```

**Best for**: Production, enterprise deployments

### Option 3: Automated CI/CD

Using GitHub Actions for continuous deployment:

```bash
# Push to main branch triggers staging deployment
git push origin main

# Tag for production deployment
git tag -a v1.8.0 -m "Production release"
git push origin v1.8.0
```

**Best for**: Continuous delivery, DevOps teams

---

## Prerequisites

### Required

- [ ] Docker 24.0+
- [ ] Docker Compose 2.20+
- [ ] Ubuntu 22.04 LTS or later
- [ ] 4 CPU cores, 8GB RAM minimum
- [ ] 100GB disk space
- [ ] Domain name with DNS configured
- [ ] SSL certificate (Let's Encrypt or commercial)
- [ ] Hacienda production certificate
- [ ] Hacienda API credentials
- [ ] SMTP server access

### Optional

- [ ] Prometheus/Grafana for monitoring
- [ ] S3-compatible storage for backups
- [ ] fail2ban for security
- [ ] Redis for caching

---

## Deployment Flow

```
┌─────────────────────┐
│  Pre-Deployment     │
│  Checklist          │ (200+ items)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Create Backup      │ (5 min)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Deploy             │ (30 min)
│  ./deploy.sh        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Smoke Tests        │ (5 min)
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
  Pass          Fail
    │             │
    ▼             ▼
┌───────┐   ┌──────────┐
│Monitor│   │ Rollback │ (15 min)
│24 hrs │   └──────────┘
└───────┘
```

---

## Command Reference

### Deployment

```bash
# Full automated deployment
./scripts/deploy_production.sh

# Skip backup (not recommended)
./scripts/deploy_production.sh --skip-backup

# Rollback
./scripts/deploy_production.sh --rollback
```

### Backup & Restore

```bash
# Create backup
./scripts/backup_database.sh

# Create encrypted backup
./scripts/backup_database.sh --encrypt

# Upload to cloud
./scripts/backup_database.sh --encrypt --upload

# Restore from backup
./scripts/restore_database.sh backup_file.dump

# Restore encrypted backup
./scripts/restore_database.sh backup_file.dump.enc --decrypt
```

### Health & Monitoring

```bash
# Run health check
./scripts/health_check.sh

# With email alerts
./scripts/health_check.sh --alert-email admin@example.com

# Run smoke tests
python3 deployment/smoke_tests.py

# Test specific URL
python3 deployment/smoke_tests.py --url https://gms-cr.com

# Verbose output
python3 deployment/smoke_tests.py --verbose
```

### Service Management

```bash
# Start services
cd docker
docker-compose up -d

# Stop services
docker-compose down

# Restart Odoo
docker-compose restart odoo

# View logs
docker-compose logs -f odoo

# Check status
docker-compose ps
```

---

## Deployment Timeline

### Standard Deployment (30 minutes)

| Time | Task | Duration |
|------|------|----------|
| T-0 | Create backup | 5 min |
| T+5 | Stop services | 2 min |
| T+7 | Pull latest code | 3 min |
| T+10 | Build Docker images | 10 min |
| T+20 | Start database | 2 min |
| T+22 | Run migrations | 5 min |
| T+27 | Start all services | 3 min |
| T+30 | Run smoke tests | 5 min |
| **Total** | **Deployment complete** | **35 min** |

### Rollback (15 minutes)

| Time | Task | Duration |
|------|------|----------|
| T-0 | Stop services | 2 min |
| T+2 | Restore database | 8 min |
| T+10 | Restore filestore | 2 min |
| T+12 | Start services | 3 min |
| **Total** | **Rollback complete** | **15 min** |

---

## Testing

### Before Deployment

```bash
# Run all tests
cd ..
pytest tests/ -v

# Run specific test suite
pytest tests/test_hacienda_api.py -v

# Check code quality
flake8 models/ wizards/ tests/
pylint models/ wizards/ tests/
```

### After Deployment

```bash
# Smoke tests
python3 deployment/smoke_tests.py

# Health check
./scripts/health_check.sh

# Functional test (create test invoice)
docker-compose exec odoo odoo shell < test_create_invoice.py
```

---

## Monitoring

### Health Dashboard

Access Grafana dashboard (if monitoring enabled):
```
http://your-domain:3000
```

Default credentials: admin / (configured password)

### Metrics

Prometheus metrics endpoint:
```
http://your-domain:9090
```

### Logs

```bash
# Odoo application logs
docker-compose logs -f odoo

# Nginx access logs
docker-compose logs -f nginx

# Database logs
docker-compose logs -f db

# All logs
docker-compose logs -f
```

### Alerts

Configured alerts in `/monitoring/alerts.yml`:
- Critical: Service down, database issues, disk space
- Warning: High CPU/memory, slow queries
- Business: Invoice rejections, API errors

---

## Troubleshooting

### Deployment Failed

```bash
# Check logs
cat docker/logs/deployment_*.log

# Check service status
docker-compose ps

# Check specific service
docker-compose logs odoo
```

**Common Issues**:
1. Database connection failed → Check `.env` credentials
2. Port already in use → Stop conflicting service
3. Permission denied → Check file permissions

### Services Won't Start

```bash
# Verify configuration
docker-compose config

# Test database connection
docker-compose exec db pg_isready

# Test Odoo configuration
docker-compose exec odoo odoo --test-enable --stop-after-init
```

### Rollback Failed

```bash
# Find latest backup
ls -lt docker/backups/

# Manual restore
./scripts/restore_database.sh docker/backups/pre_deploy_*.dump

# If still failing, contact support
```

---

## Security

### SSL/TLS

Setup SSL certificate:
```bash
# See detailed guide
cat ../security/SSL_SETUP.md

# Quick Let's Encrypt setup
sudo certbot certonly --standalone -d your-domain.com
```

### Firewall

Configure firewall:
```bash
# Run firewall setup
sudo ../security/firewall_rules.sh

# Check firewall status
sudo ufw status
```

### Hacienda Certificates

Install Hacienda certificate:
```bash
# See detailed guide
cat ../security/HACIENDA_CERTIFICATE_SETUP.md

# Copy certificate
cp certificate.p12 docker/certificates/
chmod 600 docker/certificates/certificate.p12
```

---

## Performance Tuning

### Odoo Configuration

Edit `docker/odoo.conf`:
```ini
workers = 8  # (CPU cores * 2) + 1
limit_memory_hard = 4294967296  # 4GB
limit_memory_soft = 3221225472  # 3GB
db_maxconn = 128
```

### Database Optimization

```bash
# Weekly maintenance
docker-compose exec db psql -U odoo -d odoo -c "VACUUM ANALYZE;"

# Reindex
docker-compose exec db psql -U odoo -d odoo -c "REINDEX DATABASE odoo;"
```

### Nginx Tuning

Already optimized in `docker/nginx.conf`:
- Gzip compression
- Static file caching
- Connection pooling
- Rate limiting

---

## Backup Strategy

### Automated Backups

```bash
# Setup daily backups at 2 AM
crontab -e

# Add line:
0 2 * * * /opt/gms-odoo/l10n_cr_einvoice/scripts/backup_database.sh --encrypt --upload
```

### Backup Retention

- Local: 30 days
- Cloud: 90 days (if S3 configured)
- Critical backups: Keep indefinitely

### Backup Verification

```bash
# Test restore monthly
./scripts/restore_database.sh --target test_odoo backup_file.dump

# Verify integrity
pg_restore --list backup_file.dump
```

---

## Disaster Recovery

### Recovery Time Objectives

- **RTO** (Recovery Time): 1 hour
- **RPO** (Recovery Point): 15 minutes

### Recovery Procedure

1. **Identify Issue**
   ```bash
   ./scripts/health_check.sh
   ```

2. **Execute Rollback**
   ```bash
   ./scripts/deploy_production.sh --rollback
   ```

3. **Verify Recovery**
   ```bash
   python3 deployment/smoke_tests.py
   ```

4. **Monitor**
   ```bash
   ./scripts/health_check.sh --alert-email admin@example.com
   ```

---

## Support

### Documentation

- **Admin Guide**: [../docs/ADMIN_GUIDE.md](../docs/ADMIN_GUIDE.md)
- **User Guide**: [../docs/USER_GUIDE.md](../docs/USER_GUIDE.md)
- **Troubleshooting**: [../docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md)
- **API Reference**: [../docs/API_REFERENCE.md](../docs/API_REFERENCE.md)

### Support Channels

**Email**: support@gms-cr.com
**Hours**: Mon-Fri 8AM-6PM CST
**Emergency**: 24/7 hotline (critical issues)

### Escalation

1. Technical Lead (0-30 min)
2. DevOps Manager (30-60 min)
3. CTO (>60 min)

---

## Checklist Quick Reference

### Pre-Deployment (200+ items)

- [ ] Infrastructure ready
- [ ] SSL certificates configured
- [ ] Hacienda credentials ready
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Security hardened
- [ ] Team trained

See: [PRE_DEPLOYMENT_CHECKLIST.md](PRE_DEPLOYMENT_CHECKLIST.md)

### Deployment (12 steps)

1. [ ] Create backup
2. [ ] Stop services
3. [ ] Pull latest code
4. [ ] Update configuration
5. [ ] Build Docker images
6. [ ] Start database
7. [ ] Run migrations
8. [ ] Start all services
9. [ ] Wait for services
10. [ ] Run smoke tests
11. [ ] Functional validation
12. [ ] Monitor for issues

See: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)

### Post-Deployment

- [ ] All services healthy
- [ ] All tests passing
- [ ] No errors in logs
- [ ] Response time acceptable
- [ ] Monitored for 24 hours

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 19.0.1.8.0 | 2024-12-29 | Phase 7: Production deployment complete |
| 19.0.1.7.0 | 2024-12-XX | Phase 6: Analytics & reporting |
| 19.0.1.6.0 | 2024-12-XX | Phase 5: POS integration |
| 19.0.1.5.0 | 2024-12-XX | Phase 4: PDF & email delivery |
| 19.0.1.4.0 | 2024-12-XX | Phase 3: Enhanced API integration |
| 19.0.1.3.0 | 2024-12-XX | Phase 1C: CIIU codes |
| 19.0.1.2.0 | 2024-12-XX | Phase 1B: Discount codes |
| 19.0.1.1.0 | 2024-12-XX | Phase 1A: Payment methods |
| 19.0.1.0.0 | 2024-12-XX | Initial release |

---

## License

LGPL-3

---

## Contact

**GMS Development Team**
- Website: https://gms-cr.com
- Email: dev@gms-cr.com
- Support: support@gms-cr.com

---

**Ready for Production**
**Version 19.0.1.8.0**
**Enterprise-Grade E-Invoicing**
