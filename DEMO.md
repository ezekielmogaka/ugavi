# Ugavi Demo Walkthrough

> A scripted journey through the full Ugavi supply chain flow, plus negative-path tests.

**Target audience:** Evaluators, auditors, donor representatives.
**Duration:** ~25 minutes.
**Prerequisites:** `make setup && make seed` completed. Site at http://ugavi.localhost:8000.

---

## 1. Login & Dashboard (2 min)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1.1 | http://ugavi.localhost:8000 | Login screen |
| 1.2 | Login as `Administrator` | Ugavi workspace cards |
| 1.3 | **Ugavi Procurement** workspace | KPIs: Pending PRs, Active Tenders, POs |

---

## 2. Supplier Prequalification (3 min)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 2.1 | **Supplier Prequalification** > New | Fields: Supplier, Category, Status, Expiry, Documents |
| 2.2 | Search `Kenya Medical Supplies` | Seeded record shows |
| 2.3 | Prequalification badge | Green = Prequalified, Red = Expired |

**Key control:** Only prequalified suppliers in Restricted Tenders.

---

## 3. Procurement Rules Engine (2 min)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 3.1 | **Ugavi Procurement Settings** | Direct <200K, Restricted 200K-499K, Open >500K |
| 3.2 | Default currency: `KES` | All amounts in KSh |
| 3.3 | "Require Waiver for Override" | Threshold bypass needs documented waiver |

---

## 4. Purchase Requisition — Happy Path (4 min)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 4.1 | Create **Purchase Requisition** | Coded: `PR-2026-0001` |
| 4.2 | Donor: `USAID Kenya`, Category: `Medical Supplies` | |
| 4.3 | Item: `Antimalarial Tablets (ALU)`, Qty 500, Unit 350 | Total: 175,000 KES |
| 4.4 | Save | Method auto: **Direct (RFQ)** (under 200K) |
| 4.5 | Budget check | Budget available: 175,000 KES |
| 4.6 | Submit | DoA: 1 approver (Supervisor) |

**Key control:** Method auto-determined — cannot override without waiver.

---

## 5. Restricted Tender Flow (5 min)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 5.1 | Create **PR-2026-0002** | |
| 5.2 | Donor: `The Global Fund`, Cat: `IT Equipment` | |
| 5.3 | Item: `Laptop - Dell Latitude`, Qty 5, Unit 85K | Total: 425,000 KES |
| 5.4 | Save | Method: **Restricted Tender** |
| 5.5 | "Only prequalified suppliers eligible" | |
| 5.6 | Approve: Supervisor → Programme Manager | Two-step DoA |
| 5.7 | **Create Tender** from PR | TND-2026-0001 |

---

## 6. Tender Publishing & Bid Submission (4 min)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 6.1 | Open TND-2026-0001 | Title, Value, Method, Deadline (+14d) |
| 6.2 | Attach tender documents | Specs, ToR attached |
| 6.3 | Publish | Status → `Published`; countdown starts |
| 6.4 | Login `supplier1@supplier.co.ke` (pwd: `Ugavi@2024!`) | Supplier Portal |
| 6.5 | Supplier sees TND-2026-0001 | Listed as published |
| 6.6 | Submit bid: 410,000 KES, 30d delivery | Encrypted with tender public key |
| 6.7 | Bid confirmed; content sealed | Cannot view other bids |

---

## 7. Three-Officer Sealed Bid Opening (3 min)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 7.1 | After deadline, open TND-2026-0001 | Status: `Bids Received` |
| 7.2 | Click **Open Bids** | 3 Bid Opening Officers identified |
| 7.3 | Each officer receives OTP (check Mailpit: :8025) | 6-digit, 5min expiry |
| 7.4 | Officer 1 enters OTP → Verified | 1/3 shares unlocked |
| 7.5 | Officer 2 enters OTP → Verified | 2/3 shares unlocked |
| 7.6 | Officer 3 enters OTP → Verified | Key reconstructed, bids decrypted |
| 7.7 | **Bid Opening Record** PDF | Who/When/IP; signed audit trail |

---

## 8. Evaluation & Award (2 min)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 8.1 | Committee reviews bids | Price, delivery, compliance visible |
| 8.2 | Award to winner | Status → `Awarded` |
| 8.3 | Auto-generate **Purchase Order** | PO-2026-0001 linked to TND-2026-0001 |

---

## 9. PO → Receipt → Stock Ledger (2 min)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 9.1 | Open PO-2026-0001 | Line items confirmed |
| 9.2 | Supplier acknowledges | Status → `Confirmed` |
| 9.3 | **Purchase Receipt** from PO | GRN created |
| 9.4 | Receive into `USAID Main Store - Nairobi` | Stock ledger: USAID only |
| 9.5 | **Donor Stock Ledger** report | USAID balance up; Global Fund unchanged |

**Key control:** Stock segregated by donor.

---

## 10. Negative-Path Tests (3 min)

### 10.1 Threshold Bypass Blocked

| Step | Action | Expected Result |
|------|--------|-----------------|
| 10.1.1 | PR with value 600,000 KES | Method: **Open Tender** |
| 10.1.2 | Try changing to "Direct (RFQ)" | Blocked — "Waiver required" |

### 10.2 Single-User Bid Opening Blocked

| Step | Action | Expected Result |
|------|--------|-----------------|
| 10.2.1 | Attempt opening with 1 or 2 OTPs | Blocked — "All 3 officers required" |
| 10.2.2 | System logs attempt | Audit: failed opening recorded |

### 10.3 Cross-Donor Stock Blocked

| Step | Action | Expected Result |
|------|--------|-----------------|
| 10.3.1 | Try issuing USAID stock to Global Fund project | Blocked — "Donor segregation violation" |

---

## 11. Supplier Scorecard & Dashboard (2 min)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 11.1 | **Supplier Scorecard** after receipt | Delivery, Quality, Documentation scores |
| 11.2 | Score < 60 triggers suspension | Review notification |
| 11.3 | **Procurement Dashboard** | Charts: PRs, Tenders, POs, Supplier heatmap |

---

## Completion Checklist

- [ ] Login & Dashboard
- [ ] Supplier Prequalification
- [ ] Procurement Rules
- [ ] Direct procurement (PR-0001)
- [ ] Restricted tender (PR-0002 → TND-0001)
- [ ] Supplier portal bid
- [ ] Three-officer bid opening
- [ ] Evaluation & award
- [ ] PO → Receipt → Donor ledger
- [ ] [NEG] Threshold bypass blocked
- [ ] [NEG] Single-user opening blocked
- [ ] [NEG] Cross-donor stock blocked
- [ ] Scorecard & dashboard

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Site not loading | `docker exec devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && bench start"` |
| Seed missing | `bench --site ugavi.localhost execute ugavi.scripts.seed_demo.run` |
| OTP not received | http://localhost:8025 (Mailpit) |
| Port unreachable | VS Code: ensure port 8000 forwarded |