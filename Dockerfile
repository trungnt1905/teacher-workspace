# Teacher Workspace — one image serving the Vue SPA + Laravel API + Python Excel engine
# (DETAIL_DESIGN §13, §14). Multi-stage: Node and Composer are build-time only.

# --- 1. Vue SPA assets -----------------------------------------------------------------------
FROM node:20-bookworm-slim AS assets
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY vite.config.js ./
COPY resources ./resources
RUN npm run build

# --- 2. PHP dependencies (no dev packages) ---------------------------------------------------
FROM composer:2 AS vendor
WORKDIR /app
COPY composer.json composer.lock ./
RUN composer install --no-dev --no-interaction --no-progress --no-scripts --prefer-dist --optimize-autoloader --ignore-platform-reqs

# --- 3. Runtime ------------------------------------------------------------------------------
FROM php:8.3-fpm-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx supervisor gettext-base python3 python3-venv \
    && docker-php-ext-install opcache \
    && rm -rf /var/lib/apt/lists/*

# Python engine in its own venv (openpyxl, lxml, defusedxml)
COPY python/requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

COPY docker/php.ini /usr/local/etc/php/conf.d/zz-app.ini
COPY docker/php-fpm.conf /usr/local/etc/php-fpm.d/zz-app.conf
COPY docker/nginx.conf.template /etc/nginx/app.conf.template
COPY docker/supervisord.conf /etc/supervisor/conf.d/app.conf
COPY docker/entrypoint.sh /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint && rm -f /etc/nginx/sites-enabled/default

WORKDIR /var/www/app
COPY --chown=www-data:www-data . .
COPY --from=vendor --chown=www-data:www-data /app/vendor ./vendor
COPY --from=assets --chown=www-data:www-data /app/public/build ./public/build
RUN php artisan package:discover --ansi

ENV APP_NAME="Teacher Workspace" \
    APP_ENV=production \
    APP_DEBUG=false \
    LOG_CHANNEL=stderr \
    SESSION_DRIVER=cookie \
    SESSION_SECURE_COOKIE=true \
    SESSION_LIFETIME=10080 \
    CACHE_STORE=array \
    QUEUE_CONNECTION=sync \
    PYTHON_BINARY=/opt/venv/bin/python \
    PORT=10000

EXPOSE 10000
ENTRYPOINT ["entrypoint"]
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
