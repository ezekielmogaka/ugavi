# R0: TRIAGE — Reproduction & Reclassification

> **Engineer:** Principal Frappe remediation
> **Date:** 2026-10-19 | **Source:** validation/FINDINGS.md
> **Method:** Each finding reproduced independently with command-line evidence.

---

## F-001 | Test Suite Unrunnable

**Reproduction:**
```
$ python3 -m pytest ugavi/tests/ 2>&1 | tail -3
ERROR ugavi/tests/unit/test_procurement.py
!!!!!!!!!!!!!!!!!!! Interrupted: 9 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 9 errors in 0.10s ===============================

$ python3 -m pytest tests/ 2>&1 | tail -3
collected 0 items
============================ no tests ran in 0.01s =============================
```
Root cause: No Frappe bench installed. `import frappe` fails universally.
57 test functions across 13 files (some duplicated between tests/ and ugavi/tests/).

**Verdict:** CONFIRMED — CRITICAL

---

## F-002 | 17 DocType Directories Missing .json Schema Files

**Reproduction:** 32 JSON files found. 17 directories confirmed missing .json:

| Module | DocType | Has .py? | Has .json? | Status |
|--------|---------|----------|------------|--------|
| Fleet | vehicle | Yes | No | MISSING |
| Fleet | vehicle_allocation | Yes | No | MISSING |
| Fleet | fuel_log | Yes | No | MISSING |
| Fleet | spare_parts_issue | Yes | No | MISSING |
| Fleet | trip_log | Yes | No | MISSING |
| Assets | asset_register | Yes | No | MISSING |
| Assets | asset_movement | Yes | No | MISSING |
| Assets | asset_disposal | Yes | No | MISSING |
| Assets | asset_verification | Yes | No | MISSING |
| Tendering | bid_submission | No | No | EMPTY SHELL |
| Tendering | clarification | No | No | EMPTY SHELL |
| Tendering | coi_declaration | Yes | No | MISSING |
| Tendering | bid_evaluation_summary | Yes | No | MISSING |
| Tendering | standstill_period | Yes | No | MISSING |
| Procurement | procurement_rules | No | No | EMPTY SHELL |
| Procurement | contract_retention | Yes | No | MISSING |
| Procurement | contract_bond | Yes | No | MISSING |

**Verdict:** CONFIRMED — CRITICAL (count: exactly 17)

---

## F-003 | Fleet Services Empty

```
$ ls -la ugavi/fleet/services/
total 0
-rw-r--r--  1 ezekiel.mogaka  staff  0 Oct 20 00:13 __init__.py
```
No fleet_report.py, no monthly report implementation.

**Verdict:** CONFIRMED — CRITICAL

---

## F-004 | bid_submission & clarification Empty Shells

Empty directories with only 0-byte __init__.py. No .py, no .json. + procurement_rules also empty.

**Verdict:** CONFIRMED — HIGH (empty shells affect T2 atom -> FAIL)

---

## F-005 | JS Client Scripts Duplicated

Doctype-level JS files differ from public/js/ versions. hooks.py only references public/js/ copies.

**Verdict:** CONFIRMED — HIGH

---

## F-006 | No Running Frappe Instance

No bench, no site, no MariaDB. All runtime validation blocked.

**Verdict:** CONFIRMED — MEDIUM

---

## F-007 | RTM Doesn't Map to Client Brief

RTM uses PR1-PR10, TN1-TN14 etc. Client brief has 35 atoms (P1-D1).

**Verdict:** CONFIRMED — MEDIUM

---

## F-008 | python-jose Unused Dependency

Declared in pyproject.toml, never imported.

**Verdict:** CONFIRMED — LOW

---

## F-009 | requires-python >=3.14 vs 3.13

Python 3.14 not yet released. Running 3.13.13.

**Verdict:** CONFIRMED — LOW

---

## F-010 | Empty __init__.py Files

81 zero-byte files (verified: 81, not 85).

**Verdict:** CONFIRMED with REFINEMENT — LOW (count: 81)

---

## F-011 | Duplicate Test Structure

Both tests/ and ugavi/tests/ exist.

**Verdict:** CONFIRMED — LOW

---

## F-012 | DocType Count Refined

32 complete JSON schemas (not 29). 17 missing.

**Verdict:** REFINED — 32 complete, 17 missing

---

## Re-grade: Tendering Atoms T1-T7

| Atom | Previous | Re-grade | Reason |
|------|----------|----------|--------|
| T1 | PARTIAL | PARTIAL | Tender DocType has .json+.py |
| T2 | FAIL | **FAIL** | bid_submission EMPTY SHELL |
| T3-T7 | PARTIAL | PARTIAL | Code exists, not runtime-verified |

---

## Reclassification: D1

D1 = documentation deliverable ("suggested simplified version"). Reclassified from FAIL to BLOCKED/DEFERRED — not a software defect, needs a written proposal.

---

**All 12 findings CONFIRMED. 3 refinements (counts + D1 reclassification). Proceeding to R1.**