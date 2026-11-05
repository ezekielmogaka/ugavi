# Ugavi Demo — Presenter Runbook

> **Audience:** LOKADO (Lotus Kenya Action for Development Organization) leadership  
> **Historical stack verified 2026-10-23:** Frappe 16.53.0 + ERPNext 16.52.1 + Ugavi 0.1.0
> **Duration:** 55-75 minutes (full tour) or ~15 minutes per scene for standalone  
> **Business persona passwords:** `Ugavi@2024` (development-only; seed-script enforced)

This runbook is for the **Ugavi team** to present the working MVP1 system. It is not the
technical setup guide — for that see the inline commands and Make targets.
For the expanded November seed, use the
[step-by-step functional tour](demo/LOKADO-DEMO-TOUR.md) as the primary runbook:
it includes exact record locators, inputs, role handoffs, expected outcomes,
and intentional live-workflow boundaries. On 2026-11-05 `ugavi.localhost` was
rebuilt from scratch with `make clean && make setup && make seed-lokado`; the
acceptance and fleet gates reported `"ready": true` with no issues, and the
`make backup-demo` → `make restore-demo` round-trip passed. These are historical
results, not proof of the current site's state. The expanded tour is the
authoritative source for current scene prerequisites and limitations.
Use the [requirement-to-scene map](demo/LOKADO-DEMO-TOUR.md#4-requirement-to-scene-map)
for the original client scope and the [evidence registry](traceability/evidence.md)
for the distinction between automated checks and live presenter actions.

---

## 0. Before you present (checklist — 5 minutes)

Everything is a `make` target run from the repository root:

```bash
# Fresh disposable demo only (DESTRUCTIVE: deletes DB, files and backups/)
make clean && make setup && make seed-lokado

# Or, keep the data and load new code / refresh the seed (idempotent)
make setup && make seed-lokado

make demo-check               # LOKADO gate: 21 users, "ready": true, no issues
make fleet-check              # purchase-backed fleet reconciliation
make demo-index               # real record IDs + links for the tour worksheet
make e2e                      # browser gate, after host prerequisites below
make backup-demo              # snapshot DB + files to backups/lokado-demo/
```

After a rehearsal that opened tenders or posted stock, `make restore-demo`
returns to the snapshot. `make backup-demo` replaces any previous demo
snapshot; preserve older backups elsewhere first. `make clean` also deletes
the local `backups/` contents. `make reset-lokado` reinstalls the site and
reseeds without rebuilding containers. `make upgrade-check` rehearses an
upstream upgrade (rebuild, migrate, configure, backend tests).

`make seed-lokado`/`demo-check` run the code baked into the image; `make setup`
rebuilds it. If a count, ledger reconciliation or lineage gate fails, capture
the output and investigate the image and data; do not reset a shared site
without preserving the data and backups needed.

For source-mounted development, run `make dev-up` in one terminal, then
`make dev-config dev-seed dev-check dev-test` in another, and test it with
`UGAVI_BASE_URL=http://ugavi.localhost:8000 make e2e`. `make dev-reset`
reinstalls and reseeds from local source. `make help` and the
[Make reference](../README.md#makefile-reference) list every target.
Do not run `seed-generic` alongside the canonical LOKADO seed.

Expected output:
- `{"compatible": true, "issues": [], "missing_controllers": []}`
- `{"message":"pong"}` from `curl http://localhost:8080/api/method/frappe.ping`
- backend output: integration and unit runners both finish with `OK`
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
3. **Mailpit** at `http://localhost:8026` (local email capture; no external delivery).
   Before sending, verify the default outgoing account actually points to
   `mailpit:1025`; the seed preserves an existing default. See the
   [mail preflight](demo/LOKADO-DEMO-TOUR.md#14-communication-and-message-evidence).

---

## 1. Demo credentials — all-in-one
### Desk users (16 staff personas)

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
| 14 | Dorothy Nekesa | `committee@lokado.org` | Evaluation Committee (secretary) | Bid Evaluation |
| 15 | Grace Lokwang | `chair@lokado.org` | Tender Committee Chair | Evaluation Minutes / Bid Evaluation Summary |
| 16 | Samuel Lomuria | `evaluator@lokado.org` | Evaluation Committee (member) | Evaluation Score |

**Password for all staff:** `Ugavi@2024`

### Supplier portal users (5 supplier organizations)

| Supplier | Portal login | Password | Used for |
|---|---|---|---|
| Turkana Construction Ltd | `turkana-construction@outlook.com` | `Ugavi@2024` | Prepared receipt-backed PO and contract |
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

> **Narrative:** LOKADO works across donor-funded programmes in Turkana County.
> The demonstration connects a live requisition and tender exercise to
> separately prepared opening, standstill, receipt and finance evidence.
> Follow saved links; do not present separate branches as one completed purchase.

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

### Scene 1: Purchase Requisition — Alice needs water tanks (5 min)

```
Log out Administrator
Log in as: programme@lokado.org / Ugavi@2024
Navigate: Purchase Requisition list -> + New
```

**What to show:**
1. Follow [Scene 7](demo/LOKADO-DEMO-TOUR.md#scene-7-purchase-requisition-and-approval)
   to create Alice's IOM WASH request for 12 water tanks at KES 37,500 each.
2. Select the IOM donor and `Emergency WASH - LOKADO` department.
3. Save and show the **procurement method** is Restricted for KES 450,000.
4. Save -> system identifier generates `PR-<DONOR>-<YEAR>-<SEQUENCE>`.
5. Click **Submit for Approval** -> the displayed DoA chain determines the next role.

**What to say:** "Every purchase starts with a requisition. The system
automatically determines the procurement method based on your configured
thresholds. The saved donor and department determine the applicable context;
inspect the displayed budget response rather than assuming funds are available."

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

**What to say:** "The displayed Delegation of Authority chain controls the
required roles. Inspect the saved approval actor, time and remarks.
The requester cannot approve their own requisition."

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

**What to say:** "The seeded solar tender has four submitted sealed bids.
Supplier submission uses a different, still-open opportunity. Publishing
an opportunity does not itself send supplier invitation emails."

**Validation checkpoint:** use `make demo-index`; solar is closed with four
Submitted bids and no Bid Opening Record before the live ceremony.
The current PR **Create Tender** shortcut calls an unavailable method: use
the manual approved-PR link in
[Scene 9](demo/LOKADO-DEMO-TOUR.md#scene-9-tender-publication-and-opportunities).
---

### Scene 4: Sealed-Bid Opening Ceremony — 3 officers, 3 keys (8 min)

> This is the security showcase. Mary conducts one authorized session; each
> of the three officers supplies their own code.

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
Codes expire; the current flow permits correction of a mistyped code before
successful opening. Avoid turning the live fixture into a rate-limit test.

**Step E — Decryption:**
6. All 3 shares verified -> Shamir's 3-of-3 key reconstruction.
7. All four bid amounts are decrypted and revealed.
8. Inspect the generated BOR, its private PDF and recorded opening evidence.

**What to say:** "No single officer can open bids alone. No two officers can.
You need all three valid codes. The private key is encrypted at rest and its
wrapping key is split into three shares. The opening produces an immutable
record and hash evidence."

**Validation checkpoint:** BOR `outcome = Success`, private PDF attached, four
bid amounts visible, Tender `Under Evaluation`. The seed does not undo this
ceremony. Use `make backup-demo` beforehand and `make restore-demo` to return
to that snapshot after the rehearsal.

---

### Scene 5: Evaluation -> Standstill -> Contract evidence (7 min)

```
Log in as: procurement@lokado.org / Ugavi@2024
```

1. Follow [Scene 12](demo/LOKADO-DEMO-TOUR.md#scene-12-evaluation-and-award-decision)
   for Livestock Galla Goats USAID: three COI declarations, nine individual
   scores, chair-approved minutes and Nadirkonyen's KES 365,000 recommendation.
2. Start the genuine standstill if it is still available. Show the default
   14-day challenge window and explain the complaint gate.
3. Stop before award: confirmation requires the period to end and open
   complaints to be resolved. Do not edit the deadline.
4. For contract evidence, follow the separate receipt-backed Turkana
   Construction PO and its Ugavi Contract. Inspect its actual milestone,
   agreement, retention and bond fields.

**What to say:** "After a genuinely confirmed standstill, the award action can
create a Purchase Order and contract. Today we show the gate and a separate
prepared contract rather than inventing a same-day award."

**Validation checkpoint:** prepared recommendation and a real active standstill;
the separately linked PO/contract is not proof of this tender's award.

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
7. **Awards & Contracts** — actual supplier-scoped records; the prepared
   contract belongs to a separate receipt-backed PO and Awards may be empty.
8. **Deliveries** — Purchase Order with Acknowledge button, receipt progress
   from ERPNext.
9. **Evaluations** — post-receipt performance scores.
10. **Notifications** — submission receipts, award notifications.

**What to say:** "The portal resolves the signed-in supplier and scopes its
records accordingly. Compare two demo accounts without claiming this single
observation proves every possible access path is secure."

**Known limitation:** the supplier invoice form currently fails the native
invoice mapper's create-permission check for the seeded website user. Show a
prepared invoice; do not broaden Desk permissions to work around it. A
disabled Supplier was also able to submit an open-tender bid in a rollback-only
probe; do not claim suspension currently blocks every bid.
---

### Scene 7: Logistics & Donor Stock Segregation (6 min)

```
Log out of supplier portal
Log in as: logistics@lokado.org / Ugavi@2024
Navigate: Ugavi Logistics -> Donor Warehouse list
```

1. Donor-warehouse links across six donors.
2. Monthly Stock Report for IOM — opening/closing balance, consumption, value.
3. Inter Donor Transfer — inspect the prepared IOM -> CONCERN completed
   transfer and its linked stock entry.
4. Filter the native Stock Ledger by the mapped warehouse and item; compare
   the prepared donor-book snapshot.
5. Scheduled report email depends on recipients and workers. The current
   Monthly Stock Report Desk form has no supported Generate action.

**What to say:** "The donor book is tied to its mapped warehouse. Show the
governed inter-donor transfer and its stock posting rather than claiming that
every item master is itself donor-specific."

**Validation checkpoint:** six donor books and prepared report/transfer
evidence; use the [full scene](demo/LOKADO-DEMO-TOUR.md#scene-14-receipt-dispatch-stock-ledger-and-donor-books)
for actual links and current balances.

---

### Scene 8: Fleet Management & Assets (5 min)

```
Log out
Log in as: fleet@lokado.org / Ugavi@2024
Navigate: Ugavi Fleet -> Fleet Dashboard
```

1. Find the IOM vehicle `KDM 271I` and its active allocation.
2. Follow its submitted purchase receipt to fuel and spare reconciliation.
3. Inspect the linked Fuel Log, Spare Parts Issue and Trip Log records.
4. Open the prepared donor Fleet Utilization Report: its range is about
   60 days, not one calendar month. The current form has no Generate button.

```
Log out and log in as: assets@lokado.org / Ugavi@2024
Navigate: Ugavi Assets -> Asset Register
```

5. Asset Register — inspect donor, current custodian, location and condition.
6. Asset Movement and Verification — inspect prepared completed evidence.
7. Asset Disposal — inspect its independent authorizer and recorded outcome.

**What to say:** "These prepared records connect fleet consumption to purchase
sources and track asset custody. They do not prove a generated monthly fleet
report, live reminder delivery or native ERPNext asset depreciation."

**Validation checkpoint:** follow the exact source records and the
[asset](demo/LOKADO-DEMO-TOUR.md#scene-17-asset-management) and
[fleet](demo/LOKADO-DEMO-TOUR.md#scene-18-fleet-management) scene boundaries.

---

### Scene 9: Governance & Audit (5 min)

```
Log out
Log in as: auditor@lokado.org / Ugavi@2024
Navigate: Governance module
```

1. Audit Log — compare actual session events with illustrative seed entries.
2. Delegation of Authority — 5-tier matrix (amount x department x donor).
3. Segregation of Duties — inspect each rule's actual enforcement; a
   `Warning Only` rule is not a block.
4. Waiver — threshold bypass with all approvals logged.

**What to say:** "Inspect the recorded actor, event and outcome, and demonstrate
the requester/approver separation on the live PR. An illustrative audit row
does not prove complete coverage or independently verify every hash chain."

**Validation checkpoint:** actual applicable DoA, SoD, waiver and audit records.

---

### Scene 10: Finance — Three-Way Match & Budget Control (5 min)

```
Log out
Log in as: finance@lokado.org / Ugavi@2024
Navigate: Finance -> Three-Way Match
```

1. Open the Three-Way Match for a prepared receipt-linked invoice, e.g.
   `LOK-INV-TCL-0412`, Turkana Construction -> IOM Kakuma.
2. Drill into the linked Purchase Order → Purchase Receipt → Purchase Invoice
   and show the PO/GRN/Invoice quantity and rate comparison.
3. Payments: inspect submitted full and partial Payment Entries. Lodwar General
   Supplies (`LOK-INV-LGS-1190`) is deliberately left unpaid to show an open
   payable; inspect the linked purchase evaluations for the shown entries.
4. Landed Cost Vouchers: inspect freight allocated to a receipt's valuation.
5. Budgets: inspect donor budgets (`Budget Against = Donor Profile`), e.g.
   IOM Freight KES 1,150,000, CONCERN Admin KES 1,200,000, with Warn actions.
6. Budget Encumbrance is conditional on a submitted PO having `ugavi_budget`;
   the inspected seed contains no encumbrance rows.

**What to say:** "Invoice submission creates PO/GRN/invoice matching evidence
and flags disputes for review. Finance must review it; this is not a claim of
an automatic mismatch-payment block. A separate evaluation gate checks
supplier Pay entries that reference Purchase Invoices; do not generalize it
to unallocated advances. Do not claim a budget commitment where no encumbrance
record was created."
---

### Scene 11: Finale — Upgrade Safety & Health Check (3 min)

```
Back to terminal
```

```bash
make demo-check
# -> Review ready/issue output and ping result
```

**What to say:** "Ugavi has zero ERPNext core patches. We use hooks, custom
DocTypes, and extension points. The pinned v16 migration passes. A v17 upgrade
still requires compatibility review, migration tests and a backup/restore rehearsal."

---

### Scene 12: MVP2 Readiness Preview (5 min — Optional)

**Already implemented for MVP2:**
1. Standstill Period + Tender Complaints — supplier challenge workflow.
2. Fleet source records and a prepared date-range report; a calendar-month
   report and cost-per-km analytics are not demonstrated.
3. Asset custody and verification records; QR scanning is not rehearsed.
4. Contract milestones, retention/bond tracking and completion checks;
   demonstrate only the verified lifecycle, not an external cash release.
5. Prepared monthly donor stock-report snapshots; the current Desk form has no
   Generate action, and client-specific layouts still need approved templates.

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
| 8:00 | Scene 5: Evaluation -> Standstill gate | `procurement@lokado.org` |
| 12:00 | Scene 6: Supplier Portal | `lodwar-supplies@outlook.com` |
| 14:00 | Scene 11: Health Check + Upgrade | Terminal |
| 15:00 | Done | — |

---

## 5. Troubleshooting Demo Day

| Problem | Fix |
|---|---|
| "Backend not ready" | Wait for startup, then run `make demo-check`; use `make dev-logs` for the development stack |
| Configurator name conflict | `make upgrade-check` (handles it automatically) |
| Demo users don't exist | `make seed-lokado` (idempotent, safe to re-run) |
| Wrong password | `make seed-lokado` restores `Ugavi@2024` |
| OTP not in Mailpit | Check the default outgoing account is `mailpit:1025`, the officer recipient and Email Queue; then refresh Mailpit |
| SSL / HTTPS error | Use `http://` not `https://` (local development) |
| Browser shows old data | Hard refresh (Cmd+Shift+R) or clear cache |
| Fresh disposable site needed | Preserve required data/backups outside the workspace; `make clean && make setup && make seed-lokado` is destructive |
---

## 6. Validation Checklist (Presenter)

- [ ] All 16 staff users login with `Ugavi@2024`
- [ ] All 5 supplier portal users login with `Ugavi@2024`
- [ ] PR created with auto-determined procurement method (Restricted for KES 450K)
- [ ] Actual required approval chain completes
- [ ] Solar tender has four submitted sealed bids before opening
- [ ] Bid Opening Record: 3-of-3 officers, OTPs, decryption, hash chain
- [ ] Livestock recommendation and real standstill shown; award remains gated
- [ ] Separate prepared PO and contract checked for their saved milestone,
      agreement and applicable retention/bond fields
- [ ] Supplier portal: journey readiness + next-best-action
- [ ] Portal invoice permission limitation disclosed
- [ ] Standstill period active for Field Motorcycles tender
- [ ] Complaint intake working (supplier submits, procurement reviews)
- [ ] 6 donor books, 6 stock reports, and approved/pending/rejected transfer examples
- [ ] Fleet: purchase-backed IOM fuel, spares and trips plus prepared date-range report
- [ ] Assets: prepared custody, verification, movement and authorized disposal
- [ ] Governance: applicable DoA, SoD, waiver and actual audit events
- [ ] Three-way match: inspect actual PO, receipt and invoice comparison
- [ ] `make demo-check` passes with `"ready": true`
- [ ] `make fleet-check` passes with `"ready": true`
- [ ] Playwright prerequisites are installed and `make e2e` passes, or the
      browser gate is explicitly recorded as not executed
- [ ] Mailpit shows opening OTP emails after the local relay is verified;
      other notifications or report emails are claimed only when observed
- [ ] `make demo-check` includes a successful `{"message":"pong"}` health response

---

## 7. What's Seeded (LOKADO Dataset)

The following is the expanded seed baseline, not a promise that records still
have the same state after a rehearsal. Run `make demo-index` and the gates.

| Category | Baseline | Detail |
|---|---|---|
| Users / donors / suppliers | 16 staff + 5 portal / 6 / 30 | Additional supplier masters do not imply additional logins |
| Purchase Requisitions / tenders / submitted bids | 25 / 20 / 46 | Status and eligibility differ; solar is reserved for live opening |
| Opening / evaluation evidence | 2 seeded BORs, 2 approved recommendations | Livestock can start standstill; Motorcycles has a time-limited complaint window |
| Submitted purchase histories | 24 logistics + 8 fleet receipts | Separate from the not-yet-awarded live tender scenarios |
| Invoices / payments / completed evaluations | 22 receipt-linked + 4 service / 19 / 36 | Includes full, partial and unpaid examples |
| Stock / donor books | 53 Stock Entries, 6 reports, 6 completed transfers | Reports are ledger-derived snapshots |
| Vehicles / fuel / spares / trips | 8 / 16 / 16 / 16 | Six prepared donor reports span about 60 days |
| Assets | 16 registers and verifications, 4 completed movements, 1 disposal | Ugavi custody evidence, not proof of ERPNext depreciation |
| Finance setup | 8 landed-cost vouchers, 10 budgets | Budgets warn; the inspected seed has no encumbrance rows |
---

## 8. Under the Hood — What Makes Ugavi Different

| Capability | How Ugavi Does It | ERPNext Reuse |
|---|---|---|
| Procurement thresholds | Configurable rules engine; effective dates, history, donor/category specificity | PR/PO creation |
| Sealed bids | RSA-4096 + AES-256-GCM envelope, Shamir's 3-of-3 key splitting, 6-digit OTP with rate limiting | — |
| Bid opening | 3 distinct officers, codes in one authorized session, generated BOR and private PDF | — |
| Donor segregation | Donor-warehouse links, inter-donor transfer approval, donor-specific stock ledgers | Stock ledger, warehouse |
| Evaluation | Committee with chairperson/secretary/members, weighted scoring, COI declarations | — |
| Standstill | 14-day challenge window, supplier complaint intake, procurement review | — |
| Governance | DoA matrix, SoD server-enforced, hash chain audit, waiver logging | Approvals, user permissions |
| Supplier portal | Identity-bound dashboard, private files, encrypted bids and PO acknowledgement; invoice action currently blocked | Supplier, Purchase Order, Purchase Receipt, Notification Log |
| Fleet | Vehicle allocation, trip/fuel/spares tracking, service schedule, utilization reports | Vehicle master |
| Assets | App-owned register, movement/verification/disposal tracking, donor flagging | Native ERPNext Asset is a separate lifecycle |
| Upgrade safety | Zero ERPNext core patches, hooks-only customization, upgrade dry-run CI | Full ERPNext v16 |

---

## 9. Related Documents

- [Functional Requirements Tour](demo/LOKADO-DEMO-TOUR.md) — per-requirement walkthrough
- [Supplier Journey Guide](demo/SUPPLIER-JOURNEY.md) — portal-specific presenter guide
- [Requirements Traceability Matrix](traceability/RTM.md) — requirement to implementation evidence
- [Architecture](ARCHITECTURE.md) — design patterns, extension points
- [MVP2 Open Questions](mvp2/OPEN-QUESTIONS.md) — decisions awaiting client input

---

**Ugavi v0.1.0** | **For LOKADO demo only**
