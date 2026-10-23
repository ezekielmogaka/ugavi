import frappe
from frappe import _
from frappe.model.document import Document


class RecordDisposalRequest(Document):
    def validate(self):
        if self.status == "Approved" and not self.approved_by:
            frappe.throw(_("An approved request must record its approver."))
        if self.archive_file:
            is_private = frappe.db.get_value(
                "File", {"file_url": self.archive_file}, "is_private"
            )
            if not is_private:
                frappe.throw(_("The disposal archive must be a private file."))

    @frappe.whitelist()
    def approve(self):
        if self.status != "Draft":
            frappe.throw(_("Only a draft disposal request may be approved."))
        self.status = "Approved"
        self.approved_by = frappe.session.user
        self.approved_at = frappe.utils.now_datetime()
        self.save()

    @frappe.whitelist()
    def dispose(self):
        if self.status != "Approved":
            frappe.throw(_("Only an approved disposal request may be executed."))
        frappe.delete_doc(self.reference_doctype, self.reference_name)
        self.status = "Executed"
        self.executed_by = frappe.session.user
        self.executed_at = frappe.utils.now_datetime()
        self.save()
