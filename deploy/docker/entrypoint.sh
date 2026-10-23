#!/bin/bash
# Ugavi backend entrypoint
# Extends the official frappe_docker main-entrypoint.sh pattern:
#   1. Symlinks baked assets from image layer to volume (official main-entrypoint)
#   2. Creates site + installs apps if first run
#   3. Runs migrate on first install or explicit request
#   4. Starts gunicorn via official start.sh
#
# No PYTHONPATH workaround needed — ugavi is installed in the bench at build time.
# No cp -rL needed — assets live in the image layer, symlinked via official entrypoint.

set -e

# --- Step 1: Official asset symlink ---
# The official main-entrypoint.sh creates: sites/assets -> ../assets
# Since ugavi assets were built into /home/frappe/frappe-bench/assets during image build,
# this symlink gives gunicorn and nginx (in same image) direct access to baked assets.
echo "==> Linking baked assets to volume (official pattern)..."
ASSETS_PATH="/home/frappe/frappe-bench/sites/assets"
BAKED_PATH="/home/frappe/frappe-bench/assets"
rm -rf "$ASSETS_PATH"
mkdir -p "$(dirname "$ASSETS_PATH")"
ln -s "$BAKED_PATH" "$ASSETS_PATH"
echo "==> Assets linked: sites/assets -> ../assets"

# Only the backend owns site creation and migration. Worker, scheduler,
# websocket, and frontend containers must never race the backend setup.
if [ "$1" != "start.sh" ]; then
    exec "$@"
fi

# --- Step 2: Site setup (first-run only) ---
cd /home/frappe/frappe-bench
SITE_NAME="${SITE_NAME:-ugavi.localhost}"

# apps.txt is managed by configurator or first run
if ! grep -q "^ugavi$" /home/frappe/frappe-bench/sites/apps.txt 2>/dev/null; then
    echo "ugavi" >> /home/frappe/frappe-bench/sites/apps.txt
    echo "==> Added ugavi to apps.txt"
fi

# Ensure site exists
if [ ! -d "/home/frappe/frappe-bench/sites/$SITE_NAME" ]; then
    echo "==> Creating site $SITE_NAME..."
    bench new-site "$SITE_NAME" \
        --mariadb-root-password "${MARIADB_ROOT_PASSWORD:-admin}" \
        --admin-password "${ADMIN_PASSWORD:-admin}" \
        --db-host "${DB_HOST:-mariadb}" \
        --no-mariadb-socket
    # ERPNext is already in the bench (from base image), just install to site
    bench --site "$SITE_NAME" install-app erpnext
    # ugavi is already in the bench (from Dockerfile build), install to site
    bench --site "$SITE_NAME" install-app ugavi
    echo "==> Site created and apps installed."
elif ! bench --site "$SITE_NAME" list-apps 2>/dev/null | grep -q ugavi; then
    echo "==> Installing ugavi on existing site..."
    bench --site "$SITE_NAME" install-app ugavi
fi

# --- Step 3: Migrate (on first install or if lock is stale) ---
if [ ! -f "/home/frappe/frappe-bench/sites/.ugavi-migrated" ]; then
    echo "==> Running migrations for $SITE_NAME..."
    # Clean stale lock file from previous aborted run
    rm -f "/home/frappe/frappe-bench/sites/$SITE_NAME/locks/bench_migrate.lock"
    bench --site "$SITE_NAME" migrate
    bench --site "$SITE_NAME" execute ugavi.scripts.setup_config.run
    touch /home/frappe/frappe-bench/sites/.ugavi-migrated
else
    echo "==> Skipping migrate (already migrated)."
fi

# --- Step 4: Start ---
echo "==> Starting Frappe..."
exec "$@"