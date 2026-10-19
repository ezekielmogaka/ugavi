import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import today, getdate


class ApprovalDelegation(Document):
    """Delegate approval authority during absence."""

    def validate(self):
        if self.start_date and self.end_date and getdate(self.end_date) < getdate(self.start_date):
            frappe.throw(_("End date cannot be before start date"))
        if self.delegated_from == self.delegated_to:
            frappe.throw(_("Cannot delegate to yourself"))
        self._check_active()

    def _check_active(self):
        if self.active and getdate(self.end_date) < getdate(today()):
            self.active = 0

    def is_valid_for(self, amount: float, doc_type: str) -> bool:
        """Check if this delegation covers the given document type and amount."""
        if not self.active:
            return False
        today_date = getdate(today())
        if today_date < getdate(self.start_date) or today_date > getdate(self.end_date):
            return False
        if self.delegation_type != "All Procurement" and self.delegation_type != doc_type:
            return False
        if self.max_amount and self.max_amount > 0 and amount > self.max_amount:
            return False
        return True