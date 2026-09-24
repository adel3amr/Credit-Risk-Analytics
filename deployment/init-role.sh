#!/bin/sh
set -eu
case "$APP_DB_PASSWORD:$POSTGRES_PASSWORD" in
  *replace_*|*example*) echo "Set real database passwords" >&2; exit 1 ;;
esac
[ "${#APP_DB_PASSWORD}" -ge 32 ] && [ "${#POSTGRES_PASSWORD}" -ge 32 ] || { echo "Database passwords must be at least 32 characters" >&2; exit 1; }
[ "$APP_DB_PASSWORD" != "$POSTGRES_PASSWORD" ] || { echo "Use separate database passwords" >&2; exit 1; }
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=app_password="$APP_DB_PASSWORD" <<'SQL'
CREATE ROLE platform_app LOGIN PASSWORD :'app_password';
SQL
