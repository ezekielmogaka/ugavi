"""Evaluation Session Minutes controller.

Records the formal evaluation committee session, bids reviewed,
aggregated scores, and award recommendation.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from ugavi.tendering.doctype.bid_evaluation_summary.bid_evaluation_summary import (
    bid_summary_to_html,
    generate_bid_summary,
)


class EvaluationMinutes(Document):
    """Formal evaluation committee session minutes."""

    def validate(self):
        previous = self.get_doc_before_save()
        if previous and previous.status == "Approved":
            frappe.throw(_("Approved evaluation minutes cannot be changed."))
        self._validate_quorum()
        self.quorum_met = 1
        if not self.bids_reviewed:
            self._load_bids_from_scores()
        self._generate_comparative_matrix()

    def _load_bids_from_scores(self):
        """Prefill reviewed bids with averages of submitted committee scores."""
        from ugavi.tendering.services.evaluation import SCORED_STATUSES, score_ranking

        for row in score_ranking(self.tender):
            scores = frappe.get_all(
                "Evaluation Score",
                filters={"tender": self.tender, "bid": row["bid"], "status": ("in", SCORED_STATUSES)},
                fields=["technical_score", "financial_score"],
            )
            count = len(scores) or 1
            self.append("bids_reviewed", {
                "bid": row["bid"],
                "supplier": row["supplier"],
                "bid_amount": row["bid_amount"],
                "technical_avg": round(sum(s.technical_score or 0 for s in scores) / count, 2),
                "financial_avg": round(sum(s.financial_score or 0 for s in scores) / count, 2),
                "total_avg": row["average"],
                "responsive": 1,
            })

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