"""Verify the seeded LOKADO identities and minimum demo workflow evidence."""

import json

import frappe
from frappe import _
from frappe.utils import get_datetime, getdate, now_datetime, today
from frappe.utils.password import check_password

from ugavi.scripts.seed_lokado import (
    LOKADO_USERS,
    LOKADO_UPSTREAM_ROLES,
    SUPPLIER_PORTAL_LINKS,
    RECEIPT_INVOICES,
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
        for upstream_role in LOKADO_UPSTREAM_ROLES.get(email, ()):
            if upstream_role not in frappe.get_roles(email):
                issues.append(f"Missing upstream role {upstream_role}: {email}")

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
        "Supplier": 30,
        "Purchase Requisition": 25,
        "Tender": 20,
        "Bid": 46,
        "Ugavi Contract": 32,
        "Donor Warehouse": 8,
        "Monthly Stock Report": 6,
        "Inter Donor Transfer": 6,
        "Vehicle": 8,
        "Vehicle Allocation": 8,
        "Fleet Purchase Reconciliation": 16,
        "Fuel Log": 16,
        "Spare Parts Issue": 16,
        "Trip Log": 16,
        "Asset Register": 16,
        "Asset Verification": 16,
        "Ugavi Asset Movement": 2,
        "Asset Disposal": 1,
        "Purchase Receipt": 32,
        "Ugavi Supplier Evaluation": 36,
        # ── Supply Chain Depth ──
        "Quality Inspection": 20,
        "Stock Entry": 53,
        "Batch": 8,
        "Material Request": 17,
        # ── Finance + Three-Way Match ──
        "Purchase Invoice": 26,
        "Payment Entry": 17,
        "Landed Cost Voucher": 8,
        "Budget": 10,
        "Three Way Match": 22,
        # ── Notifications ──
        "Notification": 4,
        # ── Programme ──
        "Project": 3,
        # ── Procurement Depth ──
        "Purchase Order": 32,
    }
    counts = {}
    for doctype, minimum in minimum_counts.items():
        counts[doctype] = frappe.db.count(doctype)
        if counts[doctype] < minimum:
            issues.append(
                f"{doctype}: expected at least {minimum}, found {counts[doctype]}"
            )

    minimum_submitted = {
        "Purchase Invoice": 26,
        "Payment Entry": 17,
        "Landed Cost Voucher": 8,
        "Budget": 10,
        "Stock Entry": 53,
        "Material Request": 3,
        "Purchase Order": 32,
        "Purchase Receipt": 32,
        "Quality Inspection": 20,
    }
    for doctype, minimum in minimum_submitted.items():
        submitted = frappe.db.count(doctype, {"docstatus": 1})
        if submitted < minimum:
            issues.append(
                f"{doctype}: expected at least {minimum} submitted, found {submitted}"
            )

    for name in frappe.get_all("Monthly Stock Report", pluck="name"):
        report = frappe.get_doc("Monthly Stock Report", name)
        ledger = {
            row.item_code: row
            for row in frappe.db.sql(
                """SELECT item_code, SUM(actual_qty) AS qty,
                          SUM(stock_value_difference) AS value
                   FROM `tabStock Ledger Entry`
                   WHERE warehouse = %s AND posting_date <= %s AND is_cancelled = 0
                   GROUP BY item_code""",
                (report.warehouse, frappe.utils.get_last_day(report.report_month)),
                as_dict=True,
            )
        }
        recorded = {row.item_code: row for row in report.items}
        if not recorded:
            issues.append(f"Monthly Stock Report {name}: donor book has no ledger rows")
        for item_code in set(ledger) | set(recorded):
            source = ledger.get(item_code)
            row = recorded.get(item_code)
            expected_qty = float(source.qty or 0) if source else 0
            expected_value = float(source.value or 0) if source else 0
            if (
                row is None
                or abs(float(row.closing_qty or 0) - expected_qty) > 0.00001
                or abs(float(row.total_value or 0) - expected_value) > 0.01
                or row.donor != report.donor
            ):
                issues.append(f"Monthly Stock Report {name}: {item_code} does not reconcile to donor ledger")

    completed_evaluations = frappe.db.count(
        "Ugavi Supplier Evaluation", {"status": "Completed"}
    )
    if completed_evaluations < 36:
        issues.append(
            f"Ugavi Supplier Evaluation: expected at least 36 completed, found {completed_evaluations}"
        )

    pr_lifecycle_examples = {
        "Draft": "Fishing Livelihood Equipment - Lake Turkana",
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

    for bill_no, supplier, warehouse_name, _share, _mode in RECEIPT_INVOICES:
        invoices = frappe.get_all(
            "Purchase Invoice",
            filters={"bill_no": bill_no, "supplier": supplier, "docstatus": 1},
            pluck="name",
        )
        if len(invoices) != 1:
            issues.append(f"{bill_no}: expected one submitted receipt-linked invoice")
            continue
        warehouse = frappe.db.get_value("Warehouse", {"warehouse_name": warehouse_name}, "name")
        invoice = frappe.get_doc("Purchase Invoice", invoices[0])
        for row in invoice.items:
            if not row.purchase_receipt or not row.purchase_order or row.warehouse != warehouse:
                issues.append(f"{bill_no}: item {row.item_code} has wrong source or donor warehouse")
            if not frappe.db.exists("Ugavi Supplier Evaluation", {
                "purchase_receipt": row.purchase_receipt, "status": "Completed",
            }):
                issues.append(f"{bill_no}: delivery scorecard is incomplete")

    invalid_tender_sources = frappe.db.sql(
        """SELECT t.name FROM `tabTender` t
           LEFT JOIN `tabPurchase Requisition` p ON p.name = t.purchase_requisition
           WHERE p.name IS NULL OR t.donor != p.donor
              OR t.procurement_method != p.procurement_method
              OR (t.status != 'Draft' AND p.status NOT IN ('Approved', 'Converted to Tender'))""",
        as_list=True,
    )
    if invalid_tender_sources:
        issues.append(f"Tenders have invalid requisition lineage: {invalid_tender_sources}")

    premature_recommendations = frappe.db.sql(
        """SELECT DISTINCT e.name FROM `tabBid Evaluation Summary` e
           JOIN `tabBid` b ON b.tender = e.tender
           WHERE e.status = 'Approved' AND b.status = 'Submitted'""",
        as_list=True,
    )
    if premature_recommendations:
        issues.append(f"Approved recommendations reference unopened bids: {premature_recommendations}")

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

    opening_tender = frappe.db.get_value(
        "Tender", {"title": "Solar Water Pumps EU Resilience"},
        ["name", "status", "submission_deadline"], as_dict=True,
    )
    if not opening_tender:
        issues.append("Missing solar-pump live-opening demo tender")
    elif opening_tender.status in ("Published", "Bids Received"):
        if get_datetime(opening_tender.submission_deadline) >= now_datetime():
            issues.append("Solar-pump demo tender has not closed for live bid opening")
        if frappe.db.count("Bid", {"tender": opening_tender.name, "status": "Submitted"}) < 4:
            issues.append("Solar-pump live-opening demo requires four sealed submissions")
    elif not frappe.db.exists("Bid Opening Record", {"tender": opening_tender.name}):
        issues.append("Solar-pump tender advanced without verified bid-opening evidence")

    issues.extend(_evaluation_journey_issues())

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
    for plate in ("KDL 410U", "KDM 271I", "KDN 842C", "KDP 318E",
                  "KDQ 520J", "KDR 711L", "KDS 143U", "KDT 890C"):
        vehicle = frappe.db.get_value(
            "Vehicle", {"license_plate": plate}, ["name", "ugavi_donor"], as_dict=True,
        )
        if not vehicle:
            issues.append(f"Fleet: missing scenario vehicle {plate}")
            continue
        reports = frappe.get_all(
            "Fleet Utilization Report",
            filters={"donor": vehicle.ugavi_donor, "vehicle": ("is", "not set"),
                     "docstatus": ("<", 2)},
            fields=["report_data"], order_by="modified desc", limit=1,
        )
        rows = json.loads(reports[0].report_data or "[]") if reports else []
        row = next((row for row in rows if row.get("vehicle") == vehicle.name), None)
        if row is None or any(
            float(row.get(field) or 0) < minimum
            for field, minimum in (("total_trips", 2), ("total_distance", 500),
                                   ("fuel_used", 120), ("fuel_cost", 25200))
        ):
            issues.append(f"Fleet: {plate} missing its complete donor-report journey")

    return {
        "ready": not issues,
        "issues": issues,
        "users": len(LOKADO_USERS),
        "supplier_portal_users": len(SUPPLIER_PORTAL_LINKS),
        "counts": counts,
        "fleet": fleet_report,
    }


def _evaluation_journey_issues() -> list[str]:
    """The live evaluation scenes need real, controller-produced evidence."""
    from ugavi.tendering.services.evaluation import (
        approved_minutes,
        approved_recommendation,
        assert_recommendation_supported,
    )
    from ugavi.tendering.doctype.standstill_period.standstill_period import get_open_standstill

    issues = []
    expected = {
        "Field Motorcycles Peace Building USAID": "Standstill Period",
        "Livestock Galla Goats USAID": "Under Evaluation",
    }
    for title, status in expected.items():
        tender = frappe.db.get_value("Tender", {"title": title}, ["name", "status"], as_dict=True)
        label = f"Evaluation journey {title}"
        if not tender:
            issues.append(f"{label}: missing tender")
            continue
        if not frappe.db.exists("Bid Opening Record", {"tender": tender.name}):
            issues.append(f"{label}: no three-officer opening record")
        if frappe.db.count("COI Declaration", {"tender": tender.name, "has_conflict": "No"}) < 3:
            issues.append(f"{label}: committee COI declarations incomplete")
        if not approved_minutes(tender.name):
            issues.append(f"{label}: no approved evaluation minutes")
        recommendation = approved_recommendation(tender.name)
        if not recommendation:
            issues.append(f"{label}: no approved recommendation")
        else:
            try:
                assert_recommendation_supported(
                    tender.name, recommendation.recommended_bidder,
                    recommendation.recommended_amount,
                )
            except frappe.ValidationError as exc:
                issues.append(f"{label}: recommendation not supported by evidence ({exc})")
        if tender.status != status:
            issues.append(f"{label}: expected {status}, found {tender.status}")
        standstill = get_open_standstill(tender.name)
        if status == "Standstill Period":
            end_date = standstill and frappe.db.get_value("Standstill Period", standstill, "end_date")
            if not end_date or getdate(end_date) < getdate(today()):
                issues.append(f"{label}: complaint window is not open")
        elif standstill:
            issues.append(f"{label}: standstill started before the live scene")
    return issues


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
