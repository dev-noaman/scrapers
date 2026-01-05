# Docker Architecture & Deployment Guide

This document details the containerized architecture of the Single Window Scraper system, covering services, ports, images, and deployment instructions.

## 🏗 System Overview

The system consists of **4 Docker services** orchestrated via Docker Compose.

| Service | Container Name | Port (Host:Container) | Base Image | Description |
| :--- | :--- | :--- | :--- | :--- |
| **API-php** | `api-php-scraper` | **8080** : 80 | `python:3.11-slim` | PHP API wrapping a Python **Playwright** scraper. |
| **API-node** | `api-node-scraper` | **8081** : 80 | `node:20-slim` | PHP API wrapping a Node.js **Puppeteer** scraper. |
| **Portal** | `single_window_portal` | **8085** : 80 | Custom (Nginx/PHP) | The main web dashboard for users. |
| **Scraper** | `single_window_scraper` | **N/A** (Background) | `python:3.11-slim` | Heavy-duty **SeleniumBase** scraper (Undetected ChromeDriver). |

---

## 📂 Directory Structure & Dockerfiles

The project uses a split-structure where each legacy API has its own Docker context, while the new components (Portal, Scraper) are managed from the root via the `docker/` folder.

```
/ (Root)
├── docker/                   # Docker Configuration
│   ├── docker-compose.yml    # Orchestrates 'portal' and 'scraper'
│   └── DOCKER.MD             # This documentation
├── docker-scraper/           # Context for 'scraper' service
│   ├── Dockerfile            # Python 3.11 + Chrome + SeleniumBase config
│   ├── requirements.txt      # Python dependencies (seleniumbase, gspread)
│   └── drive/                # (Ignored) Stores google-credentials.json
├── Portal/                   # Context for 'portal' service
│   └── Dockerfile            # Web server config
├── API-php/                  # Legacy PHP Service
│   ├── Dockerfile            # Python 3.11 + PHP + Playwright
│   └── docker-compose.yml    # Runs on port 8080
└── API-node/                 # Legacy Node Service
    ├── Dockerfile            # Node 20 + PHP + Puppeteer
    └── docker-compose.yml    # Runs on port 8081
```

---

## 🏃‍♂️ Quick Run Commands

Run these commands from your terminal (VPS or Local) to execute scrapers immediately inside the running container:

| Scraper | Command |
| :--- | :--- |
| **English Scraper** | `docker exec -it single_window_scraper python scrape-EN.py` |
| **Arabic Scraper** | `docker exec -it single_window_scraper python scrape-AR.py` |
| **Activity Codes** | `docker exec -it single_window_scraper python scrape_codes.py` |

> **Note:** The container must be running (`cd docker && docker compose up -d`) for these to work.

---

## 🚀 Running Locally

### 1. Run the Main System (Portal + Scraper)
To start the dashboard and the background scraper:
```bash
cd docker
docker compose up -d --build
```
- **Access Portal:** [http://localhost:8085](http://localhost:8085)
- **Access Scraper:**
  ```bash
  # Shell into the scraper container
  docker exec -it single_window_scraper bash
  
  # Run a script manually
  python scrape_codes.py
  ```

### 2. Run Legacy APIs
To run the PHP or Node APIs individually:

**API-php:**
```bash
cd API-php
docker compose up -d --build
# Access: http://localhost:8080/scraper.php?code=...
```

**API-node:**
```bash
cd API-node
docker compose up -d --build
# Access: http://localhost:8081/scraper.js?code=...
```

---

## ☁️ VPS Deployment (GitHub Actions)

The system automatically deploys to the VPS using **GitHub Actions**.

### How it works:
1.  **Repo Sync:** Clones the latest code to `/root/scrapers`.
2.  **Secret Injection:** `GOOGLE_CREDENTIALS_JSON` secret is written to `docker-scraper/drive/google-credentials.json`.
3.  **Service Restart:**
    *   Stops and rebuilds `API-php` (8080).
    *   Stops and rebuilds `API-node` (8081).
    *   Stops and rebuilds `portal` (8085) and `scraper` (Background).
4.  **Reverse Proxy:** Updates Nginx on the host to route traffic:
    *   `noaman.cloud/` → Port **8085** (Portal)
    *   `noaman.cloud/api-php/` → Port **8080**
    *   `noaman.cloud/api-node/` → Port **8081**

### Manual VPS Commands
If deployment fails, you can SSH into the VPS and manage containers manually:

```bash
# Check running containers
docker ps

# View logs
docker logs -f single_window_scraper

# Restart specific service
cd /root/scrapers
docker compose restart scraper

# Full Reset (Aggressive)
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
docker network prune -f
docker compose up -d --build
```

---

## 🛠 Troubleshooting

**1. `ImportError: cannot import name 'Driver'`**
*   **Cause:** Using an old `seleniumbase` version.
*   **Fix:** Ensure `requirements.txt` has `seleniumbase>=4.22.0` and rebuild.

**2. `ContainerConfig` Error or Port Conflict**
*   **Cause:** Old container stuck or port 8080 in use.
*   **Fix:** Run `docker rm -f <container_name>` or use the Aggressive Cleanup command above.

**3. `SyntaxError` in Python**
*   **Cause:** Running Python 3 code with `python` (legacy 2.7) instead of `python3`.
*   **Fix:** The Dockerfile now defaults to Python 3.11. Use `python` command inside the container (aliased/default for 3.11 image) or explicit `python3`.

---

## ⚠️ Manual Reset & Update (VPS)

If you need to **completely wipe** all current containers and pull the latest code from GitHub manually, run these commands on your VPS:

```bash
# 1. STOP & REMOVE ALL CONTAINERS (Clean Slate)
docker stop $(docker ps -aq)
docker rm -f $(docker ps -aq)
docker network prune -f

# 2. UPDATE CODE
cd /root/scrapers
git fetch origin main
git reset --hard origin/main

# 3. RESTART EVERYTHING

# A. Start Legacy APIs
cd /root/scrapers/API-php && docker compose up -d --build
cd /root/scrapers/API-node && docker compose up -d --build

# B. Start Main System (Portal + Scraper)
cd /root/scrapers/docker
docker compose up -d --build --force-recreate

# 4. VERIFY
docker ps
```
