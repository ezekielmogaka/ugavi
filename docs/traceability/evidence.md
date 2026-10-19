# Evidence Registry

> Mapping every claim to its verified source.
> Label: `[verified: path|url]` `[tested: test_id]` `[assumption]`

## Environment
- **Frappe:** 16.52.0 (version-16, commit 4515014) `[verified: bench version]`
- **ERPNext:** 16.51.1 (version-16, commit 5af6561) `[verified: bench version]`
- **Ugavi:** 0.1.0 (main, commit 69c4b15) `[verified: bench version]`
- **Site:** ugavi.localhost `[verified: docker exec bench list-apps]`
- **Database:** MariaDB (devcontainer-mariadb-1) `[verified: docker ps]`
- **Mail:** Mailpit on :1025/:8025 `[verified: docker ps]`
- **Redis:** 2 instances (cache + queue) `[verified: docker ps]`
- **Test runner:** Frappe test runner, 0 tests found `[verified: bench run-tests --app ugavi]`
- **Seed script:** Runs successfully `[verified: bench execute ugavi.scripts.seed_demo.run]`

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

## Security Finding (CRITICAL)
- **TN13**: Sealed Bid Key doctype stores `private_key_pem` as Long Text `[verified: sealed_bid_key.json:19]`. This means an admin or DB-level access can read the private key before bid opening. This violates requirement TN13.