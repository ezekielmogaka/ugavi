# MVP3 Isolated Tenant Platform Foundation

> **Decision date:** 2026-10-22  
> **Status:** architecture and validation foundation delivered; infrastructure rollout is not complete.

## Deployment model

Each customer receives an independent Compose/Frappe bench with:

- unique Compose project;
- unique site hostname;
- separate MariaDB data and credentials;
- separate Valkey, workers and scheduler;
- separate site files and backups;
- independent application upgrade window.

The initial capacity target is 10 tenants, scaling to 50 within two years. Both
primary and disaster-recovery locations must be Kenya-hosted. The internal
Ugavi DevOps/SRE team operates the platform.

## Tenant manifest gate

Copy `deploy/tenants.example.json`, provide one record per tenant, and run:

```bash
make tenant-manifest-check TENANT_MANIFEST=deploy/tenants.production.json
```

The gate rejects:

- duplicate site names, Compose projects, ports or tenant identifiers;
- non-Kenya location identifiers;
- identical primary and disaster-recovery locations;
- invalid tenant slugs;
- manifests above the currently validated 50-tenant ceiling.

Secrets never belong in this manifest. Each tenant receives a separate,
secret-managed environment file based on `.env.example`.

## Provisioning sequence

1. Validate the tenant manifest.
2. Allocate Kenya-hosted primary and DR resources.
3. Create a tenant-specific secret store entry and environment file.
4. Start the stack with its unique Compose project.
5. Run `make upgrade-check` against the tenant site before activation.
6. Restore approved configuration or seed only non-production demonstration data.
7. Enrol privileged users in TOTP and set `UGAVI_ENFORCE_2FA=1`.
8. Run health, backup and restore acceptance checks.

## Upgrade policy

- Build one immutable image per release.
- Rehearse migration against a restored tenant data copy.
- Promote to one canary tenant with no active sealed-bid opening.
- Observe the agreed canary window.
- Promote tenants independently; never upgrade every tenant simultaneously.
- Keep the previous image and verified pre-migration backup for rollback.

## Residual decisions

Implementation of production infrastructure remains blocked on:

- cloud/provider and named Kenya facilities;
- RPO/RTO and backup retention;
- KMS/HSM ownership and rotation;
- incident notification SLA;
- monitoring/status-page provider;
- tenant offboarding and legal-hold procedure.
