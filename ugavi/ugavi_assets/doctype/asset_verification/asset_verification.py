"""Asset Verification — periodic physical verification."""
import frappe
from frappe.model.document import Document
from frappe import _


class AssetVerification(Document):
    """Physical verification of donor-funded assets."""

    def validate(self):
        if self.found == "No" and not self.notes:
            frappe.throw(_("Notes are required when an asset is not found"))

    @frappe.whitelist()
    def complete(self):
        if self.found != "Yes":
            frappe.throw(_("Only a physically found asset can be marked verified"))
        frappe.db.set_value(
            "Asset Register",
            self.asset,
            {
                "last_verified_date": self.verification_date,
                "condition": self.condition,
            },
        )