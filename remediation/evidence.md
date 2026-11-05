# R1 Evidence — Running Environment ✅ COMPLETE

## Site Status: RUNNING

```
$ curl -s -H 'Host: ugavi.localhost' http://localhost:8080/api/method/frappe.ping
{"message":"pong"}

$ curl -s -H 'Host: ugavi.localhost' http://localhost:8080/api/method/login \
    -d 'usr=Administrator&pwd=admin'
{"message":"Logged In","home_page":"desk","full_name":"Administrator"}
```

## Installed Apps

```
$ bench --site ugavi.localhost list-apps
frappe  16.52.0 UNVERSIONED
erpnext 16.51.1 UNVERSIONED
ugavi   0.1.0   UNVERSIONED
```

## Migrate Status: CLEAN

```
$ bench --site ugavi.localhost migrate
...
Queued rebuilding of search index for ugavi.localhost
```

## Test Results ✅ 23/23 PASSING

```
$ make test
Ran 12 integration tests — 12 passed ✅
Ran 11 unit tests — 11 passed ✅
Total: 23/23 passing (100%)
```

### Integration Tests (12/12)
- ✔ test_cannot_delegate_to_self (ApprovalDelegation)
- ✔ test_end_date_before_start_should_fail (UgaviContract)
- ✔ test_expiry_check_within_window (UgaviContract)
- ✔ test_retention_cannot_exceed_100 (UgaviContract)
- ✔ test_key_doc_has_no_private_key_field (SealedBidKey)
- ✔ test_key_doc_requires_three_distinct_officers (SealedBidKey)
- ✔ test_scoring_with_missing_criterion (SupplierScorecard)
- ✔ test_weighted_scoring_basic (SupplierScorecard)
- ✔ test_same_role_rejected (SegregationOfDuties)
- ✔ test_approve_waiver (Waiver)
- ✔ test_approve_without_approver_fails (Waiver)
- ✔ test_reject_waiver (Waiver)

### Unit Tests (11/11)
- ✔ test_accepts_valid_chain (DelegationOfAuthority)
- ✔ test_rejects_duplicate_roles (DelegationOfAuthority)
- ✔ test_rejects_empty_chain (DelegationOfAuthority)
- ✔ test_different_secrets (SealedBidCrypto)
- ✔ test_split_and_reconstruct (SealedBidCrypto)
- ✔ test_two_shares_cannot_reconstruct (SealedBidCrypto)
- ✔ test_cannot_override (ProcurementRulesEngine)
- ✔ test_engine_defaults (ProcurementRulesEngine)
- ✔ test_requires_prequalified (ProcurementRulesEngine)
- ✔ test_threshold_rule_applies_within_range (ProcurementRulesEngine)
- ✔ test_threshold_rule_no_upper_bound (ProcurementRulesEngine)

## DocType Inventory — 32/32 Synced

```
SELECT name, module, istable FROM tabDocType WHERE module IN
  ('Procurement','Governance','Tendering','Compliance','Logistics')
  ORDER BY module, name;

Compliance      4 DocTypes    Budget Encumbrance, Donor Profile, Donor Rule, Three Way Match
Governance      5 DocTypes    Approval Delegation, Audit Log, Delegation of Authority,
                               Segregation of Duties, Waiver
Logistics       5 DocTypes    Donor Warehouse, Inter Donor Transfer, Inter Donor Transfer Item,
                               Monthly Stock Report, Stock Ledger
Procurement    15 DocTypes    Bid, Bid Opening Detail, Bid Opening Record, Contract Document,
                               Contract Milestone, Evaluation Committee, PR Item,
                               Prequalification Category, Prequalification Document,
                               Purchase Requisition, Sealed Bid Key, Supplier Prequalification,
                               Supplier Scorecard, Ugavi Contract, Ugavi Procurement Settings
Tendering       3 DocTypes    Addendum, Tender, Tender Document
```

## API Verification

```
$ curl -s -H 'Host: ugavi.localhost' -X POST \
    http://localhost:8080/api/method/login \
    -d 'usr=Administrator&pwd=admin'
{"message":"Logged In","home_page":"desk","full_name":"Administrator"}

$ curl -s -H 'Host: ugavi.localhost' -b cookie \
    'http://localhost:8080/api/resource/Ugavi%20Contract?limit=1'
→ PermissionError (DocType exists and is resolvable; DocPerm not yet configured)
```

## Services

| Service | Image | Status |
|---------|-------|--------|
| MariaDB | mariadb:11.4 | Healthy |
| Valkey | valkey/valkey:8.1-alpine | Healthy |
| Mailpit | axllent/mailpit:v1.33.0 (pinned) | Healthy |
| Backend | frappe/erpnext:v16 | Running |

## Ports

- Frappe API: http://localhost:8080 (Host: ugavi.localhost)
- Mailpit UI: http://localhost:8026

## Key Fixes Applied

1. Created compose.yaml with Docker dev environment
2. Fixed ugavi module discovery: nested .pth file pointing to /home/frappe/frappe-bench/apps
3. Fixed DocType module names in JSONs to match modules.txt (Procurement, Governance, etc.)
4. Renamed Contract → Ugavi Contract to avoid ERPNext CRM collision
5. Renamed doctype folder contract → ugavi_contract to match DocType name
6. Fixed entrypoint.sh to use gunicorn (bench start requires Procfile)
7. Added missing controller classes for Approval Delegation, Waiver, Segregation of Duties
8. Added Document subclass to ContractDocument child doctype
9. Added before_save validators for Contract, Appointment Delegation, Segregation of Duties
10. Added approve()/reject() methods to Waiver controller
11. Fixed Supplier Group creation in test helper
12. Enabled tests with allow_tests=true
13. PYTHONPATH added to bench commands via -e flag
14. Entrypoint now skips migrate on restart (uses sentinel file)

## Reproducibility

From zero:
1. `make setup` → starts all services, creates site, installs apps, starts Frappe
2. `make seed` → seeds demo data
3. `make test` → runs test suite (23/23 passing)
4. `make stop` → stops all services