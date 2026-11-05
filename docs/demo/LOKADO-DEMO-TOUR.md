# LOKADO Functional-Requirements Demo Tour

> **Client:** Lotus Kenya Action for Development Organization (LOKADO)  
> **Tour revised:** 2026-11-05 against the expanded [LOKADO seed](../../ugavi/scripts/seed_lokado.py).
> **Full workshop:** 90-120 minutes including live handoffs. **Executive tour:** 30 minutes using prepared evidence.

This is a presenter runbook, not just a feature list. Each scene names the
business need, actor, exact seed record or input, action, expected evidence,
and stopping point. Keep this document open beside the application.

**Evidence boundary:** on 2026-11-05 the demo site `ugavi.localhost` was
rebuilt from scratch with `make clean && make setup && make seed-lokado`. The
seed ended with the acceptance gate `"ready": true` and empty issues. A second
`make seed-lokado` run (idempotent), `make demo-check`, `make fleet-check`,
`make demo-index`, `make test` (17 integration + 67 unit tests) and `make e2e`
(19 browser tests, including the committee chair and evaluator) also passed.

The seed drives two tenders through the **real** evaluation controllers. It
uses the officer codes delivered to Mailpit, signed COI declarations,
individual scores, chair-approved minutes and a chair-approved recommendation:

- **Livestock Galla Goats USAID** stops at *Under Evaluation* with an approved
  recommendation, so Peter can start the standstill live (Scene 12).
- **Field Motorcycles Peace Building USAID** is in an active 14-day standstill,
  so Lodwar General can lodge a real complaint (Scene 19).
- **Solar Water Pumps EU Resilience** stays sealed for the live three-officer
  opening (Scene 11).

No standstill is backdated and no award is fabricated. Confirm the gates
before presenting.

## 1. Prepare and validate

### 1.1 Make-only command recipes

Run everything from the repository root with `make`. No manual `docker` or
`bench` commands are required.

**Demo stack (image, port 8080): the presenter path**

```bash
# From scratch: DESTRUCTIVE (deletes DB, files and the host backups/ folder)
make clean && make setup && make seed-lokado

# Gates (the seed already runs the LOKADO gate at the end)
make demo-check
make fleet-check
make e2e                      # optional browser gate
make test                     # optional unit + integration tests

# Print this site's real record IDs and links for the worksheet (section 3.3)
make demo-index

# Freeze the verified state before rehearsing live actions
make backup-demo              # writes backups/lokado-demo/
```

| Situation | Command |
|-----------|---------|
| Code changed, keep data | `make setup && make seed-lokado` |
| Re-run seed only (idempotent) | `make seed-lokado` |
| Undo a rehearsal (opened tenders, receipts, etc.) | `make restore-demo` |
| Wipe site data but keep containers | `make reset-lokado` |
| Start over completely | `make clean && make setup && make seed-lokado` |
| Rehearse an upstream upgrade | `make upgrade-check` |
| Pause / resume without data loss | `make stop` / `make start` |

`make setup` always rebuilds the image, so it is how new code reaches port 8080.
`make seed-lokado`, `make demo-check` and `make fleet-check` run the **baked**
image code. A failure such as `expected at least 40`, unreconciled Monthly Stock
Reports or invalid tender lineage means an old image or data from an older seed.
Fix it with `make clean && make setup && make seed-lokado`.

**Development stack (mounted source, port 8000)**

```bash
make dev-up                   # terminal 1, foreground
make dev-config dev-seed dev-check dev-test     # terminal 2
UGAVI_BASE_URL=http://ugavi.localhost:8000 make e2e
make dev-reset                # DESTRUCTIVE: reinstall + config + seed + check from local source
```

Every site-scoped target accepts `SITE=<site>` to target another installed site.
It does not create a new site. Development and image services share the same
database. To inspect the seed log for warnings, capture it:

```bash
make seed-lokado > /tmp/lokado-demo-seed.log 2>&1
grep -nE 'FAILED|Traceback|Could not create|SKIP|skipped|ERROR' /tmp/lokado-demo-seed.log
```

The gate checks the expanded minimums, each invoice's PO/receipt/warehouse
and scorecard lineage, and PR-to-tender donor/method/approval alignment.
It also checks ledger-derived Monthly Stock Reports and sealed-opening
controls. It rejects approved recommendations on unopened bids. It is not
proof that a live tender award or external payment gateway has completed.

Browser prerequisites, if the chosen browser test command reports missing
dependencies or Chromium:

```bash
cd tests/e2e
npm ci
npx playwright install chromium
cd ../..
```

See the [complete Make reference](../../README.md#makefile-reference) and
[developer onboarding](../developer-onboarding.md) for build/migration details.

### 1.2 Presenter readiness checklist

- [ ] Open `http://ugavi.localhost:8000` (development) or
      `http://ugavi.localhost:8080` (image rehearsal), then `/login`.
- [ ] Open Mailpit at `http://localhost:8026` (dev-only mail catcher; the seed
      configures the **LOKADO Demo Mailpit** outgoing account). Opening codes
      arrive there as `Bid Opening OTP - <tender>`.
- [ ] Run `make demo-index` and paste the IDs into the
      [record worksheet](#33-record-finding-worksheet).
- [ ] Confirm the demo and fleet gates report `ready: true` and empty issues.
- [ ] Review seed failures even when the command exits successfully.
- [ ] Use the [record worksheet](#33-record-finding-worksheet) to locate each
      scene's real records, statuses, dates, and links.
- [ ] Confirm all five supplier accounts land on `/supplier/dashboard`.
- [ ] Prepare fictional PDF attachments: registration certificate, tax
      compliance, bid proposal, delivery acceptance, and complaint evidence.
      Mark them **DEMO ONLY**; do not upload real personal or banking data.
- [ ] Reserve the solar-pump tender for the live opening; do not consume it
      in a rehearsal on the same site.
- [ ] Confirm a still-open tender with no existing bid for the chosen supplier.
- [ ] For complaints, confirm the Motorcycles Standstill Period is **Active**
      and its end date is still in the future (`make demo-index`). The window
      was opened by the real `start_standstill` action at seed time; reseed with
      `make clean && make setup && make seed-lokado` if it has expired.
- [ ] Confirm the actual approval chain and each actor's required role.
- [ ] Rehearse action availability. Some app controllers expose server
      methods without a dedicated Desk button; use prepared evidence if the
      installed UI does not expose the action. Do not improvise status edits.
- [ ] Run `make backup-demo` before live opening, receipt, stock issue, or
      disposal; `make restore-demo` resets the rehearsal afterwards.

**Reset is not a presentation shortcut.** `make clean`, `make dev-reset` and
`make reset-lokado` destroy the current site data. Run `make backup-demo` first;
`make restore-demo` returns to that snapshot.
Re-seeding restores demo passwords and adds fixtures, but does not undo
completed opening ceremonies or business transactions.

### 1.3 Verified expanded dataset and intentional live boundaries

| Verified evidence on the isolated site | Presenter consequence |
|---|---|
| 30 suppliers, 25 PRs, 20 source-linked tenders, 46 submitted bids | Approved opportunities have bids; Draft/Pending source requests do not produce published tenders |
| New requests belong to Alice and progress through real delegated submit/approve/reject methods | Read the approval history and actual roles; no forced Approved seed status |
| Japan lantern and delivery-kit tenders are Restricted | Values below KES 500,000 follow the default bands and explicit category prequalification |
| 24 logistics receipts plus eight fleet receipts, all with submitted native POs | Prepared purchase histories are independent of the still-live tender awards |
| 22 receipt-linked invoices plus four direct-service invoices; 19 payments | Show completed, partial and unpaid obligations; Mobile Money entries are accounting examples, not live M-Pesa transfers |
| 36 completed source-linked supplier evaluations | Pending zero-score cards no longer dilute completed supplier ratings |
| 20 submitted incoming inspections, 53 Stock Entries, six completed governed transfers and six donor books | Inspect actual receipt/batch references and ledger-derived quantity/value totals |
| 16 asset registers/verifications; four completed movements; one disposal | The EU boat uses an EU destination; Own Funds fleet uses Oropoi |
| Eight vehicles, 16 fuel logs, 16 spare issues, 16 trips, six donor fleet reports | USAID and Concern each have two vehicles; reused report snapshots regenerate |
| Eight landed-cost vouchers and ten budgets across all six donors | Freight capitalization and donor budget examples extend beyond the original three vouchers |
| Two Bid Opening Records, 9 scores per evaluated tender, 6 COI declarations, 2 approved minutes and recommendations, 1 active standstill | Livestock is ready for a live **Start Standstill**; Motorcycles is ready for a live complaint |

Do not create manual BORs, force award statuses, or call historical logistics
POs tender awards. Solar stays sealed for Scene 11. The final **Award Tender**
button only appears after the standstill has ended and been confirmed, so a
same-day demo shows the award gate rather than a fabricated award.

## 2. Demo credentials and identities

**Demo only:** all 21 seeded staff/supplier users use `Ugavi@2024`. Administrator
uses the password configured at site creation/reset (local Make default:
`admin`). Never use Administrator to demonstrate a business approval.

### Staff

| Actor | Login | Main responsibility |
|---|---|---|
| Alice Akol | `programme@lokado.org` | New programme Purchase Requisition |
| Peter Ekai | `procurement@lokado.org` | Supplier review, tender, order, contract, scorecard |
| Jane Napeyok | `approver1@lokado.org` | Approval when the next role is Approver Level 1 |
| Paul Lotir | `approver2@lokado.org` | Approval when the next role is Approver Level 2 |
| Mary Akuom | `opening1@lokado.org` | Opening officer 1 / supervising opening session |
| James Ebei | `opening2@lokado.org` | Opening officer 2 / supplies own code |
| Sarah Nabwel | `opening3@lokado.org` | Opening officer 3 / supplies own code |
| Dorothy Nekesa | `committee@lokado.org` | Evaluation committee secretary: COI, scores, minutes |
| Grace Lokwang | `chair@lokado.org` | Tender Committee Chair: approves minutes and recommendation |
| Samuel Lomuria | `evaluator@lokado.org` | Evaluation committee member: COI and individual scores |
| John Ekiru | `logistics@lokado.org` | Donor books, requests and transfer evidence |
| Ruth Napeyok | `storekeeper@lokado.org` | Purchase Receipt and stock dispatch |
| David Ewoi | `fleet@lokado.org` | Allocation, fuel, spares, trips and reports |
| Agnes Ekal | `assets@lokado.org` | Asset register, custody and condition |
| Margaret Nachuk | `finance@lokado.org` | Invoice, payment, matching and budget evidence |
| Robert Lotukoi | `auditor@lokado.org` | Read-only audit/governance evidence |

The approval chain determines the actor; it is not invariably Jane then Paul.
An Administration & Finance request may also require Procurement Officer or
Finance Officer. A Stock Manager is required to approve an inter-donor
transfer; a Logistics Officer title alone does not establish that permission.

### Supplier portal

| Supplier record | Login | Suggested use |
|---|---|---|
| Turkana Construction Ltd | `turkana-construction@outlook.com` | Warehouse procurement, partial payment, solar-pump bid |
| Nadirkonyen Women's Group | `nadirkonyen-women@outlook.com` | Livestock delivery and performance |
| Rift Valley Hardware | `riftvalley-hardware@outlook.com` | HDPE procurement and solar-pump bid |
| Jopeji Enterprises | `jopeji@outlook.com` | Motorcycle procurement and deliveries |
| Lodwar General Supplies | `lodwar-supplies@outlook.com` | General portal walk-through, tank bid, unpaid invoice, prepared complaint journey |

**Thirty supplier masters do not mean thirty logins.** The twelve newly added
suppliers have no additional portal accounts in `LOKADO_USERS` /
`SUPPLIER_PORTAL_LINKS`. Present their records in Desk, not by inventing a login.

## 3. How to run the role handoffs

### 3.1 Choose a story, not a random list of screens

| Story | Business question | Scene order | Delivery mode |
|---|---|---|---|
| A. Programme need to tender | Can staff request supplies and procurement act only after approval? | 5, 6, 7, 8, 9, 10 | New Alice-owned PR and supplier actions |
| B. Shared opening and award | Can one person see sealed bids? What authorizes an award? | 11, 12, 13 | Live solar opening; award gates explained until genuine prerequisites are met |
| C. Delivery to donor stock and payable | Can we trace accepted goods, dispatch and money to the donor? | 13, 14, 16, 15 | Prepared linked receipt/invoice plus optional small live dispatch |
| D. Stewardship | Can we account for assets and each vehicle's fuel/spares? | 17, 18 | Prepared asset/fleet sources; controlled optional new records |
| E. Accountability | Can suppliers challenge decisions and auditors follow events? | 19 | Live complaint only inside an active window |

Run Scene 16 **before** the payment part of Scene 15: completed supplier
evaluation is a payment prerequisite. The scene numbers remain stable for
existing documentation links.

**30-minute route:** 5-6 (3 min), 7 read-only comparisons (4), 11 (5), 13
(3), 14 (5), 15-16 (3), 17-18 (5), 19/closing evidence (2). Do not squeeze an
entire new tender lifecycle into a short presentation by skipping approvals.

### 3.2 Session and record discipline

1. Use distinct browser profiles for simultaneous staff/supplier sessions.
   Incognito windows in the same profile can share a session.
2. Before each action, say the actor's name, show the signed-in account, and
   show the record's current status.
3. Use a unique live title such as `DEMO-<session>-IOM Water Tanks`; write it in
   the worksheet. Do not edit a completed seed record to look like a new one.
4. Save the actual document ID after every transition. Frappe IDs depend on
   site history/year; never invent `PO-0001` or link by a guessed ID.
5. Follow document Link fields. Two records mentioning the same supplier or
   donor are not necessarily one connected transaction.
6. Label each scene **LIVE**, **PREPARED EVIDENCE**, or **PLANNED EXTENSION**.
   Never describe a read-only example as an action performed in this session.

### 3.3 Record-finding worksheet

Run `make demo-index` first: it prints each anchor's real ID and Desk link
for this site. Use the table below to verify what those records must show.

Desk navigation below uses `/app/<doctype-slug>`. If the installed Frappe
version redirects to `/desk/`, use the Desk search bar to open the named
DocType. Filter by Title, supplier, tag, vehicle plate, or invoice Bill No;
then record the real **Name** and use it as the next scene's Link value.

| Evidence anchor | Find/filter | Verify before the presentation | Actual ID |
|---|---|---|---|
| Restricted PR | Title = `Water Tanks - WASH Programme (IOM)` | KES 450,000; IOM; WATER-TANK-10K; saved method Restricted | __________ |
| Open PR | Title = `Construction of IOM-Supported Warehouse - Kakuma` | KES 1,200,000; donor **JAPAN**, despite IOM in title | __________ |
| New live PR | `DEMO-<session>-IOM Water Tanks` | Requester Alice; Draft; approval chain visible | __________ |
| Live-opening Tender | Title = `Solar Water Pumps EU Resilience` | EU; KES 780,000; closed deadline; four Submitted bids; no BOR | __________ |
| Live award candidate | Title = `Water Tanks WASH IOM` or `IOM Warehouse Construction Kakuma` | Linked approved PR and submitted bids; opening/governance/award still required | __________ |
| Tank payable | Purchase Invoice Bill No = `LOK-INV-LGS-1190` | Submitted; Lodwar General Supplies; linked IOM receipt; unpaid | __________ |
| Construction payable | Bill No = `LOK-INV-TCL-0412` | Submitted; Turkana Construction; links to receipt and PO; payment share 60% | __________ |
| Livestock payable | Bill No = `LOK-INV-NWG-0088` | Submitted; Nadirkonyen; payment share 100% | __________ |
| Donor book | Monthly Stock Report: donor IOM + Kakuma warehouse + current report month | Nonempty rows; ledger quantity/value reconciliation | __________ |
| Asset | Asset Tag = `LOK-IT-001` | Current location after seed movement; custodian; active condition | __________ |
| Disposal | Asset Tag = `LOK-OLD-001`, then linked Asset Disposal | Completed disposal; independent authorizer; asset Disposed | __________ |
| Fleet source | Receipt Supplier Delivery Note = `LOKADO-DEMO-FLEET-IOM` | Submitted PO/receipt; fuel and spare reconciliation rows | __________ |
| Vehicle | License Plate = `KDM 271I` | IOM; active allocation; donor-consistent purchase sources | __________ |
| Live standstill start | Tender = `Livestock Galla Goats USAID` | Under Evaluation; approved minutes and Bid Evaluation Summary (Nadirkonyen, 365,000); **Start Standstill** button visible to Peter | __________ |
| Complaint window | Tender = `Field Motorcycles Peace Building USAID`, then Standstill Period | Active and unexpired; Jopeji recommended at 505,000; Lodwar General has an opened bid | __________ |

If a row is missing, record **not available**, not a guessed substitute.
For logistics, find the receipt by supplier + destination warehouse and
check its item rows. The finance receipts are a separate seed branch from
award-generated POs: the logistics PO title starts `LOKADO-GRN-`.

## 4. Requirement-to-scene map

| Original requirement | Scenes | Observable proof |
|---|---|---|
| 1a. Prequalification and restricted/open thresholds | 6, 8, 9 | Current category record; expiry; eligibility and value bands |
| 1b. Send/receive bids; three system codes | 10, 11 | Supplier receipt; sealed bids; three-code ceremony; generated BOR |
| 1c. Programme PR, approval, system code | 7 | Alice-owned PR ID; action history; approved before tender |
| 1d. Selected-supplier PO and system code | 12, 13 | Award evidence; submitted native PO ID and source links |
| 1e. Supplier performance after purchase | 16 | Receipt/direct-invoice-linked Completed scorecard |
| 1f. Contract management | 13 | Issued PO link; activation evidence; milestones; completion checks |
| 2a. Stock receipt/dispatch, monthly ledger, donor books | 14 | Submitted stock postings; filtered native ledger; donor report |
| 2b. Asset register, movement and condition | 17 | Asset tag, current custody/condition, controlled movement/verification |
| 2c. Fleet allocation, purchase-linked fuel/spares, monthly report | 18 | Vehicle allocation; exact purchase source; fuel/spare/trip report |
| Crucial extension: finance and landed cost | 15 | PO/GRN/invoice match; partial/full/unpaid examples; valuation adjustments |
| Crucial extension: governance and supplier redress | 6, 12, 19 | Actual approvals, COI, standstill, complaint panel, event evidence |
| Crucial extension: isolation and maintainability | 8, 14, 18, closing | Identity/donor boundaries; native ERPNext records; upgrade gate |

Client-supplied PR/PO/prequalification/evaluation/ledger templates remain a
sign-off dependency. Functional fields and available print formats do not
constitute approved client layouts.

## Scene 5: Organization and funding context

**Story:** LOKADO operates several programmes without mixing their funding.
**Actor:** Peter, `procurement@lokado.org`. **Mode:** PREPARED EVIDENCE, 3 min.

1. Sign in and open **Company** through Desk search. Show
   `Lotus Kenya Action for Development Organization`.
2. Open **Donor Profile**. Locate IOM, USAID, CONCERN, JAPAN, EU, LOKADO-OWN by
   Donor Code. Record the actual Name used by Link fields.
3. Open **Project** and a programme such as `EU Resilience Programme`.
   Inspect its donor linkage rather than assuming it is attached to every PR.
4. Open the two PRs in the worksheet. Contrast IOM water tanks with the
   warehouse construction request funded by **JAPAN**.
5. Explain: “Names describe the activity; the donor Link is the funding
   attribution. An IOM-named building does not make its funder IOM.”

**Pass:** donor codes and saved document links are visible.
**Stop/fallback:** if a project is absent or not linked, show the donor
directly and describe project linkage as a separate configuration step.

## Scene 6: Procurement thresholds and governance

**Actor:** Peter for settings, Robert for audit. **Mode:** PREPARED EVIDENCE, 5 min.

1. Open **Ugavi Procurement Settings** and show the actual saved thresholds.
2. Explain the default policy using whole-KES examples:

   | Total estimated value | Expected method |
   |---|---|
   | 199,999 | Request for Quotation (Direct) |
   | 200,000 | Restricted Tender |
   | 499,999 | Restricted Tender |
   | 500,000 | Open Tender |

3. Compare saved PR examples: `Emergency HDPE Pipe Repair - IOM WASH`
   (195,000), `Water Tanks - WASH Programme (IOM)` (450,000), and the
   warehouse construction PR (1,200,000).
4. Open **Delegation of Authority**; filter enabled rules for the chosen PR
   department and inspect effective dates, amount limits and roles.
5. Open **Segregation of Duties**. Read each rule's actual enforcement:
   `Warning Only` is not a block. Demonstrate the requester/approver rule with
   the live PR in Scene 7 rather than just pointing at a rule.
6. Switch to Robert and open **Audit Log**. Distinguish the seed's illustrative
   override entry from real events produced during this presentation.

**Pass:** saved method follows applicable policy, and real approval history
identifies the actor.
**Stop:** below-500K “Open” fixtures need an applicable documented rule or
approved waiver; a source comment is not authority to override the bands.

## Scene 7: Purchase requisition and approval

**Story:** Alice needs water tanks for an IOM-funded WASH activity.
**Actors:** Alice -> next required approver(s) -> Peter. **Mode:** LIVE, 10 min.

### 7.1 Create the request as the actual programme user

1. Sign in as `programme@lokado.org`; open **Purchase Requisition** -> **New**.
2. Enter:

   | Field | Demo input |
   |---|---|
   | Title | `DEMO-<session>-IOM Water Tanks` |
   | Requester | `programme@lokado.org` (verify, do not leave Peter selected) |
   | Department | `Emergency WASH - LOKADO` |
   | Donor | The IOM Donor Profile found in the worksheet |
   | Item | `WATER-TANK-10K` |
   | Quantity / estimated unit price / UOM | 12 / KES 37,500 / Nos |
   | Justification | `Supply 12 village water tanks; IOM WASH field requirement. DEMO ONLY.` |

3. Save. Write down the real ID; the naming pattern is
   `PR-<donor code>-<year>-<sequence>`.
4. Verify Draft, estimated total **KES 450,000**, Restricted Tender, and
   the displayed approval chain. Show any configured budget response honestly:
   no configured budget line is not proof of available funds.
5. Click **Submit for Approval**. Verify `Pending Approval`.
6. As Alice, attempt **Approve** once. Expect “The requester cannot approve
   their own requisition”; verify the status did not advance.

### 7.2 Approve in the actual required order

7. Log out, sign in as the account holding the next required role, and locate
   the PR by its recorded Name.
8. Click **Approve**, enter `Programme requirement and quantities checked`,
   and inspect approval history for role, user, timestamp and remarks.
9. If still Pending, read the next required role and switch to that actor.
   For the seeded WASH department the default role may be Approver Level 1;
   do not manufacture a finance co-approval if the chain does not ask for it.
10. Stop only when the status is **Approved**. An approval click alone is not
    final approval when other steps remain.
11. Compare the prepared `Office Consumables - Head Office` and
    `Indigenous Chicken Restocking - USAID Phase 2` rejection examples.
    Explain their recorded reasons, not a universal rule that all direct
    purchases must be rejected.

**Pass:** a new Alice-owned coded PR has real approval history and becomes
Approved. **Hand-off:** give Peter its ID.
**Fallback:** if permissions or DoA configuration block the transition,
record the exact error; show prepared examples labelled as such. Never
change the status field to simulate approval.

## Scene 8: Supplier profile and prequalification

**Story:** a supplier maintains its documents and category eligibility.
**Actors:** Lodwar General supplier -> Peter. **Mode:** LIVE / comparison, 7 min.

1. Use a separate supplier profile; sign in as
   `lodwar-supplies@outlook.com`, open `/supplier/dashboard#profile`.
2. Confirm the heading is **Lodwar General Supplies**, not another supplier.
   Change only a harmless demo contact value, click **Save profile**, reload,
   and verify persistence.
3. Open `#prequalification`. Inspect current applications before submitting:
   an existing active category can make another application inappropriate.
4. Choose a legitimate missing category, for example WASH Supplies **if it
   has no current record**, request expiry one year ahead, choose
   `Tax Compliance`, and attach the fictional PDF.
5. Click **Apply**. Record the new application ID and actual initial status;
   applying does not itself approve eligibility.
6. As Peter, open **Supplier Prequalification**, filter by that supplier and
   category, inspect its private attachment and dates.
7. Review using the installed form's supported fields/actions. The eligible
   status used by the controller is **Prequalified**, not `Active`.
   Confirm valid expiry before describing the supplier as eligible.
8. Compare masters: `Samburu Agencies` / `Eliye Springs Boat Services`
   (expired examples), `Turkana Fuel Distributors` / `Oropoi Community Supplies`
   (suspended). Inspect the disabled flag and any actual prequalification
   record; the seed may express an example through the master rather than
   creating every expired-category record.
9. Switch to another existing portal account and show its own supplier
   heading, awards and invoices. Do not attach a file owned by the first user.

**Pass:** supplier-specific identity, private evidence and actual category/
expiry determine eligibility. Open tenders do not require prequalification,
but disabled suppliers are not automatically allowed to bid.
**Fallback:** show an existing valid application if the category is already
active or the review UI is unavailable; do not duplicate it.

## Scene 9: Tender publication and opportunities

**Story:** Peter turns the approved need into a controlled opportunity.
**Actor:** Peter -> Lodwar General supplier. **Mode:** LIVE, 7 min.

1. Open the **live PR** from Scene 7. Use **Create Tender** if exposed by the
   installed form. Record the returned tender ID; inspect the PR status
   (`Converted to Tender` after successful conversion).
2. If that shortcut is absent, create a Draft **Tender** through the normal
   form and select the approved PR explicitly. Verify its saved references;
   do not claim the conversion action occurred.
3. Open the Draft tender and complete title, approved PR, donor IOM,
   estimated value 450,000, Restricted method, category WASH Supplies and a
   deadline seven days ahead.
4. Assign `opening1@lokado.org`, `opening2@lokado.org`,
   `opening3@lokado.org`. Attach fictional specifications through supported
   document fields. Check any bid-security requirement before publishing.
5. Save and click **Publish Tender**; confirm the prompt.
6. Verify Published, publication/deadline dates and generated public-key
   metadata. Do not display private key material.
7. Switch to the eligible supplier; open `#opportunities` and find the new
   title. Show the method, value, category and deadline.
8. Contrast an available Open opportunity such as
   `Emergency Shelter Tarpaulins Concern` (550,000) **if present and still open**.
   A matching category is required for Restricted, not for Open.

**Pass:** one approved PR connects to the published tender and an eligible
supplier sees the opportunity.
**Fallback:** use another still-open eligible tender. Do not use the closed
solar fixture for submission or silently reopen an awarded tender.

## Scene 10: Supplier bid and clarification

**Actors:** Lodwar General supplier -> Peter -> supplier. **Mode:** LIVE, 7 min.

1. On the live opportunity from Scene 9, click **Prepare bid**.
2. In `#bids`, verify the selected tender; enter **425,000**, currency
   **KES**, delivery days **30**, and the fictional private technical proposal.
3. Click **Encrypt and submit bid** once. Record the Bid ID and receipt
   shown in the supplier's bid list. Reload and confirm the submission exists.
4. Explain the bid is Submitted, not Opened. Do not try to edit it afterwards.
5. In `#clarifications`, select the same tender, enter
   `Does delivery include installation at all 12 village sites?`, click
   **Send question**.
6. As Peter, open **Clarification**, filter by tender/supplier, enter a
   demonstrative answer and save using the supported response fields.
7. Return to the supplier, reload, and show the answer and any generated
   notification. Check the notification actually exists before claiming delivery.

**Pass:** the same supplier/tender has a sealed bid receipt and answered
question. **Hand-off:** this newly published tender waits until its deadline;
Scene 11 uses a different, already-closed seed fixture.
**Fallback:** if a supplier already bid, inspect the existing receipt or use
the new tender; do not submit duplicates or withdraw a winning seed bid.

## Scene 11: Three-person sealed-bid opening

**Story:** no single officer should open a tender alone.
**Actors:** Mary conducting the session; James and Sarah supplying codes.
**Mode:** LIVE, one-way transition, 8 min.

1. As Mary, open Tender **Solar Water Pumps EU Resilience** by Title and
   record its real ID. Check EU / KES 780,000 and its elapsed deadline.
2. Verify status Published or Bids Received, three distinct assigned officers
   and four Submitted bids, with no existing Bid Opening Record.
3. Explain the seeded amounts below are the presenter's expected values,
   **not a screen officers may inspect before opening**:

   | Supplier | Expected amount after successful opening |
   |---|---|
   | Turkana Construction Ltd | KES 745,000 |
   | Ekaale Building Works | KES 768,000 |
   | Lokichoggio Traders Ltd | KES 790,000 |
   | Rift Valley Hardware | KES 810,000 |

4. Click **Open Sealed Bids**. This requests new system codes and opens the
   **Enter Opening Codes** dialog.
5. In local Mailpit, identify the newest message for this tender and each
   exact recipient. Each officer supplies their own code. Keep codes and
   private attachments out of screenshots or recordings.
6. Enter Officer 1/2/3 codes in the matching fields and click **Open Bids**.
   All three are collected in Mary's authorized session; the current UI is
   not three independently signed approval sessions.
7. Verify navigation to a generated **Bid Opening Record**, successful
   outcome, officers, private PDF, opened amounts and tender
   **Under Evaluation**. Record BOR and tender IDs.
8. Explain the controls: codes are stored only as salted hashes, expire after
   the configured window (default 5 minutes), and are deleted once the bids
   open. A typo by one officer can be corrected without reissuing the others'
   codes. Do not turn the presentation fixture into a rate-limit experiment.

**Pass:** system-generated BOR and opened amounts match the four bids.
**Stop:** already opened, no codes delivered, expired codes, missing key
shares or wrong officers. If opened already, show the existing BOR as
PREPARED EVIDENCE. Never fabricate a BOR or regenerate keys after submission.

## Scene 12: Evaluation and award decision

**Story:** opening is disclosure, not authority to spend.
**Actors:** Samuel and Dorothy (evaluators) -> Grace (chair) -> Peter.
**Mode:** PREPARED EVIDENCE for scoring and approvals, then LIVE
**Start Standstill** on Livestock, 7 min.

Tender: **Livestock Galla Goats USAID** (Under Evaluation). Bids opened by the
real three-code ceremony: Nadirkonyen 365,000, Moi's Bridge 378,000,
Kainuk 400,000.

1. As Peter, open the Tender. Show its **Evaluation Committee** table: Grace
   (Chairperson), Dorothy (Secretary), Samuel (Member). None of them are
   opening officers. Segregation of duties is enforced on save.
2. Open **COI Declaration** filtered by the tender. Three declarations, each
   signed by the declarant's own session, all **No** conflict. A user cannot
   score before declaring.
3. Open **Evaluation Score** filtered by the tender. Nine Submitted scores
   (three evaluators x three bids), each with criterion rows and an evaluator
   who is the session user. Submitted scores cannot be edited or deleted.
4. Open the **Evaluation Minutes** (`make demo-index`: *Livestock minutes*).
   Show quorum met, chair and secretary present, bids loaded from the scores,
   status **Approved** by Grace. Approved minutes are immutable.
5. Open the **Bid Evaluation Summary** (*Livestock recommendation*): recommended
   Nadirkonyen at 365,000, approved by Grace. The approval is rejected if the
   recommendation is not the evidence-backed top-ranked opened bid.
6. Optional live control: sign in as Dorothy and try **Approve Minutes** on a
   draft; the server refuses because only the Tender Committee Chair can approve.
7. **LIVE:** back on the Tender as Peter, the dashboard shows
   *Recommended: Nadirkonyen Women's Group (KES 365,000)*. Click
   **Start Standstill** and confirm. Every bidder is notified of the intended
   award; the tender moves to **Standstill Period** and a Standstill Period
   record opens with the configured complaint window (default 14 days).
8. Show that the Tender now offers **no Award button**. **Confirm Standstill**
   appears only after the end date, and only when no complaint is open.
   **Award Tender** then issues the PO and contract for the exact recommended
   supplier and amount.

**Pass:** an evidence chain from COI to scores to minutes to recommendation to
standstill, with each step done by the authorised person.
**Stop:** if the tender already shows *Standstill Period*, the live step was
used in a rehearsal; run `make restore-demo` or show the Motorcycles standstill.
Never edit statuses or dates to reach the award button. Solar opened in Scene 11
has no committee evidence yet, so it stops at *Awaiting approved Bid Evaluation
Summary*.

## Scene 13: Purchase order and contract

**Actors:** Peter -> winning supplier. **Mode:** PREPARED EVIDENCE plus live
acknowledgement where available, 7 min.

1. Follow the Purchase Receipt behind `LOK-INV-TCL-0412` to its logistics PO.
   A same-day demo cannot have an award-generated order, because Scene 12's
   standstill is still running. State that this is the receipt-backed branch.
2. Show system PO ID, supplier, company, item quantities/rates, schedule,
   donor, and any populated PR/tender fields. Missing references are not
   automatically inferred from the supplier name.
3. Follow the PO's contract relationship to **Ugavi Contract**. Show
   actual status: Draft is not Active.
4. Inspect activation prerequisites: submitted PO, at least one milestone,
   attached agreement, valid start/end dates, required performance bond.
5. Prepared supply contracts use a **Delivery, inspection and acceptance**
   milestone, a private **DEMO** agreement, and 10% retention. Read the saved
   amount and dates; do not claim a separate multi-stage construction contract.
6. An active contract needs verified milestone acceptance notes/evidence
   before completion. All linked receipt evaluations must be Completed.
   If the form has no lifecycle action, show existing evidence rather than
   changing status to simulate verification or completion.
7. Sign in as the winning supplier with an existing portal account. Open
   `#awards`, `#contracts`, then `#deliveries`; locate the **same PO ID**.
8. If not yet acknowledged, click **Acknowledge**, reload and show its
   acknowledged indicator. If already acknowledged, show that state.

**Pass:** issued native PO and linked contract are traceable; the supplier
sees only its own order.
**Fallback:** an expanded supplier without a portal login stays a Desk-only
example. Do not impersonate it with Lodwar General's account.

## Scene 14: Receipt, dispatch, stock ledger, and donor books

**Story:** accept stock, dispatch to programmes, preserve donor ownership.
**Actors:** Ruth -> John. **Mode:** PREPARED EVIDENCE; optional small LIVE
dispatch after balance/date checks, 10 min.

### 14.1 Trace a real receipt

1. Open Purchase Invoice Bill No **LOK-INV-TCL-0412** and follow its receipt,
   or find Purchase Receipt for Turkana Construction + Kakuma warehouse.
2. Inspect submitted status, `CEMENT-BAG` **250 at 1,100** and
   `WATER-TANK-10K` **6 at 52,000**, and their exact PO row references.
3. Follow the linked PO and show received progress. Do not create another
   receipt against a fully received PO.
4. If demonstrating a new receipt, choose a submitted PO with remaining
   quantity, use its normal **Create -> Purchase Receipt** action, set the
   donor-consistent accepted/rejected warehouses, inspect required quality
   inspections and batches, then Save/Submit. Record the new ID.
5. Explain a standalone Material Receipt Stock Entry adds stock but is not
   automatically a supplier GRN or a source for a purchase invoice.

### 14.2 Trace dispatch without overstating beneficiary evidence

6. Open **Stock Entry**, filter Stock Entry Type = Material Issue and Remarks
   contains `Issue to Concern SERVE Loima distribution`.
7. Confirm Submitted and source **LOKADO Field Store - Lokichoggio**;
   inspect HYGIENE-KIT 450 and FIRST-AID-KIT 60.
8. Open native **Stock Ledger**, filter warehouse, one item and a period
   covering the posting. Locate the voucher and its negative actual quantity.
9. An optional live dispatch can use **one HYGIENE-KIT** from that warehouse,
   only after confirming current available, unexpired batch stock. New Stock
   Entry -> Material Issue -> source warehouse -> item/qty 1 -> Save/Submit.
   Use remarks `DEMO-<session>-Loima hygiene dispatch`; record the ID.
10. Explain: a warehouse dispatch proves stock movement, not a signed
    household-level beneficiary distribution or proof of delivery.

### 14.3 Reconcile donor books and transfer controls

11. As John, open **Donor Warehouse** and compare the physical warehouse
    ownership before choosing a book:

    | Donor | Monthly-book warehouse |
    |---|---|
    | IOM | IOM Supported Warehouse - Kakuma |
    | USAID | LOKADO Main Warehouse - Lodwar |
    | CONCERN | LOKADO Field Store - Lokichoggio |
    | JAPAN | Cold Chain Storage - Lodwar |
    | EU | LOKADO Transit Store - Kitale |
    | LOKADO-OWN | LOKADO Field Store - Oropoi |

12. Open **Monthly Stock Report**, filter donor/warehouse/current report
    month. Compare opening, receipts, issues, transfer in/out, closing and
    value with the native ledger through month end.
13. Reports are snapshots generated after seed stock/valuation postings.
    After a live dispatch, regenerate through the installed supported action
    before expecting the snapshot to change. If no action is exposed, keep
    the old snapshot and explicitly show the newer ledger movement.
14. Open **Inter Donor Transfer**, find reason beginning
    `DEMO-COMPLETED: Emergency water tanks`, inspect IOM -> CONCERN and
    WATER-TANK-10K quantity 2. Locate the governed Material Transfer voucher.
15. Compare a Pending proposal and a Rejected example. A new transfer must
    first be approved by **Stock Manager**, then completed through the
    controller to create its stock posting. Do not manually submit a
    cross-donor Stock Entry to impersonate this process.

**Pass:** voucher -> ledger -> donor book links and balances are visible.
Do not promise a numeric closing balance from scenario quantities alone:
other receipts, fleet issues, transfers and landed cost also affect it.

## Scene 15: Three-way match and finance handoff

**Actor:** Margaret. **Mode:** PREPARED EVIDENCE, after Scene 16, 7 min.

1. Open **Purchase Invoice**, filter Bill No, not Name:

   | Bill No | Supplier | Seed payment intent | Story |
   |---|---|---|---|
   | `LOK-INV-TCL-0412` | Turkana Construction Ltd | 60% | Part-paid receipt-linked procurement |
   | `LOK-INV-NWG-0088` | Nadirkonyen Women's Group | 100% | Completed livestock payable |
   | `LOK-INV-LGS-1190` | Lodwar General Supplies | 0% | Open unpaid water-tank payable |
   | `LOK-INV-KRC-2207` | Kenya Red Cross Supplies | 100% | WASH kit delivery |
   | `LOK-INV-RVH-0731` | Rift Valley Hardware | 100% | Emergency pipe delivery |
   | `LOK-INV-JOP-0056` | Jopeji Enterprises | 50% | Part-paid motorcycles |

2. On each selected invoice, confirm Submitted, item-row PO/receipt links,
   totals and current outstanding amount. Payment percentages are seed
   intent; calculate from the actual document after later transactions.
3. Open **Three Way Match**, filter by the invoice; follow PO, GRN and invoice
   lines and read the actual match/dispute result. A match row is not proof
   of a hard payment block.
4. Open **Payment Entry**, locate reference number `PAY-<Bill No>` and verify
   Submitted, invoice References, allocated amount and company account.
   One submitted entry alone does not prove its invoice allocation is correct.
5. Contrast full/partial/unpaid examples using current outstanding values.
   State that these are ledger postings, not real bank or M-Pesa settlement.
6. Open **Landed Cost Voucher**, follow its receipt and charge allocation;
   return to Stock Ledger to show valuation evidence rather than a fabricated
   rate-times-quantity estimate.
7. Open **Budget** filtered Budget Against = Donor Profile and current fiscal
   year. Examples: IOM Freight 1,150,000; IOM Administration 600,000;
   USAID Travel 750,000; CONCERN Administration 1,200,000.
8. Read applicable actions: these seed budgets use **Warn**, not Stop.
   Finance Officer has read-only Budget/LCV access; use the appropriate
   administrative role for configuration, not for the payment demonstration.

**Extensions only after receipt verification:** `LOK-INV-KRS-3101` targets a
70% shelter payment; `LOK-INV-LWF-0220` targets a full classroom payment;
`LOK-INV-LPH-1405` targets full medical payment. The expanded list alone
does not create the missing submitted supplier/warehouse receipts.

## Scene 16: Supplier performance evaluation

**Story:** accept delivery quality before releasing payment.
**Actor:** Peter -> supplier -> Margaret. **Mode:** PREPARED EVIDENCE, optional
LIVE completion only through an available supported action, 5 min.

1. From the receipt in Scene 14, open **Ugavi Supplier Evaluation** filtered
   by **that Purchase Receipt ID**, not supplier alone.
2. Verify exactly one source: Purchase Receipt or a direct service Purchase
   Invoice. Examples of the latter: `LOK-SVC-EKAALE-001` and
   `LOK-SVC-MOIS-001` (Bill No).
3. Show the Completed Turkana Construction scenario:
   Quality **9.0**, Delivery **8.4**, Compliance **10.0**, Price **9.2**.
   Its weighted total is **91.4%** if these saved inputs match.
4. Explain weights: 30% quality, 25% delivery, 25% compliance, 20% price,
   with each input scored **0-10**, not 0-5.
5. If using a Pending scorecard from a new live receipt, enter 9/8/9/8
   (85.5%), today and acceptance remarks; Save. Completion requires the
   controller's `complete_evaluation` action. The status is read-only; if no
   completion action exists in the installed Desk UI, do not pretend Save
   alone completed it. Show a prepared Completed example.
6. Return as that supplier to `#evaluations`; compare the source and visible
   score/remarks. Margaret then inspects the linked payment in Scene 15.
7. Explain the separate payment gate: evaluations for relevant purchase
   sources must be Completed. A low cumulative rating below 60% can disable
   the supplier. Do not low-score a shared portal supplier for a stunt.

**Pass:** a purchase-specific Completed evaluation, correct scale/total,
and supplier-visible result. An unreferenced performance narrative fails.

## Scene 17: Asset management

**Actor:** Agnes. **Mode:** PREPARED EVIDENCE; optional same-donor LIVE move,
7 min. **Open:** Asset Register, Ugavi Asset Movement, Asset Verification,
Asset Disposal.

1. Filter Asset Register by **Asset Tag**, not a guessed document name.
   Start with `LOK-IT-001` (Programme Monitoring Laptop).
2. Inspect donor USAID, serial, custodian, current location, condition and
   latest verification. The seed may already have moved it from Lodwar to
   **USAID Field Store - Oropoi**.
3. Open its completed **Ugavi Asset Movement** and compare source/destination
   custodian/location/condition. Read the current register again.
4. For a live movement, choose an Active asset and two different locations
   mapped to **the same donor**. New movement -> select asset -> today ->
   destination/custodian/condition -> reason -> Save as Draft.
5. Use the supported **Confirm** action if exposed. It checks stale source
   custody/location/condition and updates the register. Reopen the asset to
   prove the resulting state. If the action is absent, keep this Draft and
   use prepared completed movement evidence.
6. Open **Asset Verification** for that asset. Inspect found Yes, date,
   verifier, condition and notes. A new “not found” report needs notes and
   cannot be marked successfully verified.
7. Inspect the expanded tags: `LOK-RADIO-001`, `LOK-SCALE-001`,
   `LOK-TABLET-001`, `LOK-DRONE-001`, `LOK-MEDFRIDGE-001`.
   Describe only records actually present.
8. Filter `LOK-OLD-001`; inspect its **Completed Asset Disposal**, Auction
   12,000, authorizer `approver2@lokado.org`, book value/gain-loss and
   Disposed register state. Do not dispose another shared asset live.

**Boundary:** these are Ugavi custody/condition records. Sixteen source
fixtures do not prove sixteen capitalized or depreciating native ERPNext
Assets. The EU boat moves to **EU Field Store - Lake Turkana**, preserving
EU ownership. An IOM destination would be rejected, not treated as a valid
cross-donor asset movement.

## Scene 18: Fleet management

**Story:** each vehicle's consumption is tied to a real purchase and donor.
**Actor:** David. **Mode:** PREPARED EVIDENCE, 10 min.

### 18.1 Locate the expanded fleet by plate

| Plate | Vehicle | Donor code | Purchase receipt marker |
|---|---|---|---|
| KDL 410U | Toyota Land Cruiser 76 | USAID | `LOKADO-DEMO-FLEET-USAID` |
| KDM 271I | Toyota Hilux Double Cab | IOM | `LOKADO-DEMO-FLEET-IOM` |
| KDN 842C | Isuzu D-Max | CONCERN | `LOKADO-DEMO-FLEET-CONCERN` |
| KDP 318E | Toyota Prado | EU | `LOKADO-DEMO-FLEET-EU` |
| KDQ 520J | Nissan Navara | JAPAN | `LOKADO-DEMO-FLEET-JAPAN` |
| KDR 711L | Toyota Hiace Van | LOKADO-OWN | `LOKADO-DEMO-FLEET-OWN` |
| KDS 143U | Toyota Land Cruiser 79 Pickup | USAID | `LOKADO-DEMO-FLEET-USAID2` |
| KDT 890C | Mitsubishi Canter 3T | CONCERN | `LOKADO-DEMO-FLEET-CONCERN2` |

All eight journeys were verified on the isolated site. Start with the IOM
vehicle, then compare the second USAID/Concern vehicles and Own Funds at Oropoi.

### 18.2 Trace one complete IOM journey

1. Open **Vehicle**, filter License Plate = `KDM 271I`. Show native vehicle
   details, IOM donor, Kakuma warehouse and service date.
2. Open **Vehicle Allocation**, filter this vehicle; show active period,
   allocated user and donor. Check overlap rather than merely counting rows.
3. Find Purchase Receipt Supplier Delivery Note =
   `LOKADO-DEMO-FLEET-IOM`, confirm Submitted and follow its submitted PO.
4. Open **Fleet Purchase Reconciliation**, filter by that receipt. Show
   separate Fuel and Spare Part item rows, purchased/allocated/remaining
   quantities and donor. These sources must be real receipt rows.
5. Open **Fuel Log**, filter vehicle and source reconciliation. Look for
   receipt numbers ending `-35` and `-15`: **50 L** and **70 L**, price
   **KES 210/L**, odometers **10,100** and **10,500**. Confirm submitted
   total costs **10,500** and **14,700** when those saved values match.
6. Open **Spare Parts Issue** for the vehicle/source. Inspect quantities
   **4** and **6** of the spare source and their linked submitted Material
   Issue Stock Entries. Do not create another issue against an exhausted source.
7. Open **Trip Log**: two completed submitted journeys,
   **10,000 -> 10,100** and **10,100 -> 10,500**, destination
   `Kakuma warehouse project`.
8. Open **Fleet Utilization Report**, select IOM and a range covering both
   seed trips/fuel logs. The prepared report uses about 60 days, **not one
   calendar month**.
9. When the report covers only this complete fixture, expect **2 trips,
   500 km, 120 L, KES 25,200 fuel cost and 4.17 km/L**. Check spare cost
   against source rates rather than inventing it.
10. For the monthly requirement use the installed generation action with
    From Date = first day and To Date = last day of the chosen month.
    The `-35`/`-15` relative dates may span two months, so a monthly total can
    legitimately differ from the 60-day snapshot.
11. Compare USAID and CONCERN reports: each has **two vehicles**. Re-seeding
    regenerates reused donor snapshots after the additional vehicle is posted.
12. Run `make dev-check` on local source, or `make fleet-check` on the rebuilt
    image. Read the result and investigate donor/source mismatches.

**Pass:** allocation -> PO/receipt -> reconciliation -> fuel/spare/trip ->
date-filtered donor report. A generic Vehicle list alone does not meet fleet
requirements. A cost-per-kilometre figure, if needed, must be explicitly
calculated from stated included costs; do not claim a field the report lacks.

## Scene 19: Notifications, complaints, audit, and MVP2 readiness

**Actors:** Lodwar General supplier -> Peter/panel -> supplier -> Robert.
**Mode:** LIVE inside the seeded Motorcycles complaint window, 8 min.
The window was opened by the real `start_standstill` action after a real
opening, scoring and chair approval. It was not inserted as a fixture.

1. Open supplier `#notifications`; show actual profile/prequalification,
   bid, clarification, award or acknowledgement events generated by this
   session. The journey panel is guidance, not proof of every completed stage.
2. As Peter, open **Field Motorcycles Peace Building USAID** and its
   Standstill Period (`make demo-index`: *Motorcycles standstill*). Confirm
   **Active**, a future end date, intended award Jopeji at 505,000, and that
   Lodwar General's 530,000 bid was opened.
3. As `lodwar-supplies@outlook.com`, open `#complaints`, select that tender/
   period, enter a fictional evidence-based challenge and attach a private PDF.
   Click **Submit complaint**. Record its ID.
4. As Peter, open **Tender Complaint** by that ID. Set a review panel with
   **three distinct non-conflicted users**, for example Jane, Paul and Robert
   if eligible; the complainant cannot be a member. Assign a reviewer who
   is in the panel.
5. Move Submitted -> **Under Review** and save. The Standstill Period shows
   **Challenged**, and **Confirm Standstill** is blocked while it is open.
   Review the fictional facts; record an Outcome and move to **Rejected**,
   **Upheld** or **Partially Upheld**. Upheld/Partially Upheld also requires a
   remedial action, which returns the tender to evaluation for re-scoring.
6. Return as the supplier and show the outcome notification. Do not call a
   Submitted complaint resolved or assume a resolved complaint itself
   confirms an award.
7. As Robert, inspect actor/time/outcome evidence and relevant document
   history. Distinguish real ceremony/workflow events from illustrative seed
   audit rows; never describe a sample hash as verified cryptographic history.

**Stop/fallback:** expired period, absent bid, unresolved duplicate complaint,
missing/conflicted panel. Show prepared complaint evidence if present; never
extend a historical standstill silently to make the demo pass.

**Delivered readiness slice:** identity-bound supplier portal; private files;
bid/clarification/PO acknowledgement; panel-based complaint review and
resolution notification; purchase-linked fleet consumption; donor reporting.
These are not a claim that every [MVP2 workstream](../mvp2/OPEN-QUESTIONS.md)
or every production integration is complete.

## Expanded programme catalogue: what to show after the core journey

Use this table to choose the next business story, not to promise a fully
posted lifecycle for every new supplier.

| Use case | Exact request / tender anchors | Stock / request anchor | Completion boundary |
|---|---|---|---|
| Flood shelter | `Emergency Shelter Tarpaulins - Concern DRC` / `Emergency Shelter Tarpaulins Concern` | `Receive shelter materials from Kalobeyei Refugee Supplies`; TARPAULIN-4X6 / BLANKET-FLEECE | Concern-owned Lokichoggio receipts, invoices and payments are prepared histories; this new PR remains Pending and its tender Draft |
| School furniture | `Classroom Furniture & Stationery - USAID Education` / `Classroom Furniture USAID Education` | `Receive classroom furniture from Lorugum Welding`; SCHOOL-DESK / STATIONERY-KIT | USAID Lodwar stock; explicit Educational prequalification and real sealed bids; award remains live |
| Maternal/child health | `Clean Birth Delivery Kits - Japan MNCH` / `Clean Birth Delivery Kits Japan MNCH` | `MNCH: delivery supplies for mobile clinic outreach`; DELIVERY-KIT / SURGICAL-GLOVES | Japan Cold Chain stock, Restricted tender with bids, source-linked invoice and completed scorecard |
| Fisheries | `Fishing Livelihood Equipment - Lake Turkana` / `Fishing Equipment Lake Turkana EU` | `Receive EU fishing gear from Lake Turkana Fishers Co-op`; FISHING-NET | EU Kitale stock/receipt/invoice; the separate new PR and tender remain Draft for a live approval journey |
| Food security | `Certified Sorghum Seeds - EU Food Security` / `Sorghum Seeds EU Food Security` | `Livelihoods: fishing gear and seeds for 6 co-ops`; SORGHUM-SEEDS | EU Kitale stock, Approved PR, Restricted eligible bids; historical finance does not prove new tender award |
| Emergency WASH | `Emergency Jerry Cans - IOM WASH Response` / `Emergency Jerry Cans IOM WASH` | `WASH: cholera prevention supplies for Kakuma camp`; JERRY-CAN-20L | IOM-owned Kakuma supply request; ORS examples remain in the separately mapped Concern health stock |
| Own-funds field support | `Blankets & Bedding - Internal Programme Support` / `Blankets Internal Programme Support` | Oropoi laptop/diesel receipt and issue; LOKADO-OWN donor book | Keep own-funds attribution separate from USAID fleet warehouse mapping |
| Request rejection | `Indigenous Chicken Restocking - USAID Phase 2` | Poultry restocking / CHICKEN-INDIG examples | Explain rejection and beneficiary-list revision; do not convert Rejected into procurement by status editing |

### Source inventory and verified prepared histories

| Source-defined set | Current size | What the presenter must not infer |
|---|---|---|
| Staff + supplier logins | 16 + 5 | Additional supplier masters have no new portal accounts |
| Supplier master scenarios | 30 | All are eligible, enabled, delivered, or payable |
| Programme PRs / tender scenarios | 25 / 20 | Draft/Pending PRs have Draft tenders, not a published opportunity |
| Submitted bids | 46 | Every tender is opened or awarded |
| Logistics supplier/warehouse receipts | 24 | A direct Material Receipt Stock Entry is a supplier GRN |
| Invoice scenario list / direct services | 22 / 4 | All invoices are fully paid; three receipt invoices remain unpaid |
| Scenario scorecards / total completed source cards | 18 / 36 | A pending scorecard should lower the completed supplier rating |
| Material Request scenarios | 17 | “Approved” source labels implement the Ugavi PR approval workflow; these are native Material Issue requests |
| Direct stock receipt/issue scenarios / completed-transfer scenarios | 31 / 6 | Opening balances are additional supplier purchases; they are separately identified stock postings |
| Asset / fleet scenarios | 16 / 8 | All movement destinations are valid or every donor report refreshed |
| Submitted native PO/contract histories | 32 / 32 | A historical supply order proves the separate new tender's award |

## Closing: upgrade safety and recovery

1. Show current outputs from `make upgrade-check`, `make demo-check` and
   `make fleet-check` (or dev equivalents for local source).
2. Show browser test results only if executed for this source/site. These
   cover role access and selected portal behavior, not every live transition.
3. Explain ERPNext retains Supplier, Purchase Order, Purchase Receipt,
   Purchase Invoice, Payment Entry, Stock Ledger and Vehicle. Ugavi uses
   app-owned workflows, prefixed custom fields, hooks and scoped assets.
4. Show `make backup-demo` / `make restore-demo` (native Bench backup and
   restore of database plus public and private files). A demo round-trip is
   not a production RTO/RPO test.
5. Preserve the session's document IDs and unmet prerequisites. A later
   presenter needs to know which tenders were opened and which stocks issued.

No real settlement, certified eTIMS, external SMS, production SSO/2FA,
client-approved print templates, ERPNext depreciation, or untested future
major-version upgrade is certified by this tour.

## Completion checklist

Record **LIVE / PREPARED / NOT SHOWN** and the actual IDs; a tick alone is not
evidence that a transition occurred.

| Requirement / control | Mode | Evidence IDs / outcome |
|---|---|---|
| Default thresholds and applicable approval roles | __________ | __________ |
| Alice-owned coded PR, approval history and procurement handoff | __________ | __________ |
| Supplier profile, private prequalification and category eligibility | __________ | __________ |
| Published tender -> supplier sealed bid receipt -> clarification answer | __________ | __________ |
| Three-code opening -> immutable BOR and opened amounts | __________ | __________ |
| COI -> individual scores -> chair-approved minutes and recommendation -> Start Standstill (award gated until expiry) | __________ | __________ |
| Issued native PO -> linked contract and supplier acknowledgement | __________ | __________ |
| Receipt/dispatch -> native ledger -> donor month-end book | __________ | __________ |
| Purchase-linked Completed supplier evaluation | __________ | __________ |
| PO/GRN/invoice matching + full/partial/unpaid payable | __________ | __________ |
| Asset tag -> custody/condition -> movement/verification/disposal | __________ | __________ |
| Vehicle allocation -> purchase sources -> fuel/spares/trips -> monthly report | __________ | __________ |
| Complaint panel, outcome and supplier notification | __________ | __________ |
| Upgrade/demo/fleet/browser checks actually executed | __________ | __________ |
| Backup preserved; opened tenders/live postings recorded | __________ | __________ |

Related: [shorter demo guide](../DEMO.md),
[supplier journey](./SUPPLIER-JOURNEY.md),
[requirements traceability](../traceability/RTM.md),
[historical evidence and verification limits](../traceability/evidence.md).
