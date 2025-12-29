#!/bin/bash
set -e

# Start PHP-FPM
# Start PHP-FPM (try generic first, then 8.2)
service php-fpm start || service php8.2-fpm start

# Start Nginx in foreground
nginx -g 'daemon off;'
