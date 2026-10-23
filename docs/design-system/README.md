# Ugavi Design System

> Token-based theming layer for Frappe v16 Desk. Upgrade-safe: CSS custom properties only, no deep DOM selectors.

## Design Tokens
See `ugavi/public/css/ugavi-theme.css` for full token definitions:
- **Brand:** `--ugavi-brand` (teal #0d9488)
- **Surfaces:** `--ugavi-surface`, `--ugavi-surface-alt`
- **Semantic colors:** `--ugavi-success`, `--ugavi-warning`, `--ugavi-critical`, `--ugavi-info`
- **Spacing:** 4-point grid (xs/sm/md/lg/xl/2xl)
- **Radius:** sm/md/lg/full
- **Elevation:** card, card-hover, modal
- **Motion:** fast (150ms), normal (250ms), respects `prefers-reduced-motion`

## Components
| Component | CSS Class | File |
|-----------|-----------|------|
| Status Chips | `.ugavi-chip--{draft,published,awarded,closed,critical,success}` | `ugavi-components.css` |
| Timeline | `.ugavi-timeline` + `.ugavi-timeline-item` | `ugavi-components.css` |
| Approvals Inbox | `.ugavi-approvals-inbox` + `.ugavi-approval-card` | `ugavi-components.css` |
| Skeleton Loading | `.ugavi-skeleton--{text,title,card}` | `ugavi-components.css` |
| Empty States | `.ugavi-empty-state` | `ugavi-components.css` |
| Chart Palette | `.ugavi-chart-palette` (8 colorblind-safe colors) | `ugavi-components.css` |

## Modes
- **Light:** Default token values
- **Dark:** `@media (prefers-color-scheme: dark)` + `.dark-mode` class
- **Compact density:** `.ugavi-density--compact` on container
- **Reduced motion:** `@media (prefers-reduced-motion: reduce)` — zero animation

## White-Label & Donor Branding
- **Brand accent:** Override `--brand-accent-color` CSS variable or set in System Settings
- **Donor report logo:** `.ugavi-donor-report__logo` with max-height 60px
- **Print formats:** Use `ugavi-donor-report` class with donor accent border

## Using in Custom Pages
```html
<div class="ugavi-branded">
  <div class="ugavi-approvals-inbox">
    <div class="ugavi-approval-card">
      <div class="ugavi-approval-card__header">
        <span class="ugavi-chip ugavi-chip--published">Published</span>
      </div>
    </div>
  </div>
</div>
```

## Fonts
Self-hosted only. Default: `"Inter", system-ui, -apple-system, sans-serif`. No external CDN calls from a procurement system.

## Upgrade Risk Assessment
| Area | Risk | Mitigation |
|------|------|-----------|
| CSS custom properties | Low | Frappe stable APIs |
| Bootstrap 5 class overrides | Low | `.ugavi-*` namespace |
| Deep DOM selectors | **Not used** | Policy: never target `.erpnext-*` or `.frappe-*` |
| v16 → v17 migration | Low | Token-only layer; re-test contrast + layout |