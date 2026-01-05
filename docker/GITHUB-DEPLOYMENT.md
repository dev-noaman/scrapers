# GitHub Deployment Summary

## Repository Information
- **GitHub URL**: https://github.com/dev-noaman/scrapers
- **Domain**: noaman.cloud
- **Live URLs**:
  - API-php: https://noaman.cloud/api-php/scraper.php?code=013001
  - API-node: https://noaman.cloud/api-node/api.php?code=013001

## Files Ready for GitHub

All Docker configuration files and documentation are ready to be committed to GitHub:

### Root Files
- ✅ `README.md` - Main repository documentation
- ✅ `DEPLOYMENT.md` - Comprehensive VPS deployment guide
- ✅ `QUICKSTART.md` - Quick start guide
- ✅ `.gitignore` - Git ignore rules

### API-php Directory
- ✅ `Dockerfile` - Docker image configuration
- ✅ `docker-compose.yml` - Docker Compose setup
- ✅ `nginx.conf` - Nginx web server config
- ✅ `docker-entrypoint.sh` - Container startup script
- ✅ `.dockerignore` - Docker build ignore rules
- ✅ `README.md` - API-php documentation
- ✅ `scraper.py` - Python scraper
- ✅ `scraper.php` - PHP wrapper
- ✅ `requirements.txt` - Python dependencies

### API-node Directory
- ✅ `Dockerfile` - Docker image configuration
- ✅ `docker-compose.yml` - Docker Compose setup
- ✅ `nginx.conf` - Nginx web server config
- ✅ `docker-entrypoint.sh` - Container startup script
- ✅ `.dockerignore` - Docker build ignore rules
- ✅ `README-DOCKER.md` - API-node Docker documentation
- ✅ `scraper.js` - Node.js scraper
- ✅ `api.php` - PHP API endpoint
- ✅ `package.json` - Node.js dependencies

## Git Commands to Push to GitHub

```bash
# Navigate to project directory
cd d:\Copy\Single_window_Adel

# Initialize git (if not already done)
git init

# Add remote repository
git remote add origin https://github.com/dev-noaman/scrapers.git

# Add all files
git add .

# Commit
git commit -m "Initial commit: Docker-ready scrapers with deployment configs"

# Push to GitHub
git push -u origin main
```

## VPS Deployment Steps (After GitHub Push)

### 1. SSH into VPS
```bash
ssh your_username@your_vps_ip
```

### 2. Install Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install -y docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
```

### 3. Clone Repository
```bash
cd ~
git clone https://github.com/dev-noaman/scrapers.git
cd scrapers
```

### 3.1. Upload Credentials (IMPORTANT)
Since `google-credentials.json` is a secret, it is **not** included in the git repository. You must upload it manually to the VPS.

**Upload from your local machine:**
```bash
# Run this on your LOCAL machine in the docker-scraper folder
scp drive/google-credentials.json your_username@your_vps_ip:~/scrapers/docker-scraper/drive/
```

**Or create it manually on the VPS:**
```bash
nano ~/scrapers/docker-scraper/drive/google-credentials.json
# Paste your JSON content here
```

### 4. Build and Run Containers (New Root Configuration)
We now use a single root `docker-compose.yml` to orchestrate everything.

```bash
# Build and start all services (Portal + Scraper)
docker-compose up -d --build
```

### 5. Run Scrapers
The scraper container (`single_window_scraper`) stays running in the background. You can execute scripts inside it:

```bash
# List all codes
docker-compose exec scraper python scrape_codes.py

# Scrape Arabic Details
docker-compose exec scraper python scrape-AR.py

# Scrape English Details
docker-compose exec scraper python scrape-EN.py
```

### 6. Configure Nginx (Optional)
If you are running the `portal` service on port 8080, you can configure your main VPS Nginx to reverse proxy to it:

```nginx
server {
    listen 80;
    server_name noaman.cloud www.noaman.cloud;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 7. Configure DNS
Point `noaman.cloud` A record to your VPS IP address.

### 8. Enable HTTPS (Optional but Recommended)
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d noaman.cloud -d www.noaman.cloud
```

### 9. Test Deployment
```bash
# Test locally on VPS
curl "http://localhost:8080/scraper.php?code=013001"
curl "http://localhost:8081/api.php?code=013001"

# Test via domain (from anywhere)
curl "https://noaman.cloud/api-php/scraper.php?code=013001"
curl "https://noaman.cloud/api-node/api.php?code=013001"
```

## Updating Deployment

When you push updates to GitHub:

```bash
# On VPS
cd ~/scrapers
git pull

# Restart containers
cd API-php && docker compose restart
cd ../API-node && docker compose restart

# Or rebuild if Dockerfile changed
cd API-php && docker compose down && docker compose up -d --build
cd ../API-node && docker compose down && docker compose up -d --build
```

## Monitoring

```bash
# Check container status
docker ps

# View logs
cd ~/scrapers/API-php
docker compose logs -f

cd ~/scrapers/API-node
docker compose logs -f

# Check resource usage
docker stats
```

## Backup Strategy

```bash
# Backup code (already on GitHub)
git push

# Backup Docker volumes (if any)
docker run --rm -v api-php_data:/data -v $(pwd):/backup ubuntu tar czf /backup/api-php-backup.tar.gz /data
```

## Summary

All files are ready for:
1. ✅ Commit to GitHub
2. ✅ Clone on VPS
3. ✅ Deploy with Docker
4. ✅ Access via noaman.cloud

The documentation includes:
- Complete Docker setup for both projects
- VPS deployment instructions
- Domain configuration (noaman.cloud)
- HTTPS/SSL setup guide
- Troubleshooting tips
- Maintenance procedures
