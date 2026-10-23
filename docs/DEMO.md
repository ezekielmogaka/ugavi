# Ugavi Demo — Presenter Runbook

> **Audience:** LOKADO (Lotus Kenya Action for Development Organization) leadership  
> **Stack:** Frappe 16.52.0 + ERPNext 16.51.1 + Ugavi 0.1.0  
> **Duration:** 55-75 minutes (full tour) or ~15 minutes per scene for standalone  
> **Business persona passwords:** `Ugavi@2024` (development-only; seed-script enforced)

This runbook is for the **Ugavi team** to present the working MVP1 system. It is not the
technical setup guide — for that see the inline commands, Make targets, and
`docs/demo/LOKADO-DEMO-TOUR.md`.

---

## 0. Before you present (checklist — 5 minutes)

```bash
make setup                    # Build image, bring up all services
make upgrade-check            # Rebuild + migrate + backend tests
make seed                     # Populate the LOKADO dataset (idempotent; alias: seed-lokado)
make demo-check               # Verify users, passwords, record counts (19 users, 0 issues)
make fleet-check              # Verify purchase-backed fleet reconciliation
make backup-demo              # Safety net: dump LOKADO data to backups/ (optional but recommended)
```

Expected output:
- `{"compatible": true, "issues": [], "missing_controllers": []}`
- `{"message":"pong"}` from `curl http://localhost:8080/api/method/frappe.ping`
- backend output: `Ran 57 tests` followed by `OK`
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

Open three browser tabs before the demo:
1. **Desk** at `http://localhost:8080` (log in with the persona for the first scene)
2. **Supplier portal** at `http://localhost:8080/supplier/dashboard` (logged in as `lodwar-supplies@outlook.com`)
3. **Mailpit** at `http://localhost:8026` (shows all system emails)

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
| 12 | Robert Lotukoi | `auditor@lokado.org` | Internal Auditor | Governance |
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
core ERPNext. All our features live in the `ugavi` app, which uses hooks, custom
DocTypes, and extension points. This means you get ERPNext upgrades forever
without breaking Ugavi."

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
4. Save -> system identifier generates PR-LOKADO-YYYY-XXXXX.
5. Submit -> workflow sends to Approver Level 1.

**What to say:** "Every purchase starts with a requisition. The system
automatically determines the procurement method based on your configured
thresholds. Alice doesn't need to know procurement rules — the system
applies them. The donor dimension and programme code are mandatory."

**Validation checkpoint:** PR status = "Submitted for Approval",
method = "Restricted", donor = IOM.

---

### Scene 2: Approval Chain — Two levels of sign-off (5 min)

```
Log out
Log in as: approver1@lokado.org / Ugavi@2024
Navigate: Purchase Requisition list -> find Alice's PR
```

1. Jane Napeyok (Programmes Director) opens the PR.
2. Click "Approve" -> status changes to "Approved Level 1", routed to Finance.
3. Jane notes the PR is within her DoA limit (up to KES 500,000 for IOM).

```
Log out
Log in as: approver2@lokado.org / Ugavi@2024
```

4. Paul Lotir (Finance Manager) opens the PR, clicks "Approve".
5. Status = "Approved". Show audit log entry: who, when, from which IP.

**What to say:** "The approval chain enforces LOKADO's Delegation of Authority
matrix. Every approval is audited — immutable record of who, when, and from
where. Segregation of Duties prevents the same person from both requesting
and approving."

**Validation checkpoint:** PR status = "Approved", two approval events.

---

### Scene 3: Tender Creation — From PR to published opportunity (5 min)

```
Log out
Log in as: procurement@lokado.org / Ugavi@2024
Navigate: Ugavi Tendering -> Tender list
Click on: IOM Warehouse Construction Kakuma (Open, KES 800,000)
```

1. Peter Ekai opens the pre-seeded Open Tender.
2. Show: type = Open, estimated value = KES 800,000, category = Construction.
3. Navigate to the "Bids" child table — show 3 sealed bids.
4. Show the addendum: steel spec S275->S355, deadline extended +7 days.

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

**Step A — Peter creates the BOR:**
1. Peter opens IOM Warehouse tender -> "Create Bid Opening Record".
2. System creates BOR, assigns 3 officers, generates OTPs.

**Step B — Mary Akuom:**
3. Log in as `opening1@lokado.org`, open the BOR.
4. Enter OTP from Mailpit (6-digit, 5-min expiry, 3-attempt limit).
5. System verifies, reconstructs share 1/3.

**Step C — James Ebei:** `opening2@lokado.org` -> OTP -> share 2/3.

**Step D — Sarah Nabwel:** `opening3@lokado.org` -> OTP -> share 3/3.

**Step E — Decryption:**
6. All 3 shares verified -> Shamir's 3-of-3 key reconstruction.
7. All 3 bid amounts decrypted and revealed.
8. BOR signed with hash chain, locked as immutable.

**What to say:** "No single officer can open bids alone. No two officers can.
You need all three with valid OTPs. The private key was never stored whole —
it was split into three shares at generation time. The entire ceremony is
recorded in an immutable hash chain."

