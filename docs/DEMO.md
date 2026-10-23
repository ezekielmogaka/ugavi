# Ugavi Demo — Presenter Runbook

> **Audience:** LOKADO (Lotus Kenya Action for Development Organization) leadership  
> **Stack verified 2026-10-23:** Frappe 16.53.0 + ERPNext 16.52.1 + Ugavi 0.1.0
> **Duration:** 55-75 minutes (full tour) or ~15 minutes per scene for standalone  
> **Business persona passwords:** `Ugavi@2024` (development-only; seed-script enforced)

This runbook is for the **Ugavi team** to present the working MVP1 system. It is not the
technical setup guide — for that see the inline commands, Make targets, and
`docs/demo/LOKADO-DEMO-TOUR.md`.
Use the [requirement-to-scene map](demo/LOKADO-DEMO-TOUR.md#4-requirement-to-scene-map)
for the original client scope and the [evidence registry](traceability/evidence.md)
for the distinction between automated checks and live presenter actions.

---

## 0. Before you present (checklist — 5 minutes)

```bash
make setup                    # Build image, bring up all services
make upgrade-check            # Rebuild + migrate + backend tests
make seed                     # Populate the LOKADO dataset (idempotent; alias: seed-lokado)
make demo-check               # Verify users, passwords, record counts (19 users, 0 issues)
make fleet-check              # Verify purchase-backed fleet reconciliation
make e2e                      # Browser gate, after host prerequisites below
make backup                   # Native Bench backup of database AND uploaded files
```

Run these commands from the repository root. For daily source-mounted development,
use `make dev-up` in one terminal, then `make dev-config`, `make dev-seed`,
`make dev-check`, `make dev-test` in another. Use
`UGAVI_BASE_URL=http://ugavi.localhost:8000 make e2e` to test that source.
Image rehearsal commands above test baked code, not unbuilt local edits.
`make help` and the [Make reference](../README.md#makefile-reference) list the targets.
Do not run `seed-generic` alongside the canonical LOKADO seed.

Expected output:
- `{"compatible": true, "issues": [], "missing_controllers": []}`
- `{"message":"pong"}` from `curl http://localhost:8080/api/method/frappe.ping`
- backend output: integration and unit runners both finish with `OK`
  (15 integration + 62 unit tests at this checkpoint)
- demo and fleet checks: `"ready": true` with an empty `issues` list

Browser automation is a separate host-side gate. Prepare it once, then run it
only after the seeded site is healthy:

```bash
cd tests/e2e
npm ci
npx playwright install chromium
cd ../..
make e2e
```

`make e2e` is not run inside the application container and is not part of
`make upgrade-check`. If Node dependencies or the Playwright browser binary are
missing, report the browser gate as **not executed** rather than treating it as
a product failure or claiming that it passed.

Open separate browser profiles/private sessions before the demo, not just tabs
(tabs in one profile share the login cookie):
1. **Desk** at `http://localhost:8080` (log in with the persona for the first scene)
2. **Supplier portal** at `http://localhost:8080/supplier/dashboard` (logged in as `lodwar-supplies@outlook.com`)
3. **Mailpit** at `http://localhost:8026` (local email capture; no external delivery)

---

## 1. Demo credentials — all-in-one
### Desk users (14 staff personas)

| # | Who | Login email | Role | Workspace to open |
|---|---|---|---|---|
| 1 | Alice Akol | `programme@lokado.org` | Programme Requester | Purchase Requisitions |
| 2 | Peter Ekai | `procurement@lokado.org` | Procurement Officer | Ugavi Procurement |
| 3 | Jane Napeyok | `approver1@lokado.org` | Approver Level 1 | Purchase Requisitions |
| 4 | Paul Lotir | `approver2@lokado.org` | Approver Level 2 | Approvals / Encumbrance |
| 5 | Mary Akuom | `opening1@lokado.org` | Bid Opening Officer | Bid Opening |
| 6 | James Ebei | `opening2@lokado.org` | Bid Opening Officer | Bid Opening |
| 7 | Sarah Nabwel | `opening3@lokado.org` | Bid Opening Officer | Bid Opening |
| 8 | John Ekiru | `logistics@lokado.org` | Logistics Officer | Ugavi Logistics |
| 9 | David Ewoi | `fleet@lokado.org` | Fleet Manager | Ugavi Fleet |
| 10 | Agnes Ekal | `assets@lokado.org` | Asset Manager | Ugavi Assets |
| 11 | Margaret Nachuk | `finance@lokado.org` | Finance Officer | Finance |
| 12 | Robert Lotukoi | `auditor@lokado.org` | Auditor | Governance |
| 13 | Ruth Napeyok | `storekeeper@lokado.org` | Store Keeper | Purchase Receipt |
| 14 | Dorothy Nekesa | `committee@lokado.org` | Evaluation Committee | Bid Evaluation |

**Password for all staff:** `Ugavi@2024`

### Supplier portal users (5 supplier organizations)

| Supplier | Contact email | Password | Used for |
|---|---|---|---|
| Turkana Construction Ltd | `turkana-construction@outlook.com` | `Ugavi@2024` | Awarded open-tender bidder |
| Nadirkonyen Women's Group | `nadirkonyen-women@outlook.com` | `Ugavi@2024` | Restricted-tender community supplier |
| Rift Valley Hardware Ltd | `riftvalley-hardware@outlook.com` | `Ugavi@2024` | Open-tender opportunity |
| Jopeji Enterprises | `jopeji@outlook.com` | `Ugavi@2024` | Identity isolation demo |
| Lodwar General Supplies | `lodwar-supplies@outlook.com` | `Ugavi@2024` | Primary portal demo account |

### Administrator

| Account | Login | Password |
|---|---|---|
| Administrator | `Administrator` | `admin` |
---

## 2. Demo URLs

| Service | URL | Purpose |
|---|---|---|
| Desk login | `http://localhost:8080/login` | Staff workspace access |
| Supplier portal | `http://localhost:8080/supplier/dashboard` | Supplier portal dashboard |
| Mailpit | `http://localhost:8026` | View all system emails + SMS stubs |
| Health check | `http://localhost:8080/api/method/frappe.ping` | System health |

---

## 3. Scene-by-scene walkthrough

> **Narrative:** LOKADO runs 6 donor-funded programmes across Turkana County with annual
> procurement of ~KES 240M. The demo follows a real purchase through the system:
> hygiene kit request -> open tender -> evaluation -> award -> delivery -> stock reporting.

---

### Scene 0: The Ugavi Ecosystem (2 min — Presenter Only)

```
Log in as: Administrator / admin
Navigate: Explore -> Ugavi Procurement
```

**What to say:** "Ugavi runs on Frappe/ERPNext v16. We have customized nothing in
core ERPNext. Our features live in the `ugavi` app, using hooks, custom
DocTypes, native permissions and extension points. The pinned v16 upgrade
rehearsal passes; every future upstream version must pass that rehearsal too."

**Show:**
- Module list on the Explore page — point out all 8 Ugavi modules
- Open `Ugavi Procurement Settings` -> show threshold table (Direct < 200K,
  Restricted 200K-499K, Open >= 500K)
- Open `Delegation of Authority` list -> show 5 authority levels by amount,
  department, and donor
---

### Scene 1: Purchase Requisition — Alice needs 500 hygiene kits (5 min)

```
Log out Administrator
Log in as: programme@lokado.org / Ugavi@2024
Navigate: Purchase Requisition list -> + New
```

**What to show:**
1. Alice Akol creates a PR for 500 hygiene kits (KES 250,000) for the IOM
   Women's Empowerment Programme.
2. Select item "HYGIENE-KIT", quantity 500, rate KES 500, programme
   "Women's Empowerment", donor "IOM".
3. Before saving, show the **procurement method** auto-calculates to
   "Restricted" (200K-499K range).
4. Save -> system identifier generates `PR-<DONOR>-<YEAR>-<SEQUENCE>`.
5. Click **Submit for Approval** -> the displayed DoA chain determines the next role.

**What to say:** "Every purchase starts with a requisition. The system
automatically determines the procurement method based on your configured
thresholds. Alice doesn't need to know procurement rules — the system
applies them. The donor dimension and programme code are mandatory."

**Validation checkpoint:** PR status = `Pending Approval`,
method = `Restricted Tender`, donor = IOM.

---

### Scene 2: Approval Chain — Two levels of sign-off (5 min)

```
Log out
Log in as: approver1@lokado.org / Ugavi@2024
Navigate: Purchase Requisition list -> find Alice's PR
```

1. Jane Napeyok (Programmes Director) opens the PR.
2. Click "Approve" -> approval history records Jane; status stays
   `Pending Approval` if another step remains, otherwise it becomes `Approved`.
3. Jane notes the PR is within her DoA limit (up to KES 500,000 for IOM).

```
Log out
Log in as: approver2@lokado.org / Ugavi@2024
```

4. Only if the displayed chain requires a second step, Paul opens the PR and approves.
5. Status = `Approved`. Show the approval history with actor, role and timestamp.

**What to say:** "The approval chain enforces LOKADO's Delegation of Authority
matrix. Every approval is audited — immutable record of who, when, and from
where. Segregation of Duties prevents the same person from both requesting
and approving."

**Validation checkpoint:** PR status = `Approved`, with every required step in history.
Do not promise two approvals for a value/donor whose DoA chain requires only one.

---

### Scene 3: Tender Creation — From PR to published opportunity (5 min)

```
Log out
Log in as: procurement@lokado.org / Ugavi@2024
Navigate: Ugavi Tendering -> Tender list
Click on: Solar Water Pumps EU Resilience (Open, KES 780,000)
```

1. Peter opens the solar-pump tender prepared for live opening.
2. Show `Open Tender`, estimated value KES 780,000, and the elapsed deadline.
3. Open the **Bid** list filtered to this tender: four submissions remain sealed.
4. Use a different still-open tender for a new supplier submission. The solar-pump
   fixture is deliberately closed; late bids must be rejected.

```
Navigate to: Field Motorcycles Peace Building USAID
```

5. Show this is the tender with active standstill period for complaint demo.

**What to say:** "LOKADO has 5 tenders in the system. The IOM warehouse tender
has 3 bids sealed with RSA-4096 encryption — not even Peter can see bid
amounts before the opening ceremony."

**Validation checkpoint:** 5 tenders visible, 3 bids with "status: Sealed".
---

### Scene 4: Sealed-Bid Opening Ceremony — 3 officers, 3 keys (8 min)

> This is the security showcase. Use 3 incognito windows for best effect.

```
Keep Peter Ekai logged in
Have the 3 opening officers ready:
  - Mary Akuom   (opening1@lokado.org)
  - James Ebei   (opening2@lokado.org)
  - Sarah Nabwel (opening3@lokado.org)
```

**Step A — Mary starts from the Tender (not a new BOR form):**
1. Log in as `opening1@lokado.org` and open **Solar Water Pumps EU Resilience**.
2. Select **Open Sealed Bids**. The system emails codes to the three assigned
   officers and displays a dialog for all three codes. A BOR is created only
   after successful opening; direct BOR creation is prohibited.

**Step B — Mary Akuom:**
3. Each officer reads their own code from Mailpit (6-digit, 5-min expiry,
   3-attempt limit) and provides it during the supervised ceremony.
4. Mary enters the three officer-provided codes in the Tender dialog.

**Important:** the current UI collects three codes in one authorized session;
it does not persist separate officer-session approvals. Never describe it as
three independently signed browser approvals. Mailpit is shared demo
infrastructure; production delivery must be private to each officer.
For negative-code trials, request a fresh set of codes before retrying,
because successfully verified codes are single-use.

**Step E — Decryption:**
6. All 3 shares verified -> Shamir's 3-of-3 key reconstruction.
7. All four bid amounts are decrypted and revealed.
8. BOR signed with hash chain, locked as immutable.

**What to say:** "No single officer can open bids alone. No two officers can.
You need all three valid codes. The private key is encrypted at rest and its
wrapping key is split into three shares. The opening produces an immutable
record and hash evidence."

**Validation checkpoint:** BOR `outcome = Success`, private PDF attached, four
bid amounts visible, Tender `Under Evaluation`. The seed does not undo this
ceremony. Use `make backup` before it; a destructive reset is needed for an exact replay.

---

### Scene 5: Bid Evaluation -> Award -> Contract (7 min)

```
Log in as: procurement@lokado.org / Ugavi@2024
```

1. Navigate to `Evaluation Committee` for IOM Warehouse.
2. Show: Chairperson, Secretary, 3 members, COI declarations submitted.
3. Show `Bid Evaluation Summary` — weighted scoring (technical 60%, financial 40%).
4. System recommends Turkana Construction Ltd (KES 1,150,000, score 82/100).
5. This warehouse tender is already awarded: show its existing Purchase Order
   and contract. For a fresh award, first complete evaluation, COI declarations
   and a resolved `Award Confirmed` standstill on the newly opened tender.
6. Open `Ugavi Contract` -> 4 milestones, 10% retention, KES 50K bond.
7. Navigate to `Standstill Period` — 14-day challenge window.
8. Show `Tender Complaint` feature.

**What to say:** "The award creates a Purchase Order, a Contract, and updates
the audit trail — all in one transaction. The standstill period gives
unsuccessful bidders a formal challenge window."

**Validation checkpoint:** Awarded bid, Purchase Order, Contract with 4 milestones.

---

### Scene 6: Supplier Portal — The supplier's experience (8 min)

```
Switch to supplier portal tab (lodwar-supplies@outlook.com)
Or navigate to: http://localhost:8080/supplier/dashboard
```

**Show these sections:**
1. Journey readiness progress bar and Next Best Action.
2. 4 metrics: Open opportunities, Active submissions, Awards, Notifications.
3. **Profile** — contact updates only, commercial fields are Desk-controlled.
4. **Prequalification** — approved applications, private document upload.
5. **Opportunities & Bids** — eligible tenders with deadline filtering,
   sealed bid form with encrypted amount.
6. **Complaints** — tender complaint form for Field Motorcycles (active
   standstill window).
7. **Awards & Contracts** — awarded IOM Warehouse tender, contract details.
8. **Deliveries** — Purchase Order with Acknowledge button, receipt progress
   from ERPNext.
9. **Evaluations** — post-receipt performance scores.
10. **Notifications** — submission receipts, award notifications.

**What to say:** "Each supplier gets a dedicated dashboard without exposing
other suppliers' data. Identity isolation is enforced at the controller level
— a supplier can never see another supplier's bids, contracts, or evaluations."
---

### Scene 7: Logistics & Donor Stock Segregation (6 min)

```
Log out of supplier portal
Log in as: logistics@lokado.org / Ugavi@2024
Navigate: Ugavi Logistics -> Donor Warehouse list
```

1. 8 donor-warehouse links across the six donors.
2. Monthly Stock Report for IOM — opening/closing balance, consumption, value.
3. Inter Donor Transfer — Japan -> IOM approved transfer.
4. Stock Ledger filtered by donor — no cross-donor consumption.
5. Scheduled monthly report generation and email dispatch.

**What to say:** "Every item is tagged by donor. Stock from IOM cannot be
consumed for a USAID programme without an approved inter-donor transfer."

**Validation checkpoint:** 8 donor-warehouse links, 6 stock reports and 6
transfers (2 Completed, 2 Approved, 1 Pending Approval, 1 Rejected).

---

### Scene 8: Fleet Management & Assets (5 min)

```
Log out
Log in as: fleet@lokado.org / Ugavi@2024
Navigate: Ugavi Fleet -> Fleet Dashboard
```

1. Fleet Dashboard: 4 vehicles, utilization chart, service schedule.
2. Vehicle Allocations — 4 active allocations.
3. Fuel Log — 8 submitted entries linked to fuel purchases.
4. Trip Log — 8 submitted trips with odometer readings.
5. Spare Parts Issue — parts issued to vehicles.

```
Log out and log in as: assets@lokado.org / Ugavi@2024
Navigate: Ugavi Assets -> Asset Register
```

6. Asset Register — 8 assets with donor and QR evidence.
7. Asset Movement records — custody tracking.
8. Asset Verification — scheduled reminders (every 180 days).

**What to say:** "LOKADO's fleet tracks every trip, fuel purchase, and spare
part issue. Assets are QR-tagged and tracked through movement and verification
cycles — essential for donor audit requirements."

**Validation checkpoint:** 4 vehicles, 4 allocations, 8 fuel logs, 8 spare
issues, 8 trips, 4 donor fleet reports, 8 asset verifications, 2 movements and
1 independently authorized disposal.

---

### Scene 9: Governance & Audit (5 min)

```
Log out
Log in as: auditor@lokado.org / Ugavi@2024
Navigate: Governance module
```

1. Audit Log — hash chain on a tender document.
2. Delegation of Authority — 5-tier matrix (amount x department x donor).
3. Segregation of Duties — 3 enforced separation rules.
4. Waiver — threshold bypass with all approvals logged.

**What to say:** "Every state change creates an audit log entry. Critical
documents use a hash chain — any tampering breaks the chain and is instantly
detectable. SoD is enforced at the server level, not just the UI."

**Validation checkpoint:** 5 DoA rules, 3 SoD rules, 1 Waiver, hash chain.

---

### Scene 10: Finance — Three-Way Match & Budget Control (5 min)

```
Log out
Log in as: finance@lokado.org / Ugavi@2024
Navigate: Finance -> Three-Way Match
```

1. Open the Three-Way Match list: 6 records, one per receipt-linked supplier
   invoice (e.g. `LOK-INV-TCL-0412`, Turkana Construction → IOM Kakuma).
2. Drill into the linked Purchase Order → Purchase Receipt → Purchase Invoice
   and show the PO/GRN/Invoice quantity and rate comparison.
3. Payments: 5 submitted Payment Entries (full and partial). Lodwar General
   Supplies (`LOK-INV-LGS-1190`) is deliberately left unpaid to show an open
   payable; every payment passed the completed-supplier-evaluation gate.
4. Landed Cost Vouchers: 3 submitted, spreading freight onto receipt valuation.
5. Budgets: 6 submitted donor budgets (`Budget Against = Donor Profile`), e.g.
   IOM Freight KES 1,150,000, CONCERN Admin KES 1,200,000, with Warn actions.
6. Budget Encumbrance — every submitted Purchase Order commits funds against
   its donor at PO submission.

**What to say:** "Invoice submission creates PO/GRN/invoice matching evidence
and flags disputes for review. Finance must review it; this is not a claim of
an automatic mismatch-payment block. A separate completed-supplier-evaluation
gate is enforced on payments. Encumbrance is created at PO submission."
---

### Scene 11: Finale — Upgrade Safety & Health Check (3 min)

```
Back to terminal
```

```bash
curl -s http://localhost:8080/api/method/frappe.ping
# -> {"message":"pong"}

make demo-check
# -> All users valid, all passwords match, all record counts pass
```

**What to say:** "Ugavi has zero ERPNext core patches. We use hooks, custom
DocTypes, and extension points. The pinned v16 migration passes. A v17 upgrade
still requires compatibility review, migration tests and a backup/restore rehearsal."

---

### Scene 12: MVP2 Readiness Preview (5 min — Optional)

**Already implemented for MVP2:**
1. Standstill Period + Tender Complaints — supplier challenge workflow.
2. Fleet Maintenance Schedule — upcoming service dates, cost per km tracking.
3. Asset QR Verification — print format with QR code for field verification.
4. Contract milestones, retention/bond tracking and completion checks;
   demonstrate only the verified lifecycle, not an external cash release.
5. Monthly donor stock reports and app-owned report generation; client-specific
   narrative layouts still need approved templates.

**Planned for MVP2 (awaiting external inputs):**
6. eTIMS integration (KRA registration required)
7. Africa's Talking SMS gateway (provider contract required)
8. SSO with Azure AD / Okta
9. Payment processing integration
10. Donor-specific report formats (IOM, USAID templates, etc.)

---

## 4. Quick Demo (15 min — Standalone)

| Time | Scene | Who logs in |
|---|---|---|
| 0:00 | Scene 4: Sealed-Bid Opening | `procurement@lokado.org` + 3 opening officers |
| 8:00 | Scene 5: Evaluation -> Award | `procurement@lokado.org` |
| 12:00 | Scene 6: Supplier Portal | `lodwar-supplies@outlook.com` |
| 14:00 | Scene 11: Health Check + Upgrade | Terminal |
| 15:00 | Done | — |

---

## 5. Troubleshooting Demo Day

| Problem | Fix |
|---|---|
| "Backend not ready" | `docker compose logs --tail=50 backend`; wait for bench start |
| Configurator name conflict | `make upgrade-check` (handles it automatically) |
| Demo users don't exist | `make seed-lokado` (idempotent, safe to re-run) |
| Wrong password | `make seed-lokado` restores `Ugavi@2024` |
| OTP not in Mailpit | Go to `http://localhost:8026`; emails take ~2 seconds; refresh |
| SSL / HTTPS error | Use `http://` not `https://` (local development) |
| Browser shows old data | Hard refresh (Cmd+Shift+R) or clear cache |
| Full reset needed | Take `make backup`, then `make reset-demo` (reinstalls the site database; destructive, does not delete Docker volumes) |
---

## 6. Validation Checklist (Presenter)

- [ ] All 14 staff users login with `Ugavi@2024`
- [ ] All 5 supplier portal users login with `Ugavi@2024`
- [ ] PR created with auto-determined procurement method (Restricted for KES 250K)
- [ ] 2-level approval chain completes
- [ ] 5 tenders visible (2 Open, 2 Restricted, 1 RFQ)
- [ ] 15 bids seeded (3 on IOM Warehouse)
- [ ] Bid Opening Record: 3-of-3 officers, OTPs, decryption, hash chain
- [ ] Award creates Purchase Order + Contract in one transaction
- [ ] Contract shows 4 milestones, 10% retention, performance bond
- [ ] Supplier portal: journey readiness + next-best-action
- [ ] Supplier portal: all sections functional
- [ ] Standstill period active for Field Motorcycles tender
- [ ] Complaint intake working (supplier submits, procurement reviews)
- [ ] 6 donor books, 6 stock reports, and approved/pending/rejected transfer examples
- [ ] Fleet: 4 vehicles, 4 allocations, and 8 submitted fuel, spare, and trip records
- [ ] Assets: 8 assets, 8 verifications, 2 completed movements, and 1 authorized disposal
- [ ] Governance: DoA, SoD, Waiver, Audit Log with hash chain
- [ ] Three-way match: PO matches GRN and Invoice within tolerance
- [ ] `make demo-check` passes with `"ready": true`
- [ ] `make fleet-check` passes with `"ready": true`
- [ ] Playwright prerequisites are installed and `make e2e` passes, or the
      browser gate is explicitly recorded as not executed
- [ ] Mailpit shows OTP emails, notifications, report dispatches
- [ ] `curl http://localhost:8080/api/method/frappe.ping` -> `{"message":"pong"}`

---

## 7. What's Seeded (LOKADO Dataset)

| Category | Count | Detail |
|---|---|---|
| Users | 14 staff + 5 portal | All use password `Ugavi@2024` |
| Donors | 6 | IOM, USAID, Concern, Japan, EU, Own Funds |
| Suppliers | 18 LOKADO scenarios | 15 prequalified, 2 expired, 1 suspended |
| Items | 17 | Stock, fleet spare and service items |
| Warehouses | 13 total | Includes ERPNext defaults/groups; 8 donor-warehouse links |
| Purchase Requisitions | 10 | Direct, restricted, and open methods across Draft, Pending Approval, Approved, and Rejected |
| Tenders | 8 | Open, Restricted and RFQ methods; value ladder 150K-800K |
| Bids | 26 | Distributed across tenders; 3 sealed on IOM Warehouse |
| Bid Opening Record | 0 seeded | Created live only by the verified 3-officer OTP ceremony |
| Evaluation Committee | 1 | Chairperson, Secretary, 3 members, COI declarations |
| Bid Evaluation Summary | 1 | Turkana Construction Ltd recommended |
| Purchase Orders / Contracts | 15 / 15 | 10 POs submitted, 5 draft; every submitted PO has its automatically linked Ugavi Contract |
| Purchase Receipts | 10 | 6 PO-backed donor-warehouse receipts + 4 fleet procurement receipts, all submitted |
| Supplier Evaluations | 12 | All Completed (0–10 scale), receipt- or invoice-linked |
| Standstill Period | 1 | Active 14-day window on Field Motorcycles tender |
| Donor Warehouse links | 8 | Each donor mapped to its physical warehouses |
| Stock Reports | 6 | Current-month, real-ledger quantities and posted values; every donor book (including Own Funds at Oropoi) has rows, gate-reconciled to the Stock Ledger |
| Inter Donor Transfers | 6 | 2 Completed (with linked Stock Entry), 2 Approved, 1 Pending, 1 Rejected |
| Stock Entries | 22 | Submitted receipts, issues and transfer-generated movements in all six donor books; 36 tracked batches |
| Quality Inspections | 8 | Submitted incoming inspections |
| Material Requests | 5 | 3 submitted, 2 draft; reorder levels on 14 item/warehouse rows |
| Purchase Invoices | 8 | 6 receipt-linked (→ 6 Three-Way Match) + 2 direct service invoices |
| Payment Entries | 5 | Full and partial payments; one invoice left unpaid |
| Landed Cost Vouchers | 3 | Submitted against logistics receipts |
| Budgets | 6 | Submitted donor budgets against Donor Profile |
| Vehicles | 4 | ERPNext Vehicles with 4 active donor allocations |
| Fleet reconciliations | 8 | Fully allocated fuel/spare receipt rows |
| Fuel / spare / trip records | 8 each | Submitted evidence linked to purchase and stock sources |
| Fleet reports | 4 | Donor-isolated USAID, IOM, Concern, and EU snapshots |
| Assets | 8 | 8 verifications, 2 completed movements, and 1 independently authorized disposal |
| DoA Rules | 5 | Amount x Department x Donor matrix |
| SoD Rules | 3 | Requester!=Approver, Opener!=Evaluator, Receiver!=Payer |
| Waivers | 1 | Threshold bypass with approval chain |
| Audit Logs | Multiple | Hash chain on critical documents |
---

## 8. Under the Hood — What Makes Ugavi Different

| Capability | How Ugavi Does It | ERPNext Reuse |
|---|---|---|
| Procurement thresholds | Configurable rules engine; effective dates, history, donor/category specificity | PR/PO creation |
| Sealed bids | RSA-4096 + AES-256-GCM envelope, Shamir's 3-of-3 key splitting, 6-digit OTP with rate limiting | — |
| Bid opening | 3 distinct officers, COI check, immutable audit log, signed BOR PDF with hash chain | — |
| Donor segregation | Donor-warehouse links, inter-donor transfer approval, donor-specific stock ledgers | Stock ledger, warehouse |
| Evaluation | Committee with chairperson/secretary/members, weighted scoring, COI declarations | — |
| Standstill | 14-day challenge window, supplier complaint intake, procurement review | — |
| Governance | DoA matrix, SoD server-enforced, hash chain audit, waiver logging | Approvals, user permissions |
| Supplier portal | Identity-bound dashboard, private file uploads, encrypted bid submission, PO acknowledgement | Supplier, PO, PR, Notification |
| Fleet | Vehicle allocation, trip/fuel/spares tracking, service schedule, utilization reports | Vehicle master |
| Assets | QR-tagged register, movement/verification/disposal tracking, donor flagging | Asset master |
| Upgrade safety | Zero ERPNext core patches, hooks-only customization, upgrade dry-run CI | Full ERPNext v16 |

---

## 9. Related Documents

- [Functional Requirements Tour](demo/LOKADO-DEMO-TOUR.md) — per-requirement walkthrough
- [Supplier Journey Guide](demo/SUPPLIER-JOURNEY.md) — portal-specific presenter guide
- [Requirements Traceability Matrix](traceability/RTM.md) — requirement to implementation evidence
- [Architecture](ARCHITECTURE.md) — design patterns, extension points
- [MVP2 Open Questions](mvp2/OPEN-QUESTIONS.md) — decisions awaiting client input

---

**Last updated:** 2026-10-23 | **Ugavi v0.1.0** | **For LOKADO demo only**
