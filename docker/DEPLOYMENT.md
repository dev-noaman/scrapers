# Deployment Guide for Ubuntu VPS

This guide covers deploying the dockerized API-php and API-node scrapers to an Ubuntu VPS.

## Prerequisites

### On Your Ubuntu VPS

1. **Docker Installation**:
```bash
# Update package index
sudo apt-get update

# Install required packages
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify installation
sudo docker --version
sudo docker compose version
```

2. **Optional: Add your user to docker group** (to run docker without sudo):
```bash
sudo usermod -aG docker $USER
newgrp docker
```

## Method 1: Transfer Files via SCP (Recommended)

### Step 1: Prepare Files on Local Machine

Create a compressed archive of each project:

```bash
# On Windows (PowerShell)
cd d:\Copy\Single_window_Adel

# Compress API-php
Compress-Archive -Path API-php\* -DestinationPath api-php.zip

# Compress API-node
Compress-Archive -Path API-node\* -DestinationPath api-node.zip
```

### Step 2: Transfer to VPS

```bash
# Replace with your VPS details
scp api-php.zip your_username@your_vps_ip:/home/your_username/
scp api-node.zip your_username@your_vps_ip:/home/your_username/
```

### Step 3: Extract on VPS

```bash
# SSH into your VPS
ssh your_username@your_vps_ip

# Create project directory
mkdir -p ~/scrapers
cd ~/scrapers

# Extract archives
unzip ~/api-php.zip -d api-php
unzip ~/api-node.zip -d api-node

# Clean up
rm ~/api-php.zip ~/api-node.zip
```

## Method 2: Transfer via Git (Alternative)

Using the GitHub repository:

```bash
# On VPS
cd ~
git clone https://github.com/dev-noaman/scrapers.git
cd scrapers
```

## Method 3: Direct File Transfer via SFTP

Use an SFTP client like FileZilla, WinSCP, or Cyberduck:
1. Connect to your VPS using SFTP
2. Upload the `API-php` and `API-node` folders to `/home/your_username/scrapers/`

## Building and Running the Containers

### API-php (Python + Playwright)

```bash
cd ~/scrapers/API-php

# Build the Docker image
docker compose build

# Start the container
docker compose up -d

# Check logs
docker compose logs -f

# Test the API
curl "http://localhost:8080/scraper.php?code=013001"
```

### API-node (Node.js + Puppeteer)

> [!NOTE]
> The Node scraper now runs as a persistent service for better performance.

```bash
cd ~/scrapers/API-node

# Build the Docker image
docker compose build

# Start the container
docker compose up -d

# Check logs (You will see "Scraper server running on http://0.0.0.0:3000")
docker compose logs -f

# Test the API
curl "http://localhost:8081/api.php?code=013001"
```

## Accessing from External Network

### Option 1: Direct Port Access

If your VPS firewall allows, you can access directly:
- API-php: `http://your_vps_ip:8080/scraper.php?code=013001`
- API-node: `http://your_vps_ip:8081/api.php?code=013001`

**Configure firewall**:
```bash
# UFW (Ubuntu Firewall)
sudo ufw allow 8080/tcp
sudo ufw allow 8081/tcp
sudo ufw reload
```

### Option 2: Nginx Reverse Proxy (Recommended for Production)

Install Nginx on the host:
```bash
sudo apt-get install nginx
```

Create configuration file `/etc/nginx/sites-available/scrapers`:
```nginx
server {
    listen 80;
    server_name noaman.cloud www.noaman.cloud;

    location /api-php/ {
        proxy_pass http://localhost:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300;
    }

    location /api-node/ {
        proxy_pass http://localhost:8081/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/scrapers /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**Configure DNS**: Point your domain `noaman.cloud` to your VPS IP address.

Now access via:
- API-php: `http://noaman.cloud/api-php/scraper.php?code=013001`
- API-node: `http://noaman.cloud/api-node/api.php?code=013001`

**Optional: Enable HTTPS with Let's Encrypt**:
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d noaman.cloud -d www.noaman.cloud
```

After SSL is enabled:
- API-php: `https://noaman.cloud/api-php/scraper.php?code=013001`
- API-node: `https://noaman.cloud/api-node/api.php?code=013001`

## Managing Containers

### View Running Containers
```bash
docker ps
```

### Stop Containers
```bash
cd ~/scrapers/API-php
docker compose down

cd ~/scrapers/API-node
docker compose down
```

### Restart Containers
```bash
docker compose restart
```

### View Logs
```bash
docker compose logs -f
docker compose logs --tail=100  # Last 100 lines
```

### Update Code
```bash
# After updating code files
docker compose restart  # If volumes are mounted
# OR
docker compose down
docker compose build
docker compose up -d
```

## Monitoring and Maintenance

### Check Container Health
```bash
docker ps  # Look for "healthy" status
```

### Check Resource Usage
```bash
docker stats
```

### Clean Up Old Images
```bash
docker system prune -a
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker compose logs

# Check if port is already in use
sudo netstat -tulpn | grep 8080
sudo netstat -tulpn | grep 8081
```

### Browser/Chromium Issues
The containers include all necessary dependencies for headless browsers. If you encounter issues:
```bash
# Rebuild with no cache
docker compose build --no-cache
```

### Permission Errors
```bash
# Ensure proper ownership
sudo chown -R $USER:$USER ~/scrapers
```

### Out of Memory
Increase Docker's memory limit or VPS resources. The scrapers need at least 2GB RAM.

### Slow Performance
- Ensure your VPS has adequate resources (2GB+ RAM recommended)
- Check network connectivity to the target website
- Monitor with `docker stats`

## Security Recommendations

1. **Use Environment Variables** for sensitive data
2. **Enable HTTPS** with Let's Encrypt if using a domain
3. **Restrict Access** using firewall rules or API authentication
4. **Regular Updates**: Keep Docker and system packages updated
5. **Monitor Logs**: Set up log rotation and monitoring

## Auto-Start on Boot

Containers with `restart: unless-stopped` will automatically start on system reboot.

To ensure Docker starts on boot:
```bash
sudo systemctl enable docker
```

## Production Deployment Checklist

- [ ] Docker and Docker Compose installed on VPS
- [ ] Files transferred and extracted
- [ ] Containers built successfully
- [ ] Containers running and healthy
- [ ] APIs accessible and returning correct responses
- [ ] Firewall configured
- [ ] (Optional) Reverse proxy configured
- [ ] (Optional) SSL/HTTPS configured
- [ ] Monitoring set up
- [ ] Backup strategy in place

## Quick Reference Commands

```bash
# Build and start
docker compose up -d --build

# Stop and remove
docker compose down

# View logs
docker compose logs -f

# Restart
docker compose restart

# Check status
docker compose ps

# Execute command in container
docker compose exec api-php bash
docker compose exec api-node bash
```

## Support

For issues specific to:
- **Docker**: Check Docker documentation
- **Scraper Logic**: Review the scraper code and logs
- **Network Issues**: Check VPS firewall and network configuration
