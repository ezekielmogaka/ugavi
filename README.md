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
make seed-generic   # generic Ugavi NGO demo data (legacy)
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
| `make start` | Start all services (fast, no health check) |
| `make stop` | Stop all services |
| `make seed` | Seed LOKADO customer demo data (**canonical**; alias for `seed-lokado`) |
| `make seed-lokado` | Same as `make seed` |
| `make seed-generic` | Seed generic Ugavi NGO demo data (legacy) |
| `make demo-check` | Verify LOKADO users, supplier links, data, and health |
| `make fleet-check` | Verify fleet purchase-to-vehicle reconciliation |
| `make backup-demo` | Export LOKADO demo data to SQL dump (safety net) |
| `make restore-demo` | Restore LOKADO demo data from SQL dump |
| `make reset-demo` | Reinstall site + re-seed LOKADO demo (alias for `reset-lokado`) |
| `make reset-lokado` | Fresh site reinstall + LOKADO seed |
| `make test` | Run full test suite |
| `make lint` | Run ruff + black format check |
| `make e2e` | Run Playwright E2E tests (requires backend running) |
| `make security-scan` | Bandit (SAST) + Safety (deps) + detect-secrets |
| `make sbom` | Generate SPDX SBOM with Syft |
| `make backup` | Database backup with files |
| `make restore DB_FILE=<path>` | Restore from backup |
| `make upgrade-check` | Rebuild + migrate + run full test suite |
| `make clean` | Tear down containers + volumes |

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

Full traceability: `docs/traceability/RTM.md`

---

## LOKADO Demo

Customer-specific demo for Lotus Kenya Action for Development Organization (LOKADO), a Turkana-based NGO:

- **6 donors**: IOM, USAID, Concern Worldwide, Embassy of Japan, EU, Own Funds
- **42 suppliers**: including Nadirkonyen Women's Group (community-based)
- **15 items**: Galla goats, WASH tanks, hygiene kits, construction materials
- **6 warehouses**: Lodwar, Kakuma, Lokichoggio, Oropoi, Kitale Transit
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