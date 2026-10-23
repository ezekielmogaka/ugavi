import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class MonthlyStockReport(Document):
    """Scheduled monthly stock report by donor/warehouse."""

    def generate(self):
        """Populate stock summary from Stock Ledger entries."""
        self.generated_at = now_datetime()
        self.items = []
        month_start = frappe.utils.get_first_day(self.report_month)
        month_end = frappe.utils.get_last_day(self.report_month)
        if not self.warehouse:
            frappe.throw("Warehouse is required for donor stock reporting")
        mapped_donor = frappe.db.get_value(
            "Donor Warehouse", {"warehouse": self.warehouse}, "donor"
        )
        if not mapped_donor or mapped_donor != self.donor:
            frappe.throw("Warehouse does not belong to the selected donor")

        rows = frappe.db.sql(
            """
            SELECT
                sle.item_code,
                SUM(CASE WHEN sle.posting_date < %(start)s
                         THEN sle.actual_qty ELSE 0 END) AS opening_qty,
                SUM(CASE WHEN sle.posting_date BETWEEN %(start)s AND %(end)s
                              AND sle.actual_qty > 0
                              AND NOT (
                                sle.voucher_type = 'Stock Entry'
                                AND COALESCE(se.stock_entry_type, '') LIKE '%%Transfer%%'
                              )
                              AND sle.voucher_type != 'Stock Reconciliation'
                         THEN sle.actual_qty ELSE 0 END) AS receipts_qty,
                ABS(SUM(CASE WHEN sle.posting_date BETWEEN %(start)s AND %(end)s
                                  AND sle.actual_qty < 0
                                  AND NOT (
                                    sle.voucher_type = 'Stock Entry'
                                    AND COALESCE(se.stock_entry_type, '') LIKE '%%Transfer%%'
                                  )
                                  AND sle.voucher_type != 'Stock Reconciliation'
                             THEN sle.actual_qty ELSE 0 END)) AS issues_qty,
                SUM(CASE WHEN sle.posting_date BETWEEN %(start)s AND %(end)s
                              AND sle.actual_qty > 0
                              AND sle.voucher_type = 'Stock Entry'
                              AND COALESCE(se.stock_entry_type, '') LIKE '%%Transfer%%'
                         THEN sle.actual_qty ELSE 0 END) AS transfer_in_qty,
                ABS(SUM(CASE WHEN sle.posting_date BETWEEN %(start)s AND %(end)s
                                  AND sle.actual_qty < 0
                                  AND sle.voucher_type = 'Stock Entry'
                                  AND COALESCE(se.stock_entry_type, '') LIKE '%%Transfer%%'
                             THEN sle.actual_qty ELSE 0 END)) AS transfer_out_qty,
                SUM(CASE WHEN sle.posting_date BETWEEN %(start)s AND %(end)s
                              AND sle.voucher_type = 'Stock Reconciliation'
                         THEN sle.actual_qty ELSE 0 END) AS adjustment_qty,
                SUM(sle.stock_value_difference) AS closing_value
            FROM `tabStock Ledger Entry` sle
            LEFT JOIN `tabStock Entry` se
              ON sle.voucher_type = 'Stock Entry' AND se.name = sle.voucher_no
            WHERE sle.warehouse = %(warehouse)s
              AND sle.posting_date <= %(end)s
              AND sle.is_cancelled = 0
            GROUP BY sle.item_code
            ORDER BY sle.item_code
            """,
            {"start": month_start, "end": month_end, "warehouse": self.warehouse},
            as_dict=True,
        )
        for row in rows:
            closing = (
                (row.opening_qty or 0)
                + (row.receipts_qty or 0)
                - (row.issues_qty or 0)
                + (row.transfer_in_qty or 0)
                - (row.transfer_out_qty or 0)
                + (row.adjustment_qty or 0)
            )
            self.append(
                "items",
                {
                    "item_code": row.item_code,
                    "opening_qty": row.opening_qty or 0,
                    "receipts_qty": row.receipts_qty or 0,
                    "issues_qty": row.issues_qty or 0,
                    "transfer_in_qty": row.transfer_in_qty or 0,
                    "transfer_out_qty": row.transfer_out_qty or 0,
                    "adjustment_qty": row.adjustment_qty or 0,
                    "closing_qty": closing,
                    "total_value": row.closing_value or 0,
                    "donor": self.donor,
                },
            )
        self.save()