# VPS Setup Commands
## Run these on your VPS to prepare for GMS deployment

### Step 1: SSH into VPS

```bash
ssh root@168.231.71.94
```

### Step 2: Upload and Run Update Script

**From your local machine:**
```bash
cd /Users/papuman/Documents/My\ Projects/GMS/deployment
scp update-vps.sh root@168.231.71.94:/root/
```

**On VPS:**
```bash
chmod +x /root/update-vps.sh
bash /root/update-vps.sh
```

This will:
- ✅ Remove n8n
- ✅ Update all packages
- ✅ Upgrade Ubuntu to latest
- ✅ Update Docker and Docker Compose
- ✅ Clean up unused packages

**Expected output:**
```
✓ n8n removed
✓ Packages updated
✓ System upgraded
✓ Docker updated
✓ Docker Compose is up to date
```

### Step 3: Reboot VPS (Recommended)

```bash
reboot
```

Wait 1-2 minutes, then reconnect:
```bash
ssh root@168.231.71.94
```

### Step 4: Verify System

```bash
# Check OS version
lsb_release -a

# Check memory (should show ~8GB)
free -h

# Check Docker
docker --version
docker-compose --version

# Check disk space
df -h
```

**Expected:**
- Ubuntu 24.04 or newer
- ~8GB RAM available
- Docker 24.x or newer
- Docker Compose 2.x or newer

### Step 5: Ready to Deploy!

Now you can run the deployment:

```bash
cd /Users/papuman/Documents/My\ Projects/GMS/deployment
./deploy.sh
```
