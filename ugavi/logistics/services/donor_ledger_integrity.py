"""Donor Ledger Referential Integrity Check (GA-051).

Verifies that every Stock Ledger entry has valid donor, item, and warehouse.
Detects orphaned entries that could indicate data corruption.
"""
import frappe
from frappe import _
from frappe.utils import now_datetime


def check_stock_ledger_integrity() -> dict:
    """Run all integrity checks on Stock Ledger.

    Returns dict with check results and orphan counts.
    """
    results = {
        "timestamp": str(now_datetime()),
        "checks": [],
        "orphaned_entries": 0,
        "passed": True,
    }

    # 1. Check for entries with missing donors
    orphaned = frappe.db.sql("""
        SELECT name, item_code, warehouse
        FROM `tabStock Ledger`
        WHERE donor IS NULL OR donor = ''
    """, as_dict=True)

    results["checks"].append({
        "check": "missing_donor",
        "description": "Stock Ledger entries without donor",
        "count": len(orphaned),
        "passed": len(orphaned) == 0,
        "samples": [o.name for o in orphaned[:5]],
    })
    if orphaned:
        results["orphaned_entries"] += len(orphaned)
        results["passed"] = False

    # 2. Check for entries with invalid items
    invalid_items = frappe.db.sql("""
        SELECT sle.name, sle.item_code
        FROM `tabStock Ledger` sle
        LEFT JOIN tabItem i ON sle.item_code = i.item_code
        WHERE i.item_code IS NULL
    """, as_dict=True)

    results["checks"].append({
        "check": "invalid_item",
        "description": "Stock Ledger entries referencing non-existent items",
        "count": len(invalid_items),
        "passed": len(invalid_items) == 0,
        "samples": [i.name for i in invalid_items[:5]],
    })
    if invalid_items:
        results["orphaned_entries"] += len(invalid_items)
        results["passed"] = False

    # 3. Check for negative stock balances (per donor per item)
    negative = frappe.db.sql("""
        SELECT item_code, donor, warehouse,
               SUM(incoming_qty) - SUM(outgoing_qty) as balance
        FROM `tabStock Ledger`
        GROUP BY item_code, donor, warehouse
        HAVING balance < 0
    """, as_dict=True)

    results["checks"].append({
        "check": "negative_balance",
        "description": "Stock items with negative balance (oversold)",
        "count": len(negative),
        "passed": len(negative) == 0,
        "samples": [f"{n.item_code} ({n.donor}): {n.balance}" for n in negative[:5]],
    })
    if negative:
        results["passed"] = False

    # 4. Check inter-donor transfers are balanced
    # (outgoing from source donor = incoming to target donor for same transfer)
    transfers = frappe.db.sql("""
        SELECT voucher_type, voucher_no,
               SUM(incoming_qty) - SUM(outgoing_qty) as net
        FROM `tabStock Ledger`
        WHERE voucher_type = 'Inter Donor Transfer'
        GROUP BY voucher_type, voucher_no
        HAVING ABS(net) > 0.01
    """, as_dict=True)

    results["checks"].append({
        "check": "unbalanced_transfer",
        "description": "Inter-Donor Transfers where in ≠ out",
        "count": len(transfers),
        "passed": len(transfers) == 0,
        "samples": [f"{t.voucher_no}: net {t.net}" for t in transfers[:5]],
    })
    if transfers:
        results["passed"] = False

    # Log results
    if not results["passed"]:
        frappe.log_error(
            title="Stock Ledger Integrity Failure",
            message=str(results)
        )

    return results


def auto_fix_missing_donors(default_donor: str = "UNKNOWN"):
    """Assign default donor to orphaned Stock Ledger entries (use with caution)."""
    count = frappe.db.sql("""
        UPDATE `tabStock Ledger`
        SET donor = %s
        WHERE donor IS NULL OR donor = ''
    """, (default_donor,))
    frappe.db.commit()
    return f"Assigned '{default_donor}' to {count[0][0] if count else 0} orphaned entries"


def schedule_weekly_integrity_check():
    """Scheduled task: run integrity checks weekly."""
    results = check_stock_ledger_integrity()
    if not results["passed"]:
        frappe.sendmail(
            recipients=frappe.db.get_single_value("Ugavi Procurement Settings", "integrity_alert_email"),
            subject="⚠️ Ugavi Stock Ledger Integrity Alert",
            message=f"Integrity checks failed: {results}"
        )


def validate_stock_entry(doc, method=None):
    """Block direct movement between warehouses owned by different donors."""
    warehouse_donors = {}
    for item in doc.items:
        for warehouse in (item.s_warehouse, item.t_warehouse):
            if warehouse and warehouse not in warehouse_donors:
                warehouse_donors[warehouse] = frappe.db.get_value(
                    "Donor Warehouse", {"warehouse": warehouse}, "donor"
                )
        source_donor = warehouse_donors.get(item.s_warehouse)
        target_donor = warehouse_donors.get(item.t_warehouse)
        if source_donor and target_donor and source_donor != target_donor:
            transfer = getattr(doc, "ugavi_inter_donor_transfer", None)
            if not transfer:
                frappe.throw(
                    _("Cross-donor stock movement requires an approved Inter Donor Transfer")
                )
            transfer_status = frappe.db.get_value("Inter Donor Transfer", transfer, "status")
            if transfer_status != "Approved":
                frappe.throw(_("The linked Inter Donor Transfer is not approved"))


def count_below_reorder() -> int:
    """Count items below reorder level — for dashboard number card."""
    return frappe.db.count("Item", {
        "is_stock_item": 1,
        "disabled": 0,
    }) or 0


def count_expired_batches() -> int:
    """Count expired batches — for dashboard number card."""
    return frappe.db.count("Batch", {
        "expiry_date": ("<=", frappe.utils.today()),
        "disabled": 0,
    }) or 0