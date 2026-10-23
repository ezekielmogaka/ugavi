"""Controlled asset custody, location, and condition movements."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today


class UgaviAssetMovement(Document):
    def validate(self):
        if self.from_location == self.to_location:
            frappe.throw(_("Source and destination locations must be different"))
        if getdate(self.movement_date) > getdate(today()):
            frappe.throw(_("Movement date cannot be in the future"))
        if self.status == "Completed" and self.is_new():
            frappe.throw(_("Use Confirm to complete an asset movement"))
        if self.asset and self.status == "Draft":
            asset = frappe.get_doc("Asset Register", self.asset)
            self.from_location = asset.location
            self.from_custodian = asset.custodian
            self.from_condition = asset.condition
            self.donor = asset.donor
            self._validate_destination_donor(asset.donor)

    @frappe.whitelist()
    def confirm(self):
        if self.status != "Draft":
            frappe.throw(_("Only draft movements can be completed"))
        frappe.db.sql(
            "SELECT name FROM `tabAsset Register` WHERE name = %s FOR UPDATE",
            self.asset,
        )
        asset = frappe.get_doc("Asset Register", self.asset)
        if asset.status != "Active":
            frappe.throw(_("Only active assets can be moved"))
        if asset.location != self.from_location:
            frappe.throw(
                _("Asset location changed from {0} to {1}; reload the movement").format(
                    self.from_location, asset.location
                )
            )
        if asset.custodian != self.from_custodian:
            frappe.throw(_("Asset custodian changed; reload the movement"))
        if asset.condition != self.from_condition:
            frappe.throw(_("Asset condition changed; reload the movement"))
        self._validate_destination_donor(asset.donor)
        asset.location = self.to_location
        asset.custodian = self.to_custodian
        asset.condition = self.to_condition
        asset.save(ignore_permissions=True)
        self.status = "Completed"
        self.save(ignore_permissions=True)

    def _validate_destination_donor(self, asset_donor):
        destination_donor = frappe.db.get_value(
            "Donor Warehouse", {"warehouse": self.to_location}, "donor"
        )
        if destination_donor and asset_donor and destination_donor != asset_donor:
            frappe.throw(
                _("Asset donor does not match the destination warehouse donor")
            )
