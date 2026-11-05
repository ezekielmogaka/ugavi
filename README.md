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

Everything is driven by `make` from the repository root. No manual `docker` or
`bench` commands are needed.

```bash
git clone <repo-url> && cd ugavi

# First run, or a clean rebuild from scratch (DESTRUCTIVE: wipes DB + files)
make clean && make setup && make seed-lokado

make demo-check     # LOKADO acceptance gate: "ready": true, "issues": []
make fleet-check    # fleet purchase-to-vehicle reconciliation
make demo-index     # print this site's demo record IDs and Desk links for the tour
make e2e            # Playwright browser tests (host prerequisites below)
```

**URL:** http://ugavi.localhost:8080 | Login: `Administrator` / `admin`

**Demo mail (dev only):** Mailpit at http://localhost:8026 catches every outgoing
email, including the bid-opening codes. Supporting images are pinned in
`compose.yaml` (`axllent/mailpit:v1.33.0`, `valkey/valkey:9.1.2-alpine`); override
them with `MAILPIT_TAG=... VALKEY_TAG=... make setup` when testing an upgrade.

**LOKADO Demo Tour:** `docs/demo/LOKADO-DEMO-TOUR.md` — complete functional-requirements walkthrough

**Supplier Journey:** `docs/demo/SUPPLIER-JOURNEY.md` — profile through evaluation and notifications

### Common command recipes

| Goal | Commands |
|------|----------|
| Brand-new environment / start over | `make clean && make setup && make seed-lokado` |
| Pick up code changes in the demo stack (keeps data) | `make setup && make seed-lokado` |
| Re-run the seed (idempotent, keeps data) | `make seed-lokado` |
| Verify the demo is presentable | `make demo-check && make fleet-check` |
| Get the record IDs for the tour worksheet | `make demo-index` |
| Wipe only the site data, keep containers | `make reset-lokado` |
| Snapshot a known-good demo | `make backup-demo` |
| Roll back to that snapshot | `make restore-demo` |
| Rehearse an upstream upgrade | `make upgrade-check` |
| Daily source-mounted development (port 8000) | `make dev-up`, then `make dev-config dev-seed dev-check dev-test` |
| Reset the dev site from local source | `make dev-reset` |
| Stop / start without losing data | `make stop` / `make start` |

`make setup` always rebuilds the image first, so it is the safe way to load new
code into the port-8080 stack. `make seed`/`seed-lokado`/`demo-check` run inside
the image: if you edit code and skip `make setup` (or `make build` +
`make upgrade-check`), they still run the **old** baked code.

---

## Makefile Reference

| Target | Description |
|--------|-------------|
| `make setup` | Build the image, start all services, create the site on first run, migrate, apply `setup_config` (safe to rerun; keeps data) |
| `make build` | Build the immutable `ugavi:0.1.0` image (override `UGAVI_IMAGE`/`UGAVI_TAG`) |
| `make start` | Start all services (fast, no health check) |
| `make stop` | Stop all services; retain data volumes |
| `make dev-up` | Build image, start source-mounted `bench serve` on port 8000 (foreground) |
| `make dev-down` | Stop the combined dev stack; retain data volumes |
| `make dev-logs` / `make dev-shell` | Follow server logs / open development-container shell |
| `make dev-migrate` | Run site migration with mounted source |
| `make dev-config` | Apply idempotent site settings and explicit business-role permissions from local source |
| `make dev-seed` | Run canonical LOKADO seed with mounted source |
| `make dev-check` | Run LOKADO and fleet gates with mounted source |
| `make dev-test` | Enable tests and run integration/unit suites with mounted source |
| `make dev-reset` | **Destructive:** reinstall the site, configure, seed and verify using local source |
| `make seed` | Seed LOKADO customer demo data (**canonical**; alias for `seed-lokado`); ends with the acceptance gate |
| `make seed-lokado` | Same as `make seed` |
| `make seed-generic` | Seed generic Ugavi NGO demo data (legacy) |
| `make seed-check` | Integrity report for the legacy generic seed (not the LOKADO gate) |
| `make demo-check` | Verify LOKADO users, supplier links, data lineage, ledger reconciliation and health |
| `make fleet-check` | Verify fleet purchase-to-vehicle reconciliation |
| `make demo-index` | Print the real IDs and Desk links of every tour anchor (tenders, evaluation, standstill, payables, assets, fleet) |
| `make tenant-manifest-check TENANT_MANIFEST=<file>` | Validate an MVP3 isolated-tenant manifest (default `deploy/tenants.example.json`) |
| `make backup-demo` | Native Bench snapshot (database + public + private files) to `backups/lokado-demo/` |
| `make restore-demo` | Restore `backups/lokado-demo/` into the site, then migrate and clear cache |
| `make reset-lokado` | **Destructive:** reinstall the site + `setup_config` + LOKADO seed + `demo-check` |
| `make reset-demo` | Alias for `reset-lokado` |
| `make test` | Enable tests on the site, then run the unit + integration suites in the image |
| `make lint` | Run ruff + black format check |
| `make e2e` | Run Playwright E2E tests (requires a seeded, running site) |
| `make security-scan` | Bandit (SAST) + Safety (deps) + detect-secrets |
| `make sbom` | Generate SPDX SBOM with Syft |
| `make container-scan` | Trivy scan of the built image (requires `trivy`) |
| `make load-test` | k6 procurement load test (requires `k6`; run against a non-demo site) |
| `make check-links` / `make spell-check` | Documentation link and spelling checks (`markdown-link-check`, `cspell`) |
| `make all-checks` | `lint` + `security-scan` + `sbom` + `test` + `e2e` |
| `make backup` | Native Bench backup with files (kept inside the `sites_data` volume) |
| `make restore DB_FILE=<path>` | Restore a database file already inside the container |
| `make upgrade-check` | Rebuild, recreate services, compatibility check, migrate, config, full tests |
| `make clean` | **Destructive:** stop release + dev stacks, delete DB/site volumes and `backups/` |
| `make help` | Show available Make targets |

