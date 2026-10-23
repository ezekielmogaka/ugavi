import frappe
from frappe import _
from frappe.model.document import Document


class LegalHold(Document):
    def validate(self):
        if not frappe.db.exists(self.reference_doctype, self.reference_name):
            frappe.throw(_("The record selected for legal hold does not exist."))
        duplicate = frappe.db.exists(
            "Legal Hold",
            {
                "reference_doctype": self.reference_doctype,
                "reference_name": self.reference_name,
                "status": "Active",
                "name": ("!=", self.name),
            },
        )
        if self.status == "Active" and duplicate:
            frappe.throw(_("This record already has an active legal hold."))

    @frappe.whitelist()
    def release(self, release_reason: str):
        if self.status != "Active":
            frappe.throw(_("Only an active legal hold may be released."))
        if not release_reason:
            frappe.throw(_("A release reason is required."))
        self.status = "Released"
        self.released_by = frappe.session.user
        self.released_at = frappe.utils.now_datetime()
        self.release_reason = release_reason
        self.save()
