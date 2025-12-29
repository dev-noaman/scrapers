FROM python:3.11-slim

# Install system dependencies including PHP, Nginx, and browser dependencies
RUN apt-get update && apt-get install -y \
    php8.2 \
    php8.2-fpm \
    php8.2-cli \
    nginx \
    wget \
    gnupg \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application files
COPY scraper.py .
COPY scraper.php .
COPY GUIDE.MD .

# Copy Nginx configuration
COPY nginx.conf /etc/nginx/sites-available/default

# Create PHP-FPM socket directory
RUN mkdir -p /run/php

# Set permissions
RUN chown -R www-data:www-data /app

# Expose port
EXPOSE 80

# Start script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

CMD ["/docker-entrypoint.sh"]
