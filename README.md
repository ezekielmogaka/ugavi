# Ugavi - Enterprise SCM for ERPNext

Enterprise Supply Chain Management solution built on Frappe/ERPNext v16 for NGO-type organizations.

## Features
- **Procurement**: Purchase Requisitions, Tenders, Sealed-Bid Opening, Supplier Prequalification
- **Tendering**: Open/Restricted/Direct RFQ, Addenda, Bid Security, supplier portal submission
- **Evaluation**: Weighted scoring, evaluation committee, COI declarations, bid comparison
- **Contract**: Milestone tracking, retention/bonds, expiry alerts, document repository
- **Logistics**: Donor-segregated warehousing, monthly stock reports, inter-donor transfers
- **Governance**: Delegation of Authority, Segregation of Duties, hash chain audit trail
- **Compliance**: Donor rules engine, budget encumbrance, three-way match
- **Fleet & Assets**: Vehicle register, fuel tracking, asset verification, QR tagging

## Quick Start

```bash
git clone <repo-url> && cd ugavi

# Docker (recommended)
make setup          # starts MariaDB, Valkey, Mailpit, backend
make seed           # canonical LOKADO demo dataset (Turkana NGO)
make demo-check     # verify LOKADO seed integrity
make fleet-check    # verify fleet reconciliation
make e2e            # Playwright browser tests
```

**URL:** http://ugavi.localhost:8080 | Login: `Administrator` / `admin`

**LOKADO Demo Tour:** `docs/demo/LOKADO-DEMO-TOUR.md` — complete functional-requirements walkthrough

**Supplier Journey:** `docs/demo/SUPPLIER-JOURNEY.md` — profile through evaluation and notifications

---

## Makefile Reference

| Target | Description |
|--------|-------------|
| `make setup` | Build image + start all Docker services (MariaDB, Valkey, Mailpit, backend) |
| `make build` | Build the immutable `ugavi:0.1.0` image (override `UGAVI_IMAGE`/`UGAVI_TAG`) |
| `make start` | Start all services (fast, no health check) |
| `make stop` | Stop all services |
| `make dev-up` | Build image, start source-mounted `bench serve` on port 8000 (foreground) |
| `make dev-down` | Stop the combined dev stack; retain data volumes |
| `make dev-logs` / `make dev-shell` | Follow server logs / open development-container shell |
| `make dev-migrate` | Run site migration with mounted source |
| `make dev-config` | Apply idempotent site settings and explicit business-role permissions from local source |
| `make dev-seed` | Run canonical LOKADO seed with mounted source |
| `make dev-check` | Run LOKADO and fleet gates with mounted source |
| `make dev-test` | Enable tests and run integration/unit suites with mounted source |
| `make dev-reset` | **Destructive:** reinstall shared site, configure, seed and verify using local source |
| `make seed` | Seed LOKADO customer demo data (**canonical**; alias for `seed-lokado`) |
| `make seed-lokado` | Same as `make seed` |
| `make seed-generic` | Seed generic Ugavi NGO demo data (legacy) |
| `make seed-check` | Integrity report for the legacy generic seed (not the LOKADO gate) |
| `make demo-check` | Verify LOKADO users, supplier links, data, and health |
| `make fleet-check` | Verify fleet purchase-to-vehicle reconciliation |
| `make tenant-manifest-check TENANT_MANIFEST=<file>` | Validate an MVP3 isolated-tenant manifest (default `deploy/tenants.example.json`) |
| `make backup-demo` / `make restore-demo` | Legacy SQL-only helpers tied to the original database name; **prefer native `backup` / `restore`**, especially after reset |
| `make reset-demo` | Reinstall site + re-seed LOKADO demo (alias for `reset-lokado`) |
| `make reset-lokado` | Fresh site reinstall + setup_config + LOKADO seed + demo-check (destructive) |
| `make test` | Run full test suite |
| `make lint` | Run ruff + black format check |
| `make e2e` | Run Playwright E2E tests (requires backend running) |
| `make security-scan` | Bandit (SAST) + Safety (deps) + detect-secrets |
| `make sbom` | Generate SPDX SBOM with Syft |
| `make container-scan` | Trivy scan of the built image (requires `trivy`) |
| `make load-test` | k6 procurement load test (requires `k6`; run against a non-demo site) |
| `make check-links` / `make spell-check` | Documentation link and spelling checks (`markdown-link-check`, `cspell`) |
| `make all-checks` | `lint` + `security-scan` + `sbom` + `test` + `e2e` |
| `make backup` | Database backup with files |
| `make restore DB_FILE=<path>` | Restore from backup |
| `make upgrade-check` | Rebuild + migrate + run full test suite |
| `make clean` | Tear down containers + volumes |
| `make help` | Show available Make targets |

