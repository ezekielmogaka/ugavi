# P0: Baseline Truth-Check — Ugavi 0.1.0

> **Generated:** 2026-10-20 | **Last verified:** 2026-10-20
> **Methodology:** Every claim verified against installed code, git history, or live API response.

---

## 1. Version Inventory

| Component | Version | Evidence |
|-----------|---------|----------|
| Frappe | 16.52.0 | [verified: `docker exec backend bench version`] |
| ERPNext | 16.51.1 | [verified: `docker exec backend bench version`] |
| Ugavi | 0.1.0 | [verified: bench version output] |
| Python | 3.14.8 | [verified: `python3 --version`] |
| Node.js | 24.22.1 | [verified: `node --version`] |
| MariaDB | 11.4.13 | [verified: `mariadb --version`] |
| Valkey | 8.1-alpine | [verified: `valkey-cli --version`] |
| Nginx | 1.27.5 (1.27-alpine) | [verified: `nginx -v`] |
| Bench CLI | 5.31.0 | [verified: `bench --version`] |
| Docker | 29.9.1 | [verified: `docker --version`] |
| frappe/erpnext image | v16, arm64, 4.35GB | [verified: 349b7f27a6db] |

---

## 2. Test Reconciliation

### 2.1 Tests On-Disk (all Python test functions found by grep "def test_")

| Location | File | Tests | Discovered? |
|----------|------|-------|-------------|
| `ugavi/tests/unit/test_crypto.py` | Inside pkg | 6 | ✅ Yes |
| `ugavi/tests/unit/test_procurement.py` | Inside pkg | 5 | ✅ Yes |
| `ugavi/tests/unit/test_domain.py` | Inside pkg | 12 | ✅ Yes |
| `tests/test_concurrency.py` | Root tests/ | 2 | ❌ No |
| `tests/test_hook_safety.py` | Root tests/ | 3 | ❌ No |
| `tests/test_tenant_isolation.py` | Root tests/ | 3 | ❌ No |
| `tests/test_transactional_boundary.py` | Root tests/ | 3 | ❌ No |
| `tests/test_graceful_degradation.py` | Root tests/ | 3 | ❌ No |
| `tests/e2e/test_procurement_workflow.py` | Root tests/e2e/ | 3 | ❌ No |
| `tests/e2e/test_logistics_workflow.py` | Root tests/e2e/ | 3 | ❌ No |
| `tests/e2e/test_governance_workflow.py` | Root tests/e2e/ | 3 | ❌ No |
| `tests/integration/__init__.py` | Root tests/ | 0 | ❌ No |

**Total on-disk: 46 test functions**
- 23 discovered (inside `ugavi/` package) — all passing ✅
- 23 undiscovered (root-level `tests/`, `tests/e2e/`, `tests/integration/`) — never executed

### 2.2 Why Tests Went From Gap to Discovery

| Date | Commit | Action |
|------|--------|--------|
| Tue Oct 20 | `81ff4c4` | Created `tests/unit/test_crypto.py` (6) + `test_procurement.py` (5) in root `tests/` |
| Tue Oct 20 | `3beaf1b` | Moved tests into `ugavi/tests/unit/` package for proper discovery |
| Tue Oct 20 | `259d9eb` | Added 16 domain tests in `ugavi/tests/unit/test_domain.py` |
| Tue Oct 20 | `0bdd969` | Removed 4 AuditLog-oriented tests (required existing records) |
| Tue Oct 20 | `aff7075` | Removed corrupted test fragments |

**Max known test function count in git history: 27** (inside the `ugavi` package). The "57 tests" claim in earlier audits refers to **57 RTM gaps (GA-006)**, not test function count — a nomenclature confusion.

### 2.3 Execution Results (2026-10-20)

```
Ran 12 integration tests for ugavi — 12 passed ✅  (0.740s)
Ran 11 unspecified-category tests — 11 passed ✅  (0.045s)
Total: 23 discovered, 23 passing (100%)
```

### 2.4 Undiscovered Tests — Assessment

All 23 undiscovered tests at `/tests/` are **valid Frappe TestCase classes** importing from `frappe.tests.utils`. They exist at the wrong directory level — Frappe discovers tests inside `<app>/tests/`, not root `tests/`.

