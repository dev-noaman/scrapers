FROM node:20-slim

# Install system dependencies for Puppeteer/Chrome
RUN apt-get update && apt-get install -y --no-install-recommends \
    php-fpm \
    php-cli \
    nginx \
    curl \
    ca-certificates \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxshmfence1 \
    libxtst6 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Set Puppeteer cache path to a shared directory
ENV PUPPETEER_CACHE_DIR=/app/.cache/puppeteer

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm ci --omit=dev

# Install Puppeteer's Chromium into the cache dir
RUN npx puppeteer browsers install chrome

# Copy application files
COPY scraper.js .
COPY api.php .
COPY README.md .

# Copy Nginx configuration
COPY nginx.conf /etc/nginx/sites-available/default

# Create PHP-FPM socket directory and cache dir
RUN mkdir -p /run/php /app/.cache/puppeteer

# Set permissions
RUN chown -R www-data:www-data /app && chmod -R 755 /app/.cache/puppeteer

# Expose port
EXPOSE 80

# Start script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

CMD ["/docker-entrypoint.sh"]
