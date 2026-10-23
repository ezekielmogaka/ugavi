import frappe
from frappe.model.document import Document
from frappe import _


class InterDonorTransfer(Document):
    """Transfer stock between donor-segregated warehouses with approval."""

    def validate(self):
        if self.from_warehouse == self.to_warehouse:
            frappe.throw(_("Source and destination warehouses must be different"))
        self._resolve_donors()

    def _resolve_donors(self):
        from_dw = frappe.db.get_value("Donor Warehouse",
                                       {"warehouse": self.from_warehouse}, "donor")
        to_dw = frappe.db.get_value("Donor Warehouse",
                                     {"warehouse": self.to_warehouse}, "donor")
        self.from_donor = from_dw
        self.to_donor = to_dw
        if from_dw and to_dw and from_dw == to_dw:
            frappe.throw(_("Cannot transfer within the same donor warehouse mapping"))

    @frappe.whitelist()
    def approve(self):
        if self.status != "Pending Approval":
            frappe.throw(_("Only pending transfers can be approved"))
        if "Stock Manager" not in frappe.get_roles() and "System Manager" not in frappe.get_roles():
            frappe.throw(_("Stock Manager role is required"))
        self.status = "Approved"
        self.approved_by = frappe.session.user
        self.save()
        frappe.msgprint(_("Inter-donor transfer approved"))

    @frappe.whitelist()
    def complete(self):
        if self.status != "Approved":
            frappe.throw(_("Transfer must be approved before completion"))
        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Transfer",
            "from_warehouse": self.from_warehouse,
            "to_warehouse": self.to_warehouse,
            "ugavi_inter_donor_transfer": self.name,
            "items": [{
                "item_code": item.item_code,
                "qty": item.qty,
                "s_warehouse": self.from_warehouse,
                "t_warehouse": self.to_warehouse,
            } for item in self.items],
        })
        se.insert()
        se.submit()
        self.status = "Completed"
        self.transfer_date = frappe.utils.today()
        self.save()
        frappe.msgprint(_("Stock Entry {0} created").format(se.name))