# Quick Start Guide - Docker Deployment

This guide helps you quickly get both scrapers running with Docker.

## Local Testing (Windows)

### Prerequisites
- Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
- Ensure Docker Desktop is running

### Test API-php

```powershell
# Navigate to API-php directory
cd d:\Copy\Single_window_Adel\API-php

# Build and start
docker compose up -d --build

# Wait for container to be healthy (30-60 seconds)
docker compose ps

# Test the API
curl "http://localhost:8080/scraper.php?code=013001"

# View logs
docker compose logs -f

# Stop when done
docker compose down
```

### Test API-node

```powershell
# Navigate to API-node directory
cd d:\Copy\Single_window_Adel\API-node

# Build and start
docker compose up -d --build

# Wait for container to be healthy (30-60 seconds)
docker compose ps

# Test the API
curl "http://localhost:8081/api.php?code=013001"

# View logs
docker compose logs -f

# Stop when done
docker compose down
```

## VPS Deployment (Ubuntu)

### Step 1: Install Docker on VPS

```bash
# SSH into your VPS
ssh your_username@your_vps_ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker compose version
```

### Step 2: Transfer Files

**Option A: Using SCP (from Windows)**
```powershell
# Create archives
cd d:\Copy\Single_window_Adel
Compress-Archive -Path API-php\* -DestinationPath api-php.zip
Compress-Archive -Path API-node\* -DestinationPath api-node.zip

# Transfer to VPS
scp api-php.zip your_username@your_vps_ip:~/
scp api-node.zip your_username@your_vps_ip:~/
```

**On VPS:**
```bash
# Extract
mkdir -p ~/scrapers
unzip ~/api-php.zip -d ~/scrapers/api-php
unzip ~/api-node.zip -d ~/scrapers/api-node
rm ~/api-php.zip ~/api-node.zip
```

**Option B: Using Git (Recommended)**
```bash
# On VPS
cd ~
git clone https://github.com/dev-noaman/scrapers.git
cd scrapers
```

### Step 3: Build and Run on VPS

```bash
# API-php
cd ~/scrapers/API-php
docker compose up -d --build

# API-node
cd ~/scrapers/API-node
docker compose up -d --build

# Check status
docker ps

# Test locally on VPS
curl "http://localhost:8080/scraper.php?code=013001"
curl "http://localhost:8081/api.php?code=013001"
```

### Step 4: Configure Firewall

```bash
# Allow ports
sudo ufw allow 8080/tcp
sudo ufw allow 8081/tcp
sudo ufw reload
```

### Step 5: Test from External

```bash
# From your local machine (replace with your VPS IP)
curl "http://your_vps_ip:8080/scraper.php?code=013001"
curl "http://your_vps_ip:8081/api.php?code=013001"

# Or if using domain noaman.cloud with reverse proxy:
curl "http://noaman.cloud/api-php/scraper.php?code=013001"
curl "http://noaman.cloud/api-node/api.php?code=013001"
```

## Common Commands

### View Logs
```bash
docker compose logs -f          # Follow logs
docker compose logs --tail=50   # Last 50 lines
```

### Restart Containers
```bash
docker compose restart
```

### Stop Containers
```bash
docker compose down
```

### Update Code
```bash
# If you updated the code files
docker compose restart  # If using volume mounts
# OR
docker compose down
docker compose build
docker compose up -d
```

### Check Resource Usage
```bash
docker stats
```

### Clean Up
```bash
docker system prune -a  # Remove unused images
```

## Troubleshooting

### Container Exits Immediately
```bash
docker compose logs  # Check error messages
```

### Port Already in Use
```bash
# Change ports in docker-compose.yml
ports:
  - "8082:80"  # Use different port
```

### Out of Memory
- Ensure VPS has at least 2GB RAM
- Check with `docker stats`

### Can't Access from External Network
- Check firewall: `sudo ufw status`
- Verify container is running: `docker ps`
- Check VPS provider's security groups/firewall

## Production Recommendations

1. **Use Nginx Reverse Proxy** - See DEPLOYMENT.md
2. **Enable HTTPS** - Use Let's Encrypt
3. **Set Up Monitoring** - Use Docker health checks
4. **Regular Backups** - Backup your code and configurations
5. **Update Regularly** - Keep Docker and images updated

## Support

For detailed instructions, see:
- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment guide
- [API-php/README.md](API-php/README.md) - API-php documentation
- [API-node/README-DOCKER.md](API-node/README-DOCKER.md) - API-node documentation
