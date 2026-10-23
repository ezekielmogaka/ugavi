# Backup & Restore Test Procedure (GA-056)

## Test Objective
Verify that Ugavi backups can be reliably restored with:
- All donor-segregated data intact
- Hash chains preserved
- Sealed-bid key shares intact
- RTO (Recovery Time Objective) < 4 hours
- RPO (Recovery Point Objective) < 1 hour

## Prerequisites
- [ ] Access to bench environment with `bench` command
- [ ] At least 2x free disk space of current DB size
- [ ] Admin credentials for site
- [ ] Test window with no production users

## Test Steps

### 1. Create Test Data (pre-backup)
```bash
# Seed known test data
bench execute ugavi.fixtures.demo_data.run

# Create 1 PR, 1 Tender, 1 Bid, 1 Stock Entry, 1 Asset
bench execute ugavi.tests.test_data.create_backup_test_data

# Record pre-backup state
bench execute frappe.db.sql --kwargs "{'query':'SELECT COUNT(*) as cnt FROM \\`tabPurchase Requisition\\`'}"
bench execute frappe.db.sql --kwargs "{'query':'SELECT COUNT(*) as cnt FROM \\`tabStock Ledger\\`'}"
```

### 2. Perform Backup
```bash
# Full backup with files
time bench backup --with-files

# Record backup file path + size
ls -lh ~/frappe-bench/sites/*/private/backups/
```

- [ ] Backup created successfully
- [ ] Backup file > 0 bytes
- [ ] Duration recorded (benchmark for RTO)

### 3. Simulate Failure
```bash
# Drop a table (TEST ONLY — never in production!)
bench execute frappe.db.sql --kwargs "{'query':'DROP TABLE IF EXISTS \\`tabTestBackupTarget\\`'}"

# Delete a file
rm ~/frappe-bench/sites/*/private/files/test_backup_file.pdf
```
- [ ] Data loss simulated

### 4. Restore from Backup
```bash
# Stop bench
bench stop

# Restore (record duration)
time bench restore <backup-file-path>

# Restart
bench start

# Run migrations
bench migrate

# Build assets
bench build --app ugavi
```

- [ ] Restore completed successfully
- [ ] Duration recorded (must be < 4h for RTO)
- [ ] Bench starts without errors

### 5. Verify Restoration

```bash
# Verify data counts match pre-backup
bench execute frappe.db.sql --kwargs "{'query':'SELECT COUNT(*) as cnt FROM \\`tabPurchase Requisition\\`'}"
# Expected: matches pre-backup count

bench execute frappe.db.sql --kwargs "{'query':'SELECT COUNT(*) as cnt FROM \\`tabStock Ledger\\`'}"
# Expected: matches pre-backup count

# Verify hash chains intact
bench execute ugavi.governance.services.hash_chain.verify_chain \
  --kwargs "{'doctype':'Tender','docname':'DEMO-TENDER-001'}"

# Verify sealed-bid keys
bench execute frappe.db.sql \
  --kwargs "{'query':'SELECT name, status FROM \\`tabSealed Bid Key\\` WHERE tender=\\'DEMO-TENDER-001\\''}"

# Verify donor segregation
bench execute ugavi.tests.test_tenant_isolation.TestDonorStockIsolation

# Health check
curl http://localhost:8000/api/method/ugavi.scripts.health_check.get_health
```

- [ ] PR count matches
- [ ] Stock Ledger count matches
- [ ] Hash chain: `intact: true`
- [ ] Sealed-Bid Key: status = Active
- [ ] Donor segregation tests pass
- [ ] Health check returns 200 OK

### 6. Measure RTO/RPO
| Metric | Target | Actual | Pass? |
|--------|--------|--------|-------|
| RTO (restore time) | < 4 hours | ________ | [ ] |
| RPO (data loss) | < 1 hour | ________ | [ ] |
| Backup size | < 10GB | ________ | [ ] |
| Hash chain intact | No breaks | ________ | [ ] |

### 7. Cleanup
```bash
# Remove test data
bench execute ugavi.tests.test_data.cleanup_backup_test_data
```

## Pass Criteria
- [ ] All data restored without loss
- [ ] All hash chains intact
- [ ] All sealed-bid keys valid
- [ ] Donor segregation maintained
- [ ] RTO < 4 hours
- [ ] Health check passes

**Tester:** ___________ | **Date:** ___________ | **Pass/Fail:** ___________