# M0 Truth Baseline — Ugavi MVP1

> **Historical audit snapshot.** This document records the repository state on
> 2026-10-21 before the subsequent schema, Docker, portal, and workflow repairs.
> It is not the current demo runbook. Use the
> [LOKADO functional-requirements tour](../demo/LOKADO-DEMO-TOUR.md) and a fresh
> `make upgrade-check` for current evidence.

> **Date:** 2026-10-21 | **Auditor:** Independent review from clean checkout
> **Method:** File-system inventory, code reading, configuration analysis. No running site (container ImportError prevents bench tests).
> **Principle:** Every claim is verified at the stated path or marked [unverified].

---

## 1. VERSION REGISTER [verified: file-system]

| Component | Version | Evidence |
|-----------|---------|----------|
| Frappe Framework | **Not measured** | Container not running; prior docs claim `16.52.0` [unverified] |
| ERPNext | **Not measured** | Prior docs claim `16.51.1` [unverified] |
| Ugavi | `0.1.0` | [verified: `/pyproject.toml` line 3] |
| Python | **Not measured** | Dockerfile line 33 path references `python3.14` [unverified] |
| MariaDB | **Not measured** | compose.yaml: `mariadb:11.4` [unverified] |
| Valkey | **Not measured** | compose.yaml: `valkey/valkey:8.1-alpine` [unverified] |

---

## 2. CODEBASE STRUCTURE [verified: file-system]

### 2.1 App root (`ugavi/ugavi/`)
- `hooks.py` — 78 lines, 8 hook categories ✅
- `config/__init__.py` — **EMPTY** (no config/docs.py, no config/desk.py)
- 8 modules: assets, compliance, fleet, governance, logistics, procurement, tendering, analytics
- 3 support dirs: integrations, public, scripts
- `tests/` — 3 files, ~25 test methods
- `fixtures/` — demo_data.py (superseded by scripts/seed_demo.py)

### 2.2 Stale Module Stubs (7 directories, empty __init__.py only)
`ugavi_asset_management/`, `ugavi_compliance/`, `ugavi_fleet/`, `ugavi_governance/`, `ugavi_logistics/`, `ugavi_procurement/`, `ugavi_tendering/`

**CRITICAL: Dead code — must be removed. Import namespace pollution risk.**

### 2.3 Duplicate Tender
- `ugavi/procurement/doctype/tender/` — orphan stub (only `__init__.py`)
- `ugavi/tendering/doctype/tender/` — real DocType (tender.json + tender.py)

**HIGH: Duplicate DocType directory — must be removed.**

---

## 3. DOCTYPE SCHEMA INVENTORY [verified: file-system]

### 3.1 Complete DocTypes (JSON schema + Python controller) — 16

| Module | DocType | Fields (JSON) |
|--------|---------|---------------|
| Compliance | Donor Profile | 13 fields |
| Compliance | Donor Rule | 5 fields (istable=1) |
| Compliance | Three-Way Match | 10 fields |
| Compliance | Budget Encumbrance | 8 fields |
| Tendering | Tender | 24 fields + 3 child tables |
| Tendering | Tender Document | 4 fields (istable=1) |
| Tendering | Addendum | 7 fields (istable=1) |
| Governance | Delegation of Authority | 8 fields |
| Governance | Approval Delegation | 6 fields |
| Governance | Segregation of Duties | 5 fields |
| Governance | Waiver | 7 fields |
| Procurement | Bid | 12 fields |
| Procurement | Bid Opening Record | 10 fields + child table |
| Procurement | Bid Opening Detail | 4 fields (istable=1) |
| Procurement | Supplier Prequalification | 12 fields + child tables |
| Procurement | Ugavi Procurement Settings | 10 fields (issingle=1) |

### 3.2 Python-Only DocTypes (code exists, NO JSON schema) — 22

| Module | DocType |
|--------|---------|
| Fleet | Vehicle, Vehicle Allocation, Fuel Log, Trip Log, Spare Parts Issue |
| Assets | Asset Register, Asset Movement, Asset Disposal, Asset Verification |
| Governance | Audit Log |
| Logistics | Stock Ledger, Monthly Stock Report, Inter Donor Transfer, Donor Warehouse, Inter Donor Transfer Item |
| Procurement | Purchase Requisition, Supplier Scorecard, Sealed Bid Key, Ugavi Contract, Evaluation Committee, PR Item, Prequalification Category, Prequalification Document, Contract Milestone, Contract Document, Contract Retention |
| Tendering | Bid Evaluation Summary, Standstill Period, COI Declaration, Clarification, Bid Submission |

**These 22 DocTypes cannot be created by `bench migrate`. Their Python controllers can never execute.**

### 3.3 Report DocTypes (JSON + Python, untested)
| Module | DocType | Status |
|--------|---------|--------|
| Fleet | Fleet Utilization Report | JSON + Python present |
| Assets | Asset Register Report | JSON + Python present |

### Summary
| Category | Count |
|----------|-------|
| Complete (JSON + Python) | 16 |
| Python only (no JSON) | 22 |
| Stale stubs (ugavi_*) | 7 |
| Orphan Tender (procurement) | 1 |
| **TOTAL DocTypes** | **38** |

**Only 42% (16/38) of DocTypes have valid JSON schemas.**
---

## 4. BUILD & DEPLOYMENT [verified: file-system]

| Item | Finding | Severity |
|------|---------|----------|
| Dockerfile | frappe/erpnext:v16 mutable tag | MEDIUM |
| compose.yaml | mailpit:latest mutable tag | MEDIUM |
| Makefile | PYTHONPATH workaround on every bench cmd | MEDIUM |
| .env | DB passwords (OK - .gitignored) | OK |

## 5. SERVICE LAYER — 11 services, ~700 lines

| Service | Lines | Assessment |
|---------|-------|------------|
| sealed_bid.py | 262 | Real crypto: SSS,RSA-4096,AES-256-GCM,OTP |
| rules_engine.py | 160 | Strategy pattern, threshold rules |
| delegation_of_authority.py | 88 | DoA matrix queries |
| scoring_engine.py | ~50 | Weighted scoring (untested) |
| hash_chain.py | ~40 | Immutable hash chain |
| rate_limiter.py | ~30 | Rate limiting |
| feature_flags.py | ~20 | Feature flag engine |

Wiring gap: Most services not called from DocType controllers.

## 6. TEST INVENTORY — 3 files, ~25 methods

| File | Methods | Type |
|------|---------|------|
| test_procurement.py | 5 | Unit |
| test_crypto.py | 6 | Unit |
| test_domain.py | 14 | Integration |
| TOTAL | ~25 | |

Prior Claims vs Reality:
- "57 tests discovered" -> ~25 in 3 files
- "23 passing" -> Cannot verify (no container)
- E2E tests -> No e2e files exist
- Load tests -> File does not exist
- CI pipeline -> .github/workflows/ci.yml does not exist

## 7. CONFIGURATION

Present: hooks.py (78 lines), setup_config.py, seed_demo.py
Missing: config/__init__.py EMPTY (no config/docs.py)

## 8. CLIENT ATOM SCORING — FILE-SYSTEM TRUTH

Score: PASS=code+schema, PARTIAL=code-no-schema, FAIL=no-code

| ID | Atom | Score | Reason |
|----|------|-------|--------|
| P1 | PR w/ approval | PARTIAL | Python; NO JSON |
| P2 | DoA routing | PARTIAL | DoA has JSON; PR doesn't |
| P3 | Method auto-determine | PARTIAL | Engine solid; PR no JSON |
| P4 | Supplier prequal | PASS | JSON+Python exist |
| P5 | PO from approved PR | FAIL | No PO linkage code |
| P6 | Contract w/ milestones | PARTIAL | Python; NO JSON |
| P7 | Three-way match | PASS | JSON+Python exist |
| T1-T6 | Tender lifecycle | PARTIAL | JSON+Python; missing child schemas |
| T7 | Bid security | PASS | JSON+Python exist [verified: tendering/doctype/bid_security/, 2026-10-21 M1 sync] |
| R1 | Monthly stock by donor | PARTIAL | Python; NO JSON |
| R2 | Supplier scorecard | PARTIAL | Python; NO JSON |
| R3 | Fleet utilization report | PASS | JSON+Python (untested) |
| R4 | Asset register report | PASS | JSON+Python (untested) |
| R5 | Audit trail report | PARTIAL | Python; NO JSON |
| O1 | Multi-donor management | PASS | Donor Profile JSON+Python |
| O2 | Donor-specific warehouses | PARTIAL | Python; NO JSON |
| O3 | Inter-donor transfers | PARTIAL | Python; NO JSON |
| O4 | Budget encumbrance | PASS | JSON+Python exist |
| S1 | Stock ledger by donor | PARTIAL | Python; NO JSON |
| S2 | Batch & expiry | FAIL | No fields in any schema |
| S3 | Stock reports | PARTIAL | Python; NO JSON |
| C1 | Segregation of duties | PASS | SoD JSON+Python |
| F1 | Waiver | PASS | Waiver JSON+Python |
| F2 | Delegation | PASS | DoA JSON+service |
| F3 | Committee | PARTIAL | Python; NO JSON |
| F4 | Audit | PARTIAL | Python; NO JSON |
| L1-L4 | Fleet | PARTIAL | Python; NO JSON |
| A1-A3 | Asset | PARTIAL | Python; NO JSON |
| D1 | Demo seed | PARTIAL | Script exists; can't run |

Summary: 8 PASS, 22 PARTIAL, 2 FAIL (P5, S2)
RTM claimed 98/98 complete (0 gaps).

## 9. TOP ANTI-PATTERNS

| ID | Finding | Severity |
|----|---------|----------|
| AP1 | 7 stale ugavi_* stubs | HIGH |
| AP2 | 22 DocTypes: Python, no JSON | CRITICAL |
| AP3 | Duplicate Tender | HIGH |
| AP4 | Mutable image tags | MEDIUM |
| AP5 | ignore_permissions on all seed | HIGH |
| AP6 | config/__init__.py empty | CRITICAL |
| AP7 | PYTHONPATH workaround | MEDIUM |
| AP8 | RTM claims 0 gaps | HIGH |
| AP9 | known-gaps refs missing CI | HIGH |
| AP10 | PR override refs unloadable class | CRITICAL |

## 10. M0 VERDICT

Real engineering exists: crypto, rules engine, DoA matrix, 748-line seed script.
But 58% of DocTypes lack JSON schemas. Without them:
1. bench migrate cannot create 22 DocTypes
2. Python controllers can never execute
3. PR override hook fails at import
4. 7 stale stubs pollute namespace
5. Tests reference non-existent DocTypes
6. RTM claims 0 gaps when only 8/32 atoms verifiably complete

M1 Priority: Create all 22 missing JSON schemas, rebuild Docker, run tests, rescore.
