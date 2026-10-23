.PHONY: setup build start stop seed seed-lokado seed-generic seed-check demo-check fleet-check tenant-manifest-check test lint backup restore backup-demo restore-demo reset-demo reset-lokado upgrade-check clean

BENCH_DIR ?= $(HOME)/frappe-bench
SITE ?= ugavi.localhost
UGAVI_IMAGE ?= ugavi
UGAVI_TAG ?= 0.1.0
ERPNEXT_TAG ?= v16.52.1
NGINX_LISTEN_PORT ?= 8080
TENANT_MANIFEST ?= deploy/tenants.example.json
COMPOSE = UGAVI_IMAGE=$(UGAVI_IMAGE) UGAVI_TAG=$(UGAVI_TAG) NGINX_LISTEN_PORT=$(NGINX_LISTEN_PORT) docker compose -f compose.yaml

setup:
	@echo "==> Setting up Ugavi development environment..."
	$(MAKE) build
	$(COMPOSE) up -d mariadb valkey mailpit
	@echo "==> Waiting for services to be healthy..."
	@$(COMPOSE) rm -sf configurator
	@$(COMPOSE) up -d backend websocket frontend scheduler queue-default queue-long
	@echo "==> Waiting for Frappe to start (this may take 2-3 min for first run)..."
	@ready=0; \
	for i in $$(seq 1 60); do \
		if curl -fsS http://localhost:$(NGINX_LISTEN_PORT)/api/method/frappe.ping >/dev/null; then \
			ready=1; break; \
		fi; \
		echo "Waiting... $$i"; sleep 10; \
	done; \
	test $$ready -eq 1
	$(COMPOSE) exec -T backend bench --site $(SITE) execute ugavi.scripts.setup_config.run
	@echo "==> Setup complete! Visit http://localhost:$(NGINX_LISTEN_PORT)"

build:
	docker build -t $(UGAVI_IMAGE):$(UGAVI_TAG) --build-arg ERPNEXT_TAG=$(ERPNEXT_TAG) .

start:
	docker compose -f compose.yaml up -d
	@echo "Services started. API at http://localhost:8080 (Host: $(SITE))"

stop:
	docker compose -f compose.yaml down
	@echo "Services stopped."

seed: seed-lokado

seed-lokado:
	@docker compose exec -T backend bench --site $(SITE) set-config developer_mode 1
	@docker compose exec -T backend bench --site $(SITE) clear-cache
	docker compose exec -T -e PYTHONPATH=/home/frappe/frappe-bench/apps backend bench --site $(SITE) execute ugavi.scripts.seed_lokado.run

seed-generic:
	docker compose exec -T -e PYTHONPATH=/home/frappe/frappe-bench/apps backend bench --site $(SITE) execute ugavi.scripts.seed_demo.run

seed-check:
	docker compose exec -T -e PYTHONPATH=/home/frappe/frappe-bench/apps backend bench --site $(SITE) execute ugavi.scripts.seed_check.run

demo-check:
	docker compose exec -T backend bench --site $(SITE) execute ugavi.scripts.check_lokado_demo.run
	@curl -fsS http://localhost:$(NGINX_LISTEN_PORT)/api/method/frappe.ping

fleet-check:
	docker compose exec -T backend bench --site $(SITE) execute ugavi.scripts.check_fleet_demo.run

tenant-manifest-check:
	python3 deploy/validate_tenant_manifest.py $(TENANT_MANIFEST)

test:
	docker compose exec -T backend bench --site $(SITE) run-tests --app ugavi

lint:
	ruff check ugavi/
	black --check ugavi/

backup:
	mkdir -p backups/
	docker compose exec -T backend bench --site $(SITE) backup --with-files
	@echo "Backup created in container. Use 'docker compose cp' to extract."

restore:
	docker compose exec -T backend bench --site $(SITE) restore $(DB_FILE)

# LOKADO-specific backup/restore for demo data safety
backup-demo:
	@mkdir -p backups/
	@docker compose exec -T backend bash -c "mysqldump -h mariadb -u root -padmin _bc703ae6065a25c3 > /tmp/lokado_demo_dump.sql"
	@docker compose cp backend:/tmp/lokado_demo_dump.sql backups/lokado_demo_dump.sql
	@echo "LOKADO demo backup saved to backups/lokado_demo_dump.sql"

restore-demo:
	@if [ ! -f backups/lokado_demo_dump.sql ]; then echo "ERROR: backups/lokado_demo_dump.sql not found. Run 'make backup-demo' first."; exit 1; fi
	@docker compose cp backups/lokado_demo_dump.sql backend:/tmp/lokado_demo_dump.sql
	@docker compose exec -T backend bash -c "mysql -h mariadb -u root -padmin _bc703ae6065a25c3 < /tmp/lokado_demo_dump.sql"
	@echo "LOKADO demo data restored from backup"

