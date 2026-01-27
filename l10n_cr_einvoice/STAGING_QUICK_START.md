# Staging Environment - Quick Start Guide

**Version:** 19.0.1.8.0 | **Environment:** Local Docker Staging | **Time:** 30 minutes

---

## Prerequisites

- Docker Desktop installed and running
- 10GB free disk space
- Ports available: 8070, 8080, 5433, 9091, 3001
- Terminal access

---

## 1. Deploy Staging (10 minutes)

```bash
cd /Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/l10n_cr_einvoice
./scripts/deploy_staging.sh
```

**What happens:**
- Checks Docker and system requirements
- Builds Docker images
- Starts 6 services (Odoo, PostgreSQL, Redis, Nginx, Prometheus, Grafana)
- Initializes database
- Installs l10n_cr_einvoice module
- Runs smoke tests

**Expected output:**
```
==========================================================================
  Staging Environment Deployed Successfully!
==========================================================================

Access Information:
  Odoo Web Interface:    http://localhost:8070
  Grafana Dashboard:     http://localhost:3001

Credentials:
  Odoo Admin:            admin
  Odoo Password:         StagingAdmin2024!SecurePass
```

---

## 2. Verify Deployment (2 minutes)

```bash
python3 deployment/staging_tests.py
```

**Expected:** 11/11 tests passing (100%)

---

## 3. Access Odoo (1 minute)

1. Open browser: http://localhost:8070
2. Login:
   - Username: `admin`
   - Password: `StagingAdmin2024!SecurePass`
3. Activate Developer Mode: Settings > Activate developer mode

---

## 4. Populate Test Data (3 minutes)

```bash
./scripts/setup_staging_data.sh
```

**Creates:**
- 8 test customers (all ID types)
- 20 test products
- 10 sample invoices

---

## 5. Run Integration Tests (5 minutes)

```bash
python3 tests/test_staging_integration.py
```

**Expected:** All 8 test suites passing

---

## 6. First Invoice Test (5 minutes)

### Manual Test

1. Go to **Accounting** > **Customers** > **Invoices**
2. Click **Create**
3. Select customer: "Juan Pérez Rodríguez"
4. Add line: "Membresía Mensual" (qty: 1)
5. Click **Confirm**
6. Verify invoice posted successfully

### Expected Result
- Invoice created with number
- Status: Posted
- Customer ID and tax information populated
- Ready for e-invoice generation (requires certificate)

---

## Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Odoo | http://localhost:8070 | admin / StagingAdmin2024!SecurePass |
| Nginx | http://localhost:8080 | - |
| Grafana | http://localhost:3001 | admin / StagingGrafana2024! |
| Prometheus | http://localhost:9091 | - |

---

## Common Commands

### View Logs
```bash
docker-compose -f docker/docker-compose.staging.yml logs -f odoo-staging
```

### Stop Staging
```bash
docker-compose -f docker/docker-compose.staging.yml stop
```

### Start Staging (After Stop)
```bash
docker-compose -f docker/docker-compose.staging.yml start
```

### Restart Services
```bash
docker-compose -f docker/docker-compose.staging.yml restart odoo-staging
```

### Clean Up (Remove Everything)
```bash
./scripts/cleanup_staging.sh --remove-data
```

---

## Next Steps - Full Configuration

### Configure Hacienda Sandbox

1. Edit: `docker/.env.staging`
2. Update:
   ```
   HACIENDA_SANDBOX_USERNAME=your_username@sandbox.comprobanteselectronicos.go.cr
   HACIENDA_SANDBOX_PASSWORD=your_password
   ```
3. Restart: `docker-compose -f docker/docker-compose.staging.yml restart odoo-staging`

### Upload Test Certificate

1. Go to Odoo: Settings > General Settings
2. Scroll to "Costa Rica E-Invoicing"
3. Upload .p12 certificate
4. Enter certificate password
5. Save

### Configure SMTP (Mailtrap)

1. Sign up: https://mailtrap.io (free)
2. Get credentials
3. Edit: `docker/.env.staging`
4. Update SMTP settings
5. Restart Odoo

---

## User Testing Scenarios

Follow detailed scenarios in: `deployment/STAGING_USER_GUIDE.md`

**7 Test Scenarios:**
1. Create and submit basic invoice (10 steps)
2. Invoice with discounts
3. Credit note creation
4. POS transaction
5. Bulk operations
6. Error handling
7. Analytics and reporting

---

## Troubleshooting

### Cannot Access Odoo
```bash
# Check if services are running
docker-compose -f docker/docker-compose.staging.yml ps

# Check Odoo logs
docker-compose -f docker/docker-compose.staging.yml logs odoo-staging

# Restart Odoo
docker-compose -f docker/docker-compose.staging.yml restart odoo-staging
```

### Port Already in Use
Edit `docker/.env.staging` and change port numbers, then redeploy.

### Out of Memory
Increase Docker Desktop memory: Docker Desktop > Settings > Resources > Memory (4GB+)

---

## Complete Documentation

- **Deployment Report:** `deployment/STAGING_DEPLOYMENT_COMPLETE.md`
- **Validation Template:** `deployment/STAGING_VALIDATION.md`
- **User Guide:** `deployment/STAGING_USER_GUIDE.md`
- **Main Documentation:** `deployment/README.md`

---

## Support

For issues or questions:
1. Check logs: `docker-compose -f docker/docker-compose.staging.yml logs`
2. Review troubleshooting: `deployment/STAGING_USER_GUIDE.md#troubleshooting`
3. Check deployment report: `deployment/STAGING_DEPLOYMENT_COMPLETE.md`

---

**Ready to deploy?** Run: `./scripts/deploy_staging.sh`
