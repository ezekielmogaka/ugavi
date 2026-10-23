import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime


class DonorReportPack(Document):
    def validate(self):
        if getdate(self.from_date) > getdate(self.to_date):
            frappe.throw(_("From Date cannot be after To Date."))

    @frappe.whitelist()
    def generate(self):
        self.report_data = json.dumps(self._build_snapshot(), default=str, indent=2)
        self.status = "Generated"
        self.generated_at = now_datetime()
        self.generated_by = frappe.session.user
        self.save()
        return self.report_data

    def _build_snapshot(self):
        result = {
            "donor": self.donor,
            "period": {"from": self.from_date, "to": self.to_date},
            "generated_at": now_datetime(),
        }
        if self.include_procurement:
            filters = {
                "ugavi_donor": self.donor,
                "transaction_date": ("between", [self.from_date, self.to_date]),
                "docstatus": ("<", 2),
            }
            result["procurement"] = _count_and_sum(
                "Purchase Order", filters, "base_grand_total"
            )
        if self.include_stock:
            filters = {
                "donor": self.donor,
                "creation": ("between", [self.from_date, self.to_date]),
            }
            result["stock"] = {
                "movements": frappe.db.count("Stock Ledger", filters),
                "incoming_qty": _sum("Stock Ledger", filters, "receipts_qty"),
                "outgoing_qty": _sum("Stock Ledger", filters, "issues_qty"),
            }
        if self.include_assets:
            result["assets"] = {
                "count": frappe.db.count(
                    "Asset Register", {"donor": self.donor, "status": "Active"}
                ),
                "purchase_value": _sum(
                    "Asset Register",
                    {"donor": self.donor, "status": "Active"},
                    "purchase_price",
                ),
            }
        if self.include_fleet:
            result["fleet"] = {
                "vehicles": frappe.db.count(
                    "Vehicle", {"ugavi_donor": self.donor, "ugavi_status": "Active"}
                ),
                "fuel_cost": _sum(
                    "Vehicle", {"ugavi_donor": self.donor}, "ugavi_total_fuel_cost"
                ),
            }
        if self.include_budget:
            result["budget_commitments"] = {
                "active": _sum(
                    "Budget Encumbrance",
                    {"donor": self.donor, "status": "Active"},
                    "encumbered_amount",
                ),
                "released": _sum(
                    "Budget Encumbrance",
                    {"donor": self.donor, "status": "Released"},
                    "encumbered_amount",
                ),
            }
        return result


def _sum(doctype, filters, fieldname):
    return float(
        frappe.db.get_value(doctype, filters, f"sum({fieldname})") or 0
    )


def _count_and_sum(doctype, filters, fieldname):
    return {
        "count": frappe.db.count(doctype, filters),
        "amount": _sum(doctype, filters, fieldname),
    }
