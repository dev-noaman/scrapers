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

# Start Nginx in foreground
echo "Starting Nginx..."
exec nginx -g 'daemon off;'
