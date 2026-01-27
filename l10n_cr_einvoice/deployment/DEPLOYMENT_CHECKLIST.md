# Deployment Checklist
## Production Deployment Execution

Execute these steps IN ORDER during deployment window.

## Pre-Deployment (T-30 minutes)

- [ ] Verify pre-deployment checklist 100% complete
- [ ] Confirm deployment window with stakeholders
- [ ] Ensure rollback plan is ready
- [ ] Have support team on standby
- [ ] Backup all critical data

## Deployment Steps

### 1. Create Backup (T-0)

```bash
cd /opt/gms-odoo/l10n_cr_einvoice
./scripts/backup_database.sh --encrypt
```

- [ ] Database backup completed successfully
- [ ] Filestore backup completed
- [ ] Certificates backup completed
- [ ] Backup integrity verified
- [ ] Backup size documented: __________ GB

### 2. Stop Services (T+5)

```bash
cd /opt/gms-odoo/l10n_cr_einvoice/docker
docker-compose down
```

- [ ] Odoo service stopped
- [ ] Nginx service stopped
- [ ] PostgreSQL service stopped gracefully
- [ ] All containers removed
- [ ] No orphaned processes running

### 3. Pull Latest Code (T+10)

```bash
cd /opt/gms-odoo/l10n_cr_einvoice
git fetch origin
git checkout main
git pull origin main
```

- [ ] Latest code pulled from repository
- [ ] Git status clean (no uncommitted changes)
- [ ] Module version confirmed: 19.0.1.8.0
- [ ] No merge conflicts
- [ ] All files intact

### 4. Update Configuration (T+12)

```bash
# Review and update .env if needed
nano docker/.env

# Verify configuration
cat docker/.env | grep -E "POSTGRES|HACIENDA|SMTP"
```

- [ ] Database credentials verified
- [ ] Hacienda API credentials verified
- [ ] SMTP settings verified
- [ ] SSL certificate paths verified
- [ ] Environment set to 'production'

### 5. Build Docker Images (T+15)

```bash
cd /opt/gms-odoo/l10n_cr_einvoice/docker
docker-compose build --no-cache
```

- [ ] Docker images built successfully
- [ ] No build errors
- [ ] Image size reasonable (<2GB)
- [ ] All dependencies installed

### 6. Start Database (T+20)

```bash
docker-compose up -d db
sleep 10
```

- [ ] PostgreSQL container started
- [ ] Database healthy (pg_isready)
- [ ] Connections accepting
- [ ] No errors in logs

### 7. Run Migrations (T+22)

```bash
docker-compose up -d odoo
sleep 30

# Update module
docker-compose exec odoo odoo \
  --update=l10n_cr_einvoice \
  --stop-after-init \
  --log-level=info
```

- [ ] Migrations executed successfully
- [ ] No migration errors
- [ ] Module updated to 19.0.1.8.0
- [ ] Database schema updated

### 8. Start All Services (T+25)

```bash
docker-compose up -d
```

- [ ] All containers started
- [ ] Odoo container healthy
- [ ] PostgreSQL container healthy
- [ ] Nginx container healthy
- [ ] Redis container healthy (if enabled)

### 9. Wait for Services (T+27)

```bash
# Wait for health checks
for i in {1..12}; do
    curl -f http://localhost/web/health && break
    echo "Waiting for services... ($i/12)"
    sleep 5
done
```

- [ ] Odoo responding to health checks
- [ ] Login page accessible
- [ ] No startup errors in logs

### 10. Run Smoke Tests (T+30)

```bash
python3 deployment/smoke_tests.py --url https://gms-cr.com
```

- [ ] All smoke tests passing
- [ ] HTTP health check: PASS
- [ ] Login page: PASS
- [ ] Database connection: PASS
- [ ] SSL certificate: PASS
- [ ] Response time: PASS

### 11. Functional Validation (T+35)

Test critical workflows:

