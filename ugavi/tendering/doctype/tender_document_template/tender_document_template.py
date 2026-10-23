import frappe
from frappe import _
from frappe.model.document import Document


class TenderDocumentTemplate(Document):
    def validate(self):
        if int(self.version or 1) < 1:
            frappe.throw(_("Template version must be at least 1."))
        if self.status == "Active" and not self.attachment:
            frappe.throw(_("An active template requires an attachment."))
        duplicate = frappe.db.exists(
            "Tender Document Template",
            {
                "template_name": self.template_name,
                "version": self.version,
                "name": ("!=", self.name),
            },
        )
        if duplicate:
            frappe.throw(_("This template name and version already exist."))

    def on_update(self):
        if self.status != "Active":
            return
        older = frappe.get_all(
            "Tender Document Template",
            filters={
                "template_name": self.template_name,
                "status": "Active",
                "name": ("!=", self.name),
            },
            pluck="name",
        )
        for name in older:
            frappe.db.set_value("Tender Document Template", name, "status", "Superseded")
