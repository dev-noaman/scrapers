#!/bin/bash
echo "--- ENTRYPOINT STARTING ---"

# Start PHP-FPM
echo "Starting PHP-FPM service..."
service php8.2-fpm start || service php-fpm start || { echo "ERROR: PHP-FPM failed to start"; exit 1; }

# Wait for socket and link to generic path
echo "Waiting for PHP-FPM socket..."
for i in {1..15}; do
    # Find any existing socket
    ACTUAL_SOCK=$(find /run/php -name "*.sock" | head -n 1)
    if [ -n "$ACTUAL_SOCK" ]; then
        echo "Found socket at: $ACTUAL_SOCK"
        # Create a symbolic link to /run/php/php-fpm.sock for Nginx
        ln -sf "$ACTUAL_SOCK" /run/php/php-fpm.sock
        ls -la /run/php/
        break
    fi
    echo "Still waiting for socket... ($i/15)"
    sleep 1
done

# Start Node.js Scraper Server
echo "Starting Node.js Scraper Server..."
node scraper.js > /var/log/scraper.log 2>&1 &

# Start Nginx in foreground
echo "Starting Nginx..."
exec nginx -g 'daemon off;'
