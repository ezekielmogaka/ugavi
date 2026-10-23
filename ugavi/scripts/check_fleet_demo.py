"""Runtime acceptance gate for the LOKADO fleet requirement."""

import json

import frappe
from frappe.utils import flt


def get_report():
    issues = []
    counts = {
        doctype: frappe.db.count(doctype)
        for doctype in (
            "Vehicle",
            "Vehicle Allocation",
            "Fleet Purchase Reconciliation",
            "Fuel Log",
            "Spare Parts Issue",
            "Trip Log",
            "Fleet Utilization Report",
        )
    }
    minimums = {
        "Vehicle": 4,
        "Vehicle Allocation": 4,
        "Fleet Purchase Reconciliation": 8,
        "Fuel Log": 8,
        "Spare Parts Issue": 8,
        "Trip Log": 8,
        "Fleet Utilization Report": 4,
    }
    for doctype, minimum in minimums.items():
        if counts[doctype] < minimum:
            issues.append(f"{doctype}: expected at least {minimum}, found {counts[doctype]}")

    unreconciled = frappe.get_all(
        "Fleet Purchase Reconciliation",
        filters={"status": ("!=", "Reconciled")},
        fields=["name", "status", "remaining_qty"],
    )
    if unreconciled:
        issues.append(f"Fleet purchases are not reconciled: {unreconciled}")

    missing_sources = frappe.db.sql(
        """SELECT pri.name
           FROM `tabPurchase Receipt Item` pri
           INNER JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
           INNER JOIN `tabItem` i ON i.name = pri.item_code
           LEFT JOIN `tabFleet Purchase Reconciliation` r
             ON r.purchase_receipt_item = pri.name AND r.status != 'Cancelled'
           WHERE pr.docstatus = 1
             AND COALESCE(i.ugavi_fleet_category, '') != ''
             AND r.name IS NULL""",
        as_dict=True,
    )
    if missing_sources:
        issues.append(f"Fleet receipt rows missing reconciliation: {missing_sources}")

    stock_link_errors = frappe.db.sql(
        """SELECT sp.name, sp.stock_entry
           FROM `tabSpare Parts Issue` sp
           LEFT JOIN `tabStock Entry` se ON se.name = sp.stock_entry
           WHERE sp.docstatus = 1
             AND (sp.stock_entry IS NULL OR se.docstatus != 1
                  OR se.ugavi_spare_parts_issue != sp.name)""",
        as_dict=True,
    )
    if stock_link_errors:
        issues.append(f"Spare issues missing submitted Stock Entry links: {stock_link_errors}")

    for vehicle in frappe.get_all(
        "Vehicle",
        filters={"ugavi_donor": ("is", "set")},
        fields=["name", "ugavi_total_fuel_litres", "ugavi_total_fuel_cost"],
    ):
        totals = frappe.db.sql(
            """SELECT COALESCE(SUM(litres), 0), COALESCE(SUM(total_cost), 0)
               FROM `tabFuel Log`
               WHERE vehicle = %s AND docstatus = 1""",
            vehicle.name,
        )[0]
        if abs(flt(vehicle.ugavi_total_fuel_litres) - flt(totals[0])) > 0.000001:
            issues.append(f"{vehicle.name}: cached fuel litres do not match submitted logs")
        if abs(flt(vehicle.ugavi_total_fuel_cost) - flt(totals[1])) > 0.01:
            issues.append(f"{vehicle.name}: cached fuel cost does not match submitted logs")

    donor_report_errors = []
    for report in frappe.get_all(
        "Fleet Utilization Report",
        filters={"donor": ("is", "set")},
        fields=["name", "donor", "report_data"],
    ):
        rows = json.loads(report.report_data or "[]")
        for row in rows:
            vehicle_donor = frappe.db.get_value(
                "Vehicle", row.get("vehicle"), "ugavi_donor"
            )
            if vehicle_donor != report.donor:
                donor_report_errors.append(
                    f"{report.name} contains {row.get('vehicle')} ({vehicle_donor})"
                )
    if donor_report_errors:
        issues.append(f"Donor fleet report leakage: {donor_report_errors}")

    return {"ready": not issues, "issues": issues, "counts": counts}


def run():
    report = get_report()
    print(frappe.as_json(report))
    if report["issues"]:
        frappe.throw(
            "Fleet demo acceptance failed:\n- " + "\n- ".join(report["issues"])
        )
    return report
