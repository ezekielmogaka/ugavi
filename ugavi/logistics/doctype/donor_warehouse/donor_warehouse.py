import frappe
from frappe.model.document import Document
from frappe import _


class DonorWarehouse(Document):
    """Map warehouse to donor for segregation. Prevents cross-donor consumption."""

    def validate(self):
        if frappe.db.exists(
            "Donor Warehouse",
            {"warehouse": self.warehouse, "name": ("!=", self.name)},
        ):
            frappe.throw(_("Warehouse {0} is already assigned to a donor").format(self.warehouse))