"""Verify the seeded LOKADO identities and minimum demo workflow evidence."""

import frappe
from frappe import _
from frappe.utils.password import check_password

from ugavi.scripts.seed_lokado import (
    LOKADO_USERS,
    SUPPLIER_PORTAL_LINKS,
    _DEMO_PASSWORD,
)


def _require_developer_mode():
    if not frappe.conf.developer_mode:
        frappe.throw(_("LOKADO demo verification is disabled outside developer mode."))


def get_report() -> dict:
    _require_developer_mode()
    issues = []

    for email, _first_name, _last_name, role in LOKADO_USERS:
        user = frappe.db.get_value("User", email, ["name", "enabled"], as_dict=True)
        if not user or not user.enabled:
            issues.append(f"Missing or disabled demo user: {email}")
            continue
        try:
            check_password(email, _DEMO_PASSWORD)
        except frappe.AuthenticationError:
            issues.append(f"Demo password mismatch: {email}")
        if role and role not in frappe.get_roles(email):
            issues.append(f"Missing role {role}: {email}")

    for email, supplier in SUPPLIER_PORTAL_LINKS.items():
        if not frappe.db.exists("Supplier", supplier):
            issues.append(f"Missing supplier: {supplier}")
        if not frappe.db.exists(
            "User Permission",
            {"user": email, "allow": "Supplier", "for_value": supplier},
        ):
            issues.append(f"Missing supplier identity link: {email} -> {supplier}")

    minimum_counts = {
        "Donor Profile": 6,
        "Supplier": 18,
        "Purchase Requisition": 10,
        "Tender": 8,
        "Bid": 26,
        "Ugavi Contract": 5,
        "Donor Warehouse": 8,
        "Monthly Stock Report": 6,
        "Inter Donor Transfer": 6,
        "Standstill Period": 1,
        "Vehicle": 4,
        "Vehicle Allocation": 4,
        "Fleet Purchase Reconciliation": 8,
        "Fuel Log": 8,
        "Spare Parts Issue": 8,
        "Trip Log": 8,
        "Asset Register": 8,
        "Asset Verification": 8,
        "Ugavi Asset Movement": 2,
        "Asset Disposal": 1,
        "Purchase Receipt": 6,
        "Ugavi Supplier Evaluation": 8,
        # ── Supply Chain Depth ──
        "Quality Inspection": 0,      # items need inspection_required_before_purchase=1
        "Stock Entry": 11,
        "Batch": 8,
        "Material Request": 5,
        # ── Finance + Three-Way Match ──
        "Purchase Invoice": 8,
        "Payment Entry": 5,
        "Landed Cost Voucher": 3,
        "Budget": 6,
        "Three Way Match": 6,
        # ── Notifications ──
        "Notification": 4,
        # ── Programme ──
        "Project": 3,
        # ── Procurement Depth ──
        "Purchase Order": 4,
    }
    counts = {}
    for doctype, minimum in minimum_counts.items():
        counts[doctype] = frappe.db.count(doctype)
        if counts[doctype] < minimum:
            issues.append(
                f"{doctype}: expected at least {minimum}, found {counts[doctype]}"
            )

    minimum_submitted = {
        "Purchase Invoice": 8,
        "Payment Entry": 5,
        "Landed Cost Voucher": 3,
        "Budget": 6,
        "Stock Entry": 11,
        "Material Request": 3,
    }
    for doctype, minimum in minimum_submitted.items():
        submitted = frappe.db.count(doctype, {"docstatus": 1})
        if submitted < minimum:
            issues.append(
                f"{doctype}: expected at least {minimum} submitted, found {submitted}"
            )

    completed_evaluations = frappe.db.count(
        "Ugavi Supplier Evaluation", {"status": "Completed"}
    )
    if completed_evaluations < 12:
        issues.append(
            f"Ugavi Supplier Evaluation: expected at least 12 completed, found {completed_evaluations}"
        )

    pr_lifecycle_examples = {
        "Draft": "Solar Water Pumps - EU Resilience Programme",
        "Pending Approval": "Veterinary Outreach Kits - USAID Livelihoods",
        "Approved": "Emergency HDPE Pipe Repair - IOM WASH",
        "Rejected": "Community First Aid Kits - Japan Programme",
    }
    for required_status, title in pr_lifecycle_examples.items():
        if not frappe.db.exists(
            "Purchase Requisition", {"title": title, "status": required_status}
        ):
            issues.append(
                f"Purchase Requisition lifecycle missing {required_status}: {title}"
            )

    transfer_statuses = set(
        frappe.get_all("Inter Donor Transfer", pluck="status")
    )
    for required_status in ("Pending Approval", "Approved", "Rejected", "Completed"):
        if required_status not in transfer_statuses:
            issues.append(
                f"Inter Donor Transfer lifecycle missing {required_status} evidence"
            )

    complaint_tender = frappe.db.get_value(
        "Tender", {"title": "Field Motorcycles Peace Building USAID"}, "name"
    )
    if not complaint_tender or not frappe.db.exists(
        "Standstill Period",
        {
            "tender": complaint_tender,
            "status": ("in", ["Active", "Challenged"]),
        },
    ):
        issues.append("Missing active MVP2 complaint standstill window")

    submitted_pos_without_contracts = frappe.db.sql(
        """SELECT po.name
           FROM `tabPurchase Order` po
           LEFT JOIN `tabUgavi Contract` c ON c.purchase_order = po.name
           WHERE po.docstatus = 1 AND c.name IS NULL""",
        as_list=True,
    )
    if submitted_pos_without_contracts:
        issues.append(
            "Submitted Purchase Orders missing contract management records: "
            + ", ".join(row[0] for row in submitted_pos_without_contracts)
        )

    receipts_without_evaluations = frappe.db.sql(
        """SELECT pr.name
           FROM `tabPurchase Receipt` pr
           LEFT JOIN `tabUgavi Supplier Evaluation` e
             ON e.purchase_receipt = pr.name
           WHERE pr.docstatus = 1 AND e.name IS NULL""",
        as_list=True,
    )
    if receipts_without_evaluations:
        issues.append(
            "Submitted receipts missing supplier evaluations: "
            + ", ".join(row[0] for row in receipts_without_evaluations)
        )

    incomplete_contract_evidence = frappe.db.sql(
        """SELECT c.name
           FROM `tabUgavi Contract` c
           WHERE c.status = 'Active'
             AND (
               NOT EXISTS (
                 SELECT 1 FROM `tabContract Document` d
                 WHERE d.parent = c.name AND COALESCE(d.attachment, '') != ''
               )
               OR NOT EXISTS (
                 SELECT 1 FROM `tabContract Milestone` m
                 WHERE m.parent = c.name
               )
             )""",
        as_list=True,
    )
    if incomplete_contract_evidence:
        issues.append(
            "Active contracts missing documents or milestones: "
            + ", ".join(row[0] for row in incomplete_contract_evidence)
        )

    unsealed_bids = frappe.db.sql(
        """SELECT b.name
           FROM `tabBid` b
           INNER JOIN `tabTender` t ON t.name = b.tender
           WHERE t.procurement_method IN ('Restricted Tender', 'Open Tender')
             AND b.status = 'Submitted'
             AND COALESCE(b.encrypted_content, '') = ''""",
        as_list=True,
    )
    if unsealed_bids:
        issues.append(
            "Submitted tender bids missing sealed content: "
            + ", ".join(row[0] for row in unsealed_bids)
        )

    invalid_opening_panels = frappe.db.sql(
        """SELECT name FROM `tabTender`
           WHERE procurement_method IN ('Restricted Tender', 'Open Tender')
             AND status != 'Draft'
             AND (
               opening_officer_1 IS NULL OR opening_officer_2 IS NULL
               OR opening_officer_3 IS NULL
               OR opening_officer_1 = opening_officer_2
               OR opening_officer_1 = opening_officer_3
               OR opening_officer_2 = opening_officer_3
               OR COALESCE(public_key, '') = ''
             )""",
        as_list=True,
    )
    if invalid_opening_panels:
        issues.append(
            "Published tenders missing sealed three-officer controls: "
            + ", ".join(row[0] for row in invalid_opening_panels)
        )

    movement_gaps = frappe.db.sql(
        """SELECT name FROM `tabUgavi Asset Movement`
           WHERE status = 'Completed'
             AND (
               COALESCE(from_condition, '') = ''
               OR COALESCE(to_condition, '') = ''
               OR COALESCE(donor, '') = ''
             )""",
        as_list=True,
    )
    if movement_gaps:
        issues.append(
            "Completed asset movements missing condition/donor evidence: "
            + ", ".join(row[0] for row in movement_gaps)
        )

    from ugavi.scripts.check_fleet_demo import get_report as get_fleet_report

    fleet_report = get_fleet_report()
    issues.extend(f"Fleet: {issue}" for issue in fleet_report["issues"])

    return {
        "ready": not issues,
        "issues": issues,
        "users": len(LOKADO_USERS),
        "supplier_portal_users": len(SUPPLIER_PORTAL_LINKS),
        "counts": counts,
        "fleet": fleet_report,
    }


def run() -> dict:
    report = get_report()
    if report["issues"]:
        frappe.throw(
            _("LOKADO demo verification failed: {0}").format(
                "; ".join(report["issues"])
            )
        )
    print(frappe.as_json(report, indent=2))
    return report
