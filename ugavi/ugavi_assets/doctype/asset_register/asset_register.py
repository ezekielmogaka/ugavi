"""Asset Register — donor-segregated fixed asset tracking."""
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_url_to_form
from frappe.utils.print_format_generator import get_qr_code


class AssetRegister(Document):
    """Fixed asset register with donor and project dimensions."""

    def validate(self):
        self._validate_donor()
        self._calculate_depreciation()

    def _validate_donor(self):
        if not self.donor:
            return
        donor = frappe.get_doc("Donor Profile", self.donor)
        if not donor.enabled:
            frappe.throw(_("Cannot assign assets to inactive donor {0}").format(self.donor))

    def _calculate_depreciation(self):
        if self.purchase_price and self.useful_life_years:
            annual = (
                self.purchase_price - (self.salvage_value or 0)
            ) / self.useful_life_years
            self.annual_depreciation = round(annual, 2)

    def get_qr_data_uri(self) -> str:
        """Return an in-process SVG QR code without disclosing asset data externally."""
        return get_qr_code(get_url_to_form(self.doctype, self.name))

    @frappe.whitelist()
    def mark_verified(self):
        self.last_verified_date = frappe.utils.today()
        self.save()