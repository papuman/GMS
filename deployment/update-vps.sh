#!/bin/bash
# GMS VPS Update Script
# Run this on the VPS to update system and remove n8n

set -e

echo "========================================="
echo "  GMS VPS System Update"
echo "========================================="
echo ""

# Remove n8n
echo "Step 1: Removing n8n..."
if [ -d "/docker/n8n" ]; then
    cd /docker/n8n
    docker-compose down
    cd /
    rm -rf /docker/n8n
    echo "✓ n8n removed"
else
    echo "✓ n8n not found (already removed)"
fi

# Update package lists
echo ""
echo "Step 2: Updating package lists..."
apt-get update

# Upgrade packages
echo ""
echo "Step 3: Upgrading installed packages..."
apt-get upgrade -y

# Full distribution upgrade
echo ""
echo "Step 4: Performing distribution upgrade..."
apt-get dist-upgrade -y

# Remove unused packages
echo ""
echo "Step 5: Cleaning up unused packages..."
apt-get autoremove -y
apt-get autoclean

# Update Docker
echo ""
echo "Step 6: Updating Docker..."
apt-get install --only-upgrade docker-ce docker-ce-cli containerd.io -y

# Check Docker Compose version
echo ""
echo "Step 7: Checking Docker Compose..."
CURRENT_COMPOSE_VERSION=$(docker-compose --version | grep -oP '\d+\.\d+\.\d+')
LATEST_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -oP '"tag_name": "\K(.*)(?=")')

echo "Current Docker Compose: v$CURRENT_COMPOSE_VERSION"
echo "Latest Docker Compose: $LATEST_COMPOSE_VERSION"

if [ "v$CURRENT_COMPOSE_VERSION" != "$LATEST_COMPOSE_VERSION" ]; then
    echo "Updating Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/$LATEST_COMPOSE_VERSION/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "✓ Docker Compose updated to $LATEST_COMPOSE_VERSION"
else
    echo "✓ Docker Compose is already up to date"
fi

# Check system info
echo ""
echo "========================================="
echo "  System Information"
echo "========================================="
echo "OS Version:"
lsb_release -a
echo ""
echo "Kernel Version:"
uname -r
echo ""
echo "Docker Version:"
docker --version
echo ""
echo "Docker Compose Version:"
docker-compose --version
echo ""
echo "Available Memory:"
free -h
echo ""
echo "Disk Space:"
df -h /
echo ""
echo "========================================="
echo "  Update Complete!"
echo "========================================="
echo ""
echo "Reboot recommended: reboot"
