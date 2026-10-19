import frappe
from frappe.model.document import Document
from frappe import _


class Contract(Document):
    """Contract management with milestones, retention, and expiry alerts."""

    def validate(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            frappe.throw(_("End date cannot be before start date"))
        if self.retention_percentage and self.retention_percentage > 100:
            frappe.throw(_("Retention percentage cannot exceed 100%"))

    def on_update(self):
        if self.status == "Expired":
            return
        if self.end_date and frappe.utils.getdate(self.end_date) <= frappe.utils.getdate(frappe.utils.today()):
            self.status = "Expired"
            self.save(ignore_permissions=True)

    def check_expiry(self) -> bool:
        """Return True if contract expires within the alert window."""
        if not self.end_date or not self.expiry_alert_days:
            return False
        days_left = (frappe.utils.getdate(self.end_date) - frappe.utils.getdate(frappe.utils.today())).days
        return 0 < days_left <= self.expiry_alert_days