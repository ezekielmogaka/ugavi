"""Issue purchased spare parts from donor-segregated stock to a vehicle."""

from collections import defaultdict

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from ugavi.fleet.services.purchase_reconciliation import (
    lock_and_validate_allocation,
    refresh_reconciliation,
)


class SparePartsIssue(Document):
    def validate(self):
        if not self.items:
            frappe.throw(_("At least one spare part item is required."))
        self._apply_sources()
        self._validate_donor_warehouse()

    def before_submit(self):
        requested = defaultdict(float)
        for item in self.items:
            requested[item.source_reconciliation] += flt(item.quantity)
        for reconciliation, quantity in requested.items():
            item_code = next(
                item.item_code
                for item in self.items
                if item.source_reconciliation == reconciliation
            )
            lock_and_validate_allocation(
                reconciliation,
                quantity,
                "Spare Part",
                item_code=item_code,
                donor=self.donor,
            )

    def on_submit(self):
        self._create_stock_entry()
        for reconciliation in {i.source_reconciliation for i in self.items}:
            refresh_reconciliation(reconciliation)

    def on_cancel(self):
        if self.stock_entry:
            stock_entry = frappe.get_doc("Stock Entry", self.stock_entry)
            if stock_entry.docstatus == 1:
                stock_entry.cancel()
        frappe.db.set_value(
            self.doctype,
            self.name,
            {"status": "Draft", "issue_date": None},
            update_modified=False,
        )
        for reconciliation in {i.source_reconciliation for i in self.items}:
            refresh_reconciliation(reconciliation)

    def _apply_sources(self):
        donors = set()
        orders = set()
        invoices = set()
        for item in self.items:
            source = frappe.get_doc(
                "Fleet Purchase Reconciliation", item.source_reconciliation
            )
            if source.fleet_category != "Spare Part":
                frappe.throw(
                    _("Fleet purchase {0} is not a spare-part purchase.").format(
                        source.name
                    )
                )
            item.item_code = source.item_code
            item.uom = source.stock_uom
            item.valuation_rate = source.valuation_rate
            item.amount = flt(item.quantity) * flt(item.valuation_rate)
            if source.donor:
                donors.add(source.donor)
            if source.purchase_order:
                orders.add(source.purchase_order)
            if source.purchase_invoice:
                invoices.add(source.purchase_invoice)
        if len(donors) > 1:
            frappe.throw(_("A spare-parts issue cannot mix donor purchases."))
        if len(orders) > 1:
            frappe.throw(_("A spare-parts issue cannot mix purchase orders."))
        self.donor = next(iter(donors), None)
        self.purchase_order = next(iter(orders), None)
        self.purchase_invoice = next(iter(invoices), None) if len(invoices) == 1 else None

    def _validate_donor_warehouse(self):
        warehouse_donor = frappe.db.get_value(
            "Donor Warehouse", {"warehouse": self.warehouse}, "donor"
        )
        if self.donor and warehouse_donor != self.donor:
            frappe.throw(
                _("Warehouse {0} must be assigned to donor {1}.").format(
                    self.warehouse, self.donor
                )
            )

    def _create_stock_entry(self):
        if self.stock_entry:
            frappe.throw(_("Stock Entry {0} already exists.").format(self.stock_entry))
        stock_entry = frappe.get_doc(
            {
                "doctype": "Stock Entry",
                "stock_entry_type": "Material Issue",
                "from_warehouse": self.warehouse,
                "ugavi_vehicle": self.vehicle,
                "ugavi_spare_parts_issue": self.name,
                "items": [
                    {
                        "item_code": item.item_code,
                        "qty": item.quantity,
                        "s_warehouse": self.warehouse,
                    }
                    for item in self.items
                ],
            }
        )
        stock_entry.insert(ignore_permissions=True)
        stock_entry.submit()
        frappe.db.set_value(
            self.doctype,
            self.name,
            {
                "stock_entry": stock_entry.name,
                "status": "Issued",
                "issue_date": frappe.utils.today(),
            },
            update_modified=False,
        )

    @frappe.whitelist()
    def issue(self):
        if self.docstatus != 0:
            frappe.throw(_("Only a draft spare-parts issue can be submitted."))
        self.submit()
