"""Supplier Prequalification — manages supplier eligibility for tenders."""
import frappe
from frappe.model.document import Document
from frappe.utils import today, add_to_date


class SupplierPrequalification(Document):
    """Prequalification record for a supplier in a given category."""

    def validate(self):
        self._validate_dates()
        self._check_duplicate()

    def _validate_dates(self):
        if self.expiry_date and self.prequalification_date:
            if self.expiry_date <= self.prequalification_date:
                frappe.throw("Expiry date must be after prequalification date")

    def _check_duplicate(self):
        existing = frappe.db.exists(
            "Supplier Prequalification",
            {"supplier": self.supplier, "category": self.category, "name": ("!=", self.name)},
        )
        if existing and self.status == "Prequalified":
            frappe.throw(f"Supplier already has an active prequalification for {self.category}")

    def on_update(self):
        if self.status == "Suspended":
            self._suspend_supplier()
        elif self.status == "Prequalified":
            self._activate_supplier()

    def _suspend_supplier(self):
        frappe.db.set_value("Supplier", self.supplier, "disabled", 1)

    def _activate_supplier(self):
        frappe.db.set_value("Supplier", self.supplier, "disabled", 0)

    @frappe.whitelist()
    def renew(self, new_expiry_date: str) -> str:
        """Renew prequalification with a new expiry date."""
        self.status = "Under Review"
        self.expiry_date = new_expiry_date
        self.save()
        return self.name


def is_prequalified(supplier: str, category: str) -> bool:
    """Check if a supplier is currently prequalified for a category."""
    return bool(frappe.db.exists(
        "Supplier Prequalification",
        {"supplier": supplier, "category": category, "status": "Prequalified",
         "expiry_date": (">=", today())},
    ))


def get_prequalified_suppliers(category: str) -> list:
    """Return all prequalified suppliers for a given category."""
    return frappe.get_all(
        "Supplier Prequalification",
        filters={"category": category, "status": "Prequalified", "expiry_date": (">=", today())},
        fields=["supplier", "supplier_name"],
    )