```bash
# Test invoice creation and submission
docker-compose exec odoo odoo shell << 'EOF'
# Create test invoice
partner = env['res.partner'].search([('customer_rank', '>', 0)], limit=1)
invoice = env['account.move'].create({
    'partner_id': partner.id,
    'move_type': 'out_invoice',
    'invoice_line_ids': [(0, 0, {
        'name': 'Test Product',
        'quantity': 1,
        'price_unit': 1000,
    })]
})

# Sign and submit
invoice.action_post()
invoice.action_sign_einvoice()
invoice.action_submit_to_hacienda()

print(f"Test invoice: {invoice.name}")
print(f"Status: {invoice.einvoice_state}")
print(f"Signed: {invoice.einvoice_signed}")
EOF
```

- [ ] Invoice creation: PASS
- [ ] Invoice signing: PASS
- [ ] Hacienda submission: PASS
- [ ] Email delivery: PASS
- [ ] PDF generation: PASS

### 12. Monitor for Issues (T+40 to T+60)

```bash
# Monitor logs
docker-compose logs -f --tail=100 odoo

# Run health check
./scripts/health_check.sh
```

- [ ] No errors in Odoo logs
- [ ] No errors in Nginx logs
- [ ] No database errors
- [ ] CPU usage normal (<50%)
- [ ] Memory usage normal (<80%)
- [ ] Disk space adequate (>20% free)
- [ ] Response times acceptable (<2s)

## Post-Deployment Validation

### Verify Core Functionality

- [ ] User login successful
- [ ] Dashboard loads correctly
- [ ] Invoice list accessible
- [ ] Settings page accessible
- [ ] Reports generate successfully

### Verify E-Invoice Functionality

- [ ] Create invoice: PASS
- [ ] Sign invoice: PASS
- [ ] Submit to Hacienda: PASS
- [ ] Receive acceptance: PASS
- [ ] Generate PDF: PASS
- [ ] Send email: PASS
- [ ] Create credit note: PASS
- [ ] POS transaction: PASS (if applicable)

### Verify Integration

- [ ] Hacienda API connectivity: PASS
- [ ] SMTP email delivery: PASS
- [ ] Certificate loading: PASS
- [ ] Database queries: PASS
- [ ] Cache working: PASS (if Redis enabled)

## Success Criteria

All must be TRUE to consider deployment successful:

- [ ] All services running and healthy
- [ ] All smoke tests passing (100%)
- [ ] All functional tests passing (100%)
- [ ] No critical errors in logs
- [ ] Response time <2 seconds
- [ ] At least one successful invoice submission
- [ ] Email notifications working
- [ ] Monitoring dashboards showing green

## Rollback Decision Point

If any critical issues detected:

```bash
# Execute rollback
cd /opt/gms-odoo/l10n_cr_einvoice
./scripts/deploy_production.sh --rollback
```

Trigger rollback if:
- [ ] Any service fails to start
- [ ] Database migration fails
- [ ] Smoke tests fail
- [ ] Hacienda API not accessible
- [ ] Critical errors in logs
- [ ] Performance degradation >50%

## Communication

### Deployment Start
- [ ] Notify stakeholders: "Deployment started at HH:MM"
- [ ] Update status page (if applicable)

### Deployment Complete
- [ ] Notify stakeholders: "Deployment complete, all systems operational"
- [ ] Update status page: "All systems operational"
- [ ] Send summary email

### If Rollback Required
- [ ] Notify stakeholders immediately
- [ ] Explain issue and impact
- [ ] Provide timeline for resolution
- [ ] Update status page

## Monitoring (Next 24 Hours)

- [ ] Hour 1: Check every 15 minutes
- [ ] Hour 2-4: Check every 30 minutes
- [ ] Hour 4-8: Check hourly
- [ ] Hour 8-24: Check every 4 hours

Monitor:
- Service health
- Error logs
- Response times
- Invoice submission rate
- Email delivery rate
- User feedback

## Sign-Off

**Deployment Started**: _______________
**Deployment Completed**: _______________
**Duration**: _______________ minutes

**Technical Lead**: _________________ Date: _________
**Signature**: _________________

**Notes/Issues**:
