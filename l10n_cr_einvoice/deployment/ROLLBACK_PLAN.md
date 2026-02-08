# Rollback Plan
## Emergency Recovery Procedure

Execute if deployment fails or critical issues detected.

## When to Rollback

### Immediate Rollback Triggers (No Discussion)

1. **Service Failure**
   - Odoo won't start after 3 attempts
   - Database corruption detected
   - Nginx fails to start

2. **Data Loss Risk**
   - Migration errors affecting data integrity
   - Backup restoration fails validation
   - Database rollback transactions failing

3. **Critical Business Impact**
   - Cannot create invoices
   - Cannot submit to Hacienda (all attempts fail)
   - Email delivery completely broken
   - POS completely non-functional

### Consider Rollback (Team Decision)

1. **Performance Issues**
   - Response time >10 seconds (>5x normal)
   - CPU usage >90% sustained
   - Memory usage >95%
   - Database queries timing out

2. **Partial Functionality Loss**
   - Some features broken but workarounds available
   - Non-critical integration failures
   - Cosmetic issues affecting usability

3. **High Error Rate**
   - >10% invoice submission failures
   - >20% email delivery failures
   - Increasing error rate over time

## Rollback Procedure

### Quick Rollback (Using Script)

**Duration: ~15 minutes**

```bash
cd /opt/gms-odoo/l10n_cr_einvoice
./scripts/deploy_production.sh --rollback
```

This automated rollback:
1. Stops all services
2. Restores latest pre-deployment backup
3. Restarts services with previous version
4. Validates restoration

### Manual Rollback

If automated rollback fails, follow manual steps:

#### Step 1: Stop Services (1 minute)

```bash
cd /opt/gms-odoo/l10n_cr_einvoice/docker
docker-compose down
```

#### Step 2: Identify Latest Backup (1 minute)

```bash
ls -lt docker/backups/pre_deploy_*.dump | head -1
```

Record backup file: ______________________________

#### Step 3: Restore Database (5 minutes)

```bash
# Start database only
docker-compose up -d db
sleep 10

# Drop current database
docker-compose exec db dropdb -U odoo --if-exists odoo

# Create fresh database
docker-compose exec db createdb -U odoo odoo

# Restore backup
cat docker/backups/pre_deploy_YYYYMMDD_HHMMSS.dump | \
  docker-compose exec -T db pg_restore \
    -U odoo \
    -d odoo \
    --no-owner \
    --no-acl \
    -v
```

#### Step 4: Restore Filestore (2 minutes)

```bash
# If filestore backup exists
if [ -f docker/backups/pre_deploy_YYYYMMDD_HHMMSS_filestore.tar.gz ]; then
    docker-compose exec -T odoo rm -rf /var/lib/odoo/filestore/*
    cat docker/backups/pre_deploy_YYYYMMDD_HHMMSS_filestore.tar.gz | \
      docker-compose exec -T odoo tar xzf - -C /
fi
```

#### Step 5: Revert Code (1 minute)

```bash
# Get previous version tag
git log --oneline -5

# Checkout previous version
git checkout <previous-version-tag>
```

#### Step 6: Rebuild and Start (5 minutes)

```bash
# Rebuild with old code
docker-compose build

# Start all services
docker-compose up -d

# Wait for services
sleep 60
```

#### Step 7: Validate (5 minutes)

```bash
# Run health check
./scripts/health_check.sh

# Run smoke tests
python3 deployment/smoke_tests.py
```

## Validation After Rollback

### Critical Checks

- [ ] All services running
- [ ] Login works
- [ ] Can view existing invoices
- [ ] Can create test invoice
- [ ] Database queries work
- [ ] No errors in logs

### Data Integrity

```bash
# Verify record counts match pre-deployment
docker-compose exec db psql -U odoo -d odoo -c "
SELECT
    (SELECT COUNT(*) FROM account_move) as invoices,
    (SELECT COUNT(*) FROM res_partner) as partners,
    (SELECT COUNT(*) FROM einvoice_document) as einvoices;
"
```

Compare with pre-deployment counts.

- [ ] Invoice count matches: _______
- [ ] Partner count matches: _______
- [ ] E-invoice count matches: _______

