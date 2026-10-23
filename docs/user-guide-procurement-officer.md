# User Guide — Procurement Officer

## Role: Procurement Officer
**Can:** Create/edit PRs, tenders, bids, supplier prequalifications, bid opening records
**Cannot:** Approve PRs/tenders above DoA threshold, delete sealed bids, cross-donor access

---

## Daily Workflows

### 1. Create Purchase Requisition (PR)
1. Navigate to **Procurement > Purchase Requisition**
2. Click **New**
3. Fill: Requisition Title, Donor, Items (item, qty, estimated cost)
4. **Save** → Status: Draft
5. **Submit** → Status: Pending Approval (routed per DoA matrix)

### 2. Create Tender
1. Navigate to **Procurement > Tender**
2. Click **New**
3. Fill: Tender Title, Type (Open/Restricted), Deadline, Opening Date
4. Link to PR (optional)
5. **Save** → Status: Draft
6. **Publish** → Status: Published (visible to suppliers)

### 3. Record Bid Opening
1. Navigate to **Procurement > Bid Opening Record**
2. Select Tender → bids populate automatically
3. **3-of-3** officers present to decrypt (SSS key reconstruction)
4. Record opening date/time, attendees
5. **Save** → All bids decrypted and visible

### 4. Supplier Prequalification
1. Navigate to **Procurement > Supplier Prequalification**
2. Click **New** → select Supplier
3. Review: registration docs, tax compliance, past performance
4. **Approve** or **Reject** with reason
5. Approved suppliers automatically eligible for restricted tenders

---

## Key Rules
- **Donor segregation**: Every document must have a donor. You cannot access another donor's PRs.
- **Bid secrecy**: Never view bids before the official opening date/time. System enforces this cryptographically.
- **DoA limits**: If PR estimated cost > your DoA threshold, system routes to Procurement Manager automatically.
- **Audit trail**: All your actions are logged with hash-chain integrity (tamper-evident).