# Developer Onboarding Guide — Ugavi

## Prerequisites
- Python 3.14+ installed
- MariaDB 11.8+ installed
- Valkey 8+ installed
- Node.js 24+ installed
- Frappe Bench installed: `pip install frappe-bench`

## Quick Start

```bash
# 1. Clone the repo
git clone <repo-url>
cd ugavi

# 2. Build the development image and start the source-mounted stack
make dev-up

# 3. In another terminal, seed and verify the demo
make seed
make demo-check
make fleet-check
```

Open http://localhost:8000. The development stack uses Frappe's native
`bench start` process with the repository mounted at
`/home/frappe/frappe-bench/apps/ugavi`; Python, templates, and client assets
can therefore be iterated without rebuilding for each edit. Use `make dev-logs`
to follow the process, `make dev-shell` for a shell, and `make dev-down` to
stop it.

The development service uses Frappe's native `bench serve` process, with a
separate native Socket.IO process. The image-based `make setup`/`make start`
path remains the authoritative rehearsal and demo path. It intentionally does
not mount source code and therefore validates the same immutable application
image used for release testing. Do not use the source-mounted development
stack as an upgrade rehearsal.

Open http://localhost:8000 and login with Administrator / admin.

**LOKADO Demo:** `make seed` (canonical 19-user dataset) · `make demo-check` · `make fleet-check` · Tour: `docs/demo/LOKADO-DEMO-TOUR.md`

## Project Structure
```
ugavi/
├── docs/                    # ADRs, guides, glossary, threat model
│   ├── adr/                 # 6 ADRs
│   ├── admin-guide.md
│   ├── api-reference.md
│   ├── runbook.md
│   ├── upgrading-guide.md
│   ├── glossary.md
│   └── security/            # threat model, OWASP mapping
├── tests/                   # Unit, e2e, concurrency, tenant isolation tests
│   └── e2e/                 # Playwright test suite
├── ugavi/
│   ├── hooks.py             # App hooks (JS, scheduler, fixtures)
│   ├── procurement/         # PR, Tender, Bid, Supplier PQ, sealed-bid crypto
│   │   ├── doctype/         # DocType Python controllers
│   │   ├── services/        # sealed_bid.py crypto
│   │   ├── workspace/       # Desk workspace JSON
│   │   ├── dashboard/       # Dashboard JSON
│   │   └── portal/          # Supplier portal views
│   ├── logistics/           # Stock Ledger, Donor Warehouse, Transfer
│   ├── assets/              # Asset Register, Movement, Disposal, Verification
│   ├── fleet/               # Vehicle, Trip, Fuel, Spare Parts
│   ├── governance/          # Hash chain, rate limiter, feature flags, key rotation
│   │   └── services/
│   ├── public/js/           # Client-side JS scripts
│   ├── scripts/             # Scheduled tasks, health check
│   ├── fixtures/            # Demo data seed
│   └── translations/        # i18n scaffolding
├── CHANGELOG.md
├── Makefile
└── pyproject.toml
```

## Development Workflow

### Adding a New DocType
```bash
bench new-doctype --module ugavi.procurement --name "My DocType"
# Edit my_doctype/my_doctype.json (schema)
# Edit my_doctype/my_doctype.py (controller)
# bench migrate && bench build
```

### Running Tests
```bash
# Unit tests
bench run-tests --app ugavi

# Specific test file
bench run-tests --app ugavi --module ugavi.tests.test_concurrency

# E2E tests (Playwright)
cd tests/e2e
npm ci
npx playwright install chromium
npx playwright test
```

### Building JS Assets
```bash
bench build --app ugavi        # Full build
bench watch --app ugavi        # Watch mode for dev
```

## Code Conventions
- **Python**: Follow PEP 8, type hints encouraged
- **JS Client Scripts**: `frappe.ui.form.on("DocType", { ... })` pattern
- **Donor Segregation**: Always filter by `donor` field; never hardcode donor values
- **Security**: Never log private keys; never hardcode secrets; use frappe.cache() not global variables
- **Tests**: All new features must have at minimum a FrappeTestCase
- **Commits**: Conventional Commits format (`feat:`, `fix:`, `docs:`, `test:`, `security:`)

## Common Issues

| Issue | Solution |
|-------|----------|
| "No module named ugavi" | Run `pip install -e ~/frappe-bench/apps/ugavi` |
| Workspace not showing | Check `ugavi/<module>/workspace/<name>/<name>.json` exists |
| JS script 404 | Run `bench build --app ugavi` |
| Migration fails | Run `bench migrate --dry-run` to preview |
| "Site not found" | Run `bench use <site-name>` |

## Contributing
1. Fork → Branch (`feat/my-feature`) → PR
2. Include tests + updated docs if applicable
3. CI must pass (tests, build, lint) — see `.github/workflows/ci.yml`
4. Security-sensitive changes require security review

---

## CI/CD Pipeline

All pushes and PRs are validated by GitHub Actions (`ci.yml`). The pipeline runs in this order:

```
Lint → Unit Tests ───→ E2E Tests
       ├→ Security Scan (SAST + deps + secrets)
       ├→ SBOM Generation
       ├→ Container Scan (Trivy → CodeQL)
       └→ Docs Check (links + spelling)
Load Tests (manual trigger only)
```

### Local Pre-PR Checks

```bash
make lint                     # ruff + prettier
make test                     # Current backend suite
make security-scan            # Bandit + Safety + detect-secrets
make sbom                     # SPDX JSON
make seed && make demo-check  # LOKADO seed integrity
make fleet-check              # fleet reconciliation
make e2e                      # Playwright (backend must be running)
```

The E2E runner and browser are host-side development dependencies; they are not
baked into the Ugavi application image. A missing Node module or browser binary
means the UI gate was not executed, not that the application passed or failed.

### CI Security Gates

- **Blocking**: Lint failure, test failure, critical/high CVE
- **Warning**: Medium CVE, new secrets baseline entry, broken doc links
- **Informational**: Low CVE, SBOM changes, spelling

### Weekly Security Cron

Every Monday 6am UTC: Full security scan runs and uploads Bandit + Safety + detect-secrets reports as artifacts.