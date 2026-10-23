# LOKADO Functional-Requirements Demo Tour

> **Client:** Lotus Kenya Action for Development Organization (LOKADO)  
> **Baseline:** Frappe 16.52.0, ERPNext 16.51.1, Ugavi 0.1.0  
> **Duration:** 45-60 minutes for the full tour; scenes can be presented independently.

This is the presenter runbook for the stated procurement, logistics, asset, and fleet requirements. It distinguishes Ugavi controls from ERPNext records so the demo does not imply that upstream behavior was copied or replaced.

## 1. Prepare and validate

```bash
make setup
make upgrade-check
make seed                # canonical LOKADO seed (alias: seed-lokado)
make demo-check
make fleet-check
```

Expected validation:

- upstream compatibility reports `compatible: true`;
- migration completes;
- all 57 backend tests pass;
- all documented identities, roles, passwords and supplier links pass `make demo-check`;
- the purchase-backed fleet journey and donor isolation pass `make fleet-check`;
- `/api/method/frappe.ping` returns `{"message":"pong"}`;
- both acceptance commands return `"ready": true` and no issues.

If Docker reports a stale configurator container, rerun `make upgrade-check`. The target removes only the completed Compose `configurator` service before recreating the application services.

The optional browser gate runs on the host, not in the application container:

```bash
cd tests/e2e
npm ci
npx playwright install chromium
cd ../..
make e2e
```

Do not claim browser evidence when the Node dependencies or browser binary are
not installed. The authoritative 2026-10-22 rehearsal passed compatibility,
migration, 57 backend tests, demo acceptance, fleet acceptance, monthly stock
report reconciliation, and public health; browser E2E was not executed because
its host runtime was unavailable.

## 2. Demo credentials and identities

> **Development/demo credentials only.** These accounts and the shared password
> must not be used on a production site. The LOKADO seed is guarded by
> `developer_mode` and restores this deterministic password when it is rerun.

All seeded users use password `Ugavi@2024`.

### Staff accounts

| Persona | Name | Login | Password | Primary workspace |
|---|---|---|---|---|
| Programme Requester | Alice Akol | `programme@lokado.org` | `Ugavi@2024` | Purchase Requisitions |
| Procurement Officer | Peter Ekai | `procurement@lokado.org` | `Ugavi@2024` | Ugavi Procurement, Ugavi Tendering |
| Programme Approver | Jane Napeyok | `approver1@lokado.org` | `Ugavi@2024` | Purchase Requisitions |
| Finance Approver | Paul Lotir | `approver2@lokado.org` | `Ugavi@2024` | Approvals, encumbrance, matching |
| Opening Officer 1 | Mary Akuom | `opening1@lokado.org` | `Ugavi@2024` | Bid Opening |
| Opening Officer 2 | James Ebei | `opening2@lokado.org` | `Ugavi@2024` | Bid Opening |
| Opening Officer 3 | Sarah Nabwel | `opening3@lokado.org` | `Ugavi@2024` | Bid Opening |
| Evaluation Committee | Dorothy Nekesa | `committee@lokado.org` | `Ugavi@2024` | Bid Evaluation |
| Logistics Officer | John Ekiru | `logistics@lokado.org` | `Ugavi@2024` | Ugavi Logistics, Stock |
| Fleet Manager | David Ewoi | `fleet@lokado.org` | `Ugavi@2024` | Ugavi Fleet |
| Asset Manager | Agnes Ekal | `assets@lokado.org` | `Ugavi@2024` | Ugavi Assets |
| Finance Officer | Margaret Nachuk | `finance@lokado.org` | `Ugavi@2024` | Finance, three-way match |
| Internal Auditor | Robert Lotukoi | `auditor@lokado.org` | `Ugavi@2024` | Governance and audit evidence |
| Store Keeper | Ruth Napeyok | `storekeeper@lokado.org` | `Ugavi@2024` | Purchase Receipt, Stock Entry |

### Supplier portal accounts

Each supplier account is linked to the named ERPNext `Supplier` record and
lands at `/supplier/dashboard` after login.