**Validation checkpoint:** BOR status = "Completed", all 3 bid amounts visible.

---

### Scene 5: Bid Evaluation -> Award -> Contract (7 min)

```
Keep Peter Ekai logged in
```

1. Navigate to `Evaluation Committee` for IOM Warehouse.
2. Show: Chairperson, Secretary, 3 members, COI declarations submitted.
3. Show `Bid Evaluation Summary` — weighted scoring (technical 60%, financial 40%).
4. System recommends Turkana Construction Ltd (KES 1,150,000, score 82/100).
5. Click "Award Tender" -> auto-creates Purchase Order + Ugavi Contract.
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

1. 6 donor-segregated warehouses (Kakuma, Lodwar, Lokichoggio, Kitale, Oropoi).
2. Monthly Stock Report for IOM — opening/closing balance, consumption, value.
3. Inter Donor Transfer — Japan -> IOM approved transfer.
4. Stock Ledger filtered by donor — no cross-donor consumption.
5. Scheduled monthly report generation and email dispatch.

**What to say:** "Every item is tagged by donor. Stock from IOM cannot be
consumed for a USAID programme without an approved inter-donor transfer."

**Validation checkpoint:** 6 Donor Warehouses, 2+ Stock Reports, 1 Transfer.

---

### Scene 8: Fleet Management & Assets (5 min)

```
Log out
Log in as: fleet@lokado.org / Ugavi@2024
Navigate: Ugavi Fleet -> Fleet Dashboard
```

1. Fleet Dashboard: 5 vehicles, utilization chart, service schedule.
2. Vehicle Allocations — 4 active allocations.
3. Fuel Log — 6 entries with cost per km.
4. Trip Log — 3 trips with odometer readings.
5. Spare Parts Issue — parts issued to vehicles.

```
Navigate: Ugavi Assets -> Asset Register
```

6. Asset Register — 5 assets with QR codes.
7. Asset Movement records — custody tracking.
8. Asset Verification — scheduled reminders (every 180 days).

**What to say:** "LOKADO's fleet tracks every trip, fuel purchase, and spare
part issue. Assets are QR-tagged and tracked through movement and verification
cycles — essential for donor audit requirements."

**Validation checkpoint:** 5 vehicles, 4 allocations, 6 fuel logs, 5 assets.

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

1. Purchase Order for IOM Warehouse (KES 1,150,000).
2. Purchase Receipt (when goods are received).
3. Purchase Invoice (supplier invoice).
4. Three-Way Match — PO/GRN/Invoice comparison with tolerances.
5. Budget Encumbrance — PO committed KES 1,150,000 against IOM budget.

**What to say:** "Before payment, the system verifies PO, GRN, and Invoice
match within your configured tolerances. Budget encumbrance happens at PO
creation — money is committed before delivery."
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
DocTypes, and extension points only. When Frappe releases version 17, LOKADO
upgrades without breaking Ugavi."

---

### Scene 12: MVP2 Readiness Preview (5 min — Optional)

**Already implemented for MVP2:**
1. Standstill Period + Tender Complaints — supplier challenge workflow.
2. Fleet Maintenance Schedule — upcoming service dates, cost per km tracking.
3. Asset QR Verification — print format with QR code for field verification.
4. Contract Retention Release — automated release at final acceptance.
5. Monthly Donor Narrative Reports — PDF generation and email.

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
| Full reset needed | `make reset-demo` (destroys DB + site volumes) |
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
| Items | 15 | Hygiene kits, WASH tanks, pipes, goats, construction |
| Warehouses | 6 | Across Kakuma, Lodwar, Lokichoggio, Kitale, Oropoi |
| Purchase Requisitions | 10 | Direct, restricted, and open methods across Draft, Pending Approval, Approved, and Rejected |
| Tenders | 5 | 2 Open, 2 Restricted, 1 RFQ; value ladder 150K-800K |
| Bids | 15 | Distributed across tenders; 3 sealed on IOM Warehouse |
| Bid Opening Record | 0 seeded | Created live only by the verified 3-officer OTP ceremony |
| Evaluation Committee | 1 | Chairperson, Secretary, 3 members, COI declarations |
| Bid Evaluation Summary | 1 | Turkana Construction Ltd recommended |
| Contracts | 5 | Active evidence-backed records automatically linked to submitted Purchase Orders |
| Purchase Receipts | 4 | Submitted donor fleet procurement receipts |
| Supplier Evaluations | 4 | Completed evaluations linked to submitted receipts |
| Standstill Period | 1 | Active 14-day window on Field Motorcycles tender |
| Donor Warehouse links | 6 | Each donor mapped to physical warehouse |
| Stock Reports | 6 | One monthly stock book for every donor scenario |
| Inter Donor Transfers | 3 | Approved, pending-approval, and rejected outcomes |
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
- [Architecture Decision Record](../ARCHITECTURE.md) — design patterns, extension points
- [MVP2 Open Questions](../mvp2/OPEN-QUESTIONS.md) — decisions awaiting client input

---

**Last updated:** 2026-10-22 | **Ugavi v0.1.0** | **For LOKADO demo only**
