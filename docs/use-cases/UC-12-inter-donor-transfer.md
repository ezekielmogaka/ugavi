# UC-12: Inter-Donor Stock Transfer

**ID:** UC-12 | **Actor(s):** Logistics Officer, Approver L2 | **Phase:** Logistics
**Requirements:** LO2, LO5, LO6, LO8

## Goal
Transfer stock from one donor's warehouse to another with full approval, atomic ledger update, and integrity verification.

## Preconditions
- Source donor has sufficient stock of the item
- Transfer approved by Approver L2 (no self-approval)
- Both donors have Donor Warehouse records
- Stock Ledger entries for source donor verified (hash chain)

## Main Flow
1. Logistics Officer creates Inter-Donor Transfer (IDT) — selects source donor, target donor, items
2. System validates: source donor has >= quantity in stock, no cross-donor consumption without transfer
3. IDT submitted for approval → Approver L2
4. Approver L2 reviews and approves (or rejects with reason)
5. System posts atomic stock movement:
   - Source donor: outgoing (-qty) on Stock Ledger
   - Target donor: incoming (+qty) on Stock Ledger
6. System updates both Donor Warehouse balance records
7. System logs audit event with hash chain append

## Business Rules
- **LO2-R1:** Stock from Donor A CANNOT be consumed by Donor B without an approved IDT
- **LO6-R1:** IDT requires L2 approval; requester ≠ approver
- **LO8-R1:** Each donor has independent stock ledger (donor field as dimension)

## Data Touched
- Inter-Donor Transfer, Stock Ledger (2 entries), Donor Warehouse (2), Audit Log

## Linked Tests
- `test_transactional_boundary.py` — transfer atomicity
- `test_tenant_isolation.py` — donor segregation
- `test_concurrency.py` — stock ledger thread safety