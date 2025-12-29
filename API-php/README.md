# API-php Scraper (Python + Playwright)

Docker-ready Qatar Investor Portal scraper using Python and Playwright.

## Quick Start (Docker)

### Build and Run
```bash
docker compose up -d --build
```

### Test the API
```bash
# Using curl
curl "http://localhost:8080/scraper.php?code=013001"

# Using browser
http://localhost:8080/scraper.php?code=013001
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

**Endpoint**: `GET /scraper.php`

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
- Python 3.11+
- PHP 8.2+

### Setup
```bash
pip install -r requirements.txt
playwright install chromium
```

### Run Scraper Directly
```bash
# JSON output
python scraper.py --code 013001 --json

# Visible browser mode
python scraper.py --code 013001 --visible --json
```

### Run via PHP Wrapper
```bash
php scraper.php 013001
```

## Configuration

### Environment Variables
- `PYTHONIOENCODING=utf-8` - Ensures proper UTF-8 encoding

### Timeout Settings
- Default timeout: 120 seconds
- Nginx timeout: 300 seconds (for long-running scrapes)

## Files

- `scraper.py` - Main Python scraper using Playwright
- `scraper.php` - PHP wrapper for the Python scraper
- `Dockerfile` - Docker image configuration
- `docker-compose.yml` - Docker Compose setup
- `nginx.conf` - Nginx web server configuration
- `docker-entrypoint.sh` - Container startup script

## Deployment

See [DEPLOYMENT.md](../DEPLOYMENT.md) for VPS deployment instructions.

## Troubleshooting

### Container won't start
```bash
docker compose logs
```

### Chromium issues
```bash
docker compose build --no-cache
```

### Permission errors
```bash
sudo chown -R $USER:$USER .
```
