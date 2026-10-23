"""Scheduler tasks — contract expiry alerts, supplier suspension, stock reports."""
import frappe
from frappe import _
from frappe.utils import today, getdate, add_days


def check_contract_expiry():
    """Daily check: alert on contracts expiring within alert window."""
    contracts = frappe.get_all(
        "Ugavi Contract",
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
            "Ugavi Supplier Evaluation",
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
    from frappe.utils import get_first_day

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
            recipient = frappe.db.get_value("Donor Profile", dw.donor, "contact_email")
            if recipient:
                frappe.sendmail(
                    recipients=[recipient],
                    subject=_("Monthly Stock Report: {0}").format(dw.warehouse),
                    message=_(
                        "Attached is the donor-segregated stock report for {0}."
                    ).format(report_month),
                    attachments=[
                        frappe.attach_print(
                            "Monthly Stock Report",
                            report.name,
                            file_name=f"{report.name}.pdf",
                        )
                    ],
                )
                frappe.db.set_value(
                    "Monthly Stock Report", report.name, "sent_to", recipient
                )
            generated += 1
        except Exception as e:
            frappe.log_error(f"Stock report for {dw.warehouse}: {e}", "Scheduler")

    if generated:
        frappe.log_error(f"Generated {generated} monthly stock reports", "Scheduler")
def check_vehicle_service_due():
    """Daily: alert on vehicles due for service within 7 days."""
    vehicles = frappe.get_all(
        "Vehicle",
        filters={
            "ugavi_next_service_date": ("<=", add_days(today(), 7)),
            "ugavi_status": "Active",
        },
        fields=["name", "ugavi_next_service_date"],
    )
    for v in vehicles:
        frappe.msgprint(
            _("Vehicle {0} service due by {1}").format(
                v.name, v.ugavi_next_service_date
            )
        )


def generate_monthly_fleet_reports():
    """Generate separate, immutable snapshots for the completed month per donor."""
    from frappe.utils import add_months, get_first_day, get_last_day

    completed_month = add_months(today(), -1)
    report_month = get_first_day(completed_month)
    month_end = get_last_day(completed_month)
    donors = frappe.get_all(
        "Vehicle",
        filters={"disabled": 0, "ugavi_donor": ("is", "set")},
        pluck="ugavi_donor",
        distinct=True,
    )
    fleet_managers = frappe.get_all(
        "Has Role",
        filters={"role": "Fleet Manager", "parenttype": "User"},
        pluck="parent",
    )

    for donor in set(donors):
        if not donor:
            continue
        try:
            report = frappe.get_doc(
                {
                    "doctype": "Fleet Utilization Report",
                    "from_date": str(report_month),
                    "to_date": str(month_end),
                    "donor": donor,
                }
            )
            report.generate()
            recipients = set(fleet_managers)
            donor_email = frappe.db.get_value(
                "Donor Profile", donor, "contact_email"
            )
            if donor_email:
                recipients.add(donor_email)
            if recipients:
                frappe.sendmail(
                    recipients=list(recipients),
                    subject=_("Monthly Fleet Report — {0} — {1}").format(
                        donor, report_month
                    ),
                    message=_(
                        "Attached is the donor-isolated fleet report for {0}, "
                        "covering {1} to {2}."
                    ).format(donor, report_month, month_end),
                    attachments=[
                        frappe.attach_print(
                            "Fleet Utilization Report",
                            report.name,
                            file_name=f"fleet_report_{donor}_{report_month}.pdf",
                        )
                    ],
                )
        except Exception:
            frappe.log_error(
                title=f"Fleet report generation failed for {donor}",
                message=frappe.get_traceback(),
            )


def flag_inactive_suppliers():
    """Weekly: flag suppliers with no transactions in 180 days."""
    pass  # Requires Purchase Order/Invoice data — placeholder for Phase E


def generate_asset_verification_reminder():
    """Monthly: remind asset managers to verify donor-funded assets."""
    assets = frappe.get_all(
        "Asset Register",
        filters={
            "last_verified_date": ("<=", add_days(today(), -180)),
            "status": "Active",
        },
        fields=["name", "asset_name", "last_verified_date"],
    )
    if assets:
        frappe.sendmail(
            recipients=[frappe.db.get_single_value("System Settings", "admin_email")],
            subject=_("Monthly Asset Verification Reminder"),
            message=_("{0} assets require verification (last verified > 6 months).").format(len(assets)),
        )
        frappe.log_error(f"Asset verification reminder: {len(assets)} assets flagged", "Scheduler")