All site-scoped targets accept `SITE=<site>` (default `ugavi.localhost`), e.g.
`make dev-reset SITE=ugavi-test.localhost`.

### Troubleshooting

- **`LOKADO demo verification failed: ... expected at least 40 ...`, stock
  reports that "do not reconcile", or "invalid requisition lineage"**: the site
  holds data from an older seed, and/or the image holds old code. Rebuild from
  scratch: `make clean && make setup && make seed-lokado` (or keep containers
  and run `make setup && make reset-lokado`).
- **Seed refuses to run:** `seed-lokado` sets `developer_mode` itself; if you
  call scripts by hand, enable it first. Prefer the make targets.
- **Changes not visible on port 8080:** run `make setup` (it rebuilds the
  image). Port 8000 (`make dev-up`) uses mounted source directly.

Run from this repository root. `make seed-generic` is a legacy alternative,
not a prerequisite for LOKADO. Do not mix the datasets.

**During development:** run `make dev-up` in one terminal, then
`make dev-config && make dev-seed && make dev-check && make dev-test` in another.
Use `UGAVI_BASE_URL=http://ugavi.localhost:8000 make e2e`.
Backend/workers still use image-baked code: `make upgrade-check` rebuilds and
recreates the rehearsal stack before validating it on port 8080.

**Safety:** dev and image services share the same database/files. Run
`make backup-demo` before `clean`/`dev-reset`/`reset-demo`/`reset-lokado`; never
use them on production. `make clean` deletes persistent volumes **and** the host
`backups/` folder, so copy `backups/lokado-demo/` elsewhere first if you need it.
`make backup` writes Bench archives under `sites/<site>/private/backups` inside
the `sites_data` volume. `make backup-demo` copies database + public + private
files to the host and `make restore-demo` restores all three.

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
- **Submitted evidence**: 32 POs/receipts, 26 invoices, 19 payments, 8 landed-cost vouchers, 10 budgets, 53 Stock Entries
- **Full workflow**: PR → Tender → Sealed-Bid Opening → Evaluation → Contract → Logistics (live award steps are performed in the tour, not fabricated by the seed)

```bash
make clean && make setup && make seed-lokado   # from scratch (destructive)
make seed-lokado    # canonical LOKADO seed (idempotent; ends with the acceptance gate)
make demo-check     # verify: 21 users, "ready": true, 0 issues
make fleet-check    # verify: fleet reconciliation, donor isolation
```

Tour: `docs/demo/LOKADO-DEMO-TOUR.md` | Presenter Runbook: `docs/DEMO.md`

---

## Support

- **Issues**: GitHub Issues
- **Docs**: `docs/` — admin guide, runbook, developer onboarding, API reference
- **LOKADO**: info@lokado.org | +254722652268 | Lodwar, Turkana County, Kenya