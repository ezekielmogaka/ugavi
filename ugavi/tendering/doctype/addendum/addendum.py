import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime


class Addendum(Document):
    def validate(self):
        if self.extends_deadline and not self.new_deadline:
            frappe.throw(_("A revised submission deadline is required."))
        if self.new_deadline and get_datetime(self.new_deadline) <= get_datetime(
            self.issue_date
        ):
            frappe.throw(_("The revised deadline must be after the addendum issue date."))
