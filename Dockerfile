# Dockerfile — Ugavi Custom Image
# Extends frappe/erpnext:v16 (official image with nginx, assets, entrypoints)
# Installs ugavi app and builds assets into the image layer.
#
# Build:
#   docker build -t ugavi:16 --build-arg ERPNEXT_TAG=v16 .
#
# This follows the frappe_docker pattern:
#   - Apps installed at build time (not at container start)
#   - Assets pre-built in /home/frappe/frappe-bench/assets/
#   - sites/assets removed so clean volume mount works
#   - Same image serves backend (gunicorn) and frontend (nginx)

ARG ERPNEXT_TAG=v16.52.1
FROM frappe/erpnext:${ERPNEXT_TAG}

LABEL org.opencontainers.image.title="Ugavi SCM"
LABEL org.opencontainers.image.description="Enterprise Supply Chain Management on Frappe/ERPNext v16"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.vendor="Ugavi"

USER root

# Copy an installable Frappe app (metadata at app root, package below it).
COPY pyproject.toml README.md MANIFEST.in package.json /home/frappe/frappe-bench/apps/ugavi/
COPY ugavi /home/frappe/frappe-bench/apps/ugavi/ugavi

# Set ownership and register ugavi with bench
RUN chown -R frappe:0 /home/frappe/frappe-bench/apps/ugavi && \
    chmod -R g=u /home/frappe/frappe-bench/apps/ugavi && \
    printf '/home/frappe/frappe-bench/apps/ugavi\n' > /home/frappe/frappe-bench/env/lib/python3.14/site-packages/ugavi.pth && \
    chown frappe:0 /home/frappe/frappe-bench/env/lib/python3.14/site-packages/ugavi.pth && \
    chmod 664 /home/frappe/frappe-bench/env/lib/python3.14/site-packages/ugavi.pth && \
    printf '/home/frappe/frappe-bench/apps\n' > /usr/local/lib/python3.14/site-packages/bench-apps.pth

USER frappe

# Install ugavi-specific dependencies
RUN /home/frappe/frappe-bench/env/bin/pip install --no-cache-dir \
    cryptography>=41.0.0 \
    python-jose>=3.3.0 \
    qrcode>=7.4.0 \
    python-barcode>=0.15.0 \
    prometheus-client>=0.19.0

# Verify ugavi is importable (via .pth created in step 3)
RUN /home/frappe/frappe-bench/env/bin/python -c "import ugavi; print('ugavi import OK')"

# Build assets for ugavi (and rebuild shared bundles for all apps).
RUN cd /home/frappe/frappe-bench && \
    bench build --app ugavi

# Merge freshly-built ugavi assets into the existing image-layer /assets
# bench build writes compiled bundles to apps/ugavi/public/dist/
# and updates shared css/js/assets.json in sites/assets/
# IMPORTANT: only update if bench build actually produced valid manifests.
# The base image already has correct assets.json for frappe+erpnext.
RUN cd /home/frappe/frappe-bench && \
    # Copy shared bundles (only if they exist and have content)
    for d in css js; do \
      if [ -d "sites/assets/$d" ] && [ -n "$(ls -A sites/assets/$d 2>/dev/null)" ]; then \
        cp -r sites/assets/$d/* assets/$d/; \
      fi; \
    done && \
    # Only overwrite manifests if bench build produced valid ones (not empty "{}")
    if [ -f sites/assets/assets.json ] && [ "$(wc -c < sites/assets/assets.json)" -gt 10 ]; then \
      echo "Updating assets.json ($(wc -c < sites/assets/assets.json) bytes)"; \
      cp sites/assets/assets.json assets/; \
    fi && \
    if [ -f sites/assets/assets-rtl.json ] && [ "$(wc -c < sites/assets/assets-rtl.json)" -gt 10 ]; then \
      cp sites/assets/assets-rtl.json assets/; \
    fi && \
    # Copy ugavi public directory
    mkdir -p assets/ugavi && \
    cp -r apps/ugavi/ugavi/public/* assets/ugavi/ && \
    echo "Assets merged: $(find assets/ugavi -type f 2>/dev/null | wc -l) ugavi files" && \
    rm -rf sites/assets

USER root

# Copy our site-setup entrypoint (extends the official main-entrypoint)
COPY deploy/docker/entrypoint.sh /usr/local/bin/ugavi-entrypoint.sh
RUN chmod 755 /usr/local/bin/ugavi-entrypoint.sh

USER frappe

# Default entrypoint: symlinks assets, creates site if needed, starts gunicorn
ENTRYPOINT ["/usr/local/bin/ugavi-entrypoint.sh"]
CMD ["start.sh"]

EXPOSE 8000