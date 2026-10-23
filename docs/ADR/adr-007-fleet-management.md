# ADR-007: Fleet Management — Bespoke Ugavi Module, Not Frappe HR

> **Status:** ACCEPTED | **Date:** 2026-10-22
> **Decision:** Implement fleet management inside the Ugavi app on top of the
> ERPNext core `Vehicle` DocType. Do **not** install the `hrms` app.

## Context

LOKADO's stated logistics requirement is:

> "Fleet Management — the system should include vehicle allocation, spare parts
> and fuel monthly report. We should be able to record spares and fuel consumed
> by each vehicle every time a purchase for the same is done."

Frappe HR ([docs.frappe.io/hr/fleet-management](https://docs.frappe.io/hr/fleet-management))
ships a fleet feature built from `Vehicle`, `Vehicle Log` and `Vehicle Expenses`,
designed around employee-assigned vehicles and expense claims.

## Decision drivers

1. **Donor attribution is the core requirement.** Every LOKADO fleet cost must be
   attributable to a donor ledger. Frappe HR's `Vehicle Log` has no donor
   dimension and no link to the originating purchase document.
2. **Spend traceability to procurement.** The requirement is explicit that fuel
   and spares are recorded *at the point of purchase*. Ugavi's `Fuel Log` and
   `Spare Parts Issue` link directly to `Purchase Order` and `Purchase Invoice`;
   Frappe HR's expense model routes through HR expense claims instead.
3. **Upgrade surface.** Installing `hrms` adds a third app to every upgrade,
   migration and compatibility run, and brings payroll, leave and attendance
   schemas that LOKADO does not use.
4. **No core modification.** The Ugavi module only *links to* the ERPNext core
   `Vehicle` DocType (`erpnext/setup/doctype/vehicle`) and adds prefixed custom
   fields, so `make upgrade-check` stays clean.

## What is implemented

The `ugavi/fleet/` module provides these app-owned DocTypes:

| DocType | Naming | Covers |
|---|---|---|
| `Vehicle Allocation` | `VA-.YYYY.-.####` | Vehicle → user/project/donor assignment with start, end and actual return dates |
| `Fuel Log` | `FL-.YYYY.-.####` | Litres, cost per litre, total cost, odometer, station, receipt, donor, and links to the originating `Purchase Order` / `Purchase Invoice` |
| `Spare Parts Issue` | `SPI-.YYYY.-.####` | Parts issued to a vehicle from a warehouse, with donor and purchase-document links |
| `Trip Log` | `TRIP-.YYYY.-.####` | Start/end odometer, distance, purpose, donor |
| `Fleet Utilization Report` | — | Period snapshot per vehicle for the monthly report |
| `Fleet Purchase Reconciliation` | `FPR-.YYYY.-.#####` | Submitted receipt/invoice quantity reconciled to vehicle consumption |

Supporting assets: `ugavi/fleet/dashboard/fleet_dashboard.json`,
`ugavi/fleet/workspace/ugavi-fleet`, a `check_vehicle_service_due` daily
scheduler task, and prefixed custom fields on `Vehicle` (`ugavi_donor`,
`ugavi_status`, `ugavi_total_fuel_cost`).

Demo coverage: Scene 18 of `docs/demo/LOKADO-DEMO-TOUR.md`, logging in as
`fleet@lokado.org`.

## Requirement traceability

| Requirement element | Status | Evidence |
|---|---|---|
| Vehicle allocation | Met | `Vehicle Allocation` |
| Fuel recorded per vehicle at purchase | Met | Submitted `Fuel Log.source_reconciliation` consumes a fleet-classified receipt/invoice row |
| Spares recorded per vehicle at purchase | Met | Submitted `Spare Parts Issue` consumes the purchase row and creates an exactly linked Material Issue |
| Monthly fleet report | Met | `Fleet Utilization Report` |
| Donor attribution of fleet cost | Met | `donor` link on all four transaction DocTypes |
| No purchased quantity left unassigned | Met | Serialized reconciliation blocks over-allocation and reports remaining quantity |

## Consequences

- LOKADO gets donor-aware fleet records that Frappe HR cannot express today.
- If LOKADO later adopts Frappe HR for payroll, `hrms` may be installed
  alongside; the Ugavi DocType names do not collide with `Vehicle Log` or
  `Vehicle Expenses`, so the two can coexist. Only the ERPNext core `Vehicle`
  record is shared, which is the intended upstream extension point.