| Supplier | Contact/login | Password | Demo use |
|---|---|---|---|
| Turkana Construction Ltd | `turkana-construction@outlook.com` | `Ugavi@2024` | Open-tender bid and award |
| Nadirkonyen Women's Group | `nadirkonyen-women@outlook.com` | `Ugavi@2024` | Community supplier and prequalification |
| Rift Valley Hardware Ltd | `riftvalley-hardware@outlook.com` | `Ugavi@2024` | Open-tender opportunity and bid |
| Jopeji Enterprises | `jopeji@outlook.com` | `Ugavi@2024` | Supplier portal identity isolation |
| Lodwar General Supplies | `lodwar-supplies@outlook.com` | `Ugavi@2024` | Default browser/E2E supplier journey |

### Administrator

| Account | Login | Password | Use |
|---|---|---|---|
| Frappe Administrator | `Administrator` | `admin` | Setup and recovery only; do not use for approval demonstrations |

To confirm or inspect the seeded accounts, use the **User** and **Supplier**
lists in Desk. To restore the demo password after a local user changes it:

```bash
make seed-lokado
```

Administrator is available as `Administrator` / `admin` for setup-only actions. Do not use Administrator to demonstrate business approvals.

## 3. How to run the role handoffs

Use a separate browser profile or private window for each concurrent persona.
Do not keep Administrator signed in while demonstrating business controls:
Frappe session cookies are shared per browser profile and can make an approval
appear to have been completed by the wrong actor.

Use this run sheet as the primary presenter sequence:

| Stage | Sign in as | Open | Perform | Expected evidence | Hand off to |
|---|---|---|---|---|---|
| Request | `programme@lokado.org` | `/app/purchase-requisition` | Create a Draft PR and submit it for approval | System PR code, calculated value/method, `Pending Approval` | Approver 1 |
| First approval | `approver1@lokado.org` | `/app/purchase-requisition` | Approve the pending PR | Approval history records Jane and required role | Approver 2 when chain requires it |
| Final approval | `approver2@lokado.org` | `/app/purchase-requisition` | Complete the next approval | `Approved`; requester never approves own PR | Procurement |
| Tender preparation | `procurement@lokado.org` | `/app/tender` | Create/publish from approved PR; confirm documents and officers | Tender method/value match PR; status `Published` | Supplier |
| Prequalification | `lodwar-supplies@outlook.com` | `/supplier/dashboard#prequalification` | Submit category and private evidence | Identity-scoped application and notification | Procurement |
| Prequalification review | `procurement@lokado.org` | `/app/supplier-prequalification` | Review and decide application | Status and reviewer evidence | Supplier |
| Bid/clarification | `lodwar-supplies@outlook.com` | `/supplier/dashboard#opportunities` | Submit bid and clarification | Receipt hash, sealed content, notification | Procurement/opening officers |
| Clarification response | `procurement@lokado.org` | `/app/clarification` | Answer supplier question | Answered status and supplier notification | Supplier |
| Opening share 1 | `opening1@lokado.org` | `/app/bid-opening-record` | Enter officer 1 code | Opening remains locked | Officer 2 |
| Opening share 2 | `opening2@lokado.org` | `/app/bid-opening-record` | Enter officer 2 code | Opening remains locked | Officer 3 |
| Opening share 3 | `opening3@lokado.org` | `/app/bid-opening-record` | Enter officer 3 code and open | Bids decrypt; immutable opening record | Procurement/evaluation |
| Award | `procurement@lokado.org` | `/app/bid-evaluation-summary` | Review scores, recommendation, and award | Winning bid, PO, contract, supplier notice | Supplier/storekeeper |
| PO acknowledgement | winning supplier login | `/supplier/dashboard#deliveries` | Acknowledge the order | Timestamped `ugavi_*` acknowledgement | Store Keeper |
| Receipt | `storekeeper@lokado.org` | `/app/purchase-receipt` | Receive accepted/rejected quantities from PO | Purchase Receipt and updated PO received percentage | Logistics/finance |
| Donor stock | `logistics@lokado.org` | `/app/query-report/Stock Ledger` | Review ledger and donor warehouse/report | Receipt/dispatch trace and donor segregation | Finance |
| Match | `finance@lokado.org` | `/app/three-way-match` | Compare PO, receipt and invoice | Match/tolerance result; no payment is demonstrated | Procurement Manager |
| Evaluation | `procurement@lokado.org` | `/app/ugavi-supplier-evaluation` | Score completed receipt | Total/cumulative rating visible to supplier | Supplier/auditor |
| Audit | `auditor@lokado.org` | `/app/audit-log` | Review approvals, opening and overrides | Actor/time/outcome and hash-chain evidence | Presenter |
| Fleet | `fleet@lokado.org` | `/app/vehicle-allocation` | Review allocation, fuel, spares and utilization | Vehicle-linked source documents and report | Presenter |

