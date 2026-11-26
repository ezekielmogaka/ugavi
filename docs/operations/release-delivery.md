# Ugavi Release Delivery

## Release model

Ugavi is built as one immutable Frappe/ERPNext image. The image contains the
Ugavi application, Solvronix Desk, Python dependencies and compiled assets.
Containers do not install applications or mutate assets during normal startup.

Versioned production references must be:

```text
ghcr.io/<owner>/ugavi:vX.Y.Z
ghcr.io/<owner>/ugavi:sha-<full-commit>
```

Deploy the image by digest for the highest reproducibility. Do not deploy a
moving `latest` reference.

## CI gates

Every push/PR runs:

1. Ruff and Black.
2. Tenant-manifest and pinned-app-version validation.
3. One cached Buildx image build with embedded release/source revision.
4. Trivy `CRITICAL` image gate; the full JSON report is retained as an artifact
   and `HIGH` findings remain visible for review. Unfixed advisories are ignored.
5. Fresh MariaDB/Valkey/Frappe setup.
6. Migration, setup configuration and canonical LOKADO seed.
7. Backend tests, LOKADO/fleet checks and upgrade compatibility check.
8. Playwright browser smoke tests.

Tag pushes create a scanned GHCR image with:

- semantic version and full-commit tags;
- OCI source/revision labels;
- BuildKit provenance;
- BuildKit SBOM;
- a one-year release-manifest artifact containing the digest.

## Required release inputs

Before production deployment, record:

- exact image digest;
- Ugavi commit and release tag;
- Frappe/ERPNext/Solvronix versions;
- tenant/site and Compose project;
- verified database + public/private file backup location and checksum;
- previous known-good image digest and backup as rollback pair;
- named change approver and maintenance window.

Secrets stay in the deployment secret store/environment, never in the image,
release manifest, repository or tenant manifest.

## Production rollout

The release overlay disables runtime migration:

```bash
UGAVI_IMAGE=ghcr.io/<owner>/ugavi \
UGAVI_TAG=vX.Y.Z \
UGAVI_AUTO_MIGRATE=0 \
make release-deploy
```

`release-deploy`:

1. pulls the named image;
2. creates a Bench database + files backup;
3. stops backend, frontend, websocket, scheduler and workers;
4. runs the one-shot `migrator` service;
5. recreates services on the new image;
6. waits for the public health endpoint;
7. runs upstream-compatibility verification.

Before step 1, copy/replicate the existing backup off-host and verify the
restore checksum. The Make target creates a backup, but retention and residency
remain operator responsibilities.

## Canary and tenant promotion

Do not promote every tenant at once. Rehearse against a restored production
copy, deploy one non-busy canary tenant, observe the agreed window, then
promote additional tenants independently.

Production must never run `seed_lokado`, `seed_demo`, `reset-lokado` or
`bootstrap`.

## Rollback

Frappe migrations are forward-only. An old image is not a database rollback.

If the release health or smoke gate fails:

1. Keep traffic stopped and preserve failed-container logs.
2. Restore the verified pre-release database and file backup as one set.
3. Start the previous known-good image digest.
4. Migrate only if the restored backup and image version require it.
5. Re-run health, compatibility and business smoke checks before reopening.

Never point an older application image at a database that completed newer
irreversible migrations.
