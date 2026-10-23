# Use Case Index — Ugavi 0.1.0

| UC-ID | Use Case | Actor(s) | Phase | Requirements Covered |
|-------|----------|----------|-------|---------------------|
| UC-01 | Create Purchase Requisition | Procurement Officer | Procurement | PR1, PR2, PR3, PR6, PR7 |
| UC-02 | Publish Open Tender | Procurement Officer | Tendering | TN1, TN3, TN4 |
| UC-03 | Publish Restricted Tender | Procurement Officer | Tendering | TN1, TN2, TN3 |
| UC-04 | Submit Bid (Supplier Portal) | Supplier | Tendering | TN5, TN6, TN7 |
| UC-05 | Open Sealed Bids (3-Officer) | Bid Opening Officers | Tendering | TN8, TN9, TN10, TN11, TN12, TN13, TN14 |
| UC-06 | Evaluate Bids & Award | Evaluation Committee | Evaluation | EV1, EV2, EV3, EV4, EV5, EV6, EV7 |
| UC-07 | Approve PR via DoA | Approver | Procurement | PR6, GV1, GV6 |
| UC-08 | Process Waiver | Procurement Officer + Approver | Procurement | PR5, GV1 |
| UC-09 | Issue Purchase Order | Procurement Officer | Procurement | PR8, PR10 |
| UC-10 | Three-Way Match (PO/GRN/Invoice) | Finance Officer | Procurement | PR9 |
| UC-11 | Receive Goods & Post Stock | Logistics Officer | Logistics | LO1, LO2, LO3, LO8 |
| UC-12 | Inter-Donor Stock Transfer | Logistics Officer | Logistics | LO5, LO6 |
| UC-13 | Generate Monthly Stock Report | System / Logistics Officer | Logistics | LO7 |
| UC-14 | Register Asset & Assign Custody | Asset Manager | Assets | AS1, AS2, AS3, AS5 |
| UC-15 | Dispose Asset | Asset Manager + Approver | Assets | AS6 |
| UC-16 | Schedule Asset Verification | System / Asset Manager | Assets | AS4, AS7 |
| UC-17 | Allocate Vehicle & Log Trip | Fleet Manager | Fleet | FL1, FL2, FL3 |
| UC-18 | Record Fuel & Spares | Fleet Manager | Fleet | FL3, FL5 |
| UC-19 | Renew Supplier Prequalification | Supplier + Procurement Officer | Supplier Mgmt | SP1, SP2, SP3, SP4, SP5 |
| UC-20 | Manage Contract Milestones | Contract Manager | Contract Mgmt | CT1, CT2, CT3, CT4 |
| UC-21 | Audit Trail Inspection | Auditor | Governance | GV5, TN11 |
| UC-22 | Backup & Restore | System Administrator | Operations | OP1, OP2, OP5 |
| UC-23 | LOKADO Demo: Complete P2P | All Roles | Demo | ALL (98 requirements, full coverage) |

## Demo Coverage

The canonical LOKADO demo (`make seed`, tour at
`../demo/LOKADO-DEMO-TOUR.md`) covers all use cases with lifecycle-rich Turkana
supply-chain scenarios: 10 requisitions, 18 supplier profiles, six donor stock
books, three transfer outcomes, eight verified assets, and four fully
purchase-backed fleet journeys. See the tour for the actor-by-actor walkthrough.

## Actor-Role Matrix

| Actor | Proc. | Tendering | Logistics | Assets | Fleet | Governance | Portal |
|-------|-------|-----------|-----------|--------|-------|-----------|--------|
| Procurement Officer | ✅ CRUD | ✅ CRUD | ❌ | ❌ | ❌ | ❌ | ❌ |
| Bid Opening Officer (1-3) | ❌ | ✅ Open only | ❌ | ❌ | ❌ | ❌ | ❌ |
| Evaluation Committee | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Logistics Officer | ❌ | ❌ | ✅ CRUD | ❌ | ❌ | ❌ | ❌ |
| Fleet Manager | ❌ | ❌ | ❌ | ❌ | ✅ CRUD | ❌ | ❌ |
| Asset Manager | ❌ | ❌ | ❌ | ✅ CRUD | ❌ | ❌ | ❌ |
| Approver L1/L2 | ✅ Approve | ❌ | ✅ Approve | ✅ Approve | ❌ | ❌ | ❌ |
| Auditor | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Read | ❌ |
| System Admin | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Full | ❌ |
| Supplier | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Bids/PQ