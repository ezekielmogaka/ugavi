"""Controlled asset disposal with authorization and value evidence."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class AssetDisposal(Document):
    def validate(self):
        if flt(self.disposal_value) < 0:
            frappe.throw(_("Disposal value cannot be negative"))
        asset = frappe.get_doc("Asset Register", self.asset)
        if asset.status == "Disposed" and self.status != "Completed":
            frappe.throw(_("Asset is already disposed"))
        self.book_value = asset.current_value or asset.purchase_price or 0
        self.gain_loss = flt(self.disposal_value) - flt(self.book_value)
        duplicate = frappe.db.exists(
            "Asset Disposal",
            {
                "asset": self.asset,
                "name": ("!=", self.name),
                "status": ("!=", "Completed"),
            },
        )
        if duplicate:
            frappe.throw(_("An active disposal already exists for this asset"))

    @frappe.whitelist()
    def approve(self):
        if self.status != "Draft":
            frappe.throw(_("Only draft disposals can be approved"))
        if not self.authorized_by:
            frappe.throw(_("An independent authorizer is required"))
        if self.authorized_by == self.owner:
            frappe.throw(_("The disposal creator cannot authorize the disposal"))
        if not frappe.db.get_value("User", self.authorized_by, "enabled"):
            frappe.throw(_("The authorizer must be an enabled user"))
        self.status = "Approved"
        self.save()

    @frappe.whitelist()
    def complete_disposal(self):
        if self.status != "Approved":
            frappe.throw(_("Disposal must be approved before completion"))
        frappe.db.sql(
            "SELECT name FROM `tabAsset Register` WHERE name = %s FOR UPDATE",
            self.asset,
        )
        asset = frappe.get_doc("Asset Register", self.asset)
        if asset.status != "Active":
            frappe.throw(_("Only an active asset can be disposed"))
        asset.status = "Disposed"
        asset.condition = "Disposed"
        asset.save(ignore_permissions=True)
        self.status = "Completed"
        self.save()
