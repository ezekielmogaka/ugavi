# ADR-008: Solvronix Ecosystem Use

**Status:** Accepted  
**Date:** 2026-11-25  
**Deciders:** Ugavi team

## Context

The Solvronix organization publishes four relevant public resources:

- [Solvronix-Desk](https://github.com/Solvronix/Solvronix-Desk)
- [Solvronix-Pilot-Connector](https://github.com/Solvronix/Solvronix-Pilot-Connector)
- [Edvronix-App](https://github.com/Solvronix/Edvronix-App)
- [Solvronix-Docs](https://github.com/Solvronix/Solvronix-Docs)

They solve different problems. Installing each because the publisher and visual
language are familiar would introduce unnecessary applications, data domains,
external services and upgrade surface.

## Decision

### Use Solvronix Desk

Install and pin Solvronix Desk for:

- ERPNext/Frappe Desk and login theming;
- Theme Studio publishing;
- light/dark/auto themes;
- configurable typography, density, focus, high contrast and colour-blind
  presentation;
- command palette, workspace navigation, notifications, progressive forms and
  other Desk-specific interactions.

Ugavi pins the same release as the upstream v3.2.0 repository revision and
configures native Theme Settings through `setup_config.py`.

### Bridge published tokens to Website and Supplier Portal

The LOKADO public website and supplier portal remain Ugavi-owned Frappe portal
pages. They do not import Solvronix Desk layout, sidebar or component CSS.

Ugavi may reuse only the published, public Theme Studio variables through
`solvronix_desk.api.get_theme_css` so brand and accent changes propagate
without an asset rebuild. LOKADO-specific fallback tokens remain in Ugavi,
therefore the site continues to render if Solvronix is unavailable.

This gives Desk, login, public website and supplier portal one brand system
without coupling public DOM to Solvronix's Desk selectors.

### Do not install Solvronix Pilot Connector by default

Pilot Connector is an optional internal staff aid. It is not part of the public
website or supplier experience and must not be enabled silently.

Before a pilot, the owner must document and approve:

- the external Pilot service's data processing, retention, hosting region and
  incident terms;
- procurement/privacy/security approval;
- exact allowed Frappe roles;
- excluded sensitive records and workflows;
- notification forwarding behaviour (name and recipient are sent to Pilot);
- operational owner, cost ceiling, disable procedure and evidence that Pilot
  continues to use each user's ERPNext permissions.

Phone alerts remain disabled unless separately approved. The connector's
read-only implementation does not remove external-service or disclosure risk.

### Do not install Edvronix App in Ugavi

Edvronix targets Pakistani K-12 school management and requires Frappe
Education v17+. It introduces school-specific custom fields, fee/reporting
flows, CNIC/B-Form data and workspace overrides that are outside Ugavi's
humanitarian procurement, logistics, fleet and asset scope.

Treat it as a reference implementation only. Reuse ideas through design
review or deliberate code extraction, not by adding the app to the site.

### Use Solvronix Docs as a reference

Solvronix Docs is not an application and is not installed. Use it together
with the Solvronix Desk README and Theme Studio guide for configuration,
upgrade validation and operator training.

## Performance and UI rules

1. The public token bridge must use the public display-only theme endpoint and
   fail open to Ugavi's static LOKADO tokens.
2. No Solvronix Desk CSS selector or JavaScript runtime is loaded onto public
   pages.
3. Public/supplier navigation, content hierarchy and forms remain Ugavi-owned.
4. Theme updates must preserve server-rendered fallbacks, so the first paint is
   usable and branded without waiting for JavaScript.
5. Interactive transitions respect `prefers-reduced-motion`; focus rings,
   contrast and mobile navigation remain testable independently.
6. No AI button is exposed to Guest or Supplier Portal users.
7. Pilot, if later enabled, is restricted to explicitly approved staff roles.

## Consequences

- **Positive:** one colour/typography/motion system across internal and public
  experiences; Solvronix remains supported and replaceable; public pages keep
  their independent information architecture.
- **Positive:** no unrelated Education domain or external AI service is added
  by default.
- **Trade-off:** public pages maintain Ugavi-owned templates rather than using
  Solvronix Desk's Desk layouts directly.
- **Operational requirement:** Theme Studio publication and upgrade checks
  must include the public website and supplier portal, not only Desk.

## References

- Solvronix Desk README (v3.2.0), including Theme Studio, auto colours, density,
  dark mode, motion and WCAG controls.
- Solvronix Pilot Connector README (v0.1.7), including read-only scope,
  per-user permissions and notification forwarding.
- Edvronix README, including Pakistan/K-12 scope, Education v17+ requirement
  and custom fields.
- Frappe Forum: `Solvronix Desk — Modern white-label theme for Frappe v16`
  (announcement, 2026-06-15).
- Ugavi verification: `apps.json` pins Solvronix Desk `v3.2.0`.