Run from this repository root. `make seed-generic` is a legacy alternative,
not a prerequisite for LOKADO. Do not mix the datasets.

**During development:** run `make dev-up` in one terminal, then
`make dev-config && make dev-seed && make dev-check && make dev-test` in another.
Use `UGAVI_BASE_URL=http://ugavi.localhost:8000 make e2e`.
Backend/workers still use image-baked code: `make upgrade-check` rebuilds and
recreates the rehearsal stack before validating it on port 8080.

**Safety:** dev and image services share the same database/files. Back up before
`dev-reset`/`reset-demo`/`reset-lokado`; never use them on production.
`make clean` also deletes persistent volumes and host backup contents.
`make backup` writes Bench database + file archives under
`sites/<site>/private/backups` in the `sites_data` volume; copy them off the
container with `docker compose cp` before removing volumes. Restoring the
database alone does not restore attachments or prove disaster recovery.

Browser prerequisites (only needed once or when dependencies change):
`cd tests/e2e && npm ci && npx playwright install chromium`, then return to the
repository root. Security/SBOM/load targets require their respective host tools.

---

## CI/CD Pipeline

Automated via GitHub Actions (`.github/workflows/ci.yml`). Runs on push to `main`/`develop` and all PRs:

| Job | Tools | Purpose |
|-----|-------|---------|
| **Lint & Format** | ruff, prettier | Python + JSON/MD formatting |
| **Unit Tests** | frappe-bench + MariaDB + Valkey | Full test suite in CI container |
| **LOKADO Smoke** | seed_lokado + demo-check + fleet-check | Seed LOKADO data, verify integrity |
| **E2E Tests** | Playwright (Chromium) | Browser-based procurement workflows |
| **Security Scan** | Bandit, Safety, detect-secrets | SAST, dependency vulns, secrets |
| **SBOM** | Anchore Syft | SPDX JSON bill of materials |
| **Container Scan** | Trivy → GitHub CodeQL | CRITICAL/HIGH CVE detection |
| **Docs Check** | markdown-link-check, cspell | Broken links, spelling |
| **Load Test** | Grafana k6 (manual trigger) | Procurement workflow stress test |

Weekly security scan cron: Monday 6am UTC.

---

## Requirements Coverage

**98 functional requirements** across 13 domains (`docs/requirements/REQUIREMENTS.md`):

Procurement (10) · Tendering (14) · Evaluation (7) · Suppliers (6) · Contracts (4) · Logistics (8) · Assets (7) · Fleet (6) · Governance (12) · Finance (7) · Notifications (7) · Operations (5) · Upgradeability (5)

Full traceability: [RTM](docs/traceability/RTM.md). These are scope and
implementation classifications, **not 98 independently passed end-to-end
acceptance tests**. See the [demo coverage map](docs/demo/LOKADO-DEMO-TOUR.md#4-requirement-to-scene-map)
and [current evidence](docs/traceability/evidence.md) for verified boundaries.

---

## LOKADO Demo

Customer-specific demo for Lotus Kenya Action for Development Organization (LOKADO), a Turkana-based NGO:

- **6 donors**: IOM, USAID, Concern Worldwide, Embassy of Japan, EU, Own Funds
- **18 suppliers**: including Nadirkonyen Women's Group (community-based)
- **Stock and service items**: Galla goats, WASH tanks, hygiene kits, construction materials, fuel/spares and field works
- **8 donor-warehouse links**: six donors, including Lodwar, Kakuma, Lokichoggio and Kitale
- **Submitted evidence**: 10 POs/receipts, 8 invoices, 5 payments, 3 landed-cost vouchers, 6 budgets, 22 Stock Entries
- **Full workflow**: PR → Tender → Sealed-Bid Opening → Award → Contract → Logistics

```bash
make seed           # canonical LOKADO seed (idempotent)
make demo-check     # verify: 19 users, 0 issues
make fleet-check    # verify: fleet reconciliation, donor isolation
```

Tour: `docs/demo/LOKADO-DEMO-TOUR.md` | Presenter Runbook: `docs/DEMO.md`

---

## Support

- **Issues**: GitHub Issues
- **Docs**: `docs/` — admin guide, runbook, developer onboarding, API reference
- **LOKADO**: info@lokado.org | +254722652268 | Lodwar, Turkana County, Kenya