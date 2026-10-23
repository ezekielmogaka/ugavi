import frappe
from frappe import _
from frappe.model.document import Document


class RecordRetentionPolicy(Document):
    def validate(self):
        if int(self.retention_years or 0) < 1:
            frappe.throw(_("Retention must be at least one year."))
        duplicate = frappe.db.exists(
            "Record Retention Policy",
            {
                "reference_doctype": self.reference_doctype,
                "enabled": 1,
                "name": ("!=", self.name),
            },
        )
        if self.enabled and duplicate:
            frappe.throw(_("Only one active retention policy is allowed per DocType."))
