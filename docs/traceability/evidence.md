# Evidence Registry

> Mapping every claim to its verified source.
> Label: `[verified: path|url]` `[tested: test_id]` `[assumption]`

## Current demo validation — 2026-10-23

This section supersedes historical snapshots below. It certifies only the
checks actually executed, not every requirement or production deployment.

### Environment and reproducible commands

- Frappe **16.53.0**, ERPNext **16.52.1**, Ugavi **0.1.0** (`bench version`).
- Site: `ugavi.localhost`; image frontend `:8080`; source-mounted server
  `http://ugavi.localhost:8000`; Mailpit `http://localhost:8026`.
- MariaDB 11.4; one Valkey service; no ERPNext/Frappe core source edits.
- From repository root, development: `make dev-config`, `make dev-seed`,
  `make dev-check`, `make dev-test`,
  `UGAVI_BASE_URL=http://ugavi.localhost:8000 make e2e`.
- Immutable-image rehearsal: `make upgrade-check`, `make demo-check`,
  `make fleet-check`, `make e2e`.
- `make help` and the [Make reference](../../README.md#makefile-reference)
  describe each command. Avoid `seed-generic` on the LOKADO demo.

### Verified outcomes

| Check | Result and scope |
|---|---|
| Seed rerun | Exit 0; no FAILED/skipped/tracebacks; pre/post acceptance counts unchanged |
| Backend tests | 15 integration + 62 unit tests passed; count both Frappe runners |
| Real opening integration | Generates keys, seals a bid, rejects one/two codes, accepts all three, decrypts original amount, creates immutable BOR/private PDF |
| Role configuration | Repeated configuration adds no duplicate permission rows and retains native ERPNext permissions; auditor governance and finance Budget/LCV grants are read-only |
| Browser staff access | 17/17 Chromium tests passed against both image `:8080` and mounted source `:8000`; all 14 staff logins can read documented records without System Manager |
| Supplier browser | Anonymous sign-in boundary; identity-scoped dashboard, LOKADO brand, mobile single-column layout with no horizontal overflow |
| LOKADO/fleet gates | `ready: true`, empty issues; source references, supplier scorecards, contracts and donor-isolated fleet reports checked |
| Monthly donor books | Generated from actual Stock Ledger after all postings; gate compares every item closing quantity/value and finds missing rows; uses posted stock-value differences, not highest historical rate |
| Image upgrade rehearsal | Rebuild, compatibility (`67` Ugavi / `529` ERPNext DocTypes, no issues/missing controllers), migration, configuration, both test runners and health passed |
| Documentation checks | Documented Make targets exist; local Markdown file links resolve; `git diff --check` passes |

### Fresh baseline used by gates

| Domain | Evidence |
|---|---|
| Identities | 14 staff + 5 supplier portal users; 6 donors; 18 suppliers; 17 Items; 13 Warehouses including groups/defaults |
| Procurement | 10 PRs; 8 tenders; 26 bids; 15 POs (10 submitted, 5 draft); 15 contracts |
| Receiving/evaluation | 10 submitted receipts; 8 submitted Quality Inspections; 12 Completed scorecards |
| Stock | 22 submitted Stock Entries; 36 batches; 8 donor-warehouse links; 6 monthly stock reports; 6 transfers (2 completed, 2 approved, 1 pending, 1 rejected) |
| Finance | 8 submitted invoices; 5 submitted payments; 6 line-level matches; 3 submitted landed-cost vouchers; 6 submitted donor budgets |
| Fleet | 4 Vehicles/allocations/reports; 8 reconciliations, submitted fuel logs, spare issues and trips |
| Assets | 8 Ugavi registers/verifications; 2 movements; 1 authorized disposal |

### Explicit limits / presenter handoff

- **Live opening remains ready:** Solar Water Pumps EU Resilience has an elapsed
  deadline and four sealed bids. Integration tests use disposable fixtures and
  do not consume the presenter tender. The UI collects three codes in one
  authorized session, not three independently signed sessions. Re-request
  codes after failed partial verification; valid codes are single-use.
- The seed leaves Draft/Pending PRs, two Approved and one Pending transfer for
  live actions; repeated seed does not undo completed business transitions.
- Browser tests prove role access and selected supplier UI, not every PR →
  award → receipt transition. Follow the [tour](../demo/LOKADO-DEMO-TOUR.md)
  to demonstrate handoffs; use a disposable site for destructive trials.
- Native matching creates dispute/review evidence, not a payment mismatch
  hard block. Demo budgets use Warn actions. Completed supplier evaluations
  are enforced separately before payments.
- No real bank/M-Pesa settlement, certified eTIMS, external SMS delivery,
  production SSO/2FA, client-approved document templates, load/SLA benchmarks
  or disaster-recovery RTO/RPO certification is claimed.
- Ugavi Asset Register evidence does not prove capitalized/depreciating
  ERPNext Assets (zero native Asset records in this demo). The upstream
  capitalization workflow is separate.
- Passing the pinned v16 rehearsal does not certify an untested v17 upgrade.
- Browser timing: in the final run the first image-port (`:8080`) browser
  pass, started immediately after `upgrade-check` recreated the containers,
  had one connection-level failure (`chrome-error://chromewebdata/` on the
  procurement login redirect; 16/17 passed). Two immediate reruns passed 17/17
  in about 14 s, and the source-mounted `:8000` pass was 17/17. Wait for the
  stack to settle after recreation before presenting.

### Final run record (2026-10-23, fresh site)

Executed in order from the repository root against working tree based on
`e9cc177`; every step's full output was retained outside the repository.

| # | Command | Exit | Key output |
|---|---|---|---|
| 1 | `make backup` | 0 | Database + public/private file archives written |
| 2 | `make dev-reset` (reinstall, `setup_config`, seed, gates) | 0 | 0 `FAILED`/`skipped`/tracebacks; all six donor books have ledger rows |
| 3 | `make dev-seed` (rerun) | 0 | 0 failures; acceptance counts unchanged |
| 4 | `make dev-check` | 0 | LOKADO and fleet: `"ready": true`, `"issues": []` |
| 5 | `make dev-test` | 0 | `Ran 15 tests … OK`; `Ran 62 tests … OK` |
| 6 | `make upgrade-check` | 0 | `compatible: true` (67 Ugavi / 529 ERPNext DocTypes); migrate; 15 + 62 tests OK; `pong` |
| 7 | `make demo-check` | 0 | `ready: true`, 19 users, 5 supplier portal links, `pong` |
| 8 | `make fleet-check` | 0 | `ready: true`, no issues |
| 9 | `make e2e` (`:8080`) | 2, then 0, 0 | 16/17 (transient, see above), then 17/17 twice |
| 10 | `UGAVI_BASE_URL=http://ugavi.localhost:8000 make e2e` | 0 | 17/17 passed |

Documentation check: every `make <target>` cited in `README.md` and `docs/`
exists in the Makefile, every Makefile target appears in the README reference
and `make help`, all local Markdown links resolve, and `git diff --check` passes.
Rerun the sequence above to reproduce in another environment.

## Historical snapshots (superseded; retained for provenance)

The tables and dated notes below record earlier findings. Old versions,
counts, missing-schema reports and risk statuses are not the current state.

## Verified DocTypes (JSON exists)
| DocType | Path |
|----------|------|
| Purchase Requisition | `ugavi/procurement/doctype/purchase_requisition/purchase_requisition.json` |
| PR Item (child) | `ugavi/procurement/doctype/pr_item/pr_item.json` |
| Supplier Prequalification | `ugavi/procurement/doctype/supplier_prequalification/supplier_prequalification.json` |
| Prequalification Category (child) | `ugavi/procurement/doctype/prequalification_category/prequalification_category.json` |
| Prequalification Document (child) | `ugavi/procurement/doctype/prequalification_document/prequalification_document.json` |
| Tender | `ugavi/tendering/doctype/tender/tender.json` |
| Tender Document (child) | `ugavi/tendering/doctype/tender_document/tender_document.json` |
| Addendum (child) | `ugavi/tendering/doctype/addendum/addendum.json` |
| Evaluation Committee (child) | `ugavi/procurement/doctype/evaluation_committee/evaluation_committee.json` |
| Bid | `ugavi/procurement/doctype/bid/bid.json` |
| Bid Opening Record | `ugavi/procurement/doctype/bid_opening_record/bid_opening_record.json` |
| Bid Opening Detail (child) | `ugavi/procurement/doctype/bid_opening_detail/bid_opening_detail.json` |
| Sealed Bid Key | `ugavi/procurement/doctype/sealed_bid_key/sealed_bid_key.json` |
| Ugavi Procurement Settings | `ugavi/procurement/doctype/ugavi_procurement_settings/ugavi_procurement_settings.json` |
| Delegation of Authority | `ugavi/governance/doctype/delegation_of_authority/delegation_of_authority.json` |
| Donor Profile | `ugavi/compliance/doctype/donor_profile/donor_profile.json` |
| Donor Rule (child) | `ugavi/compliance/doctype/donor_rule/donor_rule.json` |

## Verified Python Services
| Service | Path |
|---------|------|
| Procurement Rules Engine | `ugavi/procurement/services/rules_engine.py` |
| Delegation of Authority | `ugavi/procurement/services/delegation_of_authority.py` |
| Sealed Bid Crypto | `ugavi/procurement/services/sealed_bid.py` |
| SMS Provider Adapter | `ugavi/integrations/sms/base.py` |

## ERPNext Standard Capabilities Verified
| Capability | Path |
|-----------|------|
| Purchase Requisition | `apps/erpnext/erpnext/buying/doctype/purchase_requisition/` |
| Purchase Order | `apps/erpnext/erpnext/buying/doctype/purchase_order/` |
| Purchase Receipt | `apps/erpnext/erpnext/stock/doctype/purchase_receipt/` |
| Budget | `apps/erpnext/erpnext/accounts/doctype/budget/` |
| Stock Entry | `apps/erpnext/erpnext/stock/doctype/stock_entry/` |
| Asset | `apps/erpnext/erpnext/assets/doctype/asset/` |

## DocType directories WITHOUT JSON (stubs only)
- procurement: contract, supplier_scorecard, procurement_rules
- governance: waiver, approval_delegation, audit_log, segregation_of_duties
- compliance: budget_encumbrance, three_way_match
- logistics: donor_warehouse, inter_donor_transfer, monthly_stock_report, stock_ledger
- assets: asset_disposal, asset_movement, asset_register, asset_verification
- fleet: fuel_log, spare_parts_issue, trip_log, vehicle, vehicle_allocation

## Missing JS client scripts (listed in hooks but not created)
- `procurement/doctype/purchase_requisition/purchase_requisition.js`
- `procurement/doctype/supplier_prequalification/supplier_prequalification.js`
- `tendering/doctype/tender/tender.js`
- `procurement/doctype/bid/bid.js`
- `procurement/doctype/bid_opening_record/bid_opening_record.js`

## MVP2 W0 Update (2026-10-21)

### Test Results [measured: bench run-tests --app ugavi, 2026-10-21]
- **27/27 tests pass** (0.338s)
- 12 integration tests: TestApprovalDelegation, TestContractLifecycle, TestKeyDistribution, TestScoringEngine, TestSegregationOfDuties, TestWaiverWorkflow
- 15 unit tests: TestProcurementRulesEngine, TestDelegationOfAuthority, TestOTP, TestSealedBidCrypto

### LOKADO Seed [tested: bench execute ugavi.scripts.seed_lokado.run]
- 868-line seed script, 19 functions, covers LOKADO (Turkana-based Kenyan NGO)
- Seeds: Company, 19 users (14 staff + 5 supplier portal), 6 donors, 42 suppliers, 15 items, 6 warehouses
- Procurement: 6 PRs, 5 tenders, 15 bids, 1 award, 1 contract, milestones
- Governance: DoA, SoD, Waiver, Audit, donor-warehouse links
- Fleet: 4 vehicles, 8 fuel logs, 8 trip logs, 8 spare parts issues, 4 donor-isolated fleet utilization reports
- Assets: 4 registers, 2 movements, 1 disposal
- Compiles clean, production-guarded (refuses to run outside dev/demo environments)
- **Canonical seed:** `make seed` → `make seed-lokado` (default; `make seed-generic` for legacy generic data)
- **Validation:** `make demo-check` and `make fleet-check` both return `"ready": true, "issues": []`
- **Safety:** `make backup-demo` / `make restore-demo` protect against data loss

### Crypto Verification [tested: 2026-10-21]
- **SV-01 RESOLVED (FALSE POSITIVE):** `cryptography==50.0.2` IS installed in bench venv at `/home/frappe/frappe-bench/env/`
- Full RSA-4096 + AES-256-GCM cycle verified PASS
- Prior false negative caused by using system Python (`/usr/local/bin/python3`) instead of bench venv Python

### Seed Data State [measured: frappe.db.count + demo-check, 2026-10-22]
- 42 Suppliers, 15 Items, 2 Vehicles, 8 Donor Profiles
- 6 PRs, 5 Tenders, 15 Bids, 2 Sealed Bid Keys, 0 Bid Opening Records (created live)
- R3 (seed incomplete): RESOLVED — full procurement workflow seeded, verified by `make demo-check`

### DocType DB State
- 60 DocTypes in DB with JSON schemas
- The 22 "missing" DocTypes listed in BASELINE.md section 3.2 actually all have JSON schemas (verified in Docker, not yet reflected on host FS due to 161 uncommitted changes)

### Updated Risk Assessment
- R0 (cryptography absent): RESOLVED
- R1 (161 uncommitted files): STILL OPEN
- R2 (14 schemas in Docker not on host): Partially resolved — schemas exist in Docker
- R3 (seed incomplete): RESOLVED — LOKADO seed now canonical, 19 users, full procurement workflow with validation
- R5 (Contract → UgaviContract rename): Partially resolved — both exist in DB

### Crypto Audit Updates (SEALED-BID-REPORT.md)
- SV-01: FALSE POSITIVE — cryptography installed. Corrected.
- SV-02: Shares plaintext in DB. PENDING share wrapping.
- SV-03-05: Accepted as design decisions.
- Settings integration: OTP expiry + max attempts from Ugavi Procurement Settings DocType.
- Constant-time OTP: uses secrets.compare_digest.

### W0 Deliverables Created
- docs/mvp1/GO-NO-GO.md — MVP1 gate assessment
- docs/mvp2/SCOPE.md — Full 13-workstream scope with client decisions
- docs/mvp2/OPEN-QUESTIONS.md — 10 blocking + 5 non-blocking questions
- docs/mvp2/ (this file updated) — Evidence registry
## M1 Sync Update (2026-10-21)

### Docker → Host Sync
13 DocType directories and all service files synced from Docker to host FS:
- **Tendering:** bid_security, bid_evaluation_summary, coi_declaration, standstill_period
- **Assets:** asset_disposal, asset_movement, asset_register, asset_verification
- **Fleet:** fuel_log, spare_parts_issue, trip_log, vehicle, vehicle_allocation
- **Services:** procurement, tendering, governance, compliance, fleet, assets, logistics

### Host → Docker Sync
2 report DocTypes pushed to Docker:
- `asset_register_report` → Docker: /assets/doctype/asset_register_report/
- `fleet_utilization_report` → Docker: /fleet/doctype/fleet_utilization_report/

### bench migrate
- Ran successfully, no errors [tested: 2026-10-21]
- Asset Register Report: registered ✅
- Fleet Utilization Report: registered ✅

### Bid Security (T7)
- **Status: PASS (was FAIL)** [verified: Docker + host, 2026-10-21]
- JSON + Python controller exist at tendering/doctype/bid_security/
- Loads correctly: `frappe.get_doc("DocType", "Bid Security")` succeeds

### Remaining FAIL Atoms (2)
- P5: PO from approved PR — still FAIL
- S2: Batch & expiry — still FAIL

### 161 Uncommitted Changes
- Reduced but not eliminated. Core DocType files now exist on both sides.
- `git status` still shows divergence for __pycache__, old stubs, etc.
## Security Finding (CRITICAL)
## MVP3 W0 — Hosting & Tenancy Analysis (2026-10-21)

### Gate Check

| Gate | Status | Evidence |
|------|--------|----------|
| MVP1 GO-NO-GO | CONDITIONAL-GO (demo) / NO-GO (pilot) | docs/mvp1/GO-NO-GO.md |
| MVP2 GO-NO-GO | ❌ NOT MET (W1-W13 unbuilt) | docs/mvp2/GO-NO-GO.md |
| Tests | ✅ 15/15 pass 0.038s | [tested: 2026-10-21] |
| bench migrate | ✅ Clean | [tested: 2026-10-21] |
| Core DocTypes | ✅ All load | [tested: 2026-10-21] |

### W0 Deliverables

| Deliverable | Path | Status |
|-------------|------|--------|
| MVP2 Gate Assessment | docs/mvp2/GO-NO-GO.md | ✅ Created |
| Hosting & Tenancy ADR | docs/adr/hosting-and-tenancy.md | ✅ Created (ADR-006, PROPOSED) |
| MVP3 Open Questions | docs/mvp3/OPEN-QUESTIONS.md | ✅ Created (30 questions) |

### Key Architectural Finding

Frappe's multi-site architecture shares app code across all sites on a bench [verified: `sites/` directory structure]. This means:
- **All tenants on one bench must upgrade together** — unacceptable for sealed-bid ceremonies spanning days/weeks
- **One bench per tenant (Option E)** is recommended for isolation and upgrade independence

### Frappe Version Confirmed

| Component | Version | Evidence |
|-----------|---------|----------|
| Frappe | 16.52.0 | [verified: `bench version`, 2026-10-21] |
| ERPNext | 16.51.1 | [verified: `bench version`, 2026-10-21] |
| Ugavi | 0.1.0 | [verified: `bench version`, 2026-10-21] |
| Python | 3.14.8 | [verified: `python3 --version`, 2026-10-21] |

### NEXT: STOP at MVP2 gate per W0 rules. Proceed only if client overrides.
- **TN13**: Sealed Bid Key doctype stores `public_key_pem` as Long Text (public key only — the private key is split via SSS and never stored as a single field). The `private_key_pem` claim in an earlier evidence version was a false positive ([verified: `sealed_bid_key.json`, field at line 19 is `public_key_pem`, 2026-10-21]). The architecture is correct: shares are encrypted and distributed to 3 officers.