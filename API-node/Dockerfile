FROM node:20-slim

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

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm ci --omit=dev

# Install Puppeteer's Chromium
RUN npx puppeteer browsers install chrome

# Copy application files
COPY scraper.js .
COPY api.php .
COPY README.md .

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
