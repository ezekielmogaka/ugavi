# Evidence Document — Ugavi 0.1.0

## Phase A: Foundation (Complete)
- [x] Frappe 16.52.0 installed and configured
- [x] MariaDB 11.8 running with donor-segregated schema
- [x] Python 3.14 environment with all dependencies in pyproject.toml
- [x] Valkey 8 for caching and schedule queue
- [x] Node.js 24 for JS asset compilation
- [x] Multi-tenancy model decided (ADR-001: Model A, donor as dimension)
- [x] .gitignore created (IDE, OS, pycache, node_modules, backups)

## Phase B: Procurement Core (Complete)
- [x] Purchase Requisition DocType + controller
- [x] Supplier Prequalification DocType + controller
- [x] Tender DocType + controller + JSON schema
- [x] Bid DocType + JSON schema + controller
- [x] Sealed-bid crypto service (SSS + RSA-4096 + AES-256-GCM)
- [x] Threat model documented (TN13: private key exposure fixed)
- [x] DoA matrix documented (ADR-006)

## Phase C: Logistics + Assets + Fleet (Complete)
- [x] Donor Warehouse controller
- [x] Stock Ledger controller
- [x] Inter-Donor Transfer controller
- [x] Monthly Stock Report controller
- [x] Asset Register, Movement, Disposal, Verification controllers
- [x] Vehicle, Vehicle Allocation, Trip Log, Fuel Log, Spare Parts Issue controllers
- [x] Scheduled tasks: vehicle service check, supplier flagging, asset verification reminder

## Phase D: UI + Workspaces + Tests (Complete)
- [x] 5 JS client scripts (purchase_requisition, supplier_prequalification, tender, bid, bid_opening_record)
- [x] 6 workspace JSONs (procurement, tendering, logistics, assets, fleet, governance)
- [x] 3 e2e workflow tests (procurement, logistics, governance)
- [x] Playwright config + conftest.py
- [x] 3 print formats (PR, Tender, Bid)
- [x] 3 dashboards (procurement, logistics, fleet)
- [x] Supplier portal (Python controller + HTML template)
- [x] Demo data fixtures

## Phase E: Platform Hardening (Complete)
- [x] Hash chain audit service (GA-045)
- [x] Rate limiter service (GA-010)
- [x] Feature flags service (GA-061)
- [x] Structured JSON logging (GA-053)
- [x] Key rotation service (GA-046)
- [x] Health check endpoint (GA-052)
- [x] Concurrency tests (GA-048)
- [x] Transactional boundary tests (GA-049)
- [x] Tenant isolation tests (GA-072)
- [x] Graceful degradation tests (GA-058)
- [x] OWASP ASVS mapping (GA-040)
- [x] Pen-test checklist (GA-047)

## Phase F: Platform Hardening — CI/CD & Infrastructure (Complete)
- [x] Secret scanning config — `.detect-secrets-config.yaml` (GA-041)
- [x] Container scanning — `Dockerfile` + Trivy in CI workflow (GA-042)
- [x] Security headers — `deploy/nginx/ugavi-security-headers.conf` (GA-043)
- [x] Index review script — `ugavi/scripts/index_review.sh` (GA-050)
- [x] Donor ledger integrity check — `ugavi/logistics/services/donor_ledger_integrity.py` (GA-051)
- [x] Backup restore procedure — `tests/backup_restore_procedure.md` (GA-056)
- [x] k6 load test script — `tests/load/procurement_load.js` (GA-059)
- [x] Resilience test plan — `tests/resilience_test_plan.md` (GA-060)
- [x] GitHub Actions CI/CD pipeline — `.github/workflows/ci.yml` (GA-089/090/091)
- [x] Docs CI, link check, prose lint integrated into CI pipeline

## Phase G: Portal & UI — Evaluation + Contracts + eTIMS (Complete)
- [x] COI Declaration controller — `coi_declaration.py` (GA-008)
- [x] Bid Evaluation Summary controller — `bid_evaluation_summary.py` (GA-008)
- [x] Standstill Period controller — `standstill_period.py` (GA-008)
- [x] Contract Retention & Performance Bonds — `contract_retention.py` (GA-009)
- [x] Contract Document Repository — `contract_document.py` (GA-009)
- [x] eTIMS Integration scaffold — `etims_client.py` (GA-011)
- [x] Accessibility guidelines — `docs/accessibility-guidelines.md` (GA-036)

## Phase H: Documentation (Complete)
- [x] 6 ADRs (multi-tenancy, sealed-bid crypto, AI features, rules engine, UI strategy, DoA matrix)
- [x] CHANGELOG.md (GA-024)
- [x] Admin guide (GA-082)
- [x] User guides × 3 (procurement officer, logistics officer, fleet manager) (GA-083)
- [x] API reference (GA-084)
- [x] Runbook (GA-085)
- [x] Upgrading guide (GA-086)
- [x] Glossary (GA-087)
- [x] Developer onboarding guide (GA-088)
- [x] Mobile/offline evaluation (GA-037)
- [x] i18n scaffolding (GA-038)
- [x] Accessibility guidelines (GA-036)
- [x] Threat model update
- [x] Gap analysis updated
- [x] Known gaps finalized: 70/71 resolved (99%)

## Remaining (1 — Not MVP)
- [ ] GA-063: Blue/green zero-downtime upgrades (📝 Accepted — not MVP)

## Test Coverage
```
unit/                 4 test files (existing procurement + logistics)
test_concurrency.py   1 file (10 bid submissions, 10 stock entries)
test_transactional_boundary.py  1 file (PR rollback, transfer atomicity)
test_tenant_isolation.py  1 file (donor segregation, stock isolation)
test_graceful_degradation.py  1 file (email failure, notification failure)
e2e/                  3 workflow files + conftest + playwright.config.ts
---
Total: 11 test files covering 43 assertions
```