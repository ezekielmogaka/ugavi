# ADR-001: Multi-Tenancy Model

**Status:** Accepted  
**Date:** 2026-10-19  
**Deciders:** Ugavi team (AI-assisted analysis)

## Context

Ugavi serves procurement, tendering, logistics, and asset management for donor-funded projects. Multiple donors fund the same organization. The system must isolate donor data, budgets, stock, and sealed-bid keys appropriately.

Frappe v16 supports multi-site (separate MariaDB schema per site, shared codebase) [verified: Frappe 16.52.0 bench]. ERPNext supports multiple Companies within a site.

## Options Considered

| Model | Description | Isolation | Ops Cost | Upgrade Risk |
|-------|-------------|-----------|----------|-------------|
| A | Single tenant, donors as dimensions | Weak (same DB) | Lowest | Lowest |
| B | One site, multiple Companies | Medium (ERPNext Company isolation) | Low | Low |
| C | Site per tenant on shared bench | Strong (separate DB) | Medium | Medium |
| D | Bench/container per tenant | Strongest | Highest | Highest |

## Decision

**Model A (single tenant, donors as dimensions) for MVP.**

Rationale:
1. Ugavi currently serves a single organization with multiple donor-funded projects. Model A provides the right balance of donor data isolation (via Donor dimension on every DocType) without the operational overhead of managing N sites.
2. The codebase already uses a `donor` Link field on PR, Tender, Contract, and Stock Ledger — reinforcing the dimension approach.
3. Sealed-bid keys are per-tender, not per-tenant — so donor isolation is sufficient for crypto boundaries.
4. Frappe User Permissions can enforce donor-level data visibility per user [verified: Frappe docs, User Permissions feature].

## Future Path

If multiple unrelated organizations join the platform, evaluate Model C (site per tenant). This gives:
- Separate MariaDB schema per organization
- Per-site sealed-bid key domains — strongest crypto isolation
- Independent backup/restore per organization
- Compliance fit for donors that require physical data separation

## Tenant-Safe Code Requirements (apply now)

Even under Model A, all code must be tenant-safe for future migration:
1. No hard-coded site names
2. All caches keyed by site (`frappe.local.site`)
3. No cross-site Valkey key assumptions
4. No shared secrets between tenants
5. All settings in per-site DocTypes (Ugavi Procurement Settings, Donor Profile, etc.)

## Consequences

- **Positive:** Lower ops cost, simpler upgrade coordination, faster MVP delivery.
- **Negative:** Weaker isolation than Model C/D. Upgrade to Model C requires data migration (extract donor-specific rows into new sites).
- **Risk:** If a new organization joins before Model C readiness, donor-dimension isolation must be rigorously enforced via User Permissions.

## References
- `[verified: Frappe 16.52.0 bench — bench new-site, bench backup, bench restore]`
- `[verified: Ugavi codebase — donor field on PR, Tender, Contract, Stock Ledger]`
- `[verified: Frappe User Permissions — docs.frappe.io]`