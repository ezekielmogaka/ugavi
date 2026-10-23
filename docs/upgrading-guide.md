# Upgrading Ugavi with ERPNext

Ugavi extends ERPNext through app-owned DocTypes, Custom Fields, `doc_events`,
client scripts, scheduled jobs, and Frappe website pages. It does not patch
Frappe/ERPNext files, replace core controllers, or override whitelisted methods.

## Supported versions

| Ugavi | Frappe | ERPNext | Python | MariaDB |
|---|---|---|---|---|
| 0.1.x | 16.52.0 or compatible v16 | 16.51.1 or compatible v16 | 3.14 | 11.4+ |

Exact production image versions are pinned in `Dockerfile` and `apps.json`.
The CI compatibility job also installs the current `version-16` upstream
branches. This catches incompatibilities before a pinned production upgrade.

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

The 2026-10-22 authoritative rehearsal against ERPNext 16.51.1 and Frappe
16.52.0 reported:

- 67 Ugavi DocTypes and 529 ERPNext DocTypes;
- zero compatibility issues and zero missing controllers;
- a successful migration and idempotent setup configuration;
- 57 passing backend tests; and
- `{"message":"pong"}` from the public health endpoint.

After the upgrade rehearsal, validate the seeded business evidence separately:

```bash
make seed                # or: make seed-lokado
make demo-check
make fleet-check
```

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

1. Announce the maintenance window and stop workers/scheduler.
2. Create and verify `bench backup --with-files`.
3. Record current Ugavi, Frappe, and ERPNext image/tag versions.
4. Deploy the already-rehearsed immutable image.
5. Run `bench --site <site> migrate`.
6. Run `bench build --app ugavi` when assets are not image-baked.
7. Start services, then run compatibility and health checks.
8. Complete the workflow smoke tests above.

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
