# Admin Guide — Ugavi 0.1.0

## Overview
Ugavi is a donor-segregated procurement and logistics system on Frappe v16.

## System Requirements
- Python 3.14+
- MariaDB 11.8+
- Valkey 8+
- Node.js 24+
- Frappe Bench v16

## Installation

### Docker (Recommended for Dev)

```bash
git clone <repo-url> && cd ugavi
make setup          # Creates containers, installs apps, runs migrations
make seed           # Seeds LOKADO demo data (canonical)
make seed-lokado    # Seeds LOKADO demo data (alias for make seed)
```

**URL:** http://ugavi.localhost:8080 | Login: `Administrator` / `admin`

### Local Bench Installation

```bash
# Prerequisites: Python 3.14+, MariaDB 11.8+, Valkey 8+, Node.js 24+
pip install frappe-bench
bench init frappe-bench --frappe-branch version-16
cd frappe-bench
bench get-app ugavi <repo-path>
bench new-site ugavi.localhost
bench --site ugavi.localhost install-app ugavi
bench start
```

## Configuration

### Ugavi Procurement Settings (Single DocType)
```
bench console
frappe.db.set_single_value("Ugavi Procurement Settings", "default_currency", "USD")
frappe.db.set_single_value("Ugavi Procurement Settings", "key_rotation_days", 90)
frappe.db.set_single_value("Ugavi Procurement Settings", "rate_limit_bids_per_hour", 3)
```

### User & Role Setup
| Role | Permissions |
|------|-------------|
| Procurement Officer | Create/edit PR, Tender, Bid Opening |
| Procurement Manager | Approve PR, Tender (DoA matrix bound) |
| Logistics Officer | Stock Ledger, Donor Warehouse, Transfer |
| Fleet Manager | Vehicle, Trip, Fuel, Spare Parts |
| Asset Manager | Asset Register, Movement, Disposal |
| Auditor | Read-only all modules, verify hash chain |
| Supplier (Portal) | Submit bids, check PQ status (portal only) |

### Donor Segregation
- Each document has a `donor` field (Link to Donor DocType)
- User Permissions enforce donor-level filtering
- Stock balances are donor-segregated (no cross-donor mixing)
- Inter-Donor Transfer requires bilateral approval

## Scheduled Tasks
| Task | Frequency | Purpose |
|------|-----------|---------|
| Check vehicle service due | Weekly | Flags vehicles overdue for service |
| Flag inactive suppliers | Monthly | Marks suppliers with no bids in 12 months |
| Asset verification reminder | Monthly | Creates asset verification tasks |
| Key rotation check | Daily | Flags stale sealed-bid keys |

## Backup & Recovery
```
bench backup --with-files        # Includes uploaded bid docs
bench restore <backup-file>      # Requires downtime
```

RTO target: <4 hours | RPO: <1 hour (frequent MariaDB binlog backups recommended)

## Monitoring
- Health endpoint: `GET /api/method/ugavi.scripts.health_check.get_health`
- Structured logs: `~/frappe-bench/logs/ugavi-structured.log`
- Hash chain verification: `bench execute ugavi.governance.services.hash_chain.verify_chain --kwargs "{'doctype':'Tender','docname':'TENDER-001'}"`

### Docker Monitoring
```bash
docker compose ps                     # container health
docker compose logs backend --tail=100
make seed-check                       # validate data integrity
make test                             # run test suite
```
## Troubleshooting

| Issue | Resolution |
|-------|------------|
| JS scripts not loading | Run `bench build --app ugavi` |
| Workspaces not appearing | Check `module/workspace/` directories exist |
| Sealed-bid key rotation fails | Manual: `bench execute ugavi.governance.services.key_rotation.flag_stale_keys` |
| Rate limit blocking legitimate bids | Reset: `bench execute ugavi.governance.services.rate_limiter.RateLimiter().reset` |
| Hash chain broken | Investigate audit log tampering; restore from verified backup |
| Docker containers not starting | `make clean && make setup` |
| Seed data stale | `make reset-demo` (reinstalls + reseeds) |
| LOKADO data missing | `make seed` or `make seed-lokado` (idempotent) |