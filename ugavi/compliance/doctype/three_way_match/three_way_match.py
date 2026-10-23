import frappe
from frappe import _
from frappe.model.document import Document


class ThreeWayMatch(Document):
    """Match ERPNext purchase source rows rather than document-level totals."""

    def validate(self):
        self._perform_match()

    def _perform_match(self):
        po = frappe.get_doc("Purchase Order", self.purchase_order)
        pr = frappe.get_doc("Purchase Receipt", self.purchase_receipt)
        pi = frappe.get_doc("Purchase Invoice", self.purchase_invoice)
        self._validate_sources(po, pr, pi)

        receipt_rows = {}
        for item in pr.items:
            if item.purchase_order == po.name and item.purchase_order_item:
                receipt_rows.setdefault(item.purchase_order_item, []).append(item)

        invoice_rows = {}
        for item in pi.items:
            if item.purchase_order == po.name and item.po_detail:
                invoice_rows.setdefault(item.po_detail, []).append(item)

        self.set("items", [])
        max_quantity_variance = 0.0
        max_price_variance = 0.0
        tolerance = float(self.tolerance_percent or 0)
        overall_status = "Matched"

        for po_item in po.items:
            receipts = receipt_rows.get(po_item.name, [])
            invoices = invoice_rows.get(po_item.name, [])
            if not receipts and not invoices:
                continue

            received_qty = sum(
                float(row.qty or 0) - float(row.rejected_qty or 0)
                for row in receipts
            )
            invoiced_qty = sum(float(row.qty or 0) for row in invoices)
            invoice_amount = sum(
                float(row.qty or 0) * float(row.base_rate or row.rate or 0)
                for row in invoices
            )
            invoice_rate = invoice_amount / invoiced_qty if invoiced_qty else 0
            po_rate = float(po_item.base_rate or po_item.rate or 0)
            denominator = float(po_item.qty or 0) or 1
            quantity_variance = abs(received_qty - invoiced_qty) / denominator * 100
            price_variance = (
                abs(po_rate - invoice_rate) / po_rate * 100 if po_rate else 0
            )

            line_status = "Matched"
            if quantity_variance or price_variance:
                line_status = (
                    "Within Tolerance"
                    if quantity_variance <= tolerance and price_variance <= tolerance
                    else "Disputed"
                )
            if line_status == "Disputed":
                overall_status = "Disputed"
            elif line_status == "Within Tolerance" and overall_status == "Matched":
                overall_status = "Within Tolerance"

            max_quantity_variance = max(max_quantity_variance, quantity_variance)
            max_price_variance = max(max_price_variance, price_variance)
            self.append(
                "items",
                {
                    "purchase_order_item": po_item.name,
                    "item_code": po_item.item_code,
                    "ordered_qty": po_item.qty,
                    "received_qty": received_qty,
                    "invoiced_qty": invoiced_qty,
                    "purchase_order_rate": po_rate,
                    "invoice_rate": invoice_rate,
                    "quantity_variance": round(quantity_variance, 2),
                    "price_variance": round(price_variance, 2),
                    "match_status": line_status,
                },
            )

        if not self.items:
            frappe.throw(
                _("The selected receipt and invoice have no rows from purchase order {0}.").format(
                    po.name
                )
            )
        self.quantity_variance = round(max_quantity_variance, 2)
        self.price_variance = round(max_price_variance, 2)
        self.match_status = overall_status

    @staticmethod
    def _validate_sources(po, pr, pi):
        if po.docstatus != 1 or pr.docstatus != 1 or pi.docstatus != 1:
            frappe.throw(_("Purchase order, receipt, and invoice must be submitted."))
        if len({po.supplier, pr.supplier, pi.supplier}) != 1:
            frappe.throw(_("Purchase order, receipt, and invoice suppliers must match."))


def create_for_purchase_invoice(doc, method=None):
    """Create one idempotent match per PO/receipt pair in a submitted invoice."""
    source_pairs = {
        (item.purchase_order, item.purchase_receipt)
        for item in doc.items
        if item.purchase_order and item.purchase_receipt
    }
    for purchase_order, purchase_receipt in source_pairs:
        filters = {
            "purchase_order": purchase_order,
            "purchase_receipt": purchase_receipt,
            "purchase_invoice": doc.name,
        }
        if frappe.db.exists("Three Way Match", filters):
            continue
        match = frappe.get_doc({"doctype": "Three Way Match", **filters})
        match.insert(ignore_permissions=True)
        if match.match_status == "Disputed":
            finance_user = frappe.db.get_value(
                "Has Role",
                {"role": "Finance Officer", "parenttype": "User"},
                "parent",
            )
            frappe.get_doc(
                {
                    "doctype": "ToDo",
                    "allocated_to": finance_user or "Administrator",
                    "description": _(
                        "Review three-way match {0} for invoice {1}."
                    ).format(match.name, doc.name),
                    "reference_type": "Three Way Match",
                    "reference_name": match.name,
                }
            ).insert(ignore_permissions=True)