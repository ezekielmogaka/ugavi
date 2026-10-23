# Resilience Test Plan (GA-060)

## Test Objective
Verify Ugavi degrades gracefully under common failure conditions:
1. cache unavailable (cache down)
2. MariaDB connection pool exhausted
3. Email service down
4. File storage full
5. High latency (>500ms DB queries)
6. Network partition

## Test Environment
- [ ] Staging instance (NOT production)
- [ ] Monitoring enabled (structured logs + health endpoint)
- [ ] Test data seeded: `bench execute ugavi.fixtures.demo_data.run`
- [ ] Baseline performance measured (p50/p95 response times)

---

## Test 1: Cache Unavailable

```bash
# Simulate: stop Valkey
sudo systemctl stop valkey

# Execute: PR creation
bench execute ugavi.tests.resilience.test_valkey_failure

# Verify:
# - PR creation succeeds (falls back to direct DB)
# - Health check reports cache=disconnected (not blocking)
# - Rate limiter skips gracefully (no cache = no rate limiting)

# Restore: start Valkey
sudo systemctl start valkey
```

| Assertion | Expected | Actual | Pass? |
|-----------|----------|--------|-------|
| PR created without Valkey | Success | | [ ] |
| Health check reports degraded | cache=disconnected | | [ ] |
| No 500 errors | True | | [ ] |
| System recovers after Valkey restart | < 30s | | [ ] |

---

## Test 2: MariaDB Connection Pool Exhausted

```bash
# Simulate: open 50 connections (default pool: 25)
for i in $(seq 1 50); do
  bench execute frappe.db.sql --kwargs "{'query':'SELECT SLEEP(10)'}" &
done

# During pool exhaustion, execute: stock query
bench execute frappe.db.get_list --kwargs "{'doctype':'Stock Ledger','filters':{'donor':'DEMO-DONOR-001'},'limit':10}"

# Expected: completes (queued, not failed) within 15s
```

| Assertion | Expected | Actual | Pass? |
|-----------|----------|--------|-------|
| Query completes under pool pressure | < 15s | | [ ] |
| No connection leak | Pool returns to 0 idle after test | | [ ] |
| Error rate | < 1% | | [ ] |

---

## Test 3: Email Service Down

```bash
# Block SMTP port
sudo iptables -A OUTPUT -p tcp --dport 587 -j DROP

# Execute: submit PR (triggers email notification)
bench execute ugavi.tests.resilience.test_email_failure

# Verify: PR submitted successfully despite email failure
# (See test_graceful_degradation.py for programmatic test)

# Restore:
sudo iptables -D OUTPUT -p tcp --dport 587 -j DROP
```

| Assertion | Expected | Actual | Pass? |
|-----------|----------|--------|-------|
| PR submitted despite email failure | Success | | [ ] |
| Error logged (structured logging) | "SMTP connection refused" | | [ ] |
| No 500 errors to user | True | | [ ] |

---

## Test 4: File Storage Full

```bash
# Simulate: fill disk to 95%
# (DO NOT run on shared disk — use dedicated test volume)

# Execute: upload bid attachment
# Expected: error message "Insufficient storage" (not 500 crash)

# Verify:
# - Clean error returned to user
# - Existing files not corrupted
# - Admin alerted (structured log: "disk_full" event)
```

| Assertion | Expected | Actual | Pass? |
|-----------|----------|--------|-------|
| Graceful error on disk full | 400, not 500 | | [ ] |
| Existing files intact | All accessible | | [ ] |
| Alert logged | disk_full event | | [ ] |

---

## Test 5: Slow DB Queries

```bash
# Simulate: add artificial delay to Stock Ledger queries
bench execute frappe.db.sql --kwargs "{'query':'SET GLOBAL long_query_time = 0.5'}"

# Execute: stock balance query
time bench execute frappe.db.sql --kwargs "{'query':'SELECT SUM(incoming_qty) - SUM(outgoing_qty) FROM \\`tabStock Ledger\\` WHERE donor=\\'DEMO-DONOR-001\\''}"

# Expected: completes (may be slow) but does not crash
# Restore:
bench execute frappe.db.sql --kwargs "{'query':'SET GLOBAL long_query_time = 10'}"
```

| Assertion | Expected | Actual | Pass? |
|-----------|----------|--------|-------|
| Query completes without error | True | | [ ] |
| Slow query logged | In slow query log | | [ ] |
| Other endpoints still responsive | Health check 200 OK | | [ ] |

---

## Test 6: Network Partition (Partial)

```bash
# Simulate: block Valkey port (frappe uses Valkey for cache + queue)
sudo iptables -A INPUT -p tcp --dport 6379 -j DROP

# Execute: bid submission
# Expected: succeeds (direct DB, no cache)
# Execute: scheduled job
# Expected: queued (cache unavailable, but job persisted?)
```

| Assertion | Expected | Actual | Pass? |
|-----------|----------|--------|-------|
| API calls succeed without Valkey | True | | [ ] |
| Scheduled jobs queued for retry | Documented | | [ ] |
| Recovery after network restored | < 60s | | [ ] |

---

## Summary

| Test | Status | Notes |
|------|--------|-------|
| cache unavailable | [ ] | |
| DB pool exhausted | [ ] | |
| Email service down | [ ] | |
| File storage full | [ ] | |
| Slow DB queries | [ ] | |
| Network partition | [ ] | |

**Tester:** ___________ | **Date:** ___________ | **Overall:** Pass/Fail