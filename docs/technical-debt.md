# Ugavi Technical Debt Register

> Created from MVP1 review findings. Each item has an owner, severity, and target.

---

## Active Issues

### 1. Asset Category: Hardcoded Select Options
- **Finding:** Asset Register `asset_category` uses a `Select` field with hardcoded options instead of linking to Item Group or a configurable DocType
- **Impact:** Adding a new category requires schema change + migrate
- **Fix:** Change `asset_category` fieldtype from `Select` to `Link` → `Item Group`, or create a standalone `Asset Category` DocType
- **Severity:** Medium
- **Target:** MVP2

### 2. Asset Register: salvage_value Field Access Error
- **Finding:** `AssetRegister._calculate_depreciation()` accesses `self.salvage_value` which does not exist on the current schema
- **Root cause:** The `Asset Register` DocType has `purchase_value` and `useful_life_years` fields referenced in the Python class but those fields don't exist in the current DB schema either — the JSON schema only has `purchase_price`, `current_value`, `serial_number`, and other basic fields
- **Fix:** Either add `salvage_value`, `purchase_value`, `useful_life_years` fields to Asset Register schema, or remove the depreciation calculation
- **Severity:** High (causes ValidationError on save)
- **Target:** MVP1.1

### 3. Vehicle Naming: vehicle_names Workaround
- **Finding:** The old seed used a `vehicle_names` dict to map vehicle IDs because Vehicle naming rule was ambiguous
- **Root cause:** Vehicle DocType has `vehicle_name:Data(reqd)` but no autoname or naming_rule set
- **Fix:** Set `naming_rule` to "By script" or "field:vehicle_name"; remove `vehicle_names` workaround
- **Severity:** Low
- **Target:** MVP1.1

### 4. Module Rename: "Asset Management" → "Assets"
- **Finding:** Module was renamed from "Asset Management" / "asset_management" to "Assets" / "assets" but old pycache files remain at `ugavi/asset_management/__init__.py` (container only)
- **Impact:** Import paths may resolve differently on fresh install vs container
- **Fix:** Add migration patch to clean up stale module references; rebuild Docker image
- **Severity:** Low
- **Target:** MVP1.1

### 5. DelegationOfAuthority: ImportError in Container
- **Finding:** `ugavi.governance.doctype.delegation_of_authority` module not importable in current Docker image
- **Status:** Needs Docker rebuild to pick up code changes
- **Severity:** High (blocks DoA seeding)
- **Target:** MVP1.1 (Docker rebuild)

### 6. PurchaseRequisition.validate Attribute Error
- **Finding:** Container uses old Python class without `validate` attribute
- **Status:** Needs Docker rebuild with updated `purchase_requisition.py`
- **Severity:** High
- **Target:** MVP1.1

### 7. Sealed Bid Key: Hard/Soft
- **Finding:** Bid opening currently uses stubs (no real OTP/SMS integration)
- **Impact:** Sealed bid officer verification not enforceable
- **Fix:** Implement real OTP generation + email/SMS delivery
- **Severity:** Medium
- **Target:** MVP2

### 8. Batch/Expiry Donor-Scoping (S2)
- **Finding:** Items don't carry batch or expiry date in the donor-warehouse context
- **Impact:** Cannot track which donor batch is closest to expiry for FIFO
- **Fix:** Add batch_no + expiry_date to Stock Ledger child table; add batch-level donor scoping
- **Severity:** Medium
- **Target:** MVP2

---

## Resolved

| Issue | Resolution | Date |
|-------|-----------|------|
| Seed in fixtures/ folder | Moved to `ugavi/scripts/seed_demo.py` | 2026-10-21 |
| No production guard | Added `_check_production()` | 2026-10-21 |
| No schema validation | Added `_validate_doc()` + `_STRICT_FIELDS` | 2026-10-21 |
| Hard-coded supplier prequal status | Now uses runtime Supplier Prequalification DocType | 2026-10-21 |
| Missing seed-check | Added `make seed-check` target + `seed_check.py` | 2026-10-21 |
| No DEMO.md | Created with seeded record references | 2026-10-21 |