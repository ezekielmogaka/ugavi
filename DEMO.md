# Ugavi Demo

The comprehensive, maintained demo documentation for Ugavi is:
- **[Presenter Runbook](docs/DEMO.md)** — complete scene-by-scene walkthrough with credentials,
  narrator scripts, validation checkpoints, troubleshooting, and MVP2 readiness.
- [LOKADO MVP1 functional-requirements tour](docs/demo/LOKADO-DEMO-TOUR.md)
- [Supplier portal journey](docs/demo/SUPPLIER-JOURNEY.md)

## Quick rehearsal

```bash
make setup
make seed                # canonical LOKADO seed (alias: seed-lokado)
make demo-check          # verify data integrity
make fleet-check         # verify fleet reconciliation
make backup-demo         # safety net: dump to backups/
make e2e
```

## Quick URLs

- Desk and login: <http://localhost:8080>
- Supplier portal: <http://localhost:8080/supplier/dashboard>
- Mailpit: <http://localhost:8026>

All seeded users use `Ugavi@2024` (development-only). Administrator: `Administrator` / `Ugavi@2024`.

**For full demo credentials, scene scripts, and presenter notes, see
[docs/DEMO.md](docs/DEMO.md).**