### Functionality Test

```bash
# Test critical workflow
docker-compose exec odoo odoo shell << 'EOF'
# Try to fetch an invoice
invoice = env['account.move'].search([('move_type', '=', 'out_invoice')], limit=1)
print(f"Retrieved invoice: {invoice.name}")
print(f"Partner: {invoice.partner_id.name}")
print(f"Amount: {invoice.amount_total}")
EOF
```

- [ ] Can retrieve invoices: PASS
- [ ] Data intact: PASS

## Communication During Rollback

### Immediate Notification (Within 5 minutes)

**To**: All Stakeholders
**Subject**: URGENT: Production Deployment Rollback in Progress

```
Team,

We are rolling back the production deployment due to [REASON].

Impact: [DESCRIBE IMPACT]
ETA for recovery: [TIME]
Current status: [STATUS]

We will update every 15 minutes.

Technical Lead
[NAME]
```

### Progress Updates (Every 15 minutes)

```
Rollback Update [HH:MM]:

Status: [In Progress/Complete]
Step: [Current Step]
ETA: [Estimated Time]
Issues: [Any issues encountered]

Next update: [TIME]
```

### Completion Notification

**Subject**: Production Rollback Complete - System Restored

```
Team,

Rollback completed successfully.

System Status: Operational
Services: All services running normally
Data: Validated, no data loss
Functionality: All critical features working

What happened: [Brief explanation]
Root cause: [If known]
Next steps: [Action items]

Normal operations resumed.

Technical Lead
[NAME]
```

## Post-Rollback Actions

### Immediate (0-4 hours)

- [ ] Verify all services stable
- [ ] Monitor for errors
- [ ] Collect logs from failed deployment
- [ ] Document issues encountered
- [ ] Notify users system is operational

### Short-term (4-24 hours)

- [ ] Analyze root cause
- [ ] Review deployment logs
- [ ] Identify what went wrong
- [ ] Plan corrective actions
- [ ] Update deployment procedure

### Medium-term (1-7 days)

- [ ] Fix identified issues
- [ ] Test fixes in staging
- [ ] Update deployment scripts
- [ ] Conduct deployment retrospective
- [ ] Schedule new deployment

## Root Cause Analysis Template

```markdown
## Deployment Rollback Post-Mortem

**Date**: YYYY-MM-DD
**Duration of Incident**: HH:MM to HH:MM
**Services Affected**: [List]

### What Happened
[Detailed timeline of events]

### Root Cause
[What actually caused the failure]

### Impact
- Users affected: [Number/All]
- Duration: [Minutes]
- Data loss: [Yes/No]
- Revenue impact: [If applicable]

### What Went Well
- [Things that worked during rollback]

### What Went Wrong
- [Issues encountered]

### Action Items
1. [ ] [Action] - Owner: [Name] - Due: [Date]
2. [ ] [Action] - Owner: [Name] - Due: [Date]

### Lessons Learned
- [Key takeaways]

### Prevention
- [How to prevent in future]
```

## Rollback Testing

Test rollback procedure quarterly:

```bash
# In staging environment
cd /opt/gms-odoo-staging/l10n_cr_einvoice

# Create test backup
./scripts/backup_database.sh

# Simulate deployment
./scripts/deploy_production.sh

# Practice rollback
./scripts/deploy_production.sh --rollback

# Validate
./scripts/health_check.sh
python3 deployment/smoke_tests.py
```

- [ ] Q1 rollback drill completed: _______
- [ ] Q2 rollback drill completed: _______
- [ ] Q3 rollback drill completed: _______
- [ ] Q4 rollback drill completed: _______

## Emergency Contacts

**Technical Lead**: [Name] - [Phone] - [Email]
**DevOps**: [Name] - [Phone] - [Email]
**Database Admin**: [Name] - [Phone] - [Email]
**Project Manager**: [Name] - [Phone] - [Email]

**Escalation Path**:
1. Technical Lead (0-30 min)
2. DevOps Manager (30-60 min)
3. CTO (>60 min)

## Recovery Time Objective

**Target RTO**: 15 minutes
**Maximum RTO**: 30 minutes

If rollback takes >30 minutes, escalate immediately.
