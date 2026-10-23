# MVP1 GO/NO-GO — Sealed-Bid Tendering + Compliance Controls

> **Historical gate snapshot.** Several failures below were measured before the
> current sealed-bid, schema, seed, upgrade-rehearsal, and browser-test repairs.
> For the current demo procedure and evidence, use the
> [LOKADO functional-requirements tour](../demo/LOKADO-DEMO-TOUR.md) and rerun
> `make upgrade-check`, `make demo-check`, and `make fleet-check`. Run
> `make e2e` separately after preparing the host-side Playwright runtime.

> **Date:** 2026-10-21 | **Author:** Cline QA / Architect  
> **Evidence:** validation-2/SUMMARY.md, BASELINE.md, bench test runs, seed execution  
> **Target:** Ugavi 0.1.0 on Frappe 16.52.0 + ERPNext 16.51.1

---

## Gate Criteria

Each criterion is marked PASS ✅, PARTIAL ⚠️, FAIL ❌, or BLOCKED 🔒 with evidence.

### C1: Core Crypto (Sealed-Bid) — ⚠️ PARTIAL

| Check | Result | Evidence |
|-------|--------|----------|
| Cryptography library installed | ✅ PASS | `cryptography==50.0.2` in bench venv [verified: `pip freeze` in container] |
| RSA-4096 key generation | ✅ PASS | Code in `sealed_bid.py`; HAS_CRYPTO=True |
| AES-256-GCM encrypt/decrypt | ✅ PASS | Full cycle verified [tested: 2026-10-19] |
| SSS 3-of-3 share split/reconstruct | ✅ PASS | `test_split_and_reconstruct` passes |
| OTP verification (constant-time) | ✅ PASS | `test_otp_uses_secrets_compare_digest` passes |
| Share wrapping (scrypt+AES-GCM) | ❌ FAIL | Functions written but not inserted into sealed_bid.py |
| Opening ceremony workflow | ❌ FAIL | Not implemented |
| Seed data for sealed-bid | ❌ FAIL | 0 tenders, 0 bids, 0 sealed-bid keys |

### C2: Tests — ✅ PASS

| Check | Result | Evidence |
|-------|--------|----------|
| Unit tests passing | ✅ PASS | 15/15 pass [measured: `bench run-tests --app ugavi`, 0.034s] |
| OTP tests (4) | ✅ PASS | TestOTP class: generate, verify, wrong, constant-time |
| Crypto tests (3) | ✅ PASS | TestSealedBidCrypto: reconstruct, 2-share-fail, different-secrets |
| Delegation tests (3) | ✅ PASS | valid chain, duplicate roles, empty chain |
| Procurement tests (5) | ✅ PASS | prequalification, threshold rules |

### C3: Data Integrity — ⚠️ PARTIAL

| Check | Result | Evidence |
|-------|--------|----------|
| Seed script runs idempotently | ✅ PASS | Multiple runs produce no duplicate errors [tested: 2026-10-21] |
| Audit trail | ✅ PASS | `_log_audit()` helper exists in sealed_bid.py |
| Tender/bid records | ❌ FAIL | 0 tenders, 0 bids, 0 PRs [measured: frappe.db.count] |
| Sealed-bid integration | ❌ FAIL | No end-to-end test |

### C4: Configuration & Settings — ✅ PASS

| Check | Result | Evidence |
|-------|--------|----------|
| Ugavi Procurement Settings (Single DocType) | ✅ PASS | 10 fields, exists in DB [verified: DocType list] |
| OTP expiry/min attempts from settings | ✅ PASS | `_otp_expiry_seconds()`, `_max_otp_attempts()` helpers |
| DoA matrix | ✅ PASS | Delegation of Authority DocType + service |
| Segregation of duties | ✅ PASS | SoD DocType with rules |

### C5: Documentation — ⚠️ PARTIAL

| Check | Result | Evidence |
|-------|--------|----------|
| ADRs | ✅ PASS | ADR-001 through ADR-005 exist |
| Threat model | ✅ PASS | `threat-model.md` exists |
| Design doc | ✅ PASS | `docs/security/design.md` exists |
| Use-case specs | ⚠️ PARTIAL | 3 defined (UC-05, UC-12, UC-19) |
| GO-NO-GO.md (this file) | ✅ PASS | Created now |
| HANDOFF.md | ❌ FAIL | Not created |
| OPEN-QUESTIONS.md | ❌ FAIL | Not created |

### C6: Build Reproducibility — ❌ FAIL

| Check | Result | Evidence |
|-------|--------|----------|
| `pip install` succeeds with dep list | ✅ PASS | cryptography in venv |
| Docker builds cleanly | ❌ FAIL | 161 uncommitted changes, host/docker code divergence [measured: `git status`] |
| `bench migrate` runs without error | ⚠️ PARTIAL | Some DocType stubs/warnings [BASELINE.md AP1-AP7] |

### C7: DocType Schema Completeness — ⚠️ PARTIAL

| Check | Result | Evidence |
|-------|--------|----------|
| DocTypes with JSON schema | ✅ 60 in DB | [verified: frappe.db.get_all("DocType")] |
| DocTypes with only Python (no JSON) | ⚠️ ~22 | [BASELINE.md section 3.2] |
| Stale module stubs | ❌ 7 | ugavi_* dirs with empty __init__.py [BASELINE.md AP1] |
| Duplicate Tender directory | ❌ 1 | procurement/doctype/tender/ + tendering/doctype/tender/ [BASELINE.md AP3] |

---

## Verdict

### For Client Demo: ⚠️ CONDITIONAL-GO

**Conditions for green (estimated 2-3 days):**
1. Complete share wrapping insertion (Slice 2, ~30 min)
2. Extend seed to include 2 tenders + 3 bids + 2 PRs (~2 hours)
3. Implement opening ceremony endpoint (Slice 3, ~4 hours)
4. Run full test suite (target: all passing)
5. Commit host FS changes to resolve the 161-uncommitted gap

**Works for demo:** Suppliers, items, donors, crypto primitives, settings, DoA, SoD all functional.

### For Pilot: ❌ NO-GO

**Required before pilot:**
1. All demo conditions met
2. 22 missing DocType JSON schemas created
3. Integration tests + Playwright E2E journey
4. `bench migrate` clean on fresh site
5. Adversarial crypto testing
6. Backup/restore verified
7. SSO/2FA configured
8. Performance baseline measured

---

## Next Steps (MVP2 W0 -> W1-W13)

1. ✅ Fix build reproducibility (commit changes, clean stale stubs)
2. ✅ Complete sealed-bid share wrapping + opening ceremony
3. ❓ Create 22 missing DocType JSON schemas (or remove stubs) → **MUST decide: build or remove?**
4. ❓ Extend seed for demo journey → **MUST define target demo scenario**
5. Write MVP2 SCOPE.md with client decisions needed
6. Build MVP2 RTM with atom IDs
7. Produce docs/mvp2/OPEN-QUESTIONS.md for client decisions

---

*Assessment version: 1.0. Evidence at validation-2/SUMMARY.md, validation-2/evidence/*/*, BASELINE.md.*