### Presenter rules

1. Start each stage by naming the actor and requirement being proved.
2. Show the record before acting, perform one state transition, then show the
   resulting status/history.
3. Log out before changing personas, or use isolated browser profiles.
4. Treat seeded completed records as evidence examples. Use a fresh Draft
   record when demonstrating an actual transition.
5. Do not imply that a configured or proposed MVP2 item is complete. The
   delivered MVP2-readiness slice is listed in section 19.

## 4. Requirement-to-scene map

| Client requirement | Demo scene | Primary record |
|---|---|---|
| Prequalification list and restricted-tender eligibility | 8 | `Supplier`, `Supplier Prequalification` |
| Open tender at KES 500,000 and above | 9 | `Tender`, `Ugavi Procurement Settings` |
| Send/receive bids and three-person opening | 10-11 | `Bid`, `Sealed Bid Key`, `Bid Opening Record` |
| Purchase requisition, approval, system code | 7 | `Purchase Requisition` |
| Purchase order for selected supplier, system code | 13 | ERPNext `Purchase Order` |
| Supplier performance after purchase completion | 16 | `Ugavi Supplier Evaluation` |
| Contract management after award/PO | 13 | `Ugavi Contract` |
| Stock receipts, dispatches, ledger, monthly report | 14 | ERPNext stock records plus Ugavi donor reports |
| Separate donor ledger books | 14 | `Donor Warehouse`, donor-linked stock dimensions |
| Asset register, movement, and condition | 17 | ERPNext `Asset` plus Ugavi movement/verification |
| Vehicle allocation, spares, fuel, monthly report | 18 | ERPNext `Vehicle` plus Ugavi fleet records |

## Scene 5: Organization and funding context

**Login:** `procurement@lokado.org`  
**Navigate:** Desk search → **Company**, **Project**, **Donor Profile**

1. Show Lotus Kenya Action for Development Organization.
2. Show the six donor profiles: IOM, USAID, Concern Worldwide, Embassy of Japan, EU, and Own Funds.
3. Explain that donor and project values flow from requisition to tender, order, warehouse, receipt, stock, and reporting.

**Control:** funding attribution is data, not a free-text note.

## Scene 6: Procurement thresholds and governance

**Login:** `procurement@lokado.org` for settings; `auditor@lokado.org` for evidence  
**Navigate:** `/app/ugavi-procurement-settings`, `/app/delegation-of-authority`, `/app/segregation-of-duties`

1. Show the configured KES bands:
   - below 200,000: direct/RFQ route;
   - 200,000-499,999: restricted tender;
   - 500,000 and above: open tender.
2. Show effective dates and donor/category rule hooks.
3. Show Delegation of Authority levels.
4. Show segregation rules preventing requester/approver/payer conflicts.
5. Open the seeded blocked override in **Audit Log**.

**Control:** the server determines and validates the method; the UI is not the enforcement boundary.

## Scene 7: Purchase requisition and approval

**Login sequence:** `programme@lokado.org` → `approver1@lokado.org` → `approver2@lokado.org`  
**Navigate:** `/app/purchase-requisition`

1. Open the WASH water-tank requisition (KES 450,000) and show **Restricted Tender**.
2. Open the warehouse construction requisition (KES 1.2 million) and show **Open Tender**.
3. Show the system-generated PR identifier, donor, project, department, items, estimated value, and justification.
4. As Alice Akol, create or open a Draft and select **Submit for Approval**.
5. Log out. As Jane Napeyok, approve the first required step.
6. If the displayed chain has a second step, log out and approve it as Paul Lotir.
7. Confirm that the requester cannot approve or reject their own requisition.
8. Show rejection and audit history on the seeded office-consumables example.

**Requirements:** coded PR, programme request, approval before procurement, threshold selection, DoA, SoD.

