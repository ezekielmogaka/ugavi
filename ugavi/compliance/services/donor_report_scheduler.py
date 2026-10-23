"""Scheduled donor report delivery (W8).

Generates and emails donor report packs on a schedule.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, today
from frappe.utils.file_manager import save_file


def generate_scheduled_donor_reports():
    """Scheduler job: generate all donor report packs with active schedules."""
    packs = frappe.get_all("Donor Report Pack",
                           filters={"status": ("in", ["Scheduled", "Draft"])},
                           pluck="name")
    count = 0
    for pack_name in packs:
        try:
            doc = frappe.get_doc("Donor Report Pack", pack_name)
            if not _should_generate(doc):
                continue
            doc.generate()
            _deliver(doc)
            count += 1
        except Exception as e:
            frappe.log_error(
                title="Donor Report Generation Failed",
                message=f"Pack {pack_name}: {e}"
            )
    return count


def _should_generate(doc) -> bool:
    """Check if the report is due for generation."""
    if not doc.schedule_frequency:
        return False
    last = doc.last_generated or "1970-01-01"
    days_map = {"Daily": 1, "Weekly": 7, "Monthly": 30, "Quarterly": 90}
    days = days_map.get(doc.schedule_frequency, 0)
    if days == 0:
        return False
    return (frappe.utils.getdate(today()) -
            frappe.utils.getdate(last)).days >= days


def _deliver(doc):
    """Deliver the report pack via email to recipients."""
    recipients = []
    if doc.email_to:
        recipients = [e.strip() for e in doc.email_to.split(",") if e.strip()]
    if not recipients and doc.donor:
        # Send to donor contacts
        contacts = frappe.get_all("Contact",
                                  filters={"links": [["link_doctype", "=",
                                                      "Donor Profile"],
                                                      ["link_name", "=",
                                                       doc.donor]]},
                                  fields=["email_id"])
        recipients = [c.email_id for c in contacts if c.email_id]
    if not recipients:
        return

    # Generate Excel attachment
    data = frappe._dict(frappe.parse_json(doc.report_data or "{}"))
    content = _render_report(data)
    file_name = f"Donor_Report_{doc.donor}_{today()}.json"

    frappe.sendmail(
        recipients=recipients,
        subject=f"Ugavi Donor Report: {doc.donor} ({doc.from_date} to {doc.to_date})",
        message=f"Attached is the donor report for {doc.donor}.<br><br>{content}",
    )

    doc.last_generated = today()
    doc.status = "Delivered"
    doc.delivered_at = now_datetime()
    doc.save()


def _render_report(data) -> str:
    """Render report data as HTML."""
    lines = ['<table border="1" cellpadding="5">']
    if data.get("procurement"):
        lines.append(f'<tr><th>Procurement</th><td>'
                     f'{data.procurement.get("count", 0)} POs, '
                     f'KES {data.procurement.get("amount", 0):,.2f}</td></tr>')
    if data.get("stock"):
        lines.append(f'<tr><th>Stock Movements</th><td>'
                     f'{data.stock.get("movements", 0)} movements</td></tr>')
    if data.get("assets"):
        lines.append(f'<tr><th>Active Assets</th><td>'
                     f'{data.assets.get("count", 0)} assets, '
                     f'KES {data.assets.get("purchase_value", 0):,.2f}</td></tr>')
    if data.get("fleet"):
        lines.append(f'<tr><th>Fleet</th><td>'
                     f'{data.fleet.get("vehicles", 0)} vehicles, '
                     f'KES {data.fleet.get("fuel_cost", 0):,.2f} fuel</td></tr>')
    if data.get("budget_commitments"):
        lines.append(f'<tr><th>Budget Commitments</th><td>'
                     f'KES {data.budget_commitments.get("active", 0):,.2f} active, '
                     f'KES {data.budget_commitments.get("released", 0):,.2f} released</td></tr>')
    lines.append('</table>')
    return "".join(lines)