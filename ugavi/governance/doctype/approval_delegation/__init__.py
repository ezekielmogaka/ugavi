"""Approval Delegation controller — validates delegation rules."""
import frappe
from frappe import _
from frappe.model.document import Document


class ApprovalDelegation(Document):
    def before_save(self):
        if self.delegated_from == self.delegated_to:
            frappe.throw(_("Cannot delegate to yourself."))
