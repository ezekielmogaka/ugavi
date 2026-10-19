.PHONY: setup start stop seed test lint backup restore upgrade-dry-run reset-demo clean

BENCH_DIR ?= $(HOME)/frappe-bench
SITE ?= ugavi.localhost

setup:
	@echo "==> Setting up Ugavi development environment..."
	docker compose -f compose.yaml up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	docker compose exec backend bench new-site $(SITE) --mariadb-root-password=admin --admin-password=admin
	docker compose exec backend bench --site $(SITE) install-app erpnext
	docker compose exec backend bench --site $(SITE) install-app ugavi
	docker compose exec backend bench --site $(SITE) set-config developer_mode 1
	@echo "==> Setup complete! Visit http://$(SITE):8000"

start:
	docker compose -f compose.yaml up -d
	@echo "Services started. Visit http://$(SITE):8000"

stop:
	docker compose -f compose.yaml down
	@echo "Services stopped."

seed:
	docker compose exec backend bench --site $(SITE) execute ugavi.scripts.seed_demo.run

test:
	docker compose exec backend bench --site $(SITE) run-tests --app ugavi

lint:
	ruff check ugavi/
	black --check ugavi/

backup:
	mkdir -p backups/
	docker compose exec backend bench --site $(SITE) backup --with-files
	docker compose cp backend:$$(docker compose exec backend bench --site $(SITE) backup --with-files | tail -1 | awk '{print $$NF}') backups/

restore:
	docker compose exec backend bench --site $(SITE) restore $(DB_FILE)

upgrade-dry-run:
	docker compose exec backend bench --site $(SITE) migrate --dry-run
	docker compose exec backend bench --site $(SITE) run-tests --app ugavi

reset-demo:
	docker compose exec backend bench --site $(SITE) reinstall --yes
	docker compose exec backend bench --site $(SITE) install-app ugavi
	make seed

clean:
	docker compose -f compose.yaml down -v
	rm -rf backups/*