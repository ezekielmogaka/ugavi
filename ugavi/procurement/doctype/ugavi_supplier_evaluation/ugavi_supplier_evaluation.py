import frappe
from frappe.model.document import Document
from frappe import _


class UgaviSupplierEvaluation(Document):
    """Score suppliers per delivery. Cumulative rating < 60% triggers suspension."""

    def validate(self):
        if bool(self.purchase_receipt) == bool(self.purchase_invoice):
            frappe.throw(
                _("Link exactly one Purchase Receipt or direct Purchase Invoice")
            )
        weights = {
            "quality_score": 0.30,
            "delivery_score": 0.25,
            "compliance_score": 0.25,
            "price_competitiveness": 0.20,
        }
        total = 0
        for field, weight in weights.items():
            val = self.get(field) or 0
            if not 0 <= val <= 10:
                frappe.throw(_("{0} must be between 0 and 10").format(self.meta.get_label(field)))
            total += val * weight * 10  # rating is 0-10, converted to %
        self.total_score = round(total, 1)
        self._compute_cumulative_rating()

    def _compute_cumulative_rating(self):
        """Average of last 12 months of scorecards for this supplier."""
        scores = frappe.get_all(
            "Ugavi Supplier Evaluation",
            filters={"supplier": self.supplier, "status": "Completed", "name": ("!=", self.name)},
            fields=["total_score"],
            order_by="evaluation_date desc",
            limit=11,
        )
        all_scores = [self.total_score] + [s.total_score for s in scores]
        self.cumulative_rating = round(sum(all_scores) / len(all_scores), 1)

    def on_update(self):
        if self.status == "Completed" and self.cumulative_rating < 60:
            frappe.db.set_value("Supplier", self.supplier, "disabled", 1)
            frappe.msgprint(
                _("Supplier {0} suspended — cumulative rating below 60%").format(self.supplier)
            )

    @frappe.whitelist()
    def complete_evaluation(self):
        if self.status != "Pending":
            frappe.throw(_("Only pending evaluations can be completed"))
        required = (
            self.quality_score,
            self.delivery_score,
            self.compliance_score,
            self.price_competitiveness,
        )
        if any(score is None for score in required):
            frappe.throw(_("All evaluation scores are required"))
        self.status = "Completed"
        self.save()