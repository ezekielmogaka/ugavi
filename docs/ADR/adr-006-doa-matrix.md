# ADR-006: Delegation of Authority (DoA) Matrix

**Status:** Accepted  
**Date:** 2026-10-19  
**Deciders:** Ugavi team

## Context

Approval authority for procurement must follow a delegation matrix: who can approve what amount, for which department, funded by which donor. This is a legal/compliance requirement for donor-funded procurement.

## Decision

**Multi-dimensional approval chain resolution at PR submission time.**

### Architecture:
```
Purchase Requisition.validate()
  → delegation_of_authority.resolve_approval_chain(amount, department, donor)
    → Query Delegation of Authority DocType sorted by amount_limit DESC
    → Filter by department match (or NULL = all departments)
    → Filter by donor match (or NULL = all donors)
    → Build approval chain: [L1 approver, L2 approver, …, final approver]
    → Apply Approval Delegation overrides (temporary delegation)
    → Check Segregation of Duties: requester ≠ approver ≠ payer
  → set doc.approval_chain
```

### Key design:
1. **Amount thresholds**: configurable limits per role (L1 up to 500K, L2 up to 5M, etc.)
2. **Department scoping**: NULL means "all departments" — specific department takes precedence
3. **Donor scoping**: NULL means "all donors" — specific donor takes precedence
4. **Approval Delegation**: Temporary re-assignment (with expiry) — validated for no self-delegation
5. **Segregation of Duties**: Same user cannot be requester, approver, and payer

### Consequences:
- **Positive:** Flexible, auditable, tested [tested: TestDelegationOfAuthority — 3 tests pass; TestSegregationOfDuties — 1 test passes].
- **Negative:** Complex queries at validation time. Need index on (amount_limit, department, donor) for performance.
- **Upgrade risk:** Zero — custom DocType, no core overrides.

## References
- `[verified: ugavi/procurement/services/delegation_of_authority.py]`
- `[verified: ugavi/tests/unit/test_crypto.py — TestDelegationOfAuthority]`
- `[verified: ugavi/governance/doctype/delegation_of_authority/delegation_of_authority.json]`