# Quick Start Guide
## Deploy in 30 Minutes

Fast-track deployment guide for experienced administrators.

## Prerequisites Checklist

```bash
# Check all prerequisites
[ -x "$(command -v docker)" ] && echo "✓ Docker" || echo "✗ Docker"
[ -x "$(command -v docker-compose)" ] && echo "✓ Docker Compose" || echo "✗ Docker Compose"
[ -f ".env" ] && echo "✓ .env file" || echo "✗ .env file"
[ -f "docker/ssl/fullchain.pem" ] && echo "✓ SSL cert" || echo "✗ SSL cert"
[ -f "docker/certificates/certificate.p12" ] && echo "✓ Hacienda cert" || echo "✗ Hacienda cert"
```

## 30-Minute Deployment

### Minute 0-5: Initial Setup

```bash
# Clone and configure
git clone https://github.com/your-org/gms-odoo.git
cd gms-odoo/l10n_cr_einvoice/docker

# Configure environment
cp .env.example .env
nano .env  # Edit: DB password, Hacienda creds, SMTP

# Setup SSL
mkdir -p ssl certificates
# Copy your SSL certificates to ssl/
# Copy Hacienda certificate to certificates/
```

### Minute 5-10: Build Images

```bash
# Build Docker images
docker-compose build

# Verify
docker images | grep gms
```

### Minute 10-15: Start Services

```bash
# Start all services
docker-compose up -d

# Watch logs
docker-compose logs -f
# Press Ctrl+C when you see "odoo.http: HTTP service (werkzeug) running"
```

### Minute 15-20: Initialize Odoo

```bash
# Install module
docker-compose exec odoo odoo \
  -d odoo \
  -i l10n_cr_einvoice \
  --stop-after-init \
  --without-demo=all

# Restart
docker-compose restart odoo
sleep 10
```

### Minute 20-25: Configure System

```bash
# Access Odoo
open https://your-domain.com

# Login with admin/admin (change immediately!)

# Quick config via shell:
docker-compose exec odoo odoo shell << 'EOF'
# Set company info
company = env['res.company'].browse(1)
company.write({
    'name': 'Your Company Name',
    'vat': '1234567890',  # Your Cédula Jurídica
    'email': 'info@yourcompany.com',
    'phone': '+506 2222-3333',
})

# Upload certificate (do via UI or copy file)
print("Company configured")
EOF
```

### Minute 25-30: Test & Validate

```bash
# Run smoke tests
python3 deployment/smoke_tests.py

# Create test invoice
docker-compose exec odoo odoo shell << 'EOF'
partner = env['res.partner'].create({
    'name': 'Test Customer',
    'vat': '123456789',
    'einvoice_id_type': '01',  # Física
})

invoice = env['account.move'].create({
    'partner_id': partner.id,
    'move_type': 'out_invoice',
    'invoice_line_ids': [(0, 0, {
        'name': 'Test Product',
        'quantity': 1,
        'price_unit': 1000,
    })]
})

invoice.action_post()
invoice.action_sign_einvoice()
invoice.action_submit_to_hacienda()

print(f"Invoice: {invoice.name}")
print(f"Status: {invoice.einvoice_state}")
EOF
```

## Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f odoo

# Restart Odoo
docker-compose restart odoo

# Backup database
./scripts/backup_database.sh

# Restore database
./scripts/restore_database.sh backup_file.dump

# Health check
./scripts/health_check.sh

# Deploy update
./scripts/deploy_production.sh
```

## Troubleshooting

### Odoo won't start
```bash
docker-compose logs odoo | tail -50
# Check database connection in .env
```

### Can't access website
```bash
# Check firewall
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check Nginx
docker-compose logs nginx
```

### Database connection failed
```bash
# Verify database is running
docker-compose exec db pg_isready -U odoo

# Test connection
docker-compose exec db psql -U odoo -c "SELECT 1;"
```

### SSL certificate error
```bash
# Check certificate
openssl x509 -in docker/ssl/fullchain.pem -noout -dates

# Verify Nginx config
docker-compose exec nginx nginx -t
```

## Next Steps

1. **Security**
   - Change admin password
   - Configure firewall
   - Setup backups
   - Enable monitoring

2. **Configuration**
   - Upload Hacienda production certificate
   - Configure email templates
   - Setup user accounts
   - Configure POS (if needed)

3. **Testing**
   - Create test invoices
   - Test Hacienda submission
   - Verify email delivery
   - Test all workflows

4. **Go Live**
   - Complete pre-deployment checklist
   - Follow deployment checklist
   - Monitor for 24 hours
   - Train users

## Support

**Documentation**: `/docs/ADMIN_GUIDE.md`
**Troubleshooting**: `/docs/TROUBLESHOOTING.md`
**Email**: support@gms-cr.com