upgrade-check: build
	@echo "==> Recreating the local rehearsal stack from $(UGAVI_IMAGE):$(UGAVI_TAG)..."
	@$(COMPOSE) rm -sf configurator
	$(COMPOSE) up -d --force-recreate backend frontend websocket scheduler queue-default queue-long
	@echo "==> Waiting for the rebuilt backend..."
	@ready=0; \
	for i in $$(seq 1 60); do \
		if $(COMPOSE) exec -T backend curl -fsS \
			-H "X-Frappe-Site-Name: $(SITE)" \
			http://localhost:8000/api/method/frappe.ping >/dev/null; then \
			ready=1; break; \
		fi; \
		echo "Waiting... $$i"; sleep 5; \
	done; \
	test $$ready -eq 1
	$(COMPOSE) exec -T backend bench --site $(SITE) execute ugavi.scripts.check_upstream_compatibility.run
	$(COMPOSE) exec -T backend bench --site $(SITE) migrate
	$(COMPOSE) exec -T backend bench --site $(SITE) execute ugavi.scripts.setup_config.run
	$(COMPOSE) exec -T backend bench --site $(SITE) set-config allow_tests true
	$(COMPOSE) exec -T backend bench --site $(SITE) run-tests --app ugavi
	@curl -fsS http://localhost:$(NGINX_LISTEN_PORT)/api/method/frappe.ping

reset-demo: reset-lokado

reset-lokado:
	docker compose exec -T backend bench --site $(SITE) reinstall --yes
	docker compose exec -T backend bench --site $(SITE) install-app ugavi
	$(MAKE) seed-lokado
	@echo "==> LOKADO demo reset complete. Run 'make demo-check' to verify."

clean:
	docker compose -f compose.yaml down -v
	rm -rf backups/*
e2e:
	@echo "==> Running e2e Playwright tests..."
	cd tests/e2e && npx playwright test

security-scan:
	@echo "==> SAST scan with Bandit..."
	bandit -r ugavi/ -f html -o bandit-report.html
	@echo "==> Dependency vulnerability scan with Safety..."
	safety check --full-report
	@echo "==> Secret scanning with detect-secrets..."
	detect-secrets scan --all-files ugavi/
	@echo "==> Report: bandit-report.html"

sbom:
	@echo "==> Generating SBOM with Syft..."
	syft ugavi/ -o spdx-json > sbom.spdx.json
	@echo "==> SBOM saved to sbom.spdx.json"

load-test:
	@echo "==> Running load test with k6..."
	k6 run tests/load/procurement_load.js
	@echo "==> Results in k6 summary"

container-scan:
	@echo "==> Scanning container image..."
	trivy image ugavi:latest

check-links:
	@echo "==> Checking documentation links..."
	npx markdown-link-check docs/**/*.md

spell-check:
	@echo "==> Spell checking documentation..."
	cspell "docs/**/*.md" "*.md"

all-checks: lint security-scan sbom test e2e
	@echo "==> All checks passed!"

help:
	@echo "Ugavi Makefile targets:"
	@echo "  make setup          - Initialize bench via Docker, install app"
	@echo "  make start          - Start Docker services"
	@echo "  make stop           - Stop Docker services"
	@echo "  make seed           - Seed LOKADO customer demo data (canonical)"
	@echo "  make seed-lokado    - Seed the LOKADO customer demo (same as 'make seed')"
	@echo "  make seed-generic   - Seed generic Ugavi NGO demo data (legacy)"
	@echo "  make demo-check     - Verify LOKADO users, supplier links, data, and health"
	@echo "  make fleet-check    - Verify fleet purchase-to-vehicle reconciliation"
	@echo "  make backup-demo    - Export LOKADO demo data to SQL dump (safety net)"
	@echo "  make restore-demo   - Restore LOKADO demo data from SQL dump"
	@echo "  make reset-demo     - Reinstall + re-seed LOKADO demo (alias for reset-lokado)"
	@echo "  make reset-lokado   - Fresh site reinstall + LOKADO seed"
	@echo "  make tenant-manifest-check TENANT_MANIFEST=... - Validate isolated MVP3 tenant definitions"
	@echo "  make test           - Run unit tests"
	@echo "  make e2e            - Run Playwright e2e tests"
	@echo "  make lint           - Lint Python (ruff + black)"
	@echo "  make security-scan  - SAST (Bandit), dependency (Safety), secrets (detect-secrets)"
	@echo "  make sbom           - Generate SPDX SBOM (Syft)"
	@echo "  make load-test      - Run k6 load tests"
	@echo "  make container-scan - Scan Docker image with Trivy"
	@echo "  make check-links    - Check doc links with markdown-link-check"
	@echo "  make spell-check    - Spell check docs with cspell"
	@echo "  make all-checks     - Run lint + security + test + e2e"
	@echo "  make backup         - Backup DB with files"
	@echo "  make restore        - Restore from backup"
	@echo "  make upgrade-check  - Rehearse compatibility, migration, tests, and health checks"
	@echo "  make reset-demo     - Reinstall and re-seed demo data"
	@echo "  make clean          - Remove Docker volumes and backups"
	@echo "  make help           - Show this help"