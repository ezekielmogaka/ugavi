import frappe
from frappe.model.document import Document
from frappe import _


class ThreeWayMatch(Document):
    """Match PO, GRN, and Invoice quantities and prices."""

    def validate(self):
        self._perform_match()

    def _perform_match(self):
        """Compare PO, GRN, and Invoice quantities & prices."""
        po = frappe.get_doc("Purchase Order", self.purchase_order)
        pr = frappe.get_doc("Purchase Receipt", self.purchase_receipt)
        pi = frappe.get_doc("Purchase Invoice", self.purchase_invoice)

        po_qty = sum(item.qty for item in po.items) if po.items else 0
        pr_qty = sum(item.qty for item in pr.items) if pr.items else 0
        pi_qty = sum(item.qty for item in pi.items) if pi.items else 0

        po_total = po.total or 0
        pr_total = pr.total or 0
        pi_total = pi.total or 0

        if po_qty > 0:
            self.quantity_variance = round(abs(pr_qty - pi_qty) / po_qty * 100, 2)
        else:
            self.quantity_variance = 0

        if po_total > 0:
            self.price_variance = round(abs(pr_total - pi_total) / po_total * 100, 2)
        else:
            self.price_variance = 0

        tolerance = self.tolerance_percent or 5
        if self.quantity_variance <= tolerance and self.price_variance <= tolerance:
            self.match_status = "Within Tolerance"
        elif self.quantity_variance == 0 and self.price_variance == 0:
            self.match_status = "Matched"
        else:
            self.match_status = "Disputed"