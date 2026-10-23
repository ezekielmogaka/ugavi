# MVP2 — Open Questions for Client Decision

> **Date:** 2026-10-21 | **Author:** Cline QA / Architect
> **Status:** Product decisions D1-D8 and D10 resolved on 2026-10-22. D9 and
> provider-specific credentials remain open. See
> [IMPLEMENTATION.md](./IMPLEMENTATION.md).

---

## Blocking Decisions (must answer before building)

### D1: Finance System of Record
**Blocks:** W5 (Invoices), W6 (Payments), W7 (Budgets), W8 (Donor Reports)

**Question:** Will ERPNext be the authoritative system of record for financial accounting, or will it sync with an external system (e.g., an existing ERP, QuickBooks, SunSystems)?

**Options:**
- (a) ERPNext is the sole finance system — Ugavi manages all GL entries, AR/AP, payments
- (b) External system is the system of record — ERPNext syncs purchase transactions out, receives payment confirmations back
- (c) Hybrid — ERPNext for procurement, external for treasury/banking

**Impact:** Option (a) requires full Chart of Accounts, tax configuration, payment setup. Option (b) requires only procurement-side documents + reconciliation adapters.

### D2: Applicable Tax Regime
**Blocks:** W12 (Tax)

**Question:** Which tax jurisdiction applies? What are the VAT rate(s) and withholding tax rate(s)? Are there any special exemptions for donor-funded procurement?

**Options:**
- (a) Kenya — 16% VAT, 2% / 5% WHT
- (b) Other jurisdiction — please specify
- (c) No tax applicable (donor-exempt)

### D3: E-Invoicing / eTIMS
**Blocks:** W12 (E-Invoicing)

**Question:** Is Kenya eTIMS integration required for supplier invoices? If another jurisdiction, which e-invoicing standard?

**Options:**
- (a) eTIMS (Kenya) — requires KRA sandbox credentials, staging testing
- (b) Other e-invoicing standard — please specify
- (c) No e-invoicing required at this stage

### D4: Applicable Procurement Regulation
**Blocks:** W1 (Bid Security), W2 (Evaluation), W3 (Complaints)

**Question:** Which procurement regulation governs the organization's tendering? This affects bid security thresholds, evaluation rules, standstill periods, and complaint procedures.

**Options:**
- (a) PPOA/PPDA (Kenya Public Procurement and Asset Disposal Act, 2015)
- (b) Other national regulation — please specify
- (c) Internal policy only (no statutory framework)

### D5: Donor Report Formats
**Blocks:** W8 (Donor Reporting Packs)

**Question:** Which donors require reports and in what formats? Each donor typically has a specific narrative + financial template.

**Options:**
- (a) USAID (SF-425, program reports)
- (b) European Union (narrative + financial reports)
- (c) Global Fund (PU/DR)
- (d) GAVI (program + financial)
- (e) World Bank (interim financial reports)
- (f) UN agencies (FACE form)
- (g) Other — please list
- (h) Generic only (no donor-specific templates needed for MVP2)

### D6: Records Retention Periods
**Blocks:** W9 (Retention)

**Question:** How long must procurement and financial records be retained? This may vary by donor.

**Options:**
- (a) 7 years (standard for many jurisdictions)
- (b) 10 years
- (c) Per-donor (e.g., USAID 3 years after final payment, EU 5 years after final payment) — please provide schedule
- (d) Not specified — use 7 years as default

### D7: Payment Channels
**Blocks:** W6 (Payments)

**Question:** Which payment channels will Ugavi use to disburse to suppliers?

**Options:**
- (a) Bank transfer only (EFT/RTGS)
- (b) Mobile money (M-Pesa) only
- (c) Both bank transfer and M-Pesa
- (d) Other — please specify

### D8: SSO Provider
**Blocks:** W10 (Access Control)

**Question:** Does the organization use a central identity provider for Single Sign-On? If so, which protocol?

**Options:**
- (a) Microsoft Azure AD / Entra ID (OIDC)
- (b) Google Workspace (SAML)
- (c) LDAP / Active Directory
- (d) None — use Frappe built-in authentication only
- (e) Other — please specify URL and protocol

### D9: Production Domain
**Blocks:** Cross-cutting (SSL, backups, deployment)

**Question:** What domain name will Ugavi serve from? Where should backups be stored?

**Options:**
- (a) Provided by client — domain: ________, S3 bucket: ________
- (b) Not yet decided — use ugavi.example.com placeholder

### D10: Budget/Grant Structure
**Blocks:** W7 (Budgets)

**Question:** How does the organization structure its budgets? Per donor, per project, per program year, or a combination?

**Options:**
- (a) Per donor per project per year (e.g., "GAVI — Malaria Program — FY2026")
- (b) Per program activity with multiple donors (e.g., "Immunization Campaign")
- (c) Both — budgets roll up to projects with donor attribution
- (d) Other — please describe

---

## Non-Blocking Questions (can proceed, answer when available)

### N1: Supplier Portal Branding
**Question:** Custom logo, color scheme for supplier portal?

### N2: Email Provider
**Question:** SMTP provider for system emails (SendGrid, SES, corporate SMTP)?

### N3: Language Requirements
**Question:** Is English-only acceptable, or are Swahili/French/other translations needed for the supplier portal?

### N4: Mobile Access
**Question:** Do committee members need mobile-friendly scoring/approval?

### N5: Integration Priority
**Question:** Which external system integration is highest priority (if any)?

---

*Document version: 1.0. Client to check applicable options and return.*