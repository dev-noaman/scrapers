#!/bin/bash
echo "--- ENTRYPOINT STARTING ---"
mkdir -p /run/php
chmod 777 /run/php

# Diagnostic: Find PHP binaries
echo "Searching for PHP-FPM binary..."
FPM_BIN=$(which php-fpm8.2 || which php-fpm || find /usr/sbin -name "php*fpm*" | head -n 1)

if [ -z "$FPM_BIN" ]; then
    echo "ERROR: PHP-FPM binary not found in /usr/sbin or PATH"
    ls -la /usr/sbin/php* || echo "No php files in /usr/sbin"
    exit 1
fi

echo "Found FPM binary at: $FPM_BIN"

# Start PHP-FPM
echo "Starting PHP-FPM..."
$FPM_BIN -D || { echo "ERROR: Failed to start FPM binary"; exit 1; }

# Wait for socket
echo "Waiting for PHP-FPM socket..."
for i in {1..10}; do
    if ls /run/php/*.sock >/dev/null 2>&1; then
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
