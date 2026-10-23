# Supplier Journey Demo Guide

This guide demonstrates the complete supplier experience while preserving ERPNext as the system of record for supplier, order, receipt, and notification data.

## Start the demo

```bash
make setup
make seed                # canonical LOKADO seed (alias: seed-lokado)
make demo-check
make fleet-check
```

For mounted-source development use `make dev-config`, `make dev-seed` and
`make dev-check` after `make dev-up`. See the [Make reference](../../README.md#makefile-reference).
Use separate browser profiles for supplier and staff sessions.

Open `http://localhost:8080/login` and sign in with:

- **Email:** `lodwar-supplies@outlook.com`
- **Password:** `Ugavi@2024`

The supported Frappe website-home hook redirects this linked website user to `/supplier/dashboard`.

## Journey map

| Stage | Supplier action | System record | Control demonstrated |
|---|---|---|---|
| Profile | Maintain contact, website, and tax details | ERPNext `Supplier` | Only the linked Supplier can be changed; commercial/admin fields remain Desk-controlled |
| Prequalification | Select category, expiry, and upload a private supporting document | `Supplier Prequalification` and child documents | Category validation, duplicate prevention, private-file ownership, procurement review |
| Opportunities | Review eligible open tenders | `Tender` | Deadline filtering; restricted tenders require active category prequalification |
| Bid submission | Enter amount, currency, delivery days, and private proposal | `Bid` | Server deadline, duplicate, currency, identity, and eligibility checks; sealed-bid encryption and receipt |
| Clarifications | Ask a question before close | `Clarification` | Question is supplier-bound and safely escaped; answers are recorded by procurement |
| Complaints | Challenge an outcome during active standstill | `Tender Complaint` | Bidder identity, standstill deadline, private-file ownership, duplicate-open-complaint prevention |
| Awards | Review awards issued to the supplier | `Tender` | Only tenders whose `awarded_supplier` matches the linked Supplier are exposed |
| Contracts | Review contract, value, dates, and linked order | `Ugavi Contract` | Supplier-scoped contract visibility; ERPNext Purchase Order remains the commercial commitment |
| Deliveries | Acknowledge orders and follow receipt progress | ERPNext `Purchase Order` and `Purchase Receipt` | Ownership check before acknowledgement; receipt percentage comes from ERPNext |
| Invoices | Submit a private supplier invoice against an accepted receipt | ERPNext `Purchase Invoice` | Supplier and receipt ownership are verified; commercial lines come from ERPNext's receipt mapper |
| Evaluations | Review post-receipt performance | `Ugavi Supplier Evaluation` | Evaluation is linked to the completed Purchase Receipt and cumulative supplier rating |
| Notifications | Read submission receipts, answers, awards, and acknowledgements | Frappe `Notification Log` | Notifications are addressed to the authenticated portal user and cannot be marked by another user |

The portal also shows a journey-completion indicator and one next-best action.
These values are calculated server-side from the supplier's own records and
rendered by the app-owned Frappe website template.

## Presenter walkthrough

### 1. Profile

1. Select **Profile** in the journey navigation.
2. Change the mobile number or website.
3. Select **Save profile**.
4. Explain that the portal exposes a narrow allowlist: email, mobile, website, and tax ID. Supplier group, type, payment defaults, and accounting controls stay in ERPNext Desk.

### 2. Prequalification

1. Select **Prequalification**.
2. Choose an item category and a future requested expiry date.
3. Optionally select a document type and upload a file.
4. Select **Apply**.
5. Show the `Under Review` application and the resulting portal notification.

The upload is private. The server verifies that the File belongs to the current website user before attaching it.

### 3. Opportunities and bids

1. Select **Opportunities**.
2. Point out the procurement method, estimated value, category, and deadline.
   Use a still-open tender, not the closed solar-pump opening fixture. If this
   supplier already bid on that opportunity, use another eligible supplier or
   a new draft tender; duplicate submissions are intentionally rejected.
3. Select **Prepare bid** on an opportunity.
4. Enter the bid amount, ISO currency code, delivery days, and an optional technical proposal.
5. Select **Encrypt and submit bid**.
6. Show the immutable receipt in the bid history and the notification feed.

`Published` and `Bids Received` are both accepting states. This is important because the first submitted bid moves the tender to `Bids Received`; later eligible suppliers must still be able to submit before the deadline.

### 4. Clarifications

1. Select **Clarifications**.
2. Choose an open tender, enter a question, and select **Send question**.
3. In Desk, open **Clarification**, enter an answer, and save.
4. Return to the portal and show the answer and notification.

### 5. Award and contract

1. In Desk, complete bid opening and evaluation.
2. Award the tender to a supplier with an opened/evaluated bid.
3. Return to **Awards** and **Contracts**.
4. Show that award performs one transaction that creates the ERPNext Purchase Order and Ugavi Contract, links both to the tender, updates the winning bid, and emits the supplier notification.

### 6. Standstill complaint

1. Ensure the supplier has a bid on a tender with an active Standstill Period.
2. Select **Complaints**.
3. Enter the grounds and optionally upload a private supporting document.
4. Submit the complaint and show the receipt notification.
5. As Procurement Officer, review it in `/app/tender-complaint`, record the
   outcome, and save.
6. Return as the supplier and show the resolution and notification.

This is the delivered MVP2 W3 readiness slice. It does not claim completion of
the wider complaints review-panel or statutory-policy work.

### 7. Delivery and evaluation

1. In **Orders and deliveries**, select **Acknowledge**.
2. As the storekeeper, create a Purchase Receipt from the submitted Purchase Order.
3. Return to the portal and show ERPNext's received percentage and receipt record.
4. In **Supplier invoices**, select the submitted receipt, provide the supplier
   invoice reference/date, upload a private PDF, and submit.
5. As Finance Officer, review the draft ERPNext Purchase Invoice and the
   line-level `Three Way Match`.
6. Complete the `Ugavi Supplier Evaluation` for the final receipt.
7. Return to **Supplier evaluations** and show the score and remarks.

## Security boundaries

- Every write command resolves the Supplier from the authenticated Contact or User Permission; no supplier name is accepted from the browser.
- Portal methods use explicit parameters, not arbitrary keyword dictionaries.
- General create/write permission is not granted merely to make the portal work.
- `ignore_permissions=True` is limited to identity-bound service commands after server validation.
- Files must be private and owned by the current portal user.
- Submitted bids are immutable and encrypted for sealed tender methods.
- Queries for bids, clarifications, awards, contracts, orders, receipts, and evaluations all include the resolved Supplier.
- Notification updates require `for_user == frappe.session.user`.
- Complaint intake requires an existing bid and active, unexpired standstill
  window; the browser cannot supply another Supplier identity.

## ERPNext upstream references

Ugavi reuses rather than duplicates these upstream records:

- [Supplier documentation](https://docs.frappe.io/erpnext/supplier) and [v16.52.1 Supplier schema](https://github.com/frappe/erpnext/blob/v16.52.1/erpnext/buying/doctype/supplier/supplier.json)
- [Purchase Order documentation](https://docs.frappe.io/erpnext/purchase-order) and [v16.52.1 Purchase Order controller](https://github.com/frappe/erpnext/blob/v16.52.1/erpnext/buying/doctype/purchase_order/purchase_order.py)
- [Purchase Receipt documentation](https://docs.frappe.io/erpnext/purchase-receipt) and [v16.52.1 Purchase Receipt controller](https://github.com/frappe/erpnext/blob/v16.52.1/erpnext/stock/doctype/purchase_receipt/purchase_receipt.py)
- [Frappe Notification Log schema](https://github.com/frappe/frappe/blob/version-16/frappe/desk/doctype/notification_log/notification_log.json)

Ugavi-specific prequalification, sealed tendering, clarification, contract controls, and supplier evaluation remain additive app-owned DocTypes. No ERPNext controller is replaced.
