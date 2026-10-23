"""Evaluation Session Minutes controller.

Records the formal evaluation committee session, bids reviewed,
aggregated scores, and award recommendation.
"""

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import now_datetime

from ugavi.tendering.doctype.bid_evaluation_summary.bid_evaluation_summary import (
    generate_bid_summary,
    bid_summary_to_html,
)


class EvaluationMinutes(Document):
    """Formal evaluation committee session minutes."""

    def validate(self):
        self._validate_quorum()
        self._generate_comparative_matrix()

    def _validate_quorum(self):
        expected = {row.user for row in self.attendees if row.present}
        if len(expected) < 3:
            frappe.throw(_("At least 3 committee members must be present."))
        if self.chairperson not in expected:
            frappe.throw(_("Chairperson must be present."))
        if self.secretary not in expected:
            frappe.throw(_("Secretary must be present."))

    def _generate_comparative_matrix(self):
        try:
            summary = generate_bid_summary(self.tender)
            if summary["total_bids"] == 0:
                self.comparative_matrix = (
                    "<p>No bids available for comparison.</p>"
                )
                return
            self.comparative_matrix = bid_summary_to_html(summary)
        except Exception:
            self.comparative_matrix = (
                "<p>Unable to generate comparative summary.</p>"
            )

    @frappe.whitelist()
    def approve(self):
        if self.status != "Draft":
            frappe.throw(_("Only draft minutes can be approved."))
        if "Tender Committee Chair" not in frappe.get_roles() and \
           "System Manager" not in frappe.get_roles():
            frappe.throw(_("Only the Tender Committee Chair can approve minutes."))
        self.status = "Approved"
        self.approved_by = frappe.session.user
        self.approved_at = now_datetime()
        self.save()
        frappe.msgprint(_("Evaluation minutes approved."))

    @frappe.whitelist()
    def reject(self, reason: str = ""):
        if self.status != "Draft":
            frappe.throw(_("Only draft minutes can be rejected."))
        self.status = "Rejected"
        self.dissenting_opinions = (
            (self.dissenting_opinions or "")
            + f"\n\nRejection reason: {reason}"
        )
        self.save()
        frappe.msgprint(_("Evaluation minutes rejected. Returned to draft."))