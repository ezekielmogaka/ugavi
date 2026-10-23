# ADR-006: Hosting and Multi-Tenancy Strategy

> **Status:** ACCEPTED FOR MVP3 FOUNDATION | **Date:** 2026-10-22
> **Author:** Cline Architect
> **Replaces:** None
> **Decision:** One isolated bench per tenant on managed Kenya-hosted infrastructure

## Accepted Decision

- One complete Compose/Frappe bench per tenant; no shared Valkey, workers, site
  volume, database credentials, or Compose project.
- Internal Ugavi DevOps/SRE operates the platform.
- Capacity target: up to 10 tenants at launch and 50 within two years.
- Primary and disaster-recovery locations remain within Kenya.
- Tenant definitions must pass `make tenant-manifest-check`.
- Application code remains shared and versioned, but deployment and upgrades are
  promoted independently per tenant.

---

## Context

Ugavi must serve multiple unrelated customer organizations (tenants) on a platform that:
1. Preserves sealed-bid cryptographic guarantees (ADR-001, ADR-004)
2. Provides strong tenant isolation (no cross-tenant data access)
3. Supports staged upgrades without forcing all tenants to upgrade simultaneously
4. Allows configuration per tenant (branding, workflows, thresholds) without per-tenant code forks
5. Meets data residency requirements
6. Operates with zero core edits, supported extension points only

## Frappe Multi-Site Reality [verified: code inspection + docs]

Frappe uses a **multi-site** (not multi-tenant) architecture:

- **Shared code**: All sites on a bench share Frappe + ERPNext + Ugavi app versions [verified: `bench list-apps`]
- **Separate database**: Each site has its own MariaDB database [verified: `site_config.json` per site]
- **Shared Valkey**: Cache, queue, socketio shared across sites; jobs namespaced by site name [verified: `background_jobs.py` line 133: "namespace job ids to sites"]
- **Separate files**: Each site has its own `sites/<site_name>/` directory [verified: file-system]
- **No built-in tenant concept**: Frappe has no "tenant" abstraction beyond the site

**Critical implication**: Upgrade coordination is bench-wide. When you upgrade apps, ALL sites on that bench receive the new code. This cannot be overridden without core edits.
---

## Options Evaluated

### Option A: Frappe Cloud — Private Bench Group

Use Frappe Cloud private bench. Each tenant gets a site on a shared bench.

[verified: docs.frappe.io/cloud/benches]

| Factor | Assessment |
|--------|------------|
| Isolation | Database-isolated. Valkey shared within bench |
| Upgrade | Bench-wide: all sites share one app version |
| Ops cost | Low: FC manages infra. $25+/mo [source: frappe.io/cloud Pricing] |
| Noisy-neighbor | Medium: shared compute on public bench servers |
| Data residency | Limited: region select for dedicated servers only |
| Sealed-bid risk | FC staff has infra access; upgrade coupling unacceptable |

**Verdict:** ❌ NOT RECOMMENDED. Insufficient isolation for sealed-bid procurement. Upgrade coupling forces all-tenants-at-once.

### Option B: Frappe Cloud — Dedicated Servers

Each tenant gets dedicated AWS EC2 instances (app + DB) on FC.

[verified: docs.frappe.io/cloud/servers]

| Factor | Assessment |
|--------|------------|
| Isolation | Full compute isolation: separate EC2 instances |
| Upgrade | Per-server: independent app versions per tenant |
| Ops cost | High: pay for AWS instances directly |
| Noisy-neighbor | None: dedicated compute |
| Data residency | Full: deploy in chosen AWS region |
| Sealed-bid risk | Per-server isolation. FC has AWS-level access |

**Verdict:** ✅ BEST MANAGED OPTION. Independent upgrades, full isolation, data residency. Cost: per-tenant instance pricing.

### Option C: Self-Hosted Press

Deploy Frappe Press (AGPL) on own infrastructure.

[verified: github.com/frappe/press, 27,805 commits]

| Factor | Assessment |
|--------|------------|
| Isolation | Configurable per Press deployment |
| Upgrade | Per-site versioning [verified: Press README] |
| Ops cost | VERY HIGH: maintain Agent, Ansible, Docker. Need dedicated DevOps |
| Automation | Press API + Agent CLI |

**Verdict:** ❌ NOT RECOMMENDED. Press is complex infrastructure (27k commits). Over-engineered for <50 tenants. AGPL requires legal review.

### Option D: Self-Hosted bench/frappe_docker Multi-Site

Multiple sites on one bench with custom provisioning scripts.

[verified: frappe_docker, bench commands]

| Factor | Assessment |
|--------|------------|
| Isolation | Per-site database. Shared Valkey, code, filesystem |
| Upgrade | Bench-wide: all sites share one app version — CANNOT upgrade independently |
| Ops cost | Medium: manage Docker compose, write scripts |
| Noisy-neighbor | HIGH: shared Valkey, shared workers |
| Sealed-bid risk | Upgrade coupling: cannot upgrade during active sealed-bid ceremony |

