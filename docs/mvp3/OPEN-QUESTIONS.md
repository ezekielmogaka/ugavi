# MVP3 Open Questions

> **Date:** 2026-10-21 | **Source:** MVP3 W0 analysis
> **Status:** Hosting model, scale, residency and operator decisions resolved on
> 2026-10-22. See [PLATFORM.md](./PLATFORM.md). KMS, RPO/RTO, provider and SLA
> decisions remain open.

---

## BLOCKING: Gate Failure

**MVP2 gate is NOT met** (see docs/mvp2/GO-NO-GO.md). W1-W13 are specified but NONE are built. Per MVP3 W0 rules:

> "Verify MVP1 and MVP2 gates are met. If not, STOP and report."

The following M3 decisions are blocked until MVP2 workstreams are built.

---

## Hosting Decision (ADR-006)

| # | Question | Options | Impact |
|---|----------|---------|--------|
| H1 | Self-hosted (Option E: one bench per tenant) or managed (Option B: FC Dedicated Servers)? | (a) Option E, (b) Option B, (c) Hybrid | All T1-T12 design |
| H2 | Expected tenant count at launch / 6mo / 2yr? | Number | Resource sizing for Option E |
| H3 | Data residency: which regions? | (a) Africa-only, (b) Multi-region, (c) Any | Infrastructure placement |
| H4 | Who operates the platform? | (a) Internal DevOps team, (b) Managed service provider, (c) Frappe Cloud (Option B) | Staffing, cost |
| H5 | Accept bench-wide upgrade coupling as a constraint? | Yes/No | If Yes: options A, C, D become viable but sealed-bid ceremonies are at risk |

---

## Tenant Model

| # | Question | Options | Impact |
|---|----------|---------|--------|
| T1 | Maximum tenants per bench/server? | Number | Capacity planning (T9) |
| T2 | Per-tenant customization policy? | (a) Configuration only, (b) Limited server scripts, (c) None | Upgrade safety |
| T3 | Tenant isolation level required? | (a) Database only, (b) Full bench isolation, (c) Full server isolation | Architecture |
| T4 | SSO per tenant? | (a) Yes (OIDC/SAML), (b) No (Frappe auth only), (c) Per-tenant choice | T6 |
| T5 | Tenant-admin vs platform-admin separation? | (a) Strict (no platform access to tenant data), (b) Break-glass with audit, (c) Platform can read all | T6 access model |
| T6 | Tenant data exit format? | (a) Frappe backup archive, (b) Open format (CSV/JSON), (c) Both | T8 export design |

---

## Cryptography & Security

| # | Question | Options | Impact |
|---|----------|---------|--------|
| C1 | Per-tenant key hierarchy or shared master? | (a) Separate key hierarchy per tenant, (b) Shared master with derived keys | T3 design |
| C2 | Who holds tenant key material? | (a) Tenant admin only, (b) Platform operator with break-glass, (c) External HSM/KMS | T3 implementation |
| C3 | Key rotation frequency? | (a) Per tender, (b) Quarterly, (c) Annual, (d) On-demand only | T3 procedures |
| C4 | Penetration test scope? | (a) Multi-tenant surface only, (b) Full Ugavi + ERPNext, (c) Infra + app | Security scope |
| C5 | Accept platform operator DB access risk? | Yes/No | Break-glass design |
| C6 | Cryptographic library approval process? | (a) FIPS 140-2, (b) FIPS 140-3, (c) None | crypto library selection |

---

## Operations & Lifecycle

| # | Question | Options | Impact |
|---|----------|---------|--------|
| O1 | Backup retention period? | (a) 30 days, (b) 90 days, (c) 1 year, (d) Per donor schedule | T8 backup design |
| O2 | RPO (Recovery Point Objective)? | (a) 1 hour, (b) 24 hours, (c) 0 (sync replication) | T8 backup frequency |
| O3 | RTO (Recovery Time Objective)? | (a) 1 hour, (b) 4 hours, (c) 24 hours | T8 restore process |
| O4 | Upgrade canary policy? | (a) 1 canary, wait 24hr, (b) 10% then 50%, (c) Manual per-tenant | T7 upgrade rollout |
| O5 | Tenant offboarding with legal hold? | (a) Suspend but retain data, (b) Export then delete, (c) Both | T8, T10 lifecycle |
| O6 | Incident notification SLA? | (a) 1 hour, (b) 24 hours, (c) Per contract | T9 observability |
| O7 | Status page required? | (a) Public with incident history, (b) Tenant-only dashboard, (c) None | T9 operations |

---

## Billing & Commercial (not building billing — design seams only)

| # | Question | Options | Impact |
|---|----------|---------|--------|
| B1 | Billing model? | (a) Per-tenant flat fee, (b) Per-user, (c) Per-document/storage, (d) Hybrid | T10 metering hooks |
| B2 | Metering dimensions? | Users, documents, storage, API calls, email volume | T10 counters |
| B3 | Free trial / sandbox tenant? | (a) Yes (time-limited), (b) Yes (feature-limited), (c) No | T12 onboarding |

---

## Compliance & Legal

| # | Question | | Options |
|---|----------|---|---------|
| L1 | Regulatory framework? | | (a) Kenya Data Protection Act, (b) GDPR, (c) Both, (d) Other |
| L2 | Auditor access to tenant data? | | (a) Tenant-controlled, (b) Platform-facilitated, (c) Direct DB access |
| L3 | DPA (Data Processing Agreement) template needed? | | (a) For counsel review, (b) Client provides, (c) Not needed |
| L4 | SOC 2 / ISO 27001 certification required? | | (a) Required for launch, (b) Plan for Year 1, (c) Not required |
| L5 | Retention: legal hold process? | | (a) Manual flag by platform admin, (b) Automated by donor contract dates |

---

## Decision Batching

These questions should be answered in this order:

**Batch 1 (immediate — unblocks T1-T4):** H1, H2, H4, T2, T3, C1, C2  
**Batch 2 (before building):** H3, H5, T4, T5, C3, C4, C5  
**Batch 3 (design only):** O1-O7, B1-B3, L1-L5  
**Batch 4 (before GA):** T1, T6, C6, L4

---

*Document version: 1.0. All questions are for client/counsel. No assumptions made.*