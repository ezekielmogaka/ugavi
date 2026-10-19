import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class MonthlyStockReport(Document):
    """Scheduled monthly stock report by donor/warehouse."""

    def generate(self):
        """Populate stock summary from Stock Ledger entries."""
        self.generated_at = now_datetime()
        self.items = []

        filters = {"posting_date": (">=", frappe.utils.get_first_day(self.report_month))}
        if self.warehouse:
            filters["warehouse"] = self.warehouse

        ledger = frappe.get_all(
            "Stock Ledger Entry",
            filters=filters,
            fields=["item_code", "warehouse", "actual_qty", "valuation_rate"],
            order_by="item_code",
        )

        summary = {}
        for entry in ledger:
            key = entry.item_code
            if key not in summary:
                summary[key] = {"item_code": key, "opening_qty": 0, "closing_qty": 0, "total_value": 0}
            summary[key]["closing_qty"] += entry.actual_qty
            summary[key]["total_value"] += entry.actual_qty * (entry.valuation_rate or 0)

        for item_data in summary.values():
            self.append("items", item_data)
        self.save()