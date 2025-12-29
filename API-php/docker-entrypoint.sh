#!/bin/bash
echo "--- ENTRYPOINT STARTING ---"
mkdir -p /run/php
chmod 777 /run/php

# Start PHP-FPM
echo "Attempting to start PHP-FPM..."
service php8.2-fpm start || service php-fpm start || { 
    echo "ERROR: Service command failed. Trying direct start..."
    /usr/sbin/php-fpm8.2 -D || /usr/sbin/php-fpm -D || { echo "CRITICAL: FPM failed binary start"; exit 1; }
}

# Wait for socket
echo "Waiting for PHP-FPM socket..."
for i in {1..10}; do
    if [ -S /run/php/php8.2-fpm.sock ] || [ -S /run/php/php-fpm.sock ]; then
        echo "Socket found!"
        ls -la /run/php/
        break
    fi
    echo "Still waiting for socket... ($i/10)"
    sleep 1
done

# Start Nginx in foreground
echo "Starting Nginx..."
exec nginx -g 'daemon off;'
