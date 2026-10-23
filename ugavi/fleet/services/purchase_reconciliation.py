"""Fleet purchase intake and quantity reconciliation."""

import frappe
from frappe import _
from frappe.utils import flt


FLEET_CATEGORIES = {"Fuel", "Spare Part"}


def create_for_purchase_receipt(doc, method=None):
    """Create one immutable source record per submitted fleet receipt row."""
    for item in doc.items:
        category = _fleet_category(item.item_code)
        if category not in FLEET_CATEGORIES:
            continue
        donor = _source_donor(item.purchase_order, item.warehouse)
        values = {
            "fleet_category": category,
            "item_code": item.item_code,
            "donor": donor,
            "purchase_order": item.purchase_order,
            "purchase_order_item": item.purchase_order_item,
            "purchase_receipt": doc.name,
            "purchase_receipt_item": item.name,
            "warehouse": item.warehouse,
            "purchased_qty": item.stock_qty,
            "stock_uom": item.stock_uom,
            "valuation_rate": item.valuation_rate,
        }
        _ensure_reconciliation({"purchase_receipt_item": item.name}, values)


def create_or_link_for_purchase_invoice(doc, method=None):
    """Link invoice rows to receipt reconciliations or create direct-purchase rows."""
    for item in doc.items:
        category = _fleet_category(item.item_code)
        if category not in FLEET_CATEGORIES:
            continue
        if item.pr_detail:
            reconciliation = frappe.db.get_value(
                "Fleet Purchase Reconciliation",
                {"purchase_receipt_item": item.pr_detail, "status": ("!=", "Cancelled")},
                "name",
            )
            if reconciliation:
                frappe.db.set_value(
                    "Fleet Purchase Reconciliation",
                    reconciliation,
                    {
                        "purchase_invoice": doc.name,
                        "purchase_invoice_item": item.name,
                    },
                    update_modified=False,
                )
                continue

        donor = _source_donor(item.purchase_order, None)
        values = {
            "fleet_category": category,
            "item_code": item.item_code,
            "donor": donor,
            "purchase_order": item.purchase_order,
            "purchase_order_item": item.po_detail,
            "purchase_invoice": doc.name,
            "purchase_invoice_item": item.name,
            "purchased_qty": item.stock_qty,
            "stock_uom": item.stock_uom,
            "valuation_rate": item.base_rate,
        }
        _ensure_reconciliation({"purchase_invoice_item": item.name}, values)


def prevent_source_cancellation(doc, method=None):
    """Do not cancel a source document after quantities were assigned to vehicles."""
    source_field = (
        "purchase_receipt" if doc.doctype == "Purchase Receipt" else "purchase_invoice"
    )
    allocated = frappe.db.get_value(
        "Fleet Purchase Reconciliation",
        {source_field: doc.name, "allocated_qty": (">", 0)},
        "name",
    )
    if allocated:
        frappe.throw(
            _(
                "Cannot cancel {0}; fleet purchase reconciliation {1} has vehicle "
                "allocations. Cancel those fuel/spare records first."
            ).format(doc.name, allocated)
        )


def cancel_source_reconciliations(doc, method=None):
    source_field = (
        "purchase_receipt" if doc.doctype == "Purchase Receipt" else "purchase_invoice"
    )
    frappe.db.set_value(
        "Fleet Purchase Reconciliation",
        {source_field: doc.name},
        "status",
        "Cancelled",
        update_modified=False,
    )


