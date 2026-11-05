.PHONY: setup build start stop dev-up dev-down dev-logs dev-shell dev-migrate dev-config dev-seed dev-check dev-test dev-reset seed seed-lokado seed-generic seed-check demo-check demo-index fleet-check tenant-manifest-check test lint backup restore backup-demo restore-demo reset-demo reset-lokado upgrade-check clean e2e help

BENCH_DIR ?= $(HOME)/frappe-bench
SITE ?= ugavi.localhost
UGAVI_IMAGE ?= ugavi
UGAVI_TAG ?= 0.1.0
ERPNEXT_TAG ?= v16.53.0
NGINX_LISTEN_PORT ?= 8080
TENANT_MANIFEST ?= deploy/tenants.example.json
# Local development credentials only; override for any shared environment.
DB_ROOT_PASSWORD ?= admin
ADMIN_PASSWORD ?= admin
COMPOSE = UGAVI_IMAGE=$(UGAVI_IMAGE) UGAVI_TAG=$(UGAVI_TAG) NGINX_LISTEN_PORT=$(NGINX_LISTEN_PORT) docker compose -f compose.yaml
DEV_COMPOSE = UGAVI_IMAGE=$(UGAVI_IMAGE) UGAVI_TAG=$(UGAVI_TAG) docker compose -f compose.yaml -f compose.dev.yaml

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
	$(COMPOSE) exec -T backend bench --site $(SITE) migrate
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

dev-up: build
	@echo "==> Starting source-mounted Frappe development server..."
	@$(DEV_COMPOSE) rm -sf configurator
	@$(DEV_COMPOSE) up -d mariadb valkey mailpit
	@$(DEV_COMPOSE) up -d configurator
	@$(DEV_COMPOSE) up -d backend
	@ready=0; \
	for i in $$(seq 1 60); do \
		if $(DEV_COMPOSE) exec -T backend curl -fsS \
			-H "X-Frappe-Site-Name: $(SITE)" \
			http://localhost:8000/api/method/frappe.ping >/dev/null; then \
			ready=1; break; \
		fi; \
		echo "Waiting for site setup... $$i"; sleep 5; \
	done; \
	test $$ready -eq 1
	@$(DEV_COMPOSE) up -d dev-socketio
	@$(DEV_COMPOSE) up dev-server

dev-down:
	$(DEV_COMPOSE) down

dev-logs:
	$(DEV_COMPOSE) logs -f dev-server

dev-shell:
	$(DEV_COMPOSE) exec dev-server bash

dev-migrate:
	$(DEV_COMPOSE) run --rm dev-server bench --site $(SITE) migrate

dev-config:
	$(DEV_COMPOSE) exec -T dev-server bench --site $(SITE) execute ugavi.scripts.setup_config.run

dev-seed:
	$(DEV_COMPOSE) exec -T dev-server bench --site $(SITE) execute ugavi.scripts.seed_lokado.run

dev-test:
	$(DEV_COMPOSE) exec -T dev-server bench --site $(SITE) set-config allow_tests true
	$(DEV_COMPOSE) exec -T dev-server bench --site $(SITE) run-tests --app ugavi

dev-check:
	$(DEV_COMPOSE) exec -T dev-server bench --site $(SITE) execute ugavi.scripts.check_lokado_demo.run
	$(DEV_COMPOSE) exec -T dev-server bench --site $(SITE) execute ugavi.scripts.check_fleet_demo.run

dev-reset:
	$(DEV_COMPOSE) exec -T dev-server bench --site $(SITE) reinstall --yes --db-root-password $(DB_ROOT_PASSWORD) --admin-password $(ADMIN_PASSWORD)
	$(DEV_COMPOSE) exec -T dev-server bench --site $(SITE) execute ugavi.scripts.setup_config.run
	$(MAKE) dev-seed
	$(MAKE) dev-check

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

demo-index:
	@docker compose exec -T backend bench --site $(SITE) execute ugavi.scripts.demo_index.run --kwargs "{'base_url': 'http://localhost:$(NGINX_LISTEN_PORT)'}"

fleet-check:
	docker compose exec -T backend bench --site $(SITE) execute ugavi.scripts.check_fleet_demo.run

tenant-manifest-check:
	python3 deploy/validate_tenant_manifest.py $(TENANT_MANIFEST)

test:
	$(COMPOSE) exec -T backend bench --site $(SITE) set-config allow_tests true
	$(COMPOSE) exec -T backend bench --site $(SITE) run-tests --app ugavi

lint:
	ruff check ugavi/
	black --check ugavi/

backup:
	mkdir -p backups/
	docker compose exec -T backend bench --site $(SITE) backup --with-files
	@echo "Backup created in container. Use 'docker compose cp' to extract."

