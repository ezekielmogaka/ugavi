"""Supplier complaint submitted during an active tender standstill period."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, get_datetime, now_datetime

from ugavi.procurement.portal.supplier_portal import notify_supplier_users


RESOLVED_STATUSES = {"Upheld", "Partially Upheld", "Rejected"}
OPEN_STATUSES = {"Submitted", "Under Review"}
ALLOWED_TRANSITIONS = {
    "Submitted": {"Under Review", "Withdrawn"},
    "Under Review": RESOLVED_STATUSES,
    "Upheld": set(),
    "Partially Upheld": set(),
    "Rejected": set(),
    "Withdrawn": set(),
}


class TenderComplaint(Document):
    def validate(self):
        if self.is_new():
            self._validate_submission_window()
        self._validate_status_transition()
        self._validate_review_panel()
        if self.status in RESOLVED_STATUSES and not self.outcome:
            frappe.throw(_("A resolution outcome is required."))
        if self.status in {"Upheld", "Partially Upheld"} and not self.remedial_action:
            frappe.throw(_("A remedial action is required for an upheld complaint."))

    def before_insert(self):
        self.submitted_by = self.submitted_by or frappe.session.user
        self.submission_date = self.submission_date or now_datetime()
        response_days = (
            frappe.db.get_single_value(
                "Ugavi Procurement Settings", "complaint_response_days"
            )
            or 7
        )
        self.response_due_date = self.response_due_date or add_days(
            self.submission_date, int(response_days)
        )

    def on_update(self):
        previous = self.get_doc_before_save()
        if (
            self.status in RESOLVED_STATUSES
            and (not previous or previous.status != self.status)
        ):
            self.db_set("resolution_date", now_datetime(), update_modified=False)
            notify_supplier_users(
                self.supplier,
                _("Tender complaint resolved"),
                _("Complaint {0} was resolved as {1}.").format(self.name, self.status),
                "Tender Complaint",
                self.name,
            )
            self._apply_remedial_action()

    def _validate_status_transition(self):
        previous = self.get_doc_before_save()
        if not previous or previous.status == self.status:
            return
        if self.status not in ALLOWED_TRANSITIONS.get(previous.status, set()):
            frappe.throw(
                _("Tender complaint cannot move from {0} to {1}.").format(
                    previous.status, self.status
                )
            )

    def _validate_review_panel(self):
        if self.status not in {"Under Review", *RESOLVED_STATUSES}:
            return
        members = [row.user for row in self.review_panel if row.user]
        if len(members) < 3 or len(set(members)) != len(members):
            frappe.throw(
                _("A complaint review panel requires at least three distinct members.")
            )
        if any(row.has_conflict for row in self.review_panel):
            frappe.throw(_("Conflicted members must be replaced before review begins."))
        if self.submitted_by in members:
            frappe.throw(_("The complainant cannot serve on the review panel."))
        if self.assigned_to and self.assigned_to not in members:
            frappe.throw(_("The review officer must be a review-panel member."))

    def _apply_remedial_action(self):
        if self.status not in {"Upheld", "Partially Upheld"}:
            return
        if self.remedial_action in {"Re-evaluation", "Cancel Intended Award"}:
            frappe.db.set_value("Tender", self.tender, "status", "Under Evaluation")

    def _validate_submission_window(self):
        standstill = frappe.db.get_value(
            "Standstill Period",
            self.standstill_period,
            ["tender", "status", "end_date"],
            as_dict=True,
        )
        if not standstill or standstill.tender != self.tender:
            frappe.throw(_("The standstill period does not belong to this tender."))
        if standstill.status not in {"Active", "Challenged"}:
            frappe.throw(_("This standstill period is not accepting complaints."))
        if get_datetime(standstill.end_date) < now_datetime():
            frappe.throw(_("The standstill complaint window has closed."))
        if not frappe.db.exists(
            "Bid", {"tender": self.tender, "supplier": self.supplier}
        ):
            frappe.throw(_("Only a bidder on this tender may submit a complaint."))
