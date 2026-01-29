# Odoo Docker Setup - GMS Validation

## ✅ What's Running

Your Odoo validation environment is running in Docker containers:

- **Odoo 19.0:** Running on http://localhost:8070
- **PostgreSQL 13:** Database backend
- **Network:** Isolated Docker network `gms_odoo-network`
- **Volumes:** Data persisted in Docker volumes

## 🚀 Access Odoo

**Open your browser:** http://localhost:8070

You should see the Odoo database manager screen.

### First Login Setup:
1. **Master Password:** `admin123` (from odoo.conf)
2. **Database Name:** `gms_validation` (will be created automatically)
3. **Email:** your email
4. **Password:** choose admin password
5. **Language:** English
6. **Country:** Costa Rica ⭐
7. Click "Create Database"

## 📦 Docker Commands

### Start/Stop Containers
```bash
# Start containers
docker-compose up -d

# Stop containers
docker-compose down

# Stop and remove all data (full reset)
docker-compose down -v

# View logs
docker-compose logs -f odoo
docker-compose logs -f db

# Restart Odoo only
docker-compose restart odoo
```

### Container Status
```bash
# Check running containers
docker-compose ps

# Access Odoo shell
docker exec -it gms_odoo bash

# Access PostgreSQL
docker exec -it gms_postgres psql -U odoo -d gms_validation
```

## 📂 File Structure

```
/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/
├── docker-compose.yml    # Docker orchestration
├── odoo.conf             # Odoo configuration
├── odoo/                 # Odoo source code
│   └── addons/           # Mounted to /mnt/extra-addons in container
└── docs/                 # Validation documentation
```

## 🔧 Configuration

### Ports
- **Odoo Web:** 8070 → 8069 (container)
- **PostgreSQL:** 5432 → 5432 (container)

### Database Credentials
- **Host:** db (internal), localhost (from host)
- **Port:** 5432
- **Database:** gms_validation
- **User:** odoo
- **Password:** odoo

### Admin Password
- **Master Password:** admin123 (for database management)

## 🛠️ Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs

# Remove and recreate
docker-compose down
docker-compose up -d
```

### Port already in use
Edit `docker-compose.yml` and change port 8070 to another port:
```yaml
ports:
  - "8071:8069"  # Use 8071 instead
```

### Reset everything
```bash
# Stop and remove all data
docker-compose down -v

# Start fresh
docker-compose up -d
```

### Can't access localhost:8070
- Check Docker Desktop is running
- Check containers are up: `docker-compose ps`
- Check firewall isn't blocking port 8070

## 📊 Data Persistence

Your data is stored in Docker volumes:
- `gms_odoo-db-data` - PostgreSQL database
- `gms_odoo-web-data` - Odoo filestore and sessions

**These persist even when you stop containers.**

To completely wipe data:
```bash
docker-compose down -v
```

## ⚡ Next Steps

1. ✅ **Access Odoo:** http://localhost:8070
2. ✅ **Create Database** with Costa Rica localization
3. ✅ **Install Modules:** Accounting, Sales, POS, CRM, Website, Calendar, Stock, Loyalty, HR
4. ✅ **Start Validation:** Follow docs/validation-plan.md

---

**Your Docker environment is ready for GMS validation! 🏋️**
