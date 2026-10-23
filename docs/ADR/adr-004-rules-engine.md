# ADR-004: Procurement Rules Engine — Strategy Pattern

**Status:** Accepted  
**Date:** 2026-10-19  
**Deciders:** Ugavi team

## Context

Procurement method must be auto-determined based on:
- Estimated value thresholds (< 200K, 200K-499K, ≥ 500K KES)
- Donor-specific rules (some donors mandate open tender at lower thresholds)
- Category-specific rules (some categories like pharmaceuticals may have special rules)
- Effective-date tracking for threshold changes
- Waiver-based bypass (logged, approved)

## Decision

**Strategy pattern with a rules engine pipeline.**

### Architecture:
```
Purchase Requisition.validate()
  → rules_engine.determine_procurement_method(doc)
    → load_thresholds()          # from Ugavi Procurement Settings
    → load_donor_rules(donor)    # from Donor Rule DocType
    → load_category_rules(cat)   # from Item Group rules (future)
    → resolve_conflicts()        # most restrictive wins
    → check_waiver()             # if method overridden, validate waiver
  → set doc.procurement_method
```

### Key design choices:
1. **Most restrictive rule wins**: If donor mandates Open Tender at 300K and global threshold is 500K, the donor rule takes precedence.
2. **Effective-date aware**: Thresholds carry `valid_from`/`valid_to` so historical PRs retain their original method.
3. **Waiver bypass**: Only via approved Waiver DocType with full audit trail.
4. **Testable in isolation**: Each rule source is independently testable.

## Consequences

- **Positive:** Extensible — new rule sources added as new strategy implementations. Tested [tested: TestProcurementRulesEngine — 5 tests pass].
- **Negative:** Complexity increases with each new rule source. Need careful ordering of rule evaluation.
- **Upgrade risk:** Zero — pure Python, no core ERPNext overrides.

## References
- `[verified: ugavi/procurement/services/rules_engine.py]`
- `[verified: ugavi/tests/unit/test_procurement.py — 5 tests pass]`
- `[verified: ugavi/procurement/doctype/ugavi_procurement_settings/ugavi_procurement_settings.json]`