| Undiscovered File | Tests | Valid? | Notes |
|-------------------|-------|--------|-------|
| `test_concurrency.py` | 2 | ✅ | Bid submission + stock race conditions |
| `test_hook_safety.py` | 3 | ⚠️ | 1 FrappeTestCase, 2 standalone functions (broken pattern) |
| `test_tenant_isolation.py` | 3 | ✅ | Donor segregation + stock isolation |
| `test_transactional_boundary.py` | 3 | ✅ | PR rollback + transfer atomicity |
| `test_graceful_degradation.py` | 3 | ✅ | Email/notification failure handling |
| `e2e/test_procurement_workflow.py` | 3 | ⚠️ | Playwright stubs, not runnable without browser |
| `e2e/test_logistics_workflow.py` | 3 | ⚠️ | Playwright stubs, not runnable without browser |
| `e2e/test_governance_workflow.py` | 3 | ⚠️ | Playwright stubs, not runnable without browser |

### 2.5 E2E / Real Browser Smoke

- Playwright config: `tests/e2e/playwright.config.ts` ✅ (exists)
- Playwright installed on host: ❌
- **Real browser login + Desk navigation: NOT EXECUTED**
- API smoke (curl): `/api/method/frappe.ping` → `"pong"` ✅, login → `"Logged In"` ✅
- Static assets via nginx: 4/4 assets return HTTP 200 (CSS 77KB, JS 669KB, etc.)
- Desk HTML: 12 `<link>`/`<script>` tags, login page renders correctly

---

## 3. Anti-Patterns Discovered (P0 scan)

| # | Anti-Pattern | Severity | Status |
|---|-------------|----------|--------|
| AP-1 | `cp -rL` asset copy on every container start | HIGH | ✅ FIXED — compose.yaml+entrypoint use symlinks, not cp |
| AP-2 | PYTHONPATH workaround in compose.yaml | HIGH | ✅ ACCEPTED — only kept on bench execute targets (known limitation) |
| AP-3 | MariaDB root password in compose.yaml plaintext | HIGH | ✅ MITIGATED — uses ${MARIADB_ROOT_PASSWORD:-admin} from .env |
| AP-4 | No resource limits on containers | MEDIUM | ✅ FIXED — all 10 containers have memory limits |
| AP-5 | No TLS termination | MEDIUM | 📝 ACCEPTED — dev-only; production uses reverse proxy |
| AP-6 | 23 undiscovered tests at wrong directory level | HIGH | 📝 ACCEPTED — root tests/*.py need FrappeTestCase migration |
| AP-7 | Duplicate test: tests/unit/test_crypto.py | HIGH | ✅ FIXED — deleted; canonical at ugavi/tests/unit/ |
| AP-8 | Duplicate test: tests/unit/test_procurement.py | HIGH | ✅ FIXED — deleted; canonical at ugavi/tests/unit/ |
| AP-9 | FrappeTestCase methods as standalone functions | MEDIUM | 📝 ACCEPTED — test_hook_safety.py uses pytest-style discovery |
| AP-10 | `ignore_permissions=True` in test setup | LOW | 📝 ACCEPTED — required for test data seeding |
| AP-11 | `frappe.db.commit()` in test setUp | LOW | 📝 ACCEPTED — required for test data seeding |
| AP-12 | doc_events hook registered class's own validate | HIGH | ✅ FIXED — removed; Frappe lifecycle auto-calls validate() |

---

## 4. Summary

| Metric | Value |
|--------|-------|
| Total DocTypes registered | 32 (all have controllers) |
| Test functions on disk | 46 |
| Test functions discovered by bench | 23 |
| Test functions passing | 23 (100%) |
| Test functions undiscovered | 23 (need migration into package) |
| E2E tests (Playwright) | 9 stubs, 0 executable |
| Real browser validation | NOT DONE |
| Anti-patterns identified | 11 |

## 5. P1 Gate Criteria

Before starting P2:
- [ ] Migrate 23 undiscovered tests into `ugavi/tests/` and make them pass
- [ ] Remove duplicate test files
- [ ] Install Playwright on host, run real browser smoke
- [ ] All 11 anti-patterns addressed or documented as accepted