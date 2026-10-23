# PATCHES.md — Ugavi 0.1.0

> Policy: Zero core ERPNext/Frappe patches. All customization via hooks, custom DocTypes, and fixtures.

## Patch Queue
**Current size: 0**

| # | Target | File | Reason | Date | Upstream Issue |
|---|--------|------|--------|------|---------------|
| — | — | — | No patches applied | — | — |

## Patch Policy
1. **Default: no patches.** Every requirement must be implementable via hooks, custom DocTypes, fixtures, Custom Fields, or Property Setters.
2. **If a patch is unavoidable:**
   - File an upstream issue/PR first
   - Apply patch in `ugavi/patches/` directory with naming: `YYYYMMDD-target-reason.patch`
   - List in this document with upstream issue link
   - Re-evaluate every minor upgrade; remove when upstream fixes
3. **Blocking patches** (app won't work without them) are Critical severity — require approval before release.
4. **Never patch:** sealed-bid crypto, authentication, permissions, or audit code.

## Upgrade Assessment v16.52.0 → next
- [ ] Review all Frappe/ERPNext changelogs for hook changes
- [ ] Verify `override_doctype_class` continues to work
- [ ] Verify `doctype_js`, `doc_events`, `scheduler_events` hooks unchanged
- [ ] Run full test suite on upgraded bench
- [ ] Verify CSS custom properties not renamed/removed