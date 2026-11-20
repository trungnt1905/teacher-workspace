#!/bin/sh
# Container start (DETAIL_DESIGN §13.4): check secrets, prepare runtime dirs, cache config, start services.
set -eu

missing=""
for var in APP_KEY ADMIN_EMAIL ADMIN_PASSWORD_HASH; do
    eval "value=\${$var:-}"
    [ -n "$value" ] || missing="$missing $var"
done
if [ -n "$missing" ]; then
    echo "entrypoint: missing required environment variables:$missing" >&2
    echo "entrypoint: see docs/deployment.md" >&2
    exit 1
fi

# Render exposes the public URL; use it unless APP_URL is set explicitly.
export APP_URL="${APP_URL:-${RENDER_EXTERNAL_URL:-http://localhost:${PORT}}}"

cd /var/www/app

# Runtime dirs are ephemeral on Render Free: recreate them on every start.
mkdir -p storage/app/private/timetable-jobs storage/framework/cache/data storage/framework/views storage/logs bootstrap/cache
chown -R www-data:www-data storage bootstrap/cache
chmod 700 storage/app/private/timetable-jobs

# No database in the MVP: no migrations. APP_KEY is a fixed secret: never key:generate here.
su -s /bin/sh www-data -c "php artisan config:cache && php artisan route:cache && php artisan view:cache" >/dev/null

envsubst '${PORT}' < /etc/nginx/app.conf.template > /etc/nginx/conf.d/app.conf

exec "$@"
