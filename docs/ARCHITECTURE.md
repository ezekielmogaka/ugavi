# Ugavi — Enterprise SCM on ERPNext
## Architecture Decision Record

**Version:** 0.1.0 | **Date:** 2026-10-19  
**ERPNext:** v16.51.1 (version-16) | **Frappe:** v16.52.0 (version-16)

## 1. High-Level Architecture

```
┌──────────────────────────────────────────────────────────┐
│              ugavi (Custom Frappe App)                     │
│  procurement│tendering│logistics│assets│fleet             │
│  governance│compliance│integrations│analytics│portal      │
├──────────────────────────────────────────────────────────┤
│         Frappe Framework v16 (upstream mirror)            │
├──────────────────────────────────────────────────────────┤
│         ERPNext v16 (upstream mirror)                     │
├──────────────────────────────────────────────────────────┤
│  MariaDB 10.11 │ Redis 7 │ Python 3.12 │ Node 20          │
└──────────────────────────────────────────────────────────┘
```

## 2. Repository Strategy

| Remote | URL | Purpose |
|--------|-----|---------|
| origin/erpnext | github.com/ugavi/erpnext | Our fork |
| upstream/erpnext | github.com/frappe/erpnext | Official |
| origin/frappe | github.com/ugavi/frappe | Our fork |
| upstream/frappe | github.com/frappe/frappe | Official |

- `upstream-mirror/version-16`: fast-forward-only from upstream
- `ugavi/version-16`: minimal patch queue (target: zero patches)
- `main`: the ugavi app itself

## 3. Extension Points (non-negotiable)
All customization via hooks.py:
- doc_events, override_doctype_class, override_whitelisted_methods
- scheduler_events, fixtures, Custom Fields, Property Setters
- Client/Server Scripts promoted into code, Workflows
- Print Formats, Reports, custom DocTypes, patches.txt
- **NEVER edit core in place**
## 4. Ugavi Module Layout

```
ugavi/ugavi/
├── procurement/     # PR, PO, prequal, rules engine, tenders, bids, contracts
├── tendering/       # Tender docs, bid submission, sealed opening, evaluation
├── logistics/       # Stock ledger, GRN, donor warehouse, monthly reports
├── assets/          # Asset register, movement, disposal, verification
├── fleet/           # Vehicles, allocation, trip log, fuel, spares
├── governance/      # DoA, SoD, audit log, waivers, hash chain
├── compliance/      # Donor profiles, budget encumbrance, 3-way match
├── integrations/    # SMS (abstract + Africa's Talking), eTIMS stub, SSO
└── analytics/       # Dashboards, saved reports
```

## 5. Design Patterns

| Pattern | Where Used |
|---------|------------|
| Strategy | Procurement rules engine |
| State Machine | Tenders, PRs, POs via Frappe Workflows |
| Adapter | SMS, eTIMS, KMS providers |
| Observer | Audit logging, notifications |
| Factory | Procurement method selection |

## 6. Milestones

| M0 | Environment + repo scaffold + CI |
| M1 | Procurement core: rules engine, PR, PO, prequal, DoA |
| M2 | Sealed-bid: encryption, Shamir's SSS, 3-officer opening |
| M3 | Logistics: stock/assets/fleet with donor segregation |
| M4 | Governance, analytics, portal, integrations |
| M5 | Hardening, tests, docs, demo script |

## 7. Explicit Assumptions
1. Sub-200K: RFQ/Direct (configurable) - flag for confirmation
2. Print formats: placeholders until client templates provided
3. eTIMS: stub only; full integration needs KRA registration
4. SMS: Africa's Talking stub; provider interface allows swap
5. KES: "KES 1,234,567.00" format; configurable