def lock_and_validate_allocation(
    reconciliation_name, quantity, expected_category, item_code=None, donor=None
):
    """Serialize allocation and prevent category, donor, item, or quantity drift."""
    frappe.db.sql(
        """SELECT name FROM `tabFleet Purchase Reconciliation`
           WHERE name = %s FOR UPDATE""",
        reconciliation_name,
    )
    source = frappe.get_doc("Fleet Purchase Reconciliation", reconciliation_name)
    if source.status == "Cancelled":
        frappe.throw(_("Fleet purchase {0} is cancelled.").format(source.name))
    if source.fleet_category != expected_category:
        frappe.throw(
            _("Fleet purchase {0} is for {1}, not {2}.").format(
                source.name, source.fleet_category, expected_category
            )
        )
    if item_code and source.item_code != item_code:
        frappe.throw(
            _("Item {0} does not match fleet purchase item {1}.").format(
                item_code, source.item_code
            )
        )
    if donor and source.donor and donor != source.donor:
        frappe.throw(
            _("Donor {0} does not match fleet purchase donor {1}.").format(
                donor, source.donor
            )
        )
    if flt(quantity) <= 0:
        frappe.throw(_("Allocated quantity must be greater than zero."))
    allocated = get_allocated_quantity(source.name)
    if allocated + flt(quantity) > flt(source.purchased_qty) + 0.000001:
        frappe.throw(
            _(
                "Allocation exceeds purchased quantity for {0}. "
                "Purchased: {1}, already allocated: {2}, requested: {3}."
            ).format(
                source.name,
                source.purchased_qty,
                allocated,
                quantity,
            )
        )
    return source


def refresh_reconciliation(reconciliation_name):
    if not reconciliation_name or not frappe.db.exists(
        "Fleet Purchase Reconciliation", reconciliation_name
    ):
        return
    purchased = flt(
        frappe.db.get_value(
            "Fleet Purchase Reconciliation", reconciliation_name, "purchased_qty"
        )
    )
    allocated = get_allocated_quantity(reconciliation_name)
    remaining = max(0, purchased - allocated)
    if remaining <= 0.000001:
        status = "Reconciled"
    elif allocated > 0:
        status = "Partially Allocated"
    else:
        status = "Open"
    frappe.db.set_value(
        "Fleet Purchase Reconciliation",
        reconciliation_name,
        {
            "allocated_qty": allocated,
            "remaining_qty": remaining,
            "status": status,
        },
        update_modified=False,
    )


def get_allocated_quantity(reconciliation_name):
    fuel = frappe.db.sql(
        """SELECT COALESCE(SUM(litres), 0)
           FROM `tabFuel Log`
           WHERE source_reconciliation = %s AND docstatus = 1""",
        reconciliation_name,
    )[0][0]
    spares = frappe.db.sql(
        """SELECT COALESCE(SUM(i.quantity), 0)
           FROM `tabFleet Spare Part Item` i
           INNER JOIN `tabSpare Parts Issue` p ON p.name = i.parent
           WHERE i.source_reconciliation = %s
             AND i.parenttype = 'Spare Parts Issue'
             AND p.docstatus = 1""",
        reconciliation_name,
    )[0][0]
    return flt(fuel) + flt(spares)


def _ensure_reconciliation(filters, values):
    existing = frappe.db.exists("Fleet Purchase Reconciliation", filters)
    if existing:
        return existing
    doc = frappe.get_doc(
        {
            "doctype": "Fleet Purchase Reconciliation",
            **values,
            "allocated_qty": 0,
            "remaining_qty": values["purchased_qty"],
            "status": "Open",
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def _fleet_category(item_code):
    return frappe.get_cached_value("Item", item_code, "ugavi_fleet_category")


def _source_donor(purchase_order, warehouse):
    donor = None
    if purchase_order:
        donor = frappe.db.get_value("Purchase Order", purchase_order, "ugavi_donor")
    if warehouse:
        warehouse_donor = frappe.db.get_value(
            "Donor Warehouse", {"warehouse": warehouse}, "donor"
        )
        if donor and warehouse_donor and donor != warehouse_donor:
            frappe.throw(
                _(
                    "Purchase donor {0} does not match warehouse donor {1}."
                ).format(donor, warehouse_donor)
            )
        donor = donor or warehouse_donor
    return donor
