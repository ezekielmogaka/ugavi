"""Ugavi Procurement Settings — Single DocType for global configuration."""
import frappe
from frappe.model.document import Document


class UgaviProcurementSettings(Document):
    """Singleton configuration for procurement thresholds and governance."""

    def validate(self):
        self._validate_thresholds()

    def _validate_thresholds(self):
        if self.direct_threshold >= self.restricted_threshold:
            frappe.throw("Direct threshold must be less than Restricted threshold")
        if self.restricted_threshold > self.open_threshold:
            frappe.throw("Restricted threshold must not exceed Open threshold")


def get_settings():
    """Return cached settings singleton."""
    if not hasattr(frappe.local, "_ugavi_settings"):
        frappe.local._ugavi_settings = frappe.get_single("Ugavi Procurement Settings")
    return frappe.local._ugavi_settings