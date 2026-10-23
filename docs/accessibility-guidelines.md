# Accessibility Guidelines — Ugavi 0.1.0 (GA-036)

## Accessibility Measurement Framework

Ugavi targets WCAG 2.1 Level AA compliance for all Desk UI and supplier portal pages.

### Standards Applied
| Standard | Version | Target Level |
|----------|---------|-------------|
| WCAG | 2.1 | AA |
| ARIA | 1.2 | Authoring Practices |
| EN 301 549 | V3.2.1 | EU Public Procurement |

### Audit Checklist

#### Perceivable (WCAG 2.1 — Principle 1)
- [ ] 1.1.1 Non-text Content: All images have alt text
- [ ] 1.2.1 Audio-only/Video-only: Not applicable (no media in MVP)
- [ ] 1.3.1 Info and Relationships: Form labels properly associated
- [ ] 1.3.2 Meaningful Sequence: Tab order follows visual order
- [ ] 1.3.3 Sensory Characteristics: No instructions relying solely on color/shape
- [ ] 1.4.1 Use of Color: Error states use both color + icon/text
- [ ] 1.4.3 Contrast (Minimum): Text contrast ≥ 4.5:1 (≥ 3:1 for large text)
- [ ] 1.4.4 Resize Text: 200% text resize without loss of content
- [ ] 1.4.5 Images of Text: No images used for text content

#### Operable (WCAG 2.1 — Principle 2)
- [ ] 2.1.1 Keyboard: All interactive elements keyboard-accessible
- [ ] 2.1.2 No Keyboard Trap: Focus can move away from any element
- [ ] 2.2.1 Timing Adjustable: No session timeouts without warning
- [ ] 2.3.1 Three Flashes: No content flashes >3x/second
- [ ] 2.4.1 Bypass Blocks: Skip navigation link available
- [ ] 2.4.2 Page Titled: All pages have descriptive titles
- [ ] 2.4.3 Focus Order: Focus order is logical and predictable
- [ ] 2.4.4 Link Purpose: Links have meaningful text (no "click here")
- [ ] 2.4.5 Multiple Ways: Multiple ways to find content
- [ ] 2.4.6 Headings and Labels: Descriptive headings and form labels
- [ ] 2.4.7 Focus Visible: Keyboard focus indicator is visible

#### Understandable (WCAG 2.1 — Principle 3)
- [ ] 3.1.1 Language of Page: `lang` attribute set on all HTML
- [ ] 3.2.1 On Focus: No context change on focus
- [ ] 3.2.2 On Input: No context change without warning
- [ ] 3.2.3 Consistent Navigation: Navigation consistent across pages
- [ ] 3.3.1 Error Identification: Form errors clearly identified
- [ ] 3.3.2 Labels or Instructions: All inputs have labels
- [ ] 3.3.3 Error Suggestion: Error messages suggest correction
- [ ] 3.3.4 Error Prevention (Legal/Financial): Confirmation for bid submission

#### Robust (WCAG 2.1 — Principle 4)
- [ ] 4.1.1 Parsing: Valid HTML (no duplicate IDs, proper nesting)
- [ ] 4.1.2 Name, Role, Value: ARIA roles for custom controls
- [ ] 4.1.3 Status Messages: Dynamic content announced to screen readers

### Frappe v16 Accessibility Support
| Feature | Frappe Support | Notes |
|---------|---------------|-------|
| Semantic HTML | ✅ Frappe UI v2 (Bootstrap 5) | Uses proper heading hierarchy |
| ARIA labels | ✅ Built into form controls | Custom JS may need additional labels |
| Keyboard navigation | ✅ Tab order follows layout | Custom dialogs need manual focus management |
| Color contrast | ⚠️ Bootstrap defaults need verification | Run contrast checker on branded themes |
| Screen reader | ⚠️ Requires testing with NVDA/VoiceOver | Dynamic tables need live region announcements |
| Focus management | ⚠️ Custom dialogs, modals | Bootstrap modals handle basic focus trapping |
| Form validation | ✅ Server + client side | Error messages displayed inline |
| Responsive design | ✅ Bootstrap 5 responsive grid | Test at 320px, 768px, 1024px, 1440px |

### Measurement Tools

```bash
# Automated testing
npm install -g pa11y-ci
pa11y-ci --sitemap https://ugavi.example.com/sitemap.xml

# Contrast checking
npm install -g axe-cli
axe https://ugavi.example.com --rules color-contrast

# Screen reader testing (manual)
VoiceOver (macOS): Cmd+F5
NVDA (Windows): Free download
```

### Current Scorecard (MVP)
| Area | Status | Notes |
|------|--------|-------|
| Semantic HTML | ✅ | Frappe UI v2 |
| Keyboard navigation | ⚠️ | Awaiting manual audit |
| Color contrast | ⚠️ | Needs theme verification |
| Screen reader compatibility | ⚠️ | Not yet tested |
| Form accessibility | ✅ | Frappe form framework |
| Responsive design | ✅ | Bootstrap 5 |
| Language attribute | ✅ | Frappe sets lang |
| Focus indicators | ⚠️ | Bootstrap defaults |
| ARIA labels | ⚠️ | Custom JS scripts need review |

**Next:** Manual accessibility audit by Q3 2026. Remediate critical findings before v0.2.