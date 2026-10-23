import frappe
from frappe import _
from frappe.model.document import Document


class TenderDocument(Document):
    def validate(self):
        if not self.attachment:
            frappe.throw(_("A tender document attachment is required."))
        if int(self.document_version or 1) < 1:
            frappe.throw(_("Document version must be at least 1."))
