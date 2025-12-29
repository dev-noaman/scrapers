FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    php-fpm \
    php-cli \
    nginx \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set Playwright browser path
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN mkdir -p /ms-playwright && chown www-data:www-data /ms-playwright

# Install Playwright browsers and system dependencies
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
RUN chown -R www-data:www-data /app /ms-playwright

# Expose port
EXPOSE 80

# Start script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

CMD ["/docker-entrypoint.sh"]