## Scene 8: Supplier profile and prequalification

**Login sequence:** supplier account → `procurement@lokado.org`  
**Supplier navigation:** `/supplier/dashboard#profile`, then `#prequalification`  
**Desk navigation:** `/app/supplier`, `/app/supplier-prequalification`

1. Sign in as the supplier and update allowed profile fields.
2. Submit a category prequalification with a private registration or tax document.
3. As Procurement Officer, review the application and supporting document.
4. Compare `Prequalified`, `Expired`, and `Suspended` examples.
5. Explain that only an active category match exposes a restricted tender; open tenders remain open to any linked supplier.

See [Supplier Journey Demo Guide](SUPPLIER-JOURNEY.md) for the detailed supplier script.

## Scene 9: Tender publication and opportunities

**Login sequence:** `procurement@lokado.org` → supplier account  
**Desk navigation:** `/app/tender`  
**Supplier navigation:** `/supplier/dashboard#opportunities`

1. Open the warehouse construction tender.
2. Show procurement method, value, donor, category, dates, criteria, documents, addenda, and bid security.
3. Publish a suitable draft tender.
4. Show the opportunity in the supplier portal.
5. Explain that both `Published` and `Bids Received` accept additional eligible bids until the server deadline.

**Requirements:** open/restricted route, publication, any eligible open-tender supplier, prequalified restricted suppliers, addenda, deadline.

## Scene 10: Supplier bid and clarification

**Login sequence:** supplier account → `procurement@lokado.org` → supplier account  
**Supplier navigation:** `/supplier/dashboard#bids`, then `#clarifications`

1. Select **Prepare bid**.
2. Enter amount, currency, delivery days, and a private technical proposal.
3. Submit and show the deterministic receipt.
4. Submit a clarification.
5. As Procurement Officer, answer it in `/app/clarification`.
6. Return to the portal and show the answer and notification.

**Control:** the API resolves supplier identity from the session. It does not accept a supplier identifier from the browser.

## Scene 11: Three-person sealed-bid opening

**Login sequence:** `opening1@lokado.org` → `opening2@lokado.org` → `opening3@lokado.org`  
**Navigate:** `/app/bid-opening-record`

1. Show that sealed methods create an RSA public key and an AES-wrapped private key.
2. Explain that only the 256-bit wrapping key is split into three shares.
3. Demonstrate one officer: opening fails.
4. Demonstrate two officers: opening still fails.
5. Have all three distinct officers enter their short-lived system-issued codes.
6. Open the bids and show the Bid Opening Record and hash evidence.

**Control:** 3-of-3 is enforced by cryptography and controller validation, not by hiding a button.

## Scene 12: Evaluation and award decision

**Login:** `procurement@lokado.org`  
**Navigate:** `/app/bid-evaluation-summary`, `/app/coi-declaration`, `/app/standstill-period`

1. Show committee membership and conflict-of-interest declarations.
2. Show technical and financial weighted scoring.
3. Compare opened bids in the evaluation summary.
4. Show recommendation and standstill status.
5. Award only a supplier with an opened/evaluated bid and the exact opened amount.

**Requirements:** shared evaluation, objective comparison, controlled recommendation, award approval.

## Scene 13: Purchase order and contract

**Login sequence:** `procurement@lokado.org` → winning supplier account  
**Navigate:** `/app/purchase-order`, `/app/ugavi-contract`  
**Supplier navigation:** `/supplier/dashboard#awards`, then `#contracts`

1. Show the award-generated ERPNext Purchase Order and its system identifier.
2. Show supplier, items, rate, required date, donor, project, tender, and PR references.
3. Show the linked Ugavi Contract, milestones, retention, bond, documents, and expiry settings.
4. In the supplier portal, show the award and contract.
5. Acknowledge the Purchase Order.

**Control:** award creates the order and contract in one transaction. Ugavi extends ERPNext Purchase Order with prefixed custom fields instead of replacing its controller.

## Scene 14: Receipt, dispatch, stock ledger, and donor books

**Login sequence:** `storekeeper@lokado.org` → `logistics@lokado.org`  
**Navigate:** `/app/purchase-receipt`, `/app/stock-entry`, `/app/query-report/Stock Ledger`, `/app/donor-warehouse`, `/app/monthly-stock-report`, `/app/inter-donor-transfer`

