"""Segregation of Duties controller — prevents conflicting role assignments."""
import frappe
from frappe import _
from frappe.model.document import Document


class SegregationofDuties(Document):
    def before_save(self):
        if self.role_1 == self.role_2:
            frappe.throw(_("Role 1 and Role 2 must be different."))
