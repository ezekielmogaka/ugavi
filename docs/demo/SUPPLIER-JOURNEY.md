# Supplier Journey Demo Guide

This guide follows the supplier experience while preserving ERPNext as the
system of record for suppliers, orders, receipts and invoices. It identifies
prepared evidence and current limitations; it is not a claim that every portal
action is live-ready. Use the [functional tour](./LOKADO-DEMO-TOUR.md) for
the actors, seeded record IDs, communications and requirement coverage.

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
| Opportunities | Review open tenders | `Tender` | Deadline filtering; restricted tenders require current category prequalification. A disabled Supplier was able to bid on an open tender in a rollback-only probe. |
| Bid submission | Enter amount, currency, delivery days, and private proposal | `Bid` | Server deadline, duplicate, currency, identity, and eligibility checks; sealed-bid encryption and receipt |
| Clarifications | Ask a question before close | `Clarification` | Question is supplier-bound. The current Desk answer path leaves responder/time blank, so a fully audited answer is not demonstrated. |
| Complaints | Challenge an outcome during active standstill | `Tender Complaint` | Bidder identity, standstill deadline, private-file ownership, duplicate-open-complaint prevention |
| Awards | Review awards issued to the supplier | `Tender` | Only tenders whose `awarded_supplier` matches the linked Supplier are exposed |
| Contracts | Review contract, value, dates, and linked order | `Ugavi Contract` | Supplier-scoped contract visibility; ERPNext Purchase Order remains the commercial commitment |
| Deliveries | Acknowledge orders and follow receipt progress | ERPNext `Purchase Order` and `Purchase Receipt` | Ownership check before acknowledgement; receipt percentage comes from ERPNext |
| Invoices | Intended: submit a private invoice against an accepted receipt | ERPNext `Purchase Invoice` | **Currently blocked:** the seeded website user fails the native receipt mapper's invoice-create permission check. Show a prepared invoice instead. |
| Evaluations | Review post-receipt performance | `Ugavi Supplier Evaluation` | Evaluation is linked to the completed Purchase Receipt and cumulative supplier rating |
| Notifications | Read submission receipts, answers, awards, and acknowledgements | Frappe `Notification Log` | Notifications are addressed to the authenticated portal user and cannot be marked by another user; they are not automatically email. |

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
2. Choose a missing item category and a future requested expiry date. On the
   inspected fresh seed, Lodwar General already has valid WASH Supplies
   prequalification; Shelter & NFI is a separate example if still absent.
3. Optionally select a document type and upload a file.
4. Select **Apply**.
5. Show the `Under Review` application and the resulting portal notification.

The upload is private. The server verifies that the File belongs to the current website user before attaching it.
The current Desk review/renew buttons are not a reliable live path; compare a
seeded **Prequalified** category and expiry without forcing a status change.
Do not claim a disabled supplier is blocked from open-tender bidding: the
current flow accepted one in a rollback-only check.

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
3. In Desk, open the **Open** Clarification. The current Answer field is
   hidden until Status is set to **Answered**; saving through that UI path
   leaves `answered_by` and `answered_date` blank. Stop at the submitted
   question rather than claim a fully audited answer.
4. Return to the portal and show the submitted question and any actual
   notification. The inspected fresh seed has no prepared answer.

### 5. Award and contract

1. In Desk, inspect the opened Livestock bids, committee declarations, scores,
   chair-approved minutes and recommendation in
   [Scene 12](./LOKADO-DEMO-TOUR.md#scene-12-evaluation-and-award-decision).
2. Start the real standstill, then stop: a fresh 14-day period cannot be
   confirmed or awarded in the same-day demo. Open complaints also block
   confirmation. Do not edit the date or status to bypass these gates.
3. After a genuinely ended and confirmed standstill, the supported award
   action can create the ERPNext Purchase Order and Ugavi Contract and link
   them to the tender. This later action is not shown merely by starting
   standstill.
4. For a prepared contract, sign in as `turkana-construction@outlook.com`
   and follow its receipt-backed PO under **Contracts** and **Deliveries**.
   This is a separate logistics branch, not an awarded warehouse tender.
   **Awards** may legitimately be empty.

### 6. Standstill complaint

1. Ensure the supplier has a bid on a tender with an active Standstill Period.
2. Select **Complaints**.
3. Enter the grounds and optionally upload a private supporting document.
4. Submit the complaint and show the receipt notification.
5. As Procurement Officer, review it in `/app/tender-complaint`, assign three
   distinct non-conflicted panel members and an eligible reviewer, then record
   the supported outcome. Upheld or partially upheld complaints require
   remedial action.
6. Return as the supplier and show the resolution and notification.

This demonstrates the configured panel-based workflow, not acceptance of
every statutory-policy or production notification requirement.

### 7. Delivery and evaluation

1. In **Orders and deliveries**, find the supplier's prepared PO and select
   **Acknowledge** only if it is not already acknowledged.
2. Show the linked submitted Purchase Receipt and ERPNext's received percentage.
   For a new receipt, the storekeeper must choose a submitted PO with outstanding
   quantities; do not receive a fully fulfilled PO twice.
3. The supplier invoice form is present, but a rollback-only runtime probe as
   `lodwar-supplies@outlook.com` against the unbilled IOM fleet receipt failed
   at ERPNext's mapper with a Purchase Invoice create-permission error. Do not
   grant broad Desk permissions as a shortcut. Show a prepared invoice instead.
4. The intended portal flow creates a **draft** invoice for finance review.
   A `Three Way Match` is generated when the invoice is **submitted**, not
   when that draft is created.
5. Open a prepared **Completed** `Ugavi Supplier Evaluation` linked to the
   receipt and show its score and remarks in the supplier portal. The current
   Desk form has no dedicated completion button; Save alone is not completion.

Portal notifications are in-app records. For the optional standstill email,
verify the local relay and recipient as described in the
[communication preflight](./LOKADO-DEMO-TOUR.md#14-communication-and-message-evidence);
Mailpit capture does not prove external delivery.

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

- [Supplier documentation](https://docs.frappe.io/erpnext/supplier) and [v16.53.0 Supplier schema](https://github.com/frappe/erpnext/blob/v16.53.0/erpnext/buying/doctype/supplier/supplier.json)
- [Purchase Order documentation](https://docs.frappe.io/erpnext/purchase-order) and [v16.53.0 Purchase Order controller](https://github.com/frappe/erpnext/blob/v16.53.0/erpnext/buying/doctype/purchase_order/purchase_order.py)
- [Purchase Receipt documentation](https://docs.frappe.io/erpnext/purchase-receipt) and [v16.53.0 Purchase Receipt controller](https://github.com/frappe/erpnext/blob/v16.53.0/erpnext/stock/doctype/purchase_receipt/purchase_receipt.py)
- [Frappe Notification Log schema](https://github.com/frappe/frappe/blob/version-16/frappe/desk/doctype/notification_log/notification_log.json)

Ugavi-specific prequalification, sealed tendering, clarification, contract controls, and supplier evaluation remain additive app-owned DocTypes. No ERPNext controller is replaced.