restore:
	docker compose exec -T backend bench --site $(SITE) restore $(DB_FILE)

# LOKADO demo snapshot using native bench backup/restore. The database name
# changes on every new-site/reinstall, so never address it directly.
backup-demo:
	@mkdir -p backups/
	$(COMPOSE) exec -T backend bash -c "rm -rf /tmp/ugavi-demo-backup && bench --site $(SITE) backup --with-files --backup-path /tmp/ugavi-demo-backup"
	@rm -rf backups/lokado-demo
	$(COMPOSE) cp backend:/tmp/ugavi-demo-backup backups/lokado-demo
	@echo "LOKADO demo snapshot saved to backups/lokado-demo/"

restore-demo:
	@if ! ls backups/lokado-demo/*-database.sql.gz >/dev/null 2>&1; then echo "ERROR: backups/lokado-demo/ not found. Run 'make backup-demo' first."; exit 1; fi
	tar -C backups/lokado-demo -cf - . | $(COMPOSE) exec -T backend bash -c 'set -e; d=$$(mktemp -d /tmp/ugavi-demo-restore.XXXXXX); trap "rm -rf $$d" EXIT; tar -xf - -C "$$d"; db=$$(ls $$d/*-database.sql.gz); priv=$$(ls $$d/*-private-files.tar); pub=$$(ls $$d/*-files.tar | grep -v -- -private-files.tar); cd /home/frappe/frappe-bench; bench --site $(SITE) restore "$$db" --with-public-files "$$pub" --with-private-files "$$priv" --db-root-password $(DB_ROOT_PASSWORD); bench --site $(SITE) migrate; bench --site $(SITE) clear-cache'
	@echo "LOKADO demo restored from backups/lokado-demo/"

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
	docker compose exec -T backend bench --site $(SITE) reinstall --yes --db-root-password $(DB_ROOT_PASSWORD) --admin-password $(ADMIN_PASSWORD)
	docker compose exec -T backend bench --site $(SITE) execute ugavi.scripts.setup_config.run
	$(MAKE) seed-lokado
	$(MAKE) demo-check
	@echo "==> LOKADO demo reset complete and verified."

clean:
	$(DEV_COMPOSE) down -v --remove-orphans
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
	trivy image $(UGAVI_IMAGE):$(UGAVI_TAG)

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
	@echo "  Fresh demo:  make clean && make setup && make seed-lokado"
	@echo "  make setup          - Build image, start stack, create site (first run), migrate, configure (keeps data)"
	@echo "  make build          - Build the immutable Ugavi image ($(UGAVI_IMAGE):$(UGAVI_TAG))"
	@echo "  make start          - Start Docker services"
	@echo "  make dev-up        - Build image, mount source, and run native bench serve"
	@echo "  make dev-down      - Stop the source-mounted development stack"
	@echo "  make dev-logs      - Follow native Frappe development logs"
	@echo "  make dev-shell     - Open a shell in the development container"
	@echo "  make dev-migrate   - Run a migration in the development container"
	@echo "  make dev-config    - Apply site and role configuration using local source"
	@echo "  make dev-seed      - Seed LOKADO using mounted local source"
	@echo "  make dev-check     - Check LOKADO and fleet evidence using local source"
	@echo "  make dev-test      - Enable and run backend tests using local source"
	@echo "  make dev-reset     - DESTRUCTIVE reinstall, configure, seed and check using local source"
	@echo "  make stop           - Stop Docker services"
	@echo "  make seed           - Seed LOKADO customer demo data (canonical)"
	@echo "  make seed-lokado    - Seed the LOKADO customer demo (same as 'make seed')"
	@echo "  make seed-check     - Report generic seed integrity (legacy dataset)"
	@echo "  make seed-generic   - Seed generic Ugavi NGO demo data (legacy)"
	@echo "  make demo-check     - Verify LOKADO users, supplier links, data, and health"
	@echo "  make demo-index     - Print tour evidence anchors with real record IDs and links"
	@echo "  make fleet-check    - Verify fleet purchase-to-vehicle reconciliation"
	@echo "  make backup-demo    - Native bench snapshot (DB + files) to backups/lokado-demo/"
	@echo "  make restore-demo   - Restore backups/lokado-demo/ snapshot, migrate, clear cache"
	@echo "  make reset-demo     - Reinstall + re-seed LOKADO demo (alias for reset-lokado)"
	@echo "  make reset-lokado   - DESTRUCTIVE reinstall + configuration + seed + demo-check"
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
	@echo "  make clean          - DESTRUCTIVE: stop release+dev stacks, remove volumes and backups"
	@echo "  make help           - Show this help"