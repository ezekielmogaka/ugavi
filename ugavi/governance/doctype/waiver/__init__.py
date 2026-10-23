"""Waiver controller — approval workflow for procurement rule overrides."""
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate


class Waiver(Document):
    def before_save(self):
        invalid_statuses = {"Approved", "Rejected"}
        if self.status in invalid_statuses and not self.approved_by:
            frappe.throw(_("Approved/Rejected status requires an approver (approved_by)."))

    def approve(self, user: str, remarks: str = ""):
        self.approved_by = user
        self.approval_date = nowdate()
        self.approval_remarks = remarks
        self.status = "Approved"
        self.save()

    def reject(self, user: str, remarks: str = ""):
        self.approved_by = user
        self.approval_date = nowdate()
        self.approval_remarks = remarks
        self.status = "Rejected"
        self.save()
