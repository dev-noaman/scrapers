# API-node Scraper (Node.js + Puppeteer)

Docker-ready Qatar Investor Portal scraper using Node.js and Puppeteer.

## Quick Start (Docker)

### Build and Run
```bash
docker compose up -d --build
```

### Test the API
```bash
# Using curl
curl "http://localhost:8081/api.php?code=013001"

# Using browser
http://localhost:8081/api.php?code=013001
```

### View Logs
```bash
docker compose logs -f
```

### Stop
```bash
docker compose down
```

## API Usage

**Endpoint**: `GET /api.php`

**Parameters**:
- `code` (required): Business activity code (e.g., 013001)

**Response**: JSON format
```json
{
  "status": "success",
  "data": {
    "activity_code": "013001",
    "name_en": "Activity Name in English",
    "name_ar": "اسم النشاط بالعربية",
    "locations": "Main Location 1: ...\nSub Location 1: ...\nFee 1: ...",
    "eligible": "Allowed for GCC nationals\nAllowed for Non-GCC nationals",
    "approvals": "Approval 1: ...\nAgency 1: ..."
  },
  "error": null
}
```

## Local Development (Without Docker)

### Prerequisites
- Node.js 20+
- PHP 8.2+

### Setup
```bash
npm install
```

### Run Scraper Directly
```bash
# Test with activity code
node scraper.js 013001

# Or use npm script
npm test
```

### Run via PHP API
```bash
# Start PHP built-in server
php -S localhost:8081

# Then access
curl "http://localhost:8081/api.php?code=013001"
```

## Configuration

### Environment Variables
- `NODE_ENV=production` - Production mode
- `PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true` - Skip Chromium download (uses pre-installed)
- `PUPPETEER_EXECUTABLE_PATH` - Path to Chromium executable

### Timeout Settings
- Default timeout: 120 seconds
- Nginx timeout: 300 seconds (for long-running scrapes)

## Files

- `scraper.js` - Main Node.js scraper using Puppeteer
- `api.php` - PHP API endpoint wrapper
- `package.json` - Node.js dependencies
- `Dockerfile` - Docker image configuration
- `docker-compose.yml` - Docker Compose setup
- `nginx.conf` - Nginx web server configuration
- `docker-entrypoint.sh` - Container startup script

## Performance

This Node.js implementation is optimized for speed:
- Direct URL navigation
- Aggressive resource blocking (images, fonts, stylesheets)
- Efficient DOM parsing

## Deployment

See [DEPLOYMENT.md](../DEPLOYMENT.md) for VPS deployment instructions.

## Troubleshooting

### Container won't start
```bash
docker compose logs
```

### Puppeteer/Chromium issues
```bash
docker compose build --no-cache
```

### Permission errors
```bash
sudo chown -R $USER:$USER .
```

### Out of memory
Increase shared memory size in docker-compose.yml:
```yaml
shm_size: '2gb'  # Already configured
```
