#!/bin/bash
echo "--- ENTRYPOINT STARTING ---"

# Start PHP-FPM
echo "Starting PHP-FPM service..."
service php8.2-fpm start || service php-fpm start || { echo "ERROR: PHP-FPM failed to start"; exit 1; }

# Verify PHP-FPM is running
if ! pgrep -f php-fpm > /dev/null; then
    echo "ERROR: PHP-FPM process not found after start attempt"
    exit 1
fi
echo "PHP-FPM is running."

# Start Nginx in foreground
echo "Starting Nginx..."
exec nginx -g 'daemon off;'
