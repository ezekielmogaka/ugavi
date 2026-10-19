import frappe
from frappe.model.document import Document
from frappe import _


class SupplierScorecard(Document):
    """Score suppliers per delivery. Cumulative rating < 60% triggers suspension."""

    def validate(self):
        weights = {
            "quality_score": 0.30,
            "delivery_score": 0.25,
            "compliance_score": 0.25,
            "price_competitiveness": 0.20,
        }
        total = 0
        for field, weight in weights.items():
            val = self.get(field) or 0
            total += val * weight * 10  # rating is 0-10, converted to %
        self.total_score = round(total, 1)
        self._compute_cumulative_rating()

    def _compute_cumulative_rating(self):
        """Average of last 12 months of scorecards for this supplier."""
        scores = frappe.get_all(
            "Supplier Scorecard",
            filters={"supplier": self.supplier, "name": ("!=", self.name)},
            fields=["total_score"],
            order_by="evaluation_date desc",
            limit=11,
        )
        all_scores = [self.total_score] + [s.total_score for s in scores]
        self.cumulative_rating = round(sum(all_scores) / len(all_scores), 1)

    def on_update(self):
        if self.cumulative_rating < 60:
            frappe.db.set_value("Supplier", self.supplier, "disabled", 1)
            frappe.msgprint(
                _("Supplier {0} suspended — cumulative rating below 60%").format(self.supplier)
            )