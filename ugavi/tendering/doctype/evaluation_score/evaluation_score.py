"""Individual Evaluator Scoring Sheet (EV2, GA-008).

Each committee member scores every bid on configurable criteria.
Anonymized mode hides bidder identity from the evaluator.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class EvaluationScore(Document):
    """Per-evaluator, per-bid scoring sheet."""

    def validate(self):
        self._validate_committee_membership()
        self._calculate_scores()

    def before_save(self):
        if self.status == "Submitted" and not self.submitted_at:
            self.submitted_by = frappe.session.user
            self.submitted_at = now_datetime()

    def on_trash(self):
        if self.status != "Draft":
            frappe.throw(_("Submitted evaluation scores are part of the audit trail and cannot be deleted."))

    def before_insert(self):
        if self.evaluator != frappe.session.user and "System Manager" not in frappe.get_roles():
            frappe.throw(_("Evaluators may only record their own scores."))
        self._validate_one_per_evaluator_per_bid()
        self._validate_anonymized()

    def _validate_committee_membership(self):
        tender = frappe.get_doc("Tender", self.tender)
        members = {
            row.user for row in tender.evaluation_committee
        }
        if self.evaluator not in members:
            frappe.throw(
                _("Evaluator {0} is not a member of the evaluation committee.").format(
                    self.evaluator
                )
            )

    def _validate_one_per_evaluator_per_bid(self):
        if frappe.db.exists(
            "Evaluation Score",
            {
                "tender": self.tender,
                "evaluator": self.evaluator,
                "bid": self.bid,
                "name": ("!=", self.name),
            },
        ):
            frappe.throw(
                _("Evaluator {0} has already scored bid {1}.").format(
                    self.evaluator, self.bid
                )
            )

    def _validate_anonymized(self):
        if self.anonymized and not self.is_new():
            bid = frappe.get_cached_doc("Bid", self.bid)
            if bid.supplier:
                frappe.throw(
                    _("Anonymized scoring — bidder identity must not be disclosed.")
                )

    def _calculate_scores(self):
        """Aggregate scores by category with weights."""
        cat_scores = {"Technical": 0.0, "Financial": 0.0,
                       "Delivery": 0.0, "Past Performance": 0.0}
        cat_weights = {"Technical": 0.0, "Financial": 0.0,
                        "Delivery": 0.0, "Past Performance": 0.0}
        total_weight = 0.0

        for item in self.criteria:
            if item.max_score <= 0:
                frappe.throw(_("Max score must be positive for '{0}'").format(
                    item.criterion_name))
            if item.score < 0 or item.score > item.max_score:
                frappe.throw(
                    _("Score for '{0}' must be between 0 and {1}").format(
                        item.criterion_name, item.max_score
                    )
                )
            percent = (item.score / item.max_score) * 100
            item.weighted_score = round(percent * float(item.weight or 0) / 100, 2)
            cat_scores[item.category] += percent * float(item.weight or 0)
            cat_weights[item.category] += float(item.weight or 0)
            total_weight += float(item.weight or 0)

        if abs(total_weight - 100) > 0.01:
            frappe.throw(_("Total weight must equal 100%. Current: {0}%").format(
                total_weight))

        self.technical_score = round(
            cat_scores["Technical"] / cat_weights["Technical"], 2
        ) if cat_weights["Technical"] else 0.0
        self.financial_score = round(
            cat_scores["Financial"] / cat_weights["Financial"], 2
        ) if cat_weights["Financial"] else 0.0
        self.delivery_score = round(
            cat_scores["Delivery"] / cat_weights["Delivery"], 2
        ) if cat_weights["Delivery"] else 0.0
        self.past_performance_score = round(
            cat_scores["Past Performance"] / cat_weights["Past Performance"], 2
        ) if cat_weights["Past Performance"] else 0.0
        self.weighted_total = round(
            self.technical_score * 0.4
            + self.financial_score * 0.4
            + self.delivery_score * 0.1
            + self.past_performance_score * 0.1,
            2,
        )

    @frappe.whitelist()
    def submit_score(self):
        if self.status != "Draft":
            frappe.throw(_("Only draft scores can be submitted."))
        self.status = "Submitted"
        self.submitted_by = frappe.session.user
        self.submitted_at = now_datetime()
        self.save()
        frappe.msgprint(_("Evaluation score submitted."))

    @frappe.whitelist()
    def review_score(self):
        if self.status != "Submitted":
            frappe.throw(_("Only submitted scores can be reviewed."))
        self.status = "Reviewed"
        self.save()
        frappe.msgprint(_("Evaluation score reviewed."))