1. Create a Purchase Receipt from the submitted Purchase Order.
2. Show that receipt updates the Purchase Order received percentage.
3. Create or open a Stock Entry for dispatch.
4. Open ERPNext **Stock Ledger** and filter by item and warehouse.
5. Show six donor-to-warehouse links.
6. Open the IOM and USAID Monthly Stock Reports.
7. Show the approved IOM-to-Concern inter-donor transfer.
8. Explain that cross-donor consumption requires an approved transfer.

**Requirements:** receipts, dispatches, digital ledger, monthly report, donor-segregated ledgers.

## Scene 15: Three-way match and finance handoff

**Login:** `finance@lokado.org`  
**Navigate:** `/app/three-way-match`, `/app/purchase-invoice`

1. Compare Purchase Order, Purchase Receipt/GRN, and Purchase Invoice.
2. Show tolerance handling and mismatch status.
3. Show donor/project dimensions carried into the finance handoff.

**Upstream boundary:** ERPNext owns Purchase Invoice and accounting postings; Ugavi adds donor compliance and matching evidence.

## Scene 16: Supplier performance evaluation

**Login sequence:** `procurement@lokado.org` → supplier account  
**Navigate:** `/app/ugavi-supplier-evaluation`  
**Supplier navigation:** `/supplier/dashboard#evaluations`

1. Complete the final Purchase Receipt.
2. Open the evaluation created for that supplier/receipt.
3. Score quality, delivery, compliance, and price competitiveness.
4. Show total and cumulative rating.
5. Return to the supplier portal and show the published result and remarks.

**Requirement:** evaluation is tied to an actual completed purchase, not an unreferenced spreadsheet.

## Scene 17: Asset management

**Login:** `assets@lokado.org`  
**Navigate:** `/app/asset`, `/app/ugavi-asset-movement`, `/app/asset-verification`, `/app/asset-disposal`

1. Show the ERPNext Asset register, category, capitalization, location, custodian, depreciation, and maintenance.
2. Show Ugavi donor attribution and QR/tagging extension.
3. Record a movement between custodian/location states.
4. Record condition during verification.
5. Show controlled disposal.

The LOKADO seed includes eight donor assets, eight physical verification
records, two custody/location movements with condition evidence, and one
independently authorized disposal.

## Scene 18: Fleet management

**Login:** `fleet@lokado.org`  
**Navigate:** `/app/vehicle`, `/app/fleet-purchase-reconciliation`, `/app/vehicle-allocation`, `/app/fuel-log`, `/app/spare-parts-issue`, `/app/trip-log`, `/app/fleet-utilization-report`

1. Show the four upstream ERPNext Vehicles covering USAID, IOM, Concern, and EU.
2. Open Fleet Purchase Reconciliation and show that each submitted fuel/spare
   Purchase Receipt row is fully reconciled.
3. Show the active, non-overlapping vehicle allocation and donor inheritance.
4. Open the submitted Fuel Logs: the source PO, Receipt, donor, receipt number,
   odometer, litres and cost are immutable evidence.
5. Open each submitted Spare Parts Issue and its exact linked ERPNext Material
   Issue Stock Entry.
6. Show submitted trip/odometer evidence and cost-per-kilometre.
7. Open the USAID, IOM, Concern, and EU reports and show that each snapshot
   contains only its own donor vehicle.
8. Run `make fleet-check`; it must return `"ready": true`.

`make seed-lokado` is idempotent and seeds the complete submitted fleet journey.

## Scene 19: Notifications, complaints, audit, and MVP2 readiness

**Login sequence:** supplier account → `procurement@lokado.org` → `auditor@lokado.org`  
**Supplier navigation:** `/supplier/dashboard#notifications`  
**Desk navigation:** `/app/tender-complaint`, `/app/audit-log`

1. Show the supplier journey progress and next-best-action panel.
2. Show prequalification receipt, bid receipt, clarification answer, award, and PO acknowledgement notifications.
3. For a supplier that bid on a tender with an active Standstill Period, submit a complaint with a private supporting document.
4. As Procurement Officer, open **Tender Complaint**, assign a reviewer, and move it through review to an outcome.
5. Return as the supplier and show the outcome notification.
6. Mark a supplier notification read and show that a different portal user cannot update it.
7. As Auditor, show actor/time/outcome evidence and the hash chain.
8. Finish with the successful `make upgrade-check`, `make demo-check`, and
   `make fleet-check` output. Show Playwright output only when the separately
   prepared host-side browser gate has actually run.

The LOKADO seed prepares the active standstill on **Field Motorcycles Peace
Building USAID**. Use `lodwar-supplies@outlook.com`, which has a seeded bid on
that tender, for the complaint demonstration.

### Delivered MVP2-readiness slice

The following is implemented without changing ERPNext core:

- app-owned `Tender Complaint` DocType with conventional Frappe discovery;
- bidder-only complaint intake during an active standstill window;
- private, current-user-owned supporting document enforcement;
- duplicate unresolved-complaint prevention;
- procurement review status/outcome and supplier resolution notification;
- Standstill Period complaint count and challenged/resolved states;
- supplier journey completion and next-best-action UI;
- mobile/accessibility behavior using only `ugavi-*` selectors and shared tokens.

This is a readiness slice for MVP2 W3, not a claim that all MVP2 workstreams are
complete. Finance system-of-record, payment channel, tax/eTIMS, donor report
formats, retention policy and SSO decisions remain blocked by
[MVP2 Open Questions](../mvp2/OPEN-QUESTIONS.md).

## ERPNext upstream reuse

| Capability | Upstream source retained | Ugavi extension |
|---|---|---|
| Supplier master | [Supplier docs](https://docs.frappe.io/erpnext/supplier), [v16.52.1 source](https://github.com/frappe/erpnext/tree/v16.52.1/erpnext/buying/doctype/supplier) | Prequalification, portal identity boundary, supplier-specific evaluation |
| Purchase Order | [Purchase Order docs](https://docs.frappe.io/erpnext/purchase-order), [v16.52.1 source](https://github.com/frappe/erpnext/tree/v16.52.1/erpnext/buying/doctype/purchase_order) | `ugavi_*` donor, PR, tender, method, and acknowledgement fields |
| Purchase Receipt | [Purchase Receipt docs](https://docs.frappe.io/erpnext/purchase-receipt), [v16.52.1 source](https://github.com/frappe/erpnext/tree/v16.52.1/erpnext/stock/doctype/purchase_receipt) | Donor integrity event and post-receipt evaluation |
| Stock ledger | [Stock Ledger docs](https://docs.frappe.io/erpnext/stock-ledger), [v16.52.1 stock source](https://github.com/frappe/erpnext/tree/v16.52.1/erpnext/stock) | Donor warehouse, inter-donor approval, monthly donor report |
| Assets | [Asset docs](https://docs.frappe.io/erpnext/asset), [v16.52.1 asset source](https://github.com/frappe/erpnext/tree/v16.52.1/erpnext/assets/doctype) | Donor flag, QR verification, Ugavi movement/disposal workflow |
| Vehicles | [v16.52.1 Vehicle source](https://github.com/frappe/erpnext/tree/v16.52.1/erpnext/setup/doctype/vehicle) | Allocation, fuel, spares, trip, and utilization records |
| Notifications | [Frappe version-16 Notification Log](https://github.com/frappe/frappe/tree/version-16/frappe/desk/doctype/notification_log) | Supplier-journey events scoped to linked website users |

## Completion checklist

- [ ] Each business persona used its own account.
- [ ] Restricted and open thresholds were demonstrated.
- [ ] PR approval and system identifier were shown.
- [ ] Supplier prequalification and private document upload were shown.
- [ ] Bid receipt, clarification, and 3-of-3 opening were shown.
- [ ] Award generated the Purchase Order and contract.
- [ ] Purchase Receipt updated delivery progress and stock.
- [ ] Donor ledger and monthly stock report were shown.
- [ ] Supplier evaluation was linked to receipt.
- [ ] Asset movement/condition and fleet fuel/spares were shown.
- [ ] Notifications and audit evidence were shown.
- [ ] `make upgrade-check`, `make demo-check`, and `make fleet-check` passed.
- [ ] Browser E2E passed, or was explicitly recorded as not executed because
      its host-side prerequisites were unavailable.