**Verdict:** ❌ NOT RECOMMENDED. Upgrade coupling is the killer. Sealed-bid ceremonies span days/weeks — forcing all tenants to upgrade simultaneously is unacceptable.

### Option E: One Bench Per Tenant (Strict Isolation)

Each tenant gets their own complete Frappe bench (Docker compose stack).

| Factor | Assessment |
|--------|------------|
| Isolation | FULL: separate bench, Valkey, workers, scheduler |
| Upgrade | Per-tenant: independent app versions. Canary possible |
| Ops cost | High: 5+ containers per tenant. Linear resource scaling |
| Noisy-neighbor | Low: only host-level contention |
| Data residency | Full: deploy benches in any region |
| Sealed-bid risk | Maximum isolation. Keys never share infrastructure |

**Verdict:** ✅ BEST ISOLATION. Justified by sealed-bid integrity requirements. Linear cost scaling is the tradeoff.

---

## Recommendation

### Primary: Option E (one bench per tenant) via frappe_docker

**Rationale:**
1. **Sealed-bid integrity**: No shared Valkey/workers/scheduler. Physically isolated ceremonies.
2. **Independent upgrades**: Each tenant's bench on different Ugavi/Frappe/ERPNext versions. True canary rollout (MVP3 T7).
3. **Proven pattern**: Current `ugavi-backend` stack already demonstrates single-bench model.
4. **Data residency**: Deploy benches in different regions.
5. **No vendor lock-in**: Own the infrastructure.
6. **Scriptable provisioning**: `bench new-site`, `bench install-app`, `bench migrate` all verified [tested: 2026-10-21].

### Secondary: Option B (Frappe Cloud Dedicated Servers)

For tenants requiring managed infrastructure. Comparable isolation. Acceptable when client prefers managed.

### Anti-Recommendations:
- **Options A, C, D**: All fail the upgrade-coupling test for sealed-bid ceremonies.

---

## Architecture Sketch: Option E

```
┌──────────────────────────────────────────────────────────────┐
│  Host / VM                                                     │
│  ┌── Tenant A ──────────────────┐  ┌── Tenant B ────────────┐│
│  │ bench-a/                      │  │ bench-b/                ││
│  │  sites/tenant-a.example.com/  │  │ sites/tenant-b.org/     ││
│  │  Valkey (separate instance)    │  │ Valkey (separate)        ││
│  │  Scheduler + Workers          │  │ Scheduler + Workers     ││
│  │  MariaDB (separate DB)        │  │ MariaDB (separate DB)   ││
│  └───────────────────────────────┘  └─────────────────────────┘│
│  Shared: Nginx reverse proxy, MariaDB server, monitoring      │
└──────────────────────────────────────────────────────────────┘
```

Key decisions:
- **Separate MariaDB database per tenant** (not separate server). Shared MariaDB server, per-tenant databases.
- **Separate Valkey per bench**: different Valkey DB numbers or container instances.
- **Nginx reverse proxy**: routes `tenant-a.ugavi.app` → bench-a, `tenant-b.ugavi.app` → bench-b.
- **Provisioning**: shared admin bench or host-level script.
---

## Remaining Operational Decisions

This ADR is PROPOSED pending client input on:

| # | Decision | Impact |
|---|----------|--------|
| D1 | Cloud/provider and named Kenya facilities | Terraform/provider implementation |
| D2 | RPO and RTO | Backup frequency and restore architecture |
| D3 | Tenant KMS/HSM ownership | Sealed-bid key hierarchy and rotation |
| D4 | Incident SLA and maintenance windows | On-call and rollout policy |nternal ops |
| D5 | **Billing model**: Per-tenant pricing? Metering hooks (T10)? | Option E no built-in billing |
| D6 | **Customization policy**: Default: configuration only. Confirm no per-tenant code forks | Upgrade safety |

---

## Evidence

| Claim | Source |
|-------|--------|
| Frappe multi-site shares app code | [verified: bench architecture, `sites/` structure] |
| `new-site` creates DB-isolated site | [verified: `bench new-site --help`, 2026-10-21] |
| Jobs namespaced by site name | [verified: `background_jobs.py:133`] |
| FC private bench: shared compute | [verified: docs.frappe.io/cloud/servers] |
| FC dedicated server: separate EC2 | [verified: docs.frappe.io/cloud/servers] |
| Press is AGPL, 27k+ commits | [verified: github.com/frappe/press] |
| Current: single bench, frappe_docker | [verified: `docker ps`, 2026-10-21] |
| tests pass: 15/15, 0.038s | [tested: `bench run-tests --app ugavi`, 2026-10-21] |

---

*ADR-006 version: 1.0. PROPOSED.*