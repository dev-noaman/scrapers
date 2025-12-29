#!/bin/bash
set -e

# Start PHP-FPM
service php8.2-fpm start

# Start Nginx in foreground
nginx -g 'daemon off;'
