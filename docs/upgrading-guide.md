# Upgrading Ugavi with ERPNext

Ugavi extends ERPNext through app-owned DocTypes, Custom Fields, `doc_events`,
client scripts, scheduled jobs, and Frappe website pages. It does not patch
Frappe/ERPNext files, replace core controllers, or override whitelisted methods.

## Supported versions

| Ugavi | Frappe | ERPNext | Python | MariaDB |
|---|---|---|---|---|
| 0.1.x | 16.54.0 (rehearsed) | 16.53.0 (pinned/rehearsed) | 3.14 | 11.4+ |

Production images pin Frappe/ERPNext/Solvronix app versions in `Dockerfile` and
`apps.json`. CI rebuilds the exact custom image and tests the pinned versions;
it does not rely on mutable `version-16` app branches.

## Extension contract

- App-owned DocTypes use Frappe's conventional controller discovery.
- ERPNext transactions are extended with prefixed `ugavi_*` Custom Fields.
- Cross-document behavior uses additive `doc_events`.
- Business rules remain in Python controllers/services, never only in browser code.
- Desk styling targets only `ugavi-*` classes.
- Website styling uses shared design tokens and app-owned markup.
- No `override_doctype_class`, `override_whitelisted_methods`, monkey patches, or
  files shadowing Frappe/ERPNext modules.
- Custom DocType names must not collide with ERPNext-owned DocTypes.

These invariants are enforced by:

```bash
bench --site <site> execute ugavi.scripts.check_upstream_compatibility.run
```

## Upgrade rehearsal

Never upgrade production first. Restore the latest production backup into an
isolated staging environment running the proposed Frappe and ERPNext versions.

```bash
# In the staging bench after restoring the production backup:
bench --site <staging-site> execute ugavi.scripts.check_upstream_compatibility.run
bench --site <staging-site> migrate
bench build --app ugavi
bench --site <staging-site> run-tests --app ugavi
curl -fsS http://localhost:8000/api/method/frappe.ping
```

For the Docker demo, `make upgrade-check` runs the same compatibility,
migration, app-test, and health sequence.

The current baseline is ERPNext 16.53.0 and Frappe 16.54.0. The
[evidence registry](traceability/evidence.md) records the latest rehearsal:

- 67 Ugavi DocTypes and 529 ERPNext DocTypes;
- zero compatibility issues and zero missing controllers;
- a successful migration and idempotent setup configuration;
- passing integration and unit suites (15 + 62 at this checkpoint); and
- `{"message":"pong"}` from the public health endpoint.

After the upgrade rehearsal, validate the seeded business evidence separately
(with `make demo-check` and `make fleet-check`, or re-seed with `make seed-lokado`):

For mounted local source use `make dev-config`, `make dev-seed`, `make dev-test`
and `make dev-check`, then `UGAVI_BASE_URL=http://ugavi.localhost:8000 make e2e`.
These are development checks, not an immutable-image upgrade rehearsal.
No passing v16 rehearsal guarantees compatibility with v17 or a newer v16 tag.

Both acceptance commands must return `"ready": true` with no issues. Browser
Playwright tests are a separate host-side UI gate and are not evidence produced
by `make upgrade-check`.

Validate these workflows using non-production records:

1. Create and approve a Purchase Requisition.
2. Publish a restricted and an open tender.
3. Submit a sealed bid through a supplier account.
4. Complete the three-officer opening ceremony.
5. Award a bid and verify Purchase Order plus contract creation.
6. Submit a Purchase Receipt and verify supplier evaluation creation.
7. Submit same-donor stock movement and reject unauthorized cross-donor movement.
8. Open the supplier portal at mobile and desktop widths.

## Production rollout

Use the immutable release workflow in
[release-delivery.md](operations/release-delivery.md):

1. Announce the maintenance window and stop traffic/write activity.
2. Create and verify `bench backup --with-files`, then copy it off-host.
3. Record the current/previous image digests and the pre-release backup.
4. Deploy the already-rehearsed immutable image tag/digest.
5. Run the one-shot `migrator` service before application services.
6. Recreate backend/frontend/workers from the image; assets are already baked.
7. Run compatibility and health gates.
8. Complete the workflow smoke tests above, then observe the canary window.

Do not run seed scripts on production.

## Rollback

Frappe migrations are forward migrations; checking out an old tag and running
`bench migrate` is not a database downgrade.

If rollout validation fails:

1. Stop all application processes.
2. Redeploy the previously recorded application image.
3. Restore the pre-upgrade database and files backup as one consistent set.
4. Start services and verify health before reopening access.

Keep the failed environment isolated for diagnosis. Never point old application
code at a database that has already completed newer irreversible migrations.
