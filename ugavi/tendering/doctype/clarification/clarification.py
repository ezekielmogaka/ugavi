import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from ugavi.procurement.portal.supplier_portal import notify_supplier_users


class Clarification(Document):
    def validate(self):
        if self.answer and self.status == "Open":
            self.status = "Answered"
            self.answered_by = frappe.session.user
            self.answered_date = now_datetime()

    def on_update(self):
        previous = self.get_doc_before_save()
        if (
            self.supplier
            and self.status == "Answered"
            and (not previous or previous.status != "Answered")
        ):
            notify_supplier_users(
                self.supplier,
                _("Clarification answered"),
                _("The procurement team answered question {0}.").format(self.name),
                "Clarification",
                self.name,
            )
