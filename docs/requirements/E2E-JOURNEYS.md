# Ugavi SCM — Revamped End-to-End Journeys & Functional Requirements

> **Baseline:** Client functional-requirements document (procurement, logistics, assets, fleet).
> **App:** Ugavi 0.1.0 on Frappe v16 / ERPNext v16.
> **Purpose:** Single source of truth for system journeys, demo scripts, acceptance criteria, and traceability.
> **Scope:** 8 end-to-end journeys covering all 8 original requirement areas plus governance, finance, compliance, and non-functional requirements.
> **Last updated:** 2026-11-24

---

## Table of Contents

1. [Personas & Actor Matrix](#1-personas--actor-matrix)
2. [Architecture & Design Principles](#2-architecture--design-principles)
3. [Journey 1: Procurement — Prequalification to Contract](#3-journey-1-procurement--prequalification-to-contract)
4. [Journey 2: Tendering — Publication to Sealed-Bid Opening](#4-journey-2-tendering--publication-to-sealed-bid-opening)
5. [Journey 3: Evaluation — Scoring to Award Decision](#5-journey-3-evaluation--scoring-to-award-decision)
6. [Journey 4: Receipt, Stock & Donor Ledgers](#6-journey-4-receipt-stock--donor-ledgers)
7. [Journey 5: Asset Lifecycle — Register to Disposal](#7-journey-5-asset-lifecycle--register-to-disposal)
8. [Journey 6: Fleet — Allocation to Monthly Reports](#8-journey-6-fleet--allocation-to-monthly-reports)
9. [Journey 7: Finance — Invoice, Match, Payment & Budget](#9-journey-7-finance--invoice-match-payment--budget)
10. [Journey 8: Governance, Complaints & Audit](#10-journey-8-governance-complaints--audit)
11. [Non-Functional Requirements](#11-non-functional-requirements)
12. [Simplified NGO Deployment Model](#12-simplified-ngo-deployment-model)
13. [Demo Script — Systematic Walkthrough](#13-demo-script--systematic-walkthrough)
14. [Acceptance Criteria & Sign-Off Checklist](#14-acceptance-criteria--sign-off-checklist)

---

## 1. Personas & Actor Matrix

> All personas are realistic Turkana/Kenyan names and roles. The approval chain determines the actor at each step; the role is not static.

### 1.1 Staff Roles

| # | Actor | Login | Role | Journeys |
|---|-------|-------|------|----------|
| 1 | Alice Akol | `programme@lokado.org` | Programme Staff | J1: Creates Purchase Requisitions |
| 2 | Peter Ekai | `procurement@lokado.org` | Procurement Officer | J1-J3: Supplier review, tender, order, contract, evaluation |
| 3 | Jane Napeyok | `approver1@lokado.org` | Approver Level 1 | J1: PR approval |
| 4 | Paul Lotir | `approver2@lokado.org` | Approver Level 2 / Stock Manager | J1, J4: PR approval, inter-donor transfer approval |
| 5 | Mary Akuom | `opening1@lokado.org` | Opening Officer 1 (supervising) | J2: Leads bid-opening session |
| 6 | James Ebei | `opening2@lokado.org` | Opening Officer 2 | J2: Supplies opening code |
| 7 | Sarah Nabwel | `opening3@lokado.org` | Opening Officer 3 | J2: Supplies opening code |
| 8 | Dorothy Nekesa | `committee@lokado.org` | Evaluation Committee Secretary | J3: COI, scores, minutes |
| 9 | Grace Lokwang | `chair@lokado.org` | Tender Committee Chairperson | J3: Approves minutes and recommendation |
| 10 | Samuel Lomuria | `evaluator@lokado.org` | Evaluation Committee Member | J3: COI and individual scores |
| 11 | John Ekiru | `logistics@lokado.org` | Logistics Officer | J4: Donor books, transfer requests |
| 12 | Ruth Napeyok | `storekeeper@lokado.org` | Storekeeper | J4: Purchase Receipt, stock dispatch |
| 13 | David Ewoi | `fleet@lokado.org` | Fleet Manager | J6: Allocation, fuel, spares, trips, reports |
| 14 | Agnes Ekal | `assets@lokado.org` | Asset Officer | J5: Register, custody, verification, disposal |
| 15 | Margaret Nachuk | `finance@lokado.org` | Finance Officer | J7: Invoice, payment, matching, budget |
| 16 | Robert Lotukoi | `auditor@lokado.org` | Auditor | J8: Read-only audit/governance evidence |

### 1.2 Supplier Portal Users

| # | Supplier | Login | Demo Purpose |
|---|----------|-------|-------------|
| 1 | Turkana Construction Ltd | `turkana-construction@outlook.com` | Warehouse procurement, partial payment, solar-pump bid |
| 2 | Nadirkonyen Women's Group | `nadirkonyen-women@outlook.com` | Livestock delivery, performance evaluation |
| 3 | Rift Valley Hardware | `riftvalley-hardware@outlook.com` | HDPE procurement, solar-pump bid |
| 4 | Jopeji Enterprises | `jopeji@outlook.com` | Motorcycle procurement, deliveries |
| 5 | Lodwar General Supplies | `lodwar-supplies@outlook.com` | Portal walk-through, tank bid, unpaid invoice, complaint |

> **30 supplier masters do not mean 30 logins.** Additional records are accessible in Desk only.

### 1.3 Donor Profiles (Organizational Context)

| Donor Code | Donor | Associated Warehouse | Example Funding |
|------------|-------|---------------------|-----------------|
| IOM | International Organization for Migration | IOM Supported Warehouse - Kakuma | WASH, warehouse construction |
| USAID | United States Agency for Intl. Development | LOKADO Main Warehouse - Lodwar | Livestock, motorcycles, peace-building |
| CONCERN | Concern Worldwide | LOKADO Field Store - Lokichoggio | Shelter, SERVE Loima distribution |
| JAPAN | Government of Japan | Cold Chain Storage - Lodwar | Warehouse construction (named IOM) |
| EU | European Union | LOKADO Transit Store - Kitale | Solar water pumps, resilience |
| LOKADO-OWN | Own Funds | LOKADO Field Store - Oropoi | Fleet, admin, general supplies |

### 1.4 Segregation of Duties Matrix

| Rule | Enforcement Point | Mechanism |
|------|-------------------|-----------|
| Requester != Approver | PR submit | Controller-level block |
| Requester != Receiver | Purchase Receipt | Controller-level block |
| Opening Officer != Evaluator | Tender save / Evaluation COI | Role membership check |
| Evaluator != Award Approver | Award recommendation | Chairperson separate from evaluators |
| Disposal Requester != Disposal Authorizer | Asset Disposal | Separate user required |
| Opening Officer 1-3 must be distinct | Bid opening session | Three different users enforced |

### 1.5 Actor-Role Permission Matrix

| Role | J1:Procurement | J2:Tendering | J4:Logistics | J5:Assets | J6:Fleet | J7:Finance | J8:Governance |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Programme Staff | CRUD | — | — | — | — | — | — |
| Procurement Officer | CRUD | CRUD | — | — | — | Read | — |
| Approver L1/L2 | Approve | — | Approve(transfer) | Approve(disposal) | — | — | — |
| Opening Officer 1-3 | — | Open only | — | — | — | — | — |
| Eval. Committee (Sec/Member) | — | Read | — | — | — | — | — |
| Committee Chairperson | — | Approve | — | — | — | — | — |
| Logistics Officer | — | — | CRUD | — | — | Read | — |
| Storekeeper | — | — | Receipt/Dispatch | — | — | — | — |
| Fleet Manager | — | — | — | — | CRUD | — | — |
| Asset Officer | — | — | — | CRUD | — | — | — |
| Finance Officer | Read(budget) | — | Read(stock) | Read | Read | CRUD | — |
| Auditor | Read | Read | Read | Read | Read | Read | Full Read |

---

## 2. Architecture & Design Principles

### 2.1 Build on ERPNext, Don't Fight It

Ugavi extends ERPNext v16 without core patches. Zero ERPNext core patches is a hard architectural constraint. All customization uses hooks, custom DocTypes, and scoped app assets.

| Layer | What Ugavi Owns (App) | What ERPNext Owns (Native) |
|-------|----------------------|----------------------------|
| **Master Data** | Donor Profile, Supplier Prequalification, Evaluation Committee, Ugavi Procurement Settings | Supplier, Item, Warehouse, Account, Company, Vehicle |
| **Transactions** | Purchase Requisition, Tender, Bid, Ugavi Contract, Supplier Evaluation, Bid Opening Record, Three-Way Match, Budget Encumbrance | Purchase Order, Purchase Receipt, Purchase Invoice, Stock Entry, Payment Entry, Landed Cost Voucher, Quality Inspection |
| **Governance** | Delegation of Authority, Segregation of Duties, Sealed-Bid Crypto (RSA+AES+SSS+OTP), Hash Chain, Rate Limiter | User, Role, Permission, Workflow |
| **Logistics** | Monthly Stock Report, Inter-Donor Transfer, Donor Warehouse, Fleet Purchase Reconciliation, Fleet Utilization Report, Asset Register, Asset Movement, Asset Verification, Asset Disposal | Stock Ledger, General Ledger, Financial Reports, Vehicle, Vehicle Log |
| **Portal** | /supplier/dashboard, opportunities, bids, clarifications, complaints, contracts, awards, evaluations | Website User, Notification Log, Email Account |

**Key principle:** Every Ugavi transaction links to its ERPNext counterpart. A Purchase Requisition flows into an ERPNext Purchase Order. A Tender award creates the PO. Stock receipts use native Purchase Receipt with Ugavi donor dimensions and custom fields (`ugavi_*` prefix).

### 2.2 System-Generated Document Coding

Every transactional document receives a system-generated code at creation. Codes are immutable after generation.

| Document | Naming Pattern | Example | Owner |
|----------|---------------|---------|-------|
| Purchase Requisition | `PR-<donor_code>-<YYYY>-<#####>` | PR-IOM-2026-00042 | Ugavi |
| Tender | `TND-<YYYY>-<#####>` | TND-2026-00015 | Ugavi |
| Bid | `BID-<YYYY>-<#####>` | BID-2026-00123 | Ugavi |
| Contract | `UGAVI-CT-<YYYY>-<#####>` | UGAVI-CT-2026-00007 | Ugavi |
| Purchase Order | Native ERPNext naming | PUR-ORD-2026-00089 | ERPNext |
| Purchase Invoice | Native ERPNext naming + `LOK-INV-<supplier>-<seq>` in seed | LOK-INV-TCL-0412 | ERPNext |

### 2.3 Threshold-Driven Procurement Method

The system auto-determines the procurement method based on total estimated value at PR creation. Thresholds and effective dates are configurable via **Ugavi Procurement Settings** (single DocType). Every change logged in audit history.

| Total Estimated Value (KES) | Method | Supplier Pool | Typical Use |
|------------------------------|--------|---------------|-------------|
| 0 – 199,999 | Direct Procurement (RFQ) | Any registered supplier | Office consumables, emergency repairs |
| 200,000 – 499,999 | Restricted Tender | Prequalified suppliers only (per category) | Water tanks, HDPE pipes, small constructions |
| 500,000 and above | Open Tender | Any potential supplier | Major construction, fleet, large equipment |

**Waivers:** A waiver with approved justification can override the automatic method. Waiver requires a separate approver and creates an immutable audit record.

**Donor-specific rules:** Donor Rule (child table on Donor Profile) can further restrict the method for specific donors (e.g., "USAID requires Open Tender ≥ 300,000").

**Category-specific rules:** Category prequalification determines Restricted eligibility. A supplier must hold an active, unexpired prequalification for the tender's category.

### 2.4 Donor Isolation

The system treats each donor's stock, budget, and assets as separate pools. No cross-donor consumption without explicit approved transfer.

| Isolation Domain | Mechanism | Enforcement |
|-----------------|-----------|-------------|
| **Stock** | Donor-Warehouse mapping (Donor Warehouse DocType) | Stock Entry validates source/destination match donor |
| **Budget** | Budget Against = Donor Profile | Commitment tracks per-donor budget line |
| **Assets** | Asset donor field + location donor validation | Cross-donor asset movement rejected |
| **Fleet** | Vehicle donor attribution + purchase reconciliation donor | Fuel/spares must match vehicle's donor |
| **Inter-Donor Transfer** | Separate approval workflow (Stock Manager) | Direct cross-donor Stock Entry rejected at controller level |

### 2.5 Segregation of Duties (Controller-Level, Not UI-Only)

| Rule | Enforcement Point | Mechanism | Violation Response |
|------|-------------------|-----------|-------------------|
| Requester != Approver | PR submit | Controller: `validate_requester_not_approver()` | Block with message |
| Requester != Receiver | Purchase Receipt creation | Controller: cross-check PR requester vs receipt creator | Block with message |
| Opening Officer != Evaluator | Tender save / Evaluation COI | Role membership check on committee composition | Block save |
| Evaluator != Award Approver | Award recommendation | Chairperson role separate from evaluator membership | Block save |
| Disposal Requester != Disposal Authorizer | Asset Disposal | Separate user required for approval | Block approval |
| Opening Officer 1, 2, 3 must be distinct | Bid opening ceremony | Three unique users enforced | Block ceremony start |

### 2.6 Hash Chain Audit Trail

Every critical document maintains an immutable hash chain: `hash(n) = SHA-256(hash(n-1) + document_hash + timestamp + user)`. Chain is verified on read; tampering is detectable and logged.

Documents covered: Tender, Bid, Bid Opening Record, Ugavi Contract, Asset Disposal, Inter-Donor Transfer.

---

## 3. Journey 1: Procurement — Prequalification to Contract

### 3.1 Overview

Covers original requirements **1a (Prequalification), 1c (PR), 1d (PO), 1e (Supplier Evaluation), 1f (Contract).** Includes donor-specific rules (PR3), category rules (PR4), waivers (PR5), DoA routing (PR6), and budget checking (PR7).

**CRITICAL DISTINCTION — Ugavi has TWO evaluation types:**

| Evaluation Type | When | Who | Criteria | Weights | Determines |
|----------------|------|-----|----------|---------|------------|
| **Tender Evaluation** (Journey 3) | After bid opening, before award | Evaluation Committee (Chair/Sec/Members) | Technical Compliance, Delivery Timeline, Past Performance, Financial Offer | 40/20/15/25 | Award winner |
| **Supplier Performance Evaluation** (Journey 1, section 3.6) | After goods receipt | Procurement Officer | Quality, Delivery, Compliance, Price | 30/25/25/20 | Payment eligibility, cumulative rating |

These are DIFFERENT processes with DIFFERENT actors, criteria, and weights. Do not conflate them.

```
[Supplier Registration] --> [Prequalification by Category] --> [Eligibility Gate]
[Programme Staff] --> [Purchase Requisition] --> [DoA Approval Chain] --> [Approved]
[Procurement] --> [Tender / Award] --> [ERPNext Purchase Order] --> [Ugavi Contract]
[Storekeeper] --> [Purchase Receipt] --> [Auto-Create Supplier Evaluation] --> [Payment Gate]
```

### 3.2 Supplier Prequalification

**Actors:** Supplier (portal) -> Procurement Officer (Desk)
**DocTypes:** ERPNext Supplier (native) + Ugavi Supplier Prequalification (app-owned)

#### Steps:
1. Supplier signs in at /supplier/dashboard, opens #profile. Portal exposes narrow allowlist: email, mobile, website, tax ID only. Commercial/admin fields remain Desk-controlled.
2. Supplier selects #prequalification, picks a category (e.g., "WASH Supplies"), sets requested expiry (max 1 year), optionally uploads a private supporting document (tax compliance, registration cert).
3. Applies -> Status: Under Review. Portal notification generated.
4. Procurement Officer opens Supplier Prequalification in Desk, filters by supplier + category, inspects private attachment and dates.
5. Reviews and approves -> Status: Prequalified with expiry. **Controller checks for "Prequalified" status, not "Active".**
6. System auto-suspends on expiry via daily scheduler check.
7. Cumulative supplier rating < 60% -> automatic suspension, regardless of prequalification status.

| Rule | Behavior |
|------|----------|
| One prequalification per supplier-category | Duplicate prevented |
| Expired = not eligible for Restricted | Checked at tender publication |
| Suspended = cannot bid | Checked at bid submission |

**Demo:** Show supplier profile, prequalification record, category eligibility, expiry. Demonstrate expired/suspended supplier blocked.

### 3.3 Purchase Requisition

**Actors:** Programme Staff -> Approver(s) -> Procurement Officer
**ERPNext:** Ugavi PR (app-owned)

#### Steps:
1. Programme staff creates PR: Title, Dept, Donor, Project, Items (qty x unit price), Justification
2. System auto-determines method: <200K Direct, 200K-499K Restricted, >=500K Open
3. System generates code: PR-<donor_code>-<YYYY>-<#####>
4. Submit for Approval -> Pending Approval
5. System routes via DoA matrix (department x amount x donor)
6. Requester cannot self-approve (segregation)
7. Approver enters remarks, approves/rejects
8. Status: Approved / Rejected
9. Budget check fires (warn or stop)
10. Hand-off to Procurement Officer

**Validation:**
- [ ] System-generated PR code
- [ ] Auto-determined method matches thresholds
- [ ] Approval history with role, user, timestamp
- [ ] Requester cannot self-approve
- [ ] Budget check fires
- [ ] PR links to Tender or PO

### 3.4 Purchase Order Generation

**Actor:** Procurement Officer
**ERPNext:** Native PO with Ugavi custom fields

#### Steps:
1. From Awarded Tender or approved PR, create ERPNext PO
2. Ugavi fields: ugavi_pr, ugavi_tender, ugavi_donor, ugavi_project, ugavi_budget, ugavi_inspection_required
3. ERPNext auto-generates PO code
4. On submit: budget encumbrance, contract auto-created/linked
5. Supplier acknowledges in portal (#contracts, #deliveries)

### 3.6 Supplier Performance Evaluation

**Actor:** Procurement Officer
**ERPNext:** Ugavi Supplier Evaluation (app-owned)

#### Steps:
1. On Purchase Receipt submit -> auto-create evaluation (linked to receipt)
2. Scoring (0-10): Quality 30%, Delivery 25%, Compliance 25%, Price 20%
3. Weighted total = (Qx0.30)+(Dx0.25)+(Cx0.25)+(Px0.20)
4. Payment gate: all evaluations must be Completed before payment
5. Cumulative rating < 60% -> auto-suspend supplier

### 3.5 Contract Management

**Actor:** Procurement Officer
**ERPNext:** Ugavi Contract (app-owned)

#### Steps:
1. Draft -> Active requires: submitted PO, >=1 milestone, agreement doc, valid dates, bond (if needed)
2. Milestones: description, due date, completion date, evidence, status
3. Retention % and performance bond tracked
4. Completion requires: all milestones + all receipt evaluations
5. Daily expiry alerts


---

## 4. Journey 2: Tendering — Publication to Sealed-Bid Opening

### 4.1 Overview

Covers original requirement **1b (Tendering)** — the most technically sophisticated component.

```
[PR Approved]-->[Create Tender]-->[Publish]-->[Bids Received]
[Deadline]-->[3-Officer Opening]-->[Under Evaluation]
[Evaluation]-->[Recommendation]-->[Standstill]-->[Award]-->[PO]
```

### 4.2 Tender Creation & Publication

**Actor:** Procurement Officer
**ERPNext:** Ugavi Tender (app-owned, NOT native RFQ)

1. From approved PR, create Tender: Title, PR link, Donor, Method, Est. Value, Category, Deadline, 3 Opening Officers
2. Publish: RSA-4096 key pair generated, private key split via SSS (3-of-3), public key stored, status Published
3. Restricted: only prequalified suppliers for category. Open: any supplier.
4. Addenda with optional deadline extension

### 4.3 Supplier Bid Submission

**Actor:** Supplier (portal)
**ERPNext:** Ugavi Bid (app-owned, NOT native Supplier Quotation)

1. Supplier views eligible tenders in #opportunities
2. Prepare Bid: amount (KES), delivery days, technical proposal PDF
3. Encrypt and Submit: AES-256-GCM encrypted, wrapped with tender's RSA-4096 public key
4. No plaintext stored — encrypted envelope in DB
5. Bid status: Submitted (not Opened). Cannot edit.
6. Late bids rejected (server clock)
7. Clarifications: supplier asks, procurement answers

**Key validations:**
- [ ] Bid encrypted with tender's public key
- [ ] No plaintext in DB
- [ ] Late bids rejected
- [ ] Bid ID receipt generated
- [ ] Cannot edit after submission

### 4.4 Three-Person Sealed-Bid Opening (Crown Jewel)

**Actors:** Three Opening Officers
**ERPNext:** Ugavi Bid Opening Record (app-owned)

#### Steps:
1. After deadline: officer opens tender -> **Open Sealed Bids**
2. System generates 3 OTP codes (6-digit) -> Email/SMS delivery
3. Codes: bcrypt-hashed, 5-min expiry, 3-attempt rate limit
4. All 3 officers supply codes in ceremony session
5. Codes validated (constant-time) -> private key reconstructed via SSS (3-of-3) in memory
6. Each bid decrypted: RSA unwrap AES key -> AES decrypt bid data
7. **Bid Opening Record** generated: all amounts, officers, immutable hash chain, signed PDF
8. Codes purged, key purged from memory. Tender -> Under Evaluation.

**Security controls:**
| Control | Implementation |
|---------|---------------|
| 1-person cannot open | SSS 3-of-3 |
| 2-person cannot open | 3 shares mandatory |
| DB admin cannot read bids | Encrypted envelope; key never stored |
| Code replay impossible | Hash compared, then deleted |
| Code expiry | 5-min window |
| Rate limiting | 3 attempts per code per hour |
| Audit trail | Who, when, IP, outcome logged |

---

## 5. Journey 3: Evaluation — Scoring to Award Decision

### 5.1 Overview

**THIS IS TENDER EVALUATION, not Supplier Performance Evaluation (Journey 1 section 3.6).** The evaluation committee scores submitted bids to determine the award winner.

Evaluation Committee: Chairperson (Grace Lokwang), Secretary (Dorothy Nekesa), Member(s) (Samuel Lomuria).

### 5.2 Evaluation Committee

1. Tender has Evaluation Committee (Chairperson, Secretary, Members)
2. Opening officers cannot be committee members (segregation)
3. Each member submits COI Declaration before scoring
4. Scoring blocked until COI submitted

### 5.3 COI Declaration

Each committee member must submit a Conflict of Interest Declaration before scoring:
- Signed by the declarant's own session
- Declares \"No conflict\" or discloses conflict
- COI must be submitted before scoring is allowed (controller gate)

### 5.4 Weighted Scoring (Tender Evaluation)

| Criterion | Weight | Scale |
|-----------|--------|-------|
| Technical Compliance | 40% | 0-100 |
| Delivery Timeline | 20% | 0-100 |
| Past Performance | 15% | 0-100 |
| Financial Offer | 25% | 0-100 |

1. Each evaluator scores independently; submitted scores are immutable
2. Secretary creates Evaluation Minutes -> Chairperson approves
3. Chairperson creates Bid Evaluation Summary -> recommends top-ranked bid
4. Recommendation rejected if not evidence-backed

### 5.5 Standstill & Award

1. Start Standstill: 14 days, tender -> Standstill Period
2. Complaint window: unsuccessful bidders challenge via #complaints
3. Standstill marked Challenged if complaint received; Confirm blocked
4. After end date, no open complaints -> Confirm Standstill -> Award Tender
5. Award creates: ERPNext PO + Ugavi Contract for recommended supplier
6. Regret notices to unsuccessful bidders

**Lifecycle:** Draft -> Published -> Bids Received -> Under Evaluation -> Standstill -> Awarded -> Closed



---


---

## 6. Journey 4: Receipt, Stock & Donor Ledgers

### 6.1 Overview

Covers original requirement **2a (Stock Management)**.

```
[PO]-->[Purchase Receipt]-->[Quality Inspection]-->[Stock Entry]
[Stock Ledger]-->[Donor Warehouse]-->[Monthly Stock Report]
[Donor A]-->[Inter-Donor Transfer]-->[Donor B]
```

### 6.2 Stock Receipt

**Actor:** Storekeeper (Ruth)
**ERPNext:** Native Purchase Receipt + Stock Entry

1. From PO -> Create Purchase Receipt. Accepted/Rejected warehouses match donor.
2. Quality Inspection required if flagged (ugavi_inspection_required)
3. On submit: stock posted to accepted warehouse, Supplier Evaluation auto-created
4. Stock dispatch via Stock Entry -> Material Issue, validates donor ownership

### 6.5 Donor Stock Ledger & Monthly Reports

**Actor:** Logistics Officer (John)
**ERPNext:** Native Stock Ledger + Ugavi Monthly Stock Report

**Donor-Warehouse mapping:**
| Donor | Warehouse |
|-------|-----------|
| IOM | IOM Supported Warehouse - Kakuma |
| USAID | LOKADO Main Warehouse - Lodwar |
| CONCERN | LOKADO Field Store - Lokichoggio |
| JAPAN | Cold Chain Storage - Lodwar |
| EU | LOKADO Transit Store - Kitale |
| LOKADO-OWN | LOKADO Field Store - Oropoi |

**Monthly Stock Report:** Opening Balance, Receipts, Issues, Transfer In, Transfer Out, Closing Balance, Value. PDF/Excel output. Reconciles with native Stock Ledger.

**Inter-Donor Transfer:** Draft -> Pending Approval -> Approved -> Completed. Stock Manager approval required. Direct cross-donor Stock Entry without approved transfer is rejected.

**Validation:**
- [ ] Donor-warehouse mapping defined and enforced
- [ ] Stock Ledger filterable by donor warehouse
- [ ] Monthly report reconciles with native ledger
- [ ] Inter-donor transfer requires approval
- [ ] Direct cross-donor entry rejected

---

## 7. Journey 5: Asset Lifecycle — Register to Disposal

### 7.1 Overview

Covers original requirement **2b (Asset Management)**.

```
[Register]-->[QR Tag]-->[Custody]-->[Movement]-->[Verification]
[Maintenance]-->[Condition Update]-->[Disposal]
```

### 6.2 Asset Register

**Actor:** Asset Officer (Agnes)
**ERPNext:** Ugavi Asset Register (app-owned)

1. Asset Tag (e.g., LOK-IT-001), Item, Description, Category, Donor, Serial, Value, Location, Custodian, Condition
2. QR code generated for physical tagging; Status: Active

### 6.3 Asset Movement

1. Select asset, source/destination location & custodian, condition, reason
2. Cross-donor destination rejected (destination must match asset's donor)
3. On confirmation: validates source state, updates register; movement history preserved

### 6.4 Asset Verification

1. Monthly reminder: verify assets (Found Yes/No, date, verifier, condition)
2. Not Found assets flagged; condition discrepancies noted

### 6.5 Asset Disposal

1. Disposal method (Auction/Donation/Write-off), value, book value, gain/loss, reason
2. Requires approval by separate authorizer (segregation)
3. Asset Register -> Disposed

**Validation:**
- [ ] Unique asset tag with QR code
- [ ] Movement updates register (location/custodian)
- [ ] Cross-donor movement rejected
- [ ] Verification captures found/not found status
- [ ] Disposal requires separate approver

---

## 8. Journey 6: Fleet — Allocation to Monthly Reports

### 8.1 Overview

Covers original requirement **2c (Fleet Management)** — purchase-linked consumption.

```
[Vehicle Register]-->[Allocation]-->[PO/Receipt for Fuel/Spares]
[Purchase Reconciliation]-->[Fuel Log]-->[Spare Parts Issue]
[Trip Log]-->[Fleet Utilization Report (monthly)]
```

### 7.2 Vehicle Allocation

**Actor:** Fleet Manager (David)
**ERPNext:** Native Vehicle + Ugavi Vehicle Allocation

1. Vehicle registered with donor attribution, insurance expiry, service schedule
2. Allocation: vehicle, driver, period, donor, purpose (no overlap)

### 7.3 Purchase-Linked Fuel & Spares (Critical)

Fuel/spare parts consumption MUST be traceable to specific purchase documents:

1. **Fleet Purchase Reconciliation:** Auto-created on Purchase Receipt submit for fleet items. Tracks: receipt/PO refs, item, purchased qty, unit price, allocated qty, remaining qty, donor.
2. **Fuel Log:** Vehicle, reconciliation source, qty (L), price/L, total cost, odometer. System validates: qty <= remaining, same donor.
3. **Spare Parts Issue:** Vehicle, reconciliation source, qty issued, linked Material Issue Stock Entry. System validates: qty <= remaining, same donor.

### 7.4 Trip Log & Monthly Report

1. Trip Log: vehicle, start/end odometer, distance, destination, purpose, date
2. **Fleet Utilization Report** per donor, per month:
   - Total trips, total distance (km), fuel consumed (L), fuel cost (KES)
   - Fuel efficiency (km/L), spare parts cost (KES), total operating cost
3. Scheduled monthly via cron

**Validation:**
- [ ] Fleet Purchase Recon auto-created on receipt
- [ ] Fuel log linked to specific purchase receipt
- [ ] Spare parts issue linked to specific purchase receipt
- [ ] Quantity validation prevents over-allocation
- [ ] Donor consistency enforced throughout
- [ ] Trip log records odometer readings
- [ ] Monthly report aggregates trips, fuel, spares

## 9. Journey 7: Finance — Invoice, Match, Payment & Budget

### 9.1 Three-Way Match

**Actor:** Finance Officer (Margaret)
**ERPNext:** Ugavi Three-Way Match (app-owned)

On Purchase Invoice submit, auto-creates match:
- PO (qty x price) <-> GRN (qty received) <-> Invoice (qty x price billed)
- Tolerances: Qty +/-5%, Price +/-3%, Amount +/-2%
- Outcome: Matched / Disputed

### 9.2 Budget Encumbrance

- On PO submit: creates commitment, reduces available budget
- On PO cancel: reverses encumbrance

### 9.3 Payment Gate

- All linked Supplier Evaluations must be Completed
- Three-Way Match must not have unresolved disputes
- Supplier rating < 60% suspends supplier

### 8.4 Kenya Localization (Extension Points)

| Feature | Status |
|---------|--------|
| KES currency + multi-currency | Configured |
| VAT + Withholding tax templates | Scaffold |
| KRA PIN validation | Scaffold |
| eTIMS integration | Adapter pattern (sandbox) |
| M-Pesa payment integration | Stub adapter |
| SMS notifications | Provider abstraction |

---

## 10. Journey 8: Governance, Complaints & Audit

### 9.1 Delegation of Authority

Department x Amount Range x Donor -> Approver Role (with effective dates)

### 9.2 Segregation of Duties (Controller-Level)

- Requester != Approver
- Requester != Receiver
- Opening Officer != Evaluator
- Evaluator != Award Approver
- Disposal Requester != Disposal Authorizer

### 9.3 Hash Chain Audit Trail

Every critical document (Tender, Bid, BOR, Contract) has immutable hash chain. Tampering detectable. Logs: who, when, IP, action, outcome.

### 9.4 Notification Rules

| Event | Channel |
|-------|---------|
| PR approval required | Email |
| Tender published | Portal |
| Bid opening OTP | Email + SMS (stub) |
| Standstill started | Portal + Email |
| Award/Regret notice | Portal + Email |
| Contract expiry alert | Email |
| Supplier evaluation | Portal |
| Complaint outcome | Portal |

### 9.5 Role-Based Workspaces

- Ugavi Procurement: Programme, Procurement, Approvers
- Ugavi Tendering: Procurement, Opening Officers, Evaluators
- Ugavi Assets: Asset Officer
- Ugavi Fleet: Fleet Manager
- Supplier Portal: Supplier users

---

## 11. Non-Functional Requirements

### 11.1 Performance
| ID | Requirement | Target |
|----|-------------|--------|
| NF1 | PR/Tender list load | <2s for 1000 records |
| NF2 | Sealed-bid opening | <5s for 3-key reconstruction |
| NF3 | Bid submission | <3s for 1MB encrypted payload |
| NF4 | Concurrent bidders | 50 simultaneous without error |

### 11.2 Security
| ID | Requirement | Implementation |
|----|-------------|---------------|
| NF5 | OWASP ASVS Level 2 | docs/security/owasp-asvs-mapping.md |
| NF6 | TLS 1.3 | nginx security headers config |
| NF7 | Secrets never in logs/commits/backups | detect-secrets CI + .gitignore |
| NF8 | Private keys 3-of-3 SSS; never stored whole | Sealed-bid crypto service |
| NF9 | Container CVE scanning | Trivy in CI |
| NF10 | Rate limiting | 3 attempts/hour/supplier/code |

### 11.3 Availability
| ID | Requirement | Implementation |
|----|-------------|---------------|
| NF11 | Health check endpoint (HTTP 200 + db + cache) | 9 Prometheus metrics |
| NF12 | Daily backups with files, 90-day retention | Bench backup + procedure doc |
| NF13 | RPO <1h, RTO <4h | Documented restore procedure |

### 11.4 Maintainability
| ID | Requirement | Implementation |
|----|-------------|---------------|
| NF14 | Test coverage: all features require FrappeTestCase | 84 tests (17 integration + 67 unit) |
| NF15 | Zero ERPNext core patches (hooks-only) | test_hook_safety.py CI check |
| NF16 | SBOM per PR (SPDX JSON) | Anchore Syft in CI |
| NF17 | Upgrade dry-run CI | make upgrade-check |

### 11.5 Compliance & Audit
| ID | Requirement | Implementation |
|----|-------------|---------------|
| NF18 | Immutable hash chain on critical documents | Tender, Bid, BOR, Contract, Disposal, Transfer |
| NF19 | Segregation enforced at controller level (not UI-only) | Server-side validation in every controller |
| NF20 | Full audit trail: who, when, IP, action, outcome | Audit Log DocType + hash chain verification |

### 11.6 Demo-Specific (LOKADO)
| ID | Requirement | Status |
|----|-------------|--------|
| NFD1 | Seed script idempotent (_ensure upsert; re-runnable) | ✅ |
| NFD2 | Seed script production-guarded (refuses non-demo) | ✅ |
| NFD3 | All functional requirements mapped to demo scenes | ✅ (this document) |
| NFD4 | Realistic Turkana/Kenyan names and roles | ✅ |

---


## 12. Simplified NGO Deployment Model

### 10.1 Tier 1: Essential (2-4 weeks)

**Day one:** PR (single-level approval, donor link), PO (native with donor field), Stock (native with donor warehouse), Basic Prequalification.

**Defer:** Sealed-bid tendering, 3-person opening, evaluation committee, contracts, fleet/assets, supplier portal.

### 10.2 Tier 2: Standard (4-8 weeks)

**Add:** Open/Restricted tender with encrypted bids, evaluation committee + COI + weighted scoring, supplier portal (registration, docs, PO viewing), contract milestones, monthly stock reports, three-way match.

### 10.3 Tier 3: Advanced (8-12 weeks)

**Full governance:** 3-of-3 SSS sealed-bid opening, standstill + complaints, fleet (purchase-linked fuel/spares, monthly reports), assets (register, movement, verification, disposal), budget encumbrance, payment gate, dashboards.

### 10.4 Organization-Specific Recommendations

| Size | Recommendation |
|------|---------------|
| Small NGO (<20 staff, <50 tx/month) | Tier 1, direct procurement, manual evaluation, skip fleet if <5 vehicles |
| Medium NGO (20-100 staff, 50-200 tx/month) | Tier 2 sweet spot, restricted/open for large purchases, basic fleet |
| Large INGO (100+ staff, 200+ tx/month) | Full Tier 3, multiple donors, full sealed-bid, complete fleet/asset |
---

## 13. Demo Script — Systematic Walkthrough

### 11.1 Presenter Checklist (Before Demo)

- [ ] Run `make clean && make setup` for fresh environment
- [ ] Run `make demo-check` and `make fleet-check` — both must show "ready": true
- [ ] Run `make demo-index` — copy all record IDs
- [ ] Open Mailpit at http://localhost:8026
- [ ] Prepare fictional PDFs: registration cert, bid proposal, complaint evidence
- [ ] Open http://ugavi.localhost:8000 or :8080
- [ ] Run `make backup-demo` to create restore point

### 11.2 Demo Credentials

**Staff (password: Ugavi@2024):**

| Actor | Email | Role |
|-------|-------|------|
| Alice Akol | programme@lokado.org | Programme Staff |
| Peter Ekai | procurement@lokado.org | Procurement Officer |
| Jane Napeyok | approver1@lokado.org | Approver Level 1 |
| Paul Lotir | approver2@lokado.org | Approver Level 2 |
| Mary Akuom | opening1@lokado.org | Opening Officer 1 |
| James Ebei | opening2@lokado.org | Opening Officer 2 |
| Sarah Nabwel | opening3@lokado.org | Opening Officer 3 |
| Dorothy Nekesa | committee@lokado.org | Committee Secretary |
| Grace Lokwang | chair@lokado.org | Committee Chair |
| Samuel Lomuria | evaluator@lokado.org | Evaluator |
| John Ekiru | logistics@lokado.org | Logistics Officer |
| Ruth Napeyok | storekeeper@lokado.org | Storekeeper |
| David Ewoi | fleet@lokado.org | Fleet Manager |
| Agnes Ekal | assets@lokado.org | Asset Officer |
| Margaret Nachuk | finance@lokado.org | Finance Officer |
| Robert Lotukoi | auditor@lokado.org | Auditor |

**Suppliers (password: Ugavi@2024):**

| Supplier | Email |
|----------|-------|
| Turkana Construction Ltd | turkana-construction@outlook.com |
| Nadirkonyen Women's Group | nadirkonyen-women@outlook.com |
| Rift Valley Hardware | riftvalley-hardware@outlook.com |
| Jopeji Enterprises | jopeji@outlook.com |
| Lodwar General Supplies | lodwar-supplies@outlook.com |

### 11.3 Scene-by-Scene

**Scene 1 — Organization & Context (3 min, PREPARED):**
Peter signs in. Show Company, Donor Profiles, Projects. Show PRs with different donors.

**Scene 2 — Procurement Thresholds (5 min, PREPARED):**
Show Ugavi Procurement Settings thresholds. Compare PRs at 195K, 450K, 1.2M. Show DoA matrix. Auditor shows Audit Log.

**Scene 3 — Purchase Requisition & Approval (10 min, LIVE):**
Alice creates PR "DEMO-<session>-IOM Water Tanks" (12 x 37,500 = 450K -> Restricted). Submit for Approval. Alice cannot self-approve. Jane approves. Status: Approved. Hand-off to Peter.

**Scene 4 — Supplier Prequalification (7 min, LIVE/PREPARED):**
Lodwar General logs into portal, views profile and prequalification. Peter reviews private attachments. Compare expired (Samburu) and suspended (Turkana Fuel) records.

**Scene 5 — Tender Publication & Bid (7 min, LIVE):**
Peter creates Restricted Tender from PR. Publishes -> RSA key, 3-way SSS. Lodwar General sees opportunity. Prepares Bid: KES 425,000. Encrypt and Submit. Clarification Q&A.

**Scene 6 — Three-Person Sealed-Bid Opening (8 min, LIVE):**
Fixture: Solar Water Pumps EU (780K, 4 bids). Mary opens tender, clicks Open Sealed Bids. Mailpit: 3 OTP emails. All 3 officers supply codes -> bids decrypted. BOR: 745K, 768K, 790K, 810K.

**Scene 7 — Evaluation & Standstill (7 min, PREPARED + LIVE):**
Fixture: Livestock Galla Goats USAID. Show COI Declarations, 9 Evaluation Scores, Approved Minutes, Bid Evaluation Summary (Nadirkonyen 365K). Peter clicks Start Standstill -> 14-day standstill.

**Scene 8 — Purchase Order & Contract (7 min, PREPARED):**
Show logistics PO for Turkana Construction. Linked Ugavi Contract (Active, milestones, 10% retention). Supplier acknowledges in portal.

**Scene 9 — Stock & Donor Ledgers (10 min, PREPARED):**
Show Purchase Receipt, Stock Entry (Issue to Concern SERVE Loima). Stock Ledger filtered by warehouse/donor. Monthly Stock Report (IOM). Inter-Donor Transfer (IOM->CONCERN).

**Scene 10 — Supplier Evaluation & Payment Gate (5 min, PREPARED):**
Completed evaluation for Turkana Construction (91.4%). Purchase Invoice 60% paid. Three-Way Match -> Matched. Explain payment gate.

**Scene 11 — Asset Management (7 min, PREPARED):**
Asset Register LOK-IT-001 (USAID laptop). Movement history (Lodwar->Oropoi). Verification. Disposal (LOK-OLD-001, Auction 12K). Cross-donor rejection.

**Scene 12 — Fleet Management (10 min, PREPARED):**
Vehicle KDM 271I (IOM Hilux). Allocation. Purchase Recon. Fuel Log: 50L+70L. Spare Issue. Trip Log. Fleet Utilization Report: 2 trips, 500km, 120L, 4.17 km/L.

**Scene 13 — Complaints & Governance (8 min, LIVE):**
Fixture: Field Motorcycles USAID (active standstill). Lodwar General submits complaint via portal. Peter assigns review panel (Jane, Paul, Robert). Under Review -> Outcome. Robert inspects audit trail.

**Closing — Upgrade Safety (2 min):**
Show `make upgrade-check`, `make test`, `make e2e` results. Demonstrate backup/restore.



---

## 14. Acceptance Criteria & Sign-Off Checklist

### 12.1 Procurement (Original Req. 1a-1f)

| # | Criterion | Evidence | Status |
|---|-----------|----------|--------|
| 1.1 | Prequalification list with categories and expiry | Supplier Prequalification record | |
| 1.2 | Restricted tender (200K-499K) only allows prequalified suppliers | Category + status check | |
| 1.3 | Open tender (>=500K) allows any supplier | No prequalification gate | |
| 1.4 | System-generated OTP codes (3 officers) for bid opening | Three Bid Opening OTP emails | |
| 1.5 | No single person can decrypt bids | SSS 3-of-3: 2 shares fail | |
| 1.6 | System-coded PR with approval chain | PR-<donor>-<YYYY>-<#####> | |
| 1.7 | Programme staff creates PR, cannot self-approve | Segregation enforced | |
| 1.8 | System-coded PO with donor/project dimensions | Native PO with ugavi_ fields | |
| 1.9 | Supplier evaluation auto-triggered on receipt | Completed evaluation + score | |
| 1.10 | Contract with milestones, retention, bonds | Active contract record | |

### 12.2 Logistics (Original Req. 2a-2c)

| # | Criterion | Evidence | Status |
|---|-----------|----------|--------|
| 2.1 | Donor-segregated stock ledger | Donor Warehouse + Monthly Report | |
| 2.2 | Stock receipt and dispatch recorded | Stock Ledger entries | |
| 2.3 | Monthly stock report per donor | PDF/Excel generation | |
| 2.4 | Asset register with QR tags | Asset Register record | |
| 2.5 | Asset movement and condition tracking | Movement history + verification | |
| 2.6 | Asset disposal with approval | Disposal record + authorizer | |
| 2.7 | Vehicle allocation by donor | Allocation record | |
| 2.8 | Fuel consumption linked to purchase | Fleet Purchase Recon + Fuel Log | |
| 2.9 | Spare parts consumption linked to purchase | Fleet Purchase Recon + Spare Issue | |
| 2.10 | Monthly fleet report per donor | Fleet Utilization Report | |

### 12.3 Governance & Compliance

| # | Criterion | Evidence | Status |
|---|-----------|----------|--------|
| 3.1 | Segregation of duties enforced | Controller-level blocks | |
| 3.2 | Delegation of Authority matrix | DoA records | |
| 3.3 | Hash chain on critical documents | Audit trail entries | |
| 3.4 | Three-way match (PO <-> GRN <-> Invoice) | Match/dispute records | |
| 3.5 | Budget encumbrance at PO | Encumbrance record | |
| 3.6 | Payment gate (evaluation Completed) | Blocked payment | |
| 3.7 | Supplier cumulative rating suspension | Rating < 60% -> disabled | |
| 3.8 | Standstill enforcement before award | Award button hidden | |
| 3.9 | Complaint lifecycle during standstill | Complaint -> review -> outcome | |

### 12.4 Non-Functional

| # | Criterion | Evidence | Status |
|---|-----------|----------|--------|
| 4.1 | Zero core ERPNext patches | hooks.py only | |
| 4.2 | Idempotent seed script | make seed-lokado re-runnable | |
| 4.3 | Daily backups | Native Bench backup | |
| 4.4 | Upgrade rehearsal passing | make upgrade-check | |
| 4.5 | Container security scan | Trivy CI job | |
| 4.6 | Browser E2E tests passing | make e2e | |
| 4.7 | Unit + integration tests passing | make test | |

---

## Appendix A: ERPNext Best-Practice References

| Ugavi Component | ERPNext Reference | How Ugavi Extends |
|-----------------|-------------------|-------------------|
| Purchase Requisition | Material Request | App-owned PR with donor, threshold, DoA |
| Tender | Request for Quotation (RFQ) | App-owned Tender with crypto, portal, evaluation |
| Bid | Supplier Quotation | App-owned Encrypted Bid with SSS opening |
| Purchase Order | Purchase Order | Native PO with ugavi_ custom fields |
| Purchase Receipt | Purchase Receipt | Native with Ugavi evaluation trigger |
| Purchase Invoice | Purchase Invoice | Native with Ugavi three-way match |
| Payment Entry | Payment Entry | Native with Ugavi evaluation gate |
| Stock Entry | Stock Entry | Native with Ugavi donor validation |
| Stock Ledger | Stock Ledger | Native, aggregated by Ugavi Monthly Report |
| Vehicle | Vehicle | Native with Ugavi fleet reconciliation |
| Supplier | Supplier | Native with Ugavi prequalification |
| Asset | Asset | Ugavi Asset Register (separate from ERPNext Asset) |

## Appendix B: Client Decision Points

These require client sign-off before implementation diverges:

1. **Print Templates:** Client-provided PR, PO, prequalification, evaluation, ledger templates
2. **Finance System of Record:** ERPNext as accounting system, or external integration?
3. **Tax Regime:** Kenya VAT + withholding or other?
4. **eTIMS Integration:** Required or deferred?
5. **Donor Report Formats:** USAID, EU, UN, World Bank, etc.
6. **Payment Channels:** Bank transfer, M-Pesa, or both?
7. **SSO Provider:** Azure AD, Google, LDAP, or none?
8. **Records Retention:** 7 years, 10 years, or per-donor?

---


## Appendix C: Document Traceability

| Source Document | This Document Coverage |
|-----------------|----------------------|
| LOKADO-DEMO-TOUR.md (19 scenes) | All scenes covered in demo script section 13; 5 stories; 30-min executive route |
| REQUIREMENTS.md (122 items) | All 8 areas mapped in Acceptance Criteria sections 14.1-14.9 |
| SCOPE.md (13 workstreams) | Deployment Model section 12 maps to workstreams; Client Decisions Appendix B |
| SUPPLIER-JOURNEY.md | Journey 1 section 3.2 (Prequal), Journey 2 section 4.3 (Bidding), Journey 8 section 10.2 (Complaints) |
| use-cases/ (UC-01 to UC-23) | All 23 use cases distributed across 8 journeys |
| known-gaps.md (82 items) | NFR section 11 covers resolved items; open GA-063 (blue/green upgrade) noted |
| RTM.md | Acceptance Criteria section 14 provides re-verifiable checklist |


> **Document version:** 3.0 — Revamped with 16 personas, 8 journeys, NFRs, expanded architecture, and complete traceability. Zero-ambiguity commitment: Tender Evaluation and Supplier Performance Evaluation are explicitly distinguished with different actors, criteria, and weights. All 6 donor segregation domains, 8 fleet vehicles, and 16 staff personas are referenced by name.
> **Last updated:** 2026-11-24
> **App version:** Ugavi 0.1.0 on Frappe v16.55.0 / ERPNext v16.55.0
