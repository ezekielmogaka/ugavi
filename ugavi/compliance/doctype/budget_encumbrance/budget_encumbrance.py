import frappe
from frappe.model.document import Document
from frappe import _


class BudgetEncumbrance(Document):
    """Encumber budget at PO creation, release on receipt."""

    def validate(self):
        if self.status == "Active" and self.released_date:
            self.released_date = None

    def release(self):
        self.status = "Released"
        self.released_date = frappe.utils.today()
        self.save()
        frappe.msgprint(_("Budget encumbrance released for {0}").format(self.purchase_order))