# Ugavi Requirements

> Requirements inventory: the original client procurement/logistics/assets/fleet
> scope plus derived governance, finance, operations and upgrade controls.
> The [demo coverage map](../demo/LOKADO-DEMO-TOUR.md#4-requirement-to-scene-map)
> distinguishes the original ask, crucial additions and verification limits.

## Versions
- **Frappe:** 16.53.0 (verified 2026-10-23)
- **ERPNext:** 16.52.1 (verified 2026-10-23)
- **Ugavi:** 0.1.0 (main)

---

## 1. Procurement
1. **PR1** – Purchase Requisition with auto-determined procurement method based on value thresholds
2. **PR2** – Configurable thresholds with effective dates and audit history: Direct < 200K, Restricted 200K–499K, Open ≥ 500K KES
3. **PR3** – Donor-specific procurement rules engine
4. **PR4** – Category-specific procurement rules
5. **PR5** – Threshold bypass only via approved, logged waiver
6. **PR6** – Delegation of Authority (DoA) matrix: amount × department × donor
7. **PR7** – Budget check before PR submission
8. **PR8** – Purchase Order with donor/project dimensions
9. **PR9** – Three-way match (PO ↔ GRN ↔ Invoice) with tolerances
10. **PR10** – Budget commitment (encumbrance) at PO creation

## 2. Tendering
11. **TN1** – Tender lifecycle: Draft → Published → Bids Received → Under Evaluation → Awarded → Closed
12. **TN2** – Restricted tender: prequalified suppliers only
13. **TN3** – Tender publication, deadline enforcement on server clock
14. **TN4** – Addenda support with optional deadline extension
15. **TN5** – Supplier portal bid submission with submission receipts
16. **TN6** – Late-bid rejection (server-time enforced)
17. **TN7** – Sealed-bid encryption using RSA-4096 + AES-256-GCM envelope
18. **TN8** – Shamir's Secret Sharing (3-of-3) for private key splitting
19. **TN9** – Three distinct bid-opening officers with conflict-of-interest check
20. **TN10** – OTP verification: 6-digit, 5-min expiry, 3-attempt limit, rate-limited
21. **TN11** – Immutable audit log: who, when, IP, outcome
22. **TN12** – One or two users CANNOT decrypt bids
23. **TN13** – No DB/admin path exposes plaintext before opening
24. **TN14** – Signed Bid Opening Record PDF with hash chain

## 3. Evaluation & Award
25. **EV1** – Evaluation committee with chairperson/secretary/members
26. **EV2** – Weighted scoring (technical + financial)
27. **EV3** – Conflict-of-interest declarations
28. **EV4** – Comparative bid summary
29. **EV5** – Award recommendation → approval workflow
30. **EV6** – Standstill period before contract
31. **EV7** – Auto-create PO from award

## 4. Supplier Management
32. **SP1** – Supplier prequalification by category with expiry
33. **SP2** – Document verification (registration, tax, references)
34. **SP3** – Automatic suspension on expiry
35. **SP4** – Supplier performance scorecard auto-triggered after final receipt
36. **SP5** – Cumulative rating feeding prequal renewal and suspension (< 60 = suspension)
37. **SP6** – Supplier portal: registration, document renewal, bid submission, PO acknowledgement, invoices

## 5. Contract Management
38. **CT1** – Contract milestones and variation orders
39. **CT2** – Retention and bonds tracking
40. **CT3** – Expiry alerts
41. **CT4** – Document repository

## 6. Logistics & Stock
42. **LO1** – Donor-segregated warehouses
43. **LO2** – No cross-donor stock consumption without approved transfer
44. **LO3** – Batch/expiry tracking
45. **LO4** – Reorder levels
46. **LO5** – Stock reconciliation
47. **LO6** – Inter-donor transfer approval workflow
48. **LO7** – Scheduled monthly stock report (email, PDF, Excel)
49. **LO8** – Donor-specific stock ledgers

## 7. Assets
50. **AS1** – Asset categories and depreciation
51. **AS2** – QR tagging
52. **AS3** – Custody and movement tracking
53. **AS4** – Maintenance schedules
54. **AS5** – Donor-funded flag
55. **AS6** – Asset disposal with approval workflow
56. **AS7** – Asset verification

## 8. Fleet
57. **FL1** – Vehicle and driver records
58. **FL2** – Vehicle allocation
59. **FL3** – Fuel and spares linked to originating purchase documents
60. **FL4** – Expiry alerts (insurance, license)
61. **FL5** – Cost-per-km analytics
62. **FL6** – Monthly fleet reports

## 9. Governance & Security
63. **GV1** – Segregation of duties (requester ≠ approver ≠ payer)
64. **GV2** – Least-privilege role matrix
65. **GV3** – User Permissions for donor/warehouse isolation
66. **GV4** – Field-level permissions for sensitive fields
67. **GV5** – Tamper-evident hash chain for critical documents
68. **GV6** – Approval delegation
69. **GV7** – E-signature on approvals
70. **GV8** – 2FA for approvers
71. **GV9** – Session/password policy
72. **GV10** – Rate limiting
73. **GV11** – SSO scaffolding
74. **GV12** – IDOR protection (portal documents)

## 10. Finance & Kenya Localization
75. **FI1** – Company with KES currency and multi-currency
76. **FI2** – Chart of accounts, fiscal year
77. **FI3** – Accounting dimensions: Donor, Grant, Project
78. **FI4** – Tax templates: VAT, withholding tax
79. **FI5** – KRA PIN validation
80. **FI6** – eTIMS integration hooks (adapter pattern)
81. **FI7** – SMS provider abstraction

## 11. Notifications & Reports
82. **NT1** – Email notifications (Mailpit local)
83. **NT2** – SMS notifications via provider interface
84. **NT3** – Notification rules for expiry, approval, rejection
85. **NT4** – Procurement dashboard (cycle time, spend, tender status)
86. **NT5** – Stock turnover and expiry risk dashboard
87. **NT6** – Fleet cost dashboard
88. **NT7** – Asset utilization charts

## 12. Operations
89. **OP1** – Backups (scheduled, with files)
90. **OP2** – Scheduler and background workers
91. **OP3** – Error/health endpoints
92. **OP4** – idempotent background jobs
93. **OP5** – Dry-run migration support

## 13. Upgradeability
94. **UG1** – Zero core ERPNext patches (target)
95. **UG2** – Hooks-only ERPNext overrides
96. **UG3** – UI customizations in ugavi assets only
97. **UG4** – SBOM and dependency scan
98. **UG5** – Minor and major upgrade dry-run passing

---

## 14. Non-Functional Requirements

### 14.1 Performance
99. **NF1** – PR/Tender list loads: <2s for 1000 records
100. **NF2** – Sealed-bid opening: <5s for 3-key reconstruction
101. **NF3** – Bid submission: <3s for 1MB encrypted payload
102. **NF4** – Concurrent bidders: 50 simultaneous bid submissions without error

### 14.2 Security
103. **NF5** – OWASP ASVS Level 2 compliance (see `docs/security/owasp-asvs-mapping.md`)
104. **NF6** – All communications over TLS 1.3
105. **NF7** – Secrets never in logs, commits, backups — verified by detect-secrets CI
106. **NF8** – Private keys split via 3-of-3 SSS; never stored whole
107. **NF9** – Container images scanned for CRITICAL/HIGH CVEs (Trivy in CI)
108. **NF10** – Rate limiting: 3 bid attempts per hour per supplier

### 14.3 Availability
109. **NF11** – Health check endpoint returning 200 with db + cache status
110. **NF12** – Automated daily backups (with files, retention 90 days)
111. **NF13** – RPO: <1 hour | RTO: <4 hours (from backup restore)

### 14.4 Maintainability
112. **NF14** – Test coverage: all new features require at minimum FrappeTestCase
113. **NF15** – Zero ERPNext core patches (hooks-only customization)
114. **NF16** – SBOM generated on every PR (SPDX JSON, Anchore Syft)
115. **NF17** – Upgrade dry-run CI job validates bench migrate without errors

### 14.5 Compliance & Audit
116. **NF18** – Immutable hash chain on all critical documents (Tender, Bid, BOR, Contract)
117. **NF19** – Segregation of duties enforced at controller level (not UI-only)
118. **NF20** – Full audit trail: who, when, IP, action, outcome on every state change

### 14.6 Demo-Specific (LOKADO)
119. **NFD1** – Seed script idempotent (safe to re-run, `_ensure` upsert pattern)
120. **NFD2** – Seed script production-guarded (refuses non-demo environments)
121. **NFD3** – LOKADO demo maps all functional requirements to scenes and distinguishes verified controls, live actions and externally dependent acceptance criteria (coverage target, not blanket certification)
122. **NFD4** – All demo users have realistic Turkana/Kenyan names and roles