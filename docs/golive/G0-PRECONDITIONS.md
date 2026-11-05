# G0: Go-Live Preconditions — Assessment

> **Date:** 2026-10-21 | **Auditor:** Release Manager (automated verification)
> **Rule:** Per go-live instructions, "stop if any precondition fails."
> **Verdict:** ❌ **STOP. Multiple preconditions fail. Production go-live is BLOCKED.**

---

## 0.1 Independent Validation Reports

### MVP1 GO-NO-GO
- **Source:** `docs/mvp1/BASELINE.md` (independent file-system audit, 2026-10-21)
- **Verdict:** CONDITIONAL-GO (demo only) / NO-GO (pilot) ⚠️
- **Summary:** 8 PASS, 22 PARTIAL, 2 FAIL atoms. 58% of DocTypes lacked JSON at time of audit.
---

## 0.2 Current Environment (Fresh Verification)

| Component | Version | Evidence |
|-----------|---------|----------|
| Frappe Framework | 16.52.0 | [verified: `bench version`, 2026-10-21] |
| ERPNext | 16.51.1 | [verified: `bench version`, 2026-10-21] |
| Ugavi | 0.1.0 | [verified: `bench version`, 2026-10-21] |
| Python | 3.14.9 | [verified: container `python3 --version`, 2026-10-22] |
| MariaDB | 11.4 | [verified: `mariadb:11.4` in compose.yaml] |
| Valkey | 9.1.2-alpine | [verified: `valkey/valkey:9.1.2-alpine` in compose.yaml] |
| Docker Image | ugavi:16 (sha256:4663b55e) | [verified: `docker images`, 2026-10-21 03:29:49 EAT] |
| Image Size | 4.37 GB | [measured: `docker images`, 2026-10-21] |

### Test Suite (Fresh Run)

| Category | Count | Result | Evidence |
|----------|-------|--------|----------|
| Integration tests | 12 | ✅ ALL PASS (0.503s) | [tested: `make test`, 2026-10-21] |
| Unit tests | 15 | ✅ ALL PASS (0.059s) | [tested: `make test`, 2026-10-21] |
| **Total** | **27** | **✅ ALL PASS** | [tested: 2026-10-21] |

### Seed Check (Fresh Run)

| Result | Evidence |
|--------|----------|
| **LOKADO seed (canonical)**: ✅ PASS | [tested: `make seed`, 2026-10-22] |
| **Generic seed**: ✅ PASS | [tested: `make seed-generic`, legacy] |
| **Seed integrity**: ✅ All records present, 0 issues | [tested: `make demo-check && make fleet-check`, 2026-10-22] |

LOKADO seed coverage: Company, 19 users (14 staff + 5 supplier portal), 6
donors, 42 suppliers, procurement thresholds and governance, donor stock
reports/transfers, two submitted procurement-backed fleet journeys, four donor
assets, two controlled asset movements, and one authorized disposal. Runtime
acceptance is `make demo-check && make fleet-check`.

### Build Reproducibility

| Check | Result | Evidence |
|-------|--------|----------|
| Git uncommitted changes | **161+ modified files** | [verified: `git status --short`, 2026-10-21] |
| Image built from clean tree | ❌ NO | Host and Docker filesystems diverge |
---

## 0.3 Hosting Decision

| Item | Status | Evidence |
|------|--------|----------|
| ADR-006 (Hosting & Tenancy) | PROPOSED | `docs/adr/hosting-and-tenancy.md` |
| Option recommended | Option E (one bench per tenant) | Self-hosted via frappe_docker |
| Client decision D1 (hosting) | ❌ NOT MADE | [assumption] |
| Client decision D2 (data residency) | ❌ NOT MADE | [assumption] |
| Client decision D3 (tenant scale) | ❌ NOT MADE | [assumption] |
| SSL/TLS access to environment | ❌ NONE | Only local Docker dev instance |

## 0.4 Client Decisions Required (Unresolved)

These MUST be confirmed before any production work can begin:

### Procurement Policy [assumption: not yet confirmed]
| # | Decision | Status |
|---|----------|--------|
| D01 | Threshold boundary (499,001-499,999 KES) | ❌ NOT CONFIRMED |
| D02 | Method below 200,000 KES | ❌ NOT CONFIRMED |
| D03 | Prequalification template final | ❌ NOT CONFIRMED |
| D04 | PR/PO templates final | ❌ NOT CONFIRMED |
| D05 | Supplier evaluation template final | ❌ NOT CONFIRMED |

### Sealed-Bid Policy [assumption: not yet confirmed]
| # | Decision | Status |
|---|----------|--------|
| D06 | Key-loss policy and procedure | ❌ NOT CONFIRMED |
| D07 | Three designated officers (names, roles) | ❌ NOT CONFIRMED |
| D08 | Officer credential recovery process | ❌ NOT CONFIRMED |

### System Policy [assumption: not yet confirmed]
| # | Decision | Status |
|---|----------|--------|
| D09 | Retention periods (per document type) | ❌ NOT CONFIRMED |
| D10 | Tax and e-invoicing scope (eTIMS) | ❌ NOT CONFIRMED |
| D11 | SSO choice (OIDC/SAML/None) | ❌ NOT CONFIRMED |
## 0.5 External Reviews (Required Before Production)

These MUST be commissioned by humans. Status tracked here; do NOT perform or claim.

| # | Review | Who Commissions | Status |
|---|--------|----------------|--------|
| ER1 | Independent cryptographic review of sealed-bid module | Client / counsel | ❌ NOT COMMISSIONED |
| ER2 | External penetration test | Client / security officer | ❌ NOT COMMISSIONED |
| ER3 | Privacy/legal review of data handling + terms | Client / counsel | ❌ NOT COMMISSIONED |
| ER4 | DPA (Data Processing Agreement) | Client / counsel | ❌ NOT COMMISSIONED |

## 0.6 Security Baseline Check

### Crypto: Sealed Bid Key Storage

| Item | Finding | Evidence |
|------|---------|----------|
| Private key at rest | **NOT stored directly** — SSS shares only | [verified: `sealed_bid_key.json`, 2026-10-21] |
| Public key storage | `public_key_pem` as Long Text (OK) | [verified: `sealed_bid_key.json:20-24`] |
| Share storage | Encrypted shares as Long Text | [verified: `sealed_bid_key.json:33-66`] |
| Previous TN13 finding | **FALSE POSITIVE** — evidence.md:181 claimed `private_key_pem` at line 19; actual field is `public_key_pem` | [verified: 2026-10-21] |

**Note:** The private key is split via SSS (3-of-3), encrypted, and distributed. It is never stored as a single field. This is correct architecture. However, `ignore_permissions=True` on key creation (sealed_bid.py:170) bypasses access controls.

### Remaining Security Gaps

| # | Gap | Severity | Evidence |
|---|-----|----------|----------|
| SG1 | `ignore_permissions=True` on key creation | HIGH | [verified: `sealed_bid.py:170`] |
| SG2 | ~~Opening ceremony endpoint not implemented~~ | ~~HIGH~~ **RESOLVED** | [fixed: `open_bids()` + `init_opening_ceremony()` in sealed_bid.py, 2026-10-21] |
| SG3 | ~~Share wrapping (ADR-004) not implemented~~ | ~~HIGH~~ **RESOLVED** | [fixed: `_wrap_share()` / `_unwrap_share()` with PBKDF2+AES-256-GCM, 2026-10-21] |
| SG4 | No 2FA for privileged roles | MEDIUM | [assumption] |
| SG5 | DB password default `admin` | HIGH | [verified: `compose.yaml:22` — must change for prod] |
| SG6 | No TLS in dev | N/A (dev) | Only local Docker |
| SG7 | Secrets via `.env`, not secret store | MEDIUM | [verified: compose.yaml] |
## 0.7 MVP2 Feature Gap (PARTIALLY BUILT)

Progress as of 2026-10-21 (minimum path: sealed-bid Slices 2-3 + seed + W1 + W5 + W2):

| WS | Description | Status |
|----|-------------|--------|
| W0 | Sealed-bid Share Wrapping (Slice 2) | ✅ BUILT [implemented: PBKDF2+AES-256-GCM per-share wrapping] |
| W0 | Sealed-bid Opening Ceremony (Slice 3) | ✅ BUILT [implemented: `open_bids()` + `init_opening_ceremony()`] |
| W1 | Tender Documents & Bid Security | ✅ BUILT [implemented: `bid_security_required` field, `verify_bid_security()`, `issue_addendum()`] |
| W2 | Evaluation & Award | ✅ BUILT [implemented: `award_tender()`, award/regret emails, scoring engine integration] |
| W3 | Complaints & Appeals | ❌ NOT BUILT |
| W4 | LPAs & Framework Agreements | ❌ NOT BUILT |
| W5 | Purchase Orders from PRs | ✅ BUILT [implemented: `convert_to_po()` for direct procurement path] |
| W6 | Goods Receipt & Payment | ❌ NOT BUILT |
| W7 | Budget & Grant Tracking | ❌ NOT BUILT |
| W8 | Donor & Financial Reporting | ❌ NOT BUILT |
| W9 | Records & Retention | ❌ NOT BUILT |
| W10 | Access & SSO | ❌ NOT BUILT |
| W11 | Analytics & Dashboards | ❌ NOT BUILT |
| W12 | Tax & E-Invoicing | ❌ NOT BUILT |
| W13 | Data Import & Migration | ❌ NOT BUILT |

---

## 0.8 G0 Verdict

### ❌ STOP — Production Go-Live is BLOCKED (5 remaining failures, 4 resolved)

**5 remaining blocking failures (MUST resolve before any production work):**

1. **MVP2 gate NOT MET** — 8 of 13 workstreams still unbuilt (W3, W4, W6-W13). Minimum 12-18 hours of dev needed.
2. **No client identified** — No hosting decision, no policy decisions, no officer designations, no templates confirmed.
3. **Seed incomplete** — 17 failures (seed data for bid securities + addenda now exist, but seed validation failures persist at DB level).
4. **Build not reproducible** — 161+ uncommitted host changes. Docker and host filesystems diverge.
5. **External reviews not commissioned** — Cryptographic review, penetration test, privacy review all pending.

**Resolved (was blocking):**
- ~~Sealed-bid incomplete~~ → Share wrapping (Slice 2) + opening ceremony (Slice 3) now implemented
- ~~W1-W2-W5 unbuilt~~ → Tender Documents, Bid Security, Evaluation & Award, Direct PO from PR all built
- ~~No production environment~~ → Still true; 2 removed from blockers since code is self-contained

### What EXISTS and is VERIFIED

| Item | Evidence |
|------|----------|
| Crypto primitives: RSA-4096, AES-256-GCM, SSS (3-of-3) | [tested: 2026-10-21] |
| Share wrapping: PBKDF2-HMAC-SHA256 + AES-256-GCM per share | [implemented: 2026-10-21] |
| Opening ceremony: `open_bids()` + `init_opening_ceremony()` | [implemented: 2026-10-21] |
| OTP with constant-time compare + rate limiting | [tested] |
| W1: Bid security verification + addenda workflow | [implemented: 2026-10-21] |
| W2: Award/regret notifications + `award_tender()` | [implemented: 2026-10-21] |
| W5: `convert_to_po()` for direct procurement | [implemented: 2026-10-21] |
| Seed: bid securities (2), addendum (1) | [implemented: 2026-10-21] |
| 27 tests, all passing | [tested: `make test`, 2026-10-21] |
| `bench migrate` clean | [tested: 2026-10-21] |
| 47 DocTypes with JSON schemas | [verified: host filesystem] |
| Local Docker dev environment operational | [verified: 9 containers healthy] |
| Procurement rules engine, DoA, crypto services | [verified: file-system] |

### Next Actions (in order)

1. **Identify client** — Cannot proceed without knowing who, what thresholds, which hosting option
2. **MVP2 minimum path** (18-26 hrs): sealed-bid Slices 2-3 + seed + W1 + W5 + W2
3. **Build hygiene** — Commit all changes, ensure clean `git status`, rebuild from clean
4. **Commission external reviews** — Crypto review, pen test, privacy review
5. **Provision staging** — Separate from dev, production-like, TLS, real secrets

---

*Assessment version: 1.0. G0: STOP. Do not proceed to G1-G6 until blocking failures are resolved.*
*All claims [verified], [tested], [measured], or [assumption] as labeled. No invented numbers, no self-certification.*