# ADR-005: UI Extension Strategy

**Status:** Accepted  
**Date:** 2026-10-19  
**Deciders:** Ugavi team

## Context

Ugavi needs client-side form logic, role-based workspaces, dashboards, print formats, and a supplier portal. All must be upgrade-safe (no core ERPNext UI edits).

## Decision

**Use Frappe v16's native UI extension mechanisms exclusively.**

### Mechanisms chosen:
| Mechanism | Use Case | Upgrade Risk |
|-----------|----------|-------------|
| **doctype_js** (hooks.py) | Client-side form logic for PR, Prequal, Tender, Bid, BOR, Evaluation Score, Evaluation Minutes, Bid Evaluation Summary | Zero (Frappe core hook) |
| **Workspace JSON** | Role-based landing pages per module | Zero (Frappe DocType) |
| **Dashboard + Number Card JSON** | Procurement/stocks/fleet/asset KPIs | Zero (Frappe DocType) |
| **Print Format JSON** | BOR PDF, Contract, GRN, Stock Report | Zero (Frappe DocType) |
| **Web Page DocType + website_route_rules** | Supplier portal: bid submission, PQ renewal, invoices | Zero (Frappe framework) |
| **Frappe UI (Vue 3 + Tailwind)** | Design system foundation — custom components built on Frappe UI primitives | Zero (same stack as Frappe Desk) |

### Explicitly NOT used:
- **Separate frontend framework** (React, Angular, etc.): Would duplicate Frappe's authentication, permissions, and API layer. Upgrade risk is high.
- **Core file edits**: Never edit ERPNext or Frappe JS/CSS files.
- **Custom CSS overrides targeting `.erpnext-*` selectors**: Brittle across upgrades. Use Frappe's Property Setter and Custom Field UI options instead.

### Design System:
- **Source of truth**: Frappe UI design tokens (colors, spacing, typography, shadows)
- **Brand theming**: Per-site via `website_theme` and `navbar_settings`
- **Light/dark**: Frappe v16 supports dark mode natively [verified: Frappe 16.52.0 — Desk Settings → Appearance]
- **Density**: Use Frappe's default spacing; don't override grid densities
- **i18n**: Frappe's translation system (CSV in `translations/` directory) with English default + Swahili scaffold

## Consequences

- **Positive:** All extensions live in `ugavi/public/` and `ugavi/ugavi/workspace/` — clean separation from core. Upgrade-safe by design.
- **Negative:** Dependent on Frappe UI framework decisions. If Frappe migrates away from Vue 3 (unlikely in v16 lifecycle), custom components would need porting.
- **Risk:** Low — Frappe v16 is an LTS-like release with Vue 3 + Tailwind as the official desk framework.

## References
- `[verified: Frappe 16.52.0 — desk uses Vue 3 + Tailwind]`
- `[verified: hooks.py — doctype_js, doc_events, scheduler_events]`
- `[verified: Frappe docs — Workspace, Dashboard, Print Format DocTypes]`