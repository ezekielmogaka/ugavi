"""Scheduler tasks — contract expiry alerts, supplier suspension, stock reports."""
import frappe
from frappe import _
from frappe.utils import today, getdate, add_days


def check_contract_expiry():
    """Daily check: alert on contracts expiring within alert window."""
    contracts = frappe.get_all(
        "Contract",
        filters={"status": ("in", ["Active", "Draft"])},
        fields=["name", "end_date", "expiry_alert_days", "supplier"],
    )
    alerted = 0
    for c in contracts:
        if not c.end_date or not c.expiry_alert_days:
            continue
        days_left = (getdate(c.end_date) - getdate(today())).days
        if 0 < days_left <= c.expiry_alert_days:
            frappe.sendmail(
                recipients=[frappe.db.get_single_value("System Settings", "admin_email")],
                subject=_(f"Contract Expiry Alert: {c.name}"),
                message=_(
                    "Contract {0} with supplier {1} expires in {2} days ({3})."
                ).format(c.name, c.supplier, days_left, c.end_date),
            )
            alerted += 1
    if alerted:
        frappe.log_error(f"Sent {alerted} contract expiry alerts", "Scheduler")


def check_supplier_suspension():
    """Semi-monthly check: suspend suppliers with cumulative rating < 60%."""
    suppliers = frappe.get_all("Supplier", filters={"disabled": 0}, pluck="name")
    suspended = 0
    for supplier in suppliers:
        scores = frappe.get_all(
            "Supplier Scorecard",
            filters={"supplier": supplier},
            fields=["total_score"],
            order_by="evaluation_date desc",
            limit=12,
        )
        if not scores:
            continue
        avg = sum(s.total_score for s in scores) / len(scores)
        if avg < 60:
            frappe.db.set_value("Supplier", supplier, "disabled", 1)
            frappe.msgprint(
                _("Supplier {0} auto-suspended — cumulative rating {1}%").format(
                    supplier, round(avg, 1)
                )
            )
            suspended += 1
    if suspended:
        frappe.log_error(f"Auto-suspended {suspended} suppliers", "Scheduler")


def generate_monthly_stock_reports():
    """First day of month: generate stock reports for all donor warehouses."""
    from frappe.utils import get_first_day, get_last_day

    report_month = get_first_day(today())
    warehouses = frappe.get_all(
        "Donor Warehouse", fields=["warehouse", "donor"]
    )

    generated = 0
    for dw in warehouses:
        if frappe.db.exists(
            "Monthly Stock Report",
            {"warehouse": dw.warehouse, "report_month": report_month},
        ):
            continue
        report = frappe.get_doc({
            "doctype": "Monthly Stock Report",
            "report_month": report_month,
            "warehouse": dw.warehouse,
            "donor": dw.donor,
        })
        try:
            report.generate()
            generated += 1
        except Exception as e:
            frappe.log_error(f"Stock report for {dw.warehouse}: {e}", "Scheduler")

    if generated:
        frappe.log_error(f"Generated {generated} monthly stock reports", "Scheduler")