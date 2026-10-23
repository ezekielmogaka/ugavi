# User Guide — Logistics Officer

## Role: Logistics Officer
**Can:** Manage stock ledger, donor warehouses, inter-donor transfers, monthly stock reports
**Cannot:** Create procurement documents, access sealed bids, change donor allocations

---

## Daily Workflows

### 1. Stock In (Receive Goods)
1. Navigate to **Logistics > Stock Ledger**
2. Click **New**
3. Fill: Item Code, Donor, Warehouse, Incoming Qty
4. **Voucher Type**: Stock Entry / Purchase Receipt
5. **Save** → System auto-computes running balance

### 2. Stock Out (Issue Goods)
1. Navigate to **Logistics > Stock Ledger**
2. Click **New**
3. Fill: Item Code, Donor, Warehouse, Outgoing Qty
4. **Voucher Type**: Issue Note / Transfer Out
5. **Save** → System validates sufficient stock exists for that donor

### 3. Inter-Donor Transfer
1. Navigate to **Logistics > Inter Donor Transfer**
2. Click **New**
3. Select: Source Donor, Target Donor, Items to transfer
4. **Save** → Two Stock Ledger entries created (out from source, in to target)
5. Both source and target donor managers must approve (bilateral)

### 4. Monthly Stock Report
1. Navigate to **Logistics > Monthly Stock Report**
2. Click **New**
3. Select: Month, Donor (or all donors for consolidated)
4. **Generate** → Report auto-computes from Stock Ledger
5. Export PDF/Excel via print format

---

## Key Rules
- **Donor segregation**: Stock balances are donor-specific. Item A for Donor X and Item A for Donor Y are tracked separately.
- **No negative stock**: System prevents issuing more than available (per donor).
- **Transfer audit**: Every inter-donor transfer is logged in both donors' ledgers and hash-chained.
- **Monthly reconciliation**: Stock Report must balance to zero variance; discrepancies flagged to Logistics Manager.