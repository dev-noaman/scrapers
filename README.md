# Qatar Investor Portal Scrapers - Docker Ready

Docker-ready web scrapers for the Qatar Investor Portal, available in both Python (Playwright) and Node.js (Puppeteer) implementations.

🌐 **Live Demo**: [https://noaman.cloud](https://noaman.cloud)  
📦 **GitHub**: [https://github.com/dev-noaman/scrapers](https://github.com/dev-noaman/scrapers)

## Projects

### 📦 API-php (Python + Playwright)
Python-based scraper using Playwright for browser automation.
- **Endpoint**: `/api-php/scraper.php?code={bacode}`
- **Example**: `https://noaman.cloud/api-php/scraper.php?code=013001`

### 📦 API-node (Node.js + Puppeteer)
Node.js-based scraper using Puppeteer for browser automation.
- **Endpoint**: `/api-node/api.php?code={bacode}`
- **Example**: `https://noaman.cloud/api-node/api.php?code=013001`

## Quick Start

### Local Development

```bash
# Clone repository
git clone https://github.com/dev-noaman/scrapers.git
cd scrapers

# Test API-php
cd API-php
docker compose up -d --build
curl "http://localhost:8080/scraper.php?code=013001"

# Test API-node
cd ../API-node
docker compose up -d --build
curl "http://localhost:8081/api.php?code=013001"
```

### VPS Deployment

See [QUICKSTART.md](QUICKSTART.md) for step-by-step deployment instructions.

## Documentation

- 📖 [QUICKSTART.md](QUICKSTART.md) - Quick start guide for local and VPS deployment
- 📖 [DEPLOYMENT.md](DEPLOYMENT.md) - Comprehensive deployment guide with advanced configurations
- 📖 [API-php/README.md](API-php/README.md) - API-php specific documentation
- 📖 [API-node/README-DOCKER.md](API-node/README-DOCKER.md) - API-node specific documentation

## Features

✅ **Docker Ready** - One-command deployment  
✅ **Production Ready** - Health checks, auto-restart, proper timeouts  
✅ **Dual Implementation** - Choose between Python or Node.js  
✅ **Headless Browsers** - Chromium included in containers  
✅ **JSON API** - Clean REST API responses  
✅ **Arabic Support** - Extracts both English and Arabic content  

## API Response Format

Both APIs return JSON with the following structure:

```json
{
  "status": "success",
  "data": {
    "activity_code": "013001",
    "name_en": "Business Activity Name in English",
    "name_ar": "اسم النشاط التجاري بالعربية",
    "locations": "Main Location 1: ...\nSub Location 1: ...\nFee 1: ...",
    "eligible": "Allowed for GCC nationals\nAllowed for Non-GCC nationals",
    "approvals": "Approval 1: ...\nAgency 1: ..."
  },
  "error": null
}
```

## Requirements

### Local Development
- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose

### VPS Deployment
- Ubuntu 20.04+ VPS
- 2GB+ RAM recommended
- Docker and Docker Compose

## Deployment to noaman.cloud

The project is configured for deployment to `noaman.cloud` with:
- API-php accessible at: `https://noaman.cloud/api-php/`
- API-node accessible at: `https://noaman.cloud/api-node/`

Follow the [DEPLOYMENT.md](DEPLOYMENT.md) guide for complete setup instructions including:
- Docker installation
- File transfer methods
- Nginx reverse proxy configuration
- SSL/HTTPS setup with Let's Encrypt

## Project Structure

```
scrapers/
├── API-php/              # Python + Playwright implementation
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── scraper.py
│   ├── scraper.php
│   └── ...
├── API-node/             # Node.js + Puppeteer implementation
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── scraper.js
│   ├── api.php
│   └── ...
├── DEPLOYMENT.md         # Comprehensive deployment guide
├── QUICKSTART.md         # Quick start guide
└── README.md            # This file
```

## Common Commands

```bash
# Build and start containers
docker compose up -d --build

# View logs
docker compose logs -f

# Stop containers
docker compose down

# Restart containers
docker compose restart

# Check status
docker compose ps
```

## Troubleshooting

See [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting) for detailed troubleshooting guide.

## License

MIT

## Author

Noaman - [GitHub](https://github.com/dev-noaman)

## Support

For issues and questions, please open an issue on [GitHub](https://github.com/dev-noaman/scrapers/issues).

---

## Legacy Scraper Documentation

The original scraper system (Selenium/Playwright with Google Sheets integration) documentation is preserved below for reference.

<details>
<summary>Click to expand legacy documentation</summary>

# Qatar Investor Portal Data Scraper (EN Version)

## System Overview

This automated scraper extracts business activity data from the Qatar Investor Portal (https://investor.sw.gov.qa/) and saves it to a Google Spreadsheet. The system extracts the following information for each business activity:

1. **Activity_Code**: The official activity code from the details page
2. **AR-Activity**: Arabic activity name/description (extracted by switching site language to Arabic)
3. **EN-Activity**: English activity name/description (extracted after switching back to English)
4. **Location Data**: Extracts location information including classifications, types, and fees
5. **Eligible Status**: Eligibility information for the activity
6. **Approvals Data**: All required approvals and associated agencies

### Technical Architecture

The system uses:
- **Selenium WebDriver** OR **Playwright**: For browser automation and interaction
  - `code.py`: Uses Selenium with Microsoft Edge WebDriver
  - `code_playwright.py`: Uses Playwright with Chromium (faster, more reliable)
- **Google Sheets API**: For saving extracted data to spreadsheets
- **Python**: As the programming language

[... rest of the original README content ...]

</details>






t looks like you are using a newer version of Docker where the command has changed from docker-compose to a built-in subcommand.

Try running this instead (without the hyphen):

bash
docker compose up --build -d
If that still says "command not found," you can install the classic version by running:

bash
apt update && apt install -y docker-compose
Then try the original command again:

bash
docker-compose up --build -d
