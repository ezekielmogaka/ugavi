# Runbook — Ugavi 0.1.0

## Daily Checks
| Time | Check | Command | Expected |
|------|-------|---------|----------|
| 08:00 | Scheduler status | `bench doctor` | All scheduled jobs green |
| 08:00 | Health endpoint | `curl http://localhost:8000/api/method/ugavi.scripts.health_check.get_health` | 200 OK, db=connected, cache=connected |
| 09:00 | Failed jobs | `bench execute frappe.utils.scheduler.get_scheduler_status` | No failed jobs in last 24h |
| 10:00 | Hash chain integrity | `bench execute ugavi.governance.services.hash_chain.verify_chain --kwargs "{'doctype':'Tender','docname':'latest'}"` | intact: true |

## Weekly Checks
| Day | Check | Command |
|-----|-------|---------|
| Monday | Disk usage | `df -h ~/frappe-bench` — alert if >80% |
| Monday | Backup verification | `ls -la ~/frappe-bench/sites/*/private/backups/` — last backup <24h old |
| Wednesday | Key rotation | `bench execute ugavi.governance.services.key_rotation.flag_stale_keys` |
| Friday | Stale suppliers | `bench execute ugavi.scripts.scheduled_tasks.flag_inactive_suppliers` |

## Monthly Checks
| Check | Command |
|-------|---------|
| Asset verification | `bench execute ugavi.scripts.scheduled_tasks.generate_asset_verification_reminder` |
| Vehicle service | `bench execute ugavi.scripts.scheduled_tasks.check_vehicle_service_due` |
| Log rotation | Check `~/frappe-bench/logs/ugavi-structured.log*` — <10MB current, 7 backups max |
| Database index review | `bench mariadb` then `SHOW INDEX FROM tabPurchase Requisition;` |

## Incident Response

### Hash Chain Break Detected
1. Identify broken document: `verify_chain` output shows `broken_at` index
2. Isolate affected doctype + docname
3. Check audit log entries for tampering
4. Restore from last verified backup
5. Notify security officer

### Sealed-Bid Key Compromised
1. Immediately rotate key: `bench execute ugavi.governance.services.key_rotation.check_and_rotate --kwargs "{'tender_name':'TENDER-XXX'}"`
2. Notify all 3 key share holders → re-distribute new shares
3. Flag all bids on that tender for re-encryption
4. Log security incident in structured logging

### Rate Limit Denial (Legitimate Bid Blocked)
1. Reset rate limit: `bench execute ugavi.governance.services.rate_limiter.RateLimiter().reset --kwargs "{'action':'bid:TENDER-XXX','identifier':'SUP-YYY'}"`
2. If persistent, increase limit: `frappe.db.set_single_value("Ugavi Procurement Settings", "rate_limit_bids_per_hour", 10)`

### Database Corruption
1. Stop bench: `bench stop`
2. Restore from backup: `bench restore <latest-backup>`
3. Verify hash chains: run verify_chain on all active tenders
4. Restart: `bench start`

## Backup & Recovery Procedure
```
# Daily backup (should be cron'd)
0 2 * * * cd ~/frappe-bench && bench backup --with-files

# Restore
bench restore ~/frappe-bench/sites/site1.local/private/backups/20261019_020000-site1_local-database.sql.gz
bench migrate
bench build
bench restart
```

## Escalation Path
| Severity | Contact | Response Time |
|----------|---------|---------------|
| Critical (hash chain break, bid compromise) | Security Officer + CTO | Immediate |
| High (scheduler down, backup failure) | DevOps Lead | <1 hour |
| Medium (rate limit false positive) | App Support | <4 hours |
| Low (dashboard chart stale) | App Support | <24 hours |

---

## LOKADO Demo Procedures

### Quick Reset
```bash
make reset-demo         # reinstall site + re-seed LOKADO (alias for reset-lokado)
make demo-check         # verify LOKADO identities and seeded workflow evidence
make fleet-check        # verify purchase-to-vehicle reconciliation and donor isolation
make demo-index         # print demo record IDs and Desk links for presenters
```

**Destructive:** first take `make backup` and copy its files off the container.
Reset reinstalls the site database and applies configuration before seeding.
Do not use `make clean` as routine recovery: it removes data volumes and host
backup contents. For mounted source use `make dev-reset` (also destructive).
For non-destructive daily repair use `make dev-config && make dev-seed && make dev-check`.

### Backup & Restore (safety net)
```bash
make backup             # Bench database AND uploaded-file archives in sites/<site>/private/backups
# Copy archives off the container with docker compose cp.
# Recovery on an isolated site (DB_FILE is a path INSIDE the backend container):
make restore DB_FILE=/path/to/database.sql.gz
```

The Make restore helper restores the database only. Restore public/private
file archives with the native Bench restore options described in
[backup/restore procedure](../tests/backup_restore_procedure.md).
For the demo site, `make backup-demo` saves a native Bench backup (database +
public + private files) to `backups/lokado-demo/`. `make restore-demo` restores
all three, migrates and clears the cache. Both work after `make clean`/
`make setup`/`make reset-lokado`, because they do not hard-code a database name.

### Verify LOKADO Data Integrity
```bash
make demo-check         # automated check: users, suppliers, counts, fleet
make fleet-check        # fleet-specific reconciliation
docker compose exec backend bench --site ugavi.localhost console
# In console:
# frappe.db.count('Purchase Requisition')  # fresh baseline: 10
# frappe.db.count('Supplier')              # 18
# frappe.db.count('Donor Profile')         # 6
# frappe.db.count('Tender')                # 8
```

### LOKADO Demo Tour Checklist
- [ ] Log in as `procurement@lokado.org` / `Ugavi@2024`
- [ ] Verify 10 Purchase Requisitions across Draft, Pending Approval, Approved, and Rejected
- [ ] Verify 6 Donor Profiles (IOM, USAID, Concern, Japan, EU, Own Funds)
- [ ] Verify 3 Tender Threshold Rules in Procurement Settings
- [ ] Verify 8 Tenders with 26 bids (solar-pump tender closed for live opening)
- [ ] Verify IOM Warehouse Construction contract (milestones, retention, bond)
- [ ] Verify Supplier prequalification (15 prequalified, 2 expired, 1 suspended)
- [ ] Verify Inter Donor Transfer (IOM → Concern, 200 hygiene kits)
- [ ] Verify `make demo-check` and `make fleet-check` both return `"ready": true`