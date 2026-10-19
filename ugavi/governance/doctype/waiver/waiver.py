import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import now_datetime


class Waiver(Document):
    """Approve exceptions to procurement rules."""

    def validate(self):
        if self.status == "Approved" and not self.approved_by:
            frappe.throw(_("Approved waiver must have an approver"))

    def approve(self, user: str, remarks: str = ""):
        self.status = "Approved"
        self.approved_by = user
        self.approval_date = now_datetime()
        self.approval_remarks = remarks
        self.save()
        frappe.msgprint(_("Waiver approved by {0}").format(user))

    def reject(self, user: str, remarks: str = ""):
        self.status = "Rejected"
        self.approved_by = user
        self.approval_date = now_datetime()
        self.approval_remarks = remarks or "Rejected"
        self.save()
        frappe.msgprint(_("Waiver rejected by {0}").format(user))