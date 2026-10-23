"""ERPNext purchasing event integrations."""

import frappe
from frappe import _


def validate_purchase_receipt(doc, method=None):
    validate_receiver_separation(doc, method)
    validate_required_quality_inspections(doc, method)


def validate_receiver_separation(doc, method=None):
    """Prevent the PR requester from receiving their own procurement."""
    purchase_orders = {
        item.purchase_order for item in doc.items if getattr(item, "purchase_order", None)
    }
    for purchase_order in purchase_orders:
        requisition = frappe.db.get_value("Purchase Order", purchase_order, "ugavi_pr")
        requester = (
            frappe.db.get_value("Purchase Requisition", requisition, "requester")
            if requisition
            else None
        )
        if requester and requester == frappe.session.user:
            frappe.throw(_("The requisition requester cannot receive the same purchase"))


def validate_required_quality_inspections(doc, method=None):
    """Require submitted native ERPNext inspections for flagged PO rows."""
    for item in doc.items:
        if not item.purchase_order_item:
            continue
        inspection_required = frappe.db.get_value(
            "Purchase Order Item",
            item.purchase_order_item,
            "ugavi_inspection_required",
        )
        if not inspection_required:
            continue
        if not item.quality_inspection:
            frappe.throw(
                _("Quality inspection is required for item {0}.").format(
                    item.item_code
                )
            )
        if frappe.db.get_value(
            "Quality Inspection", item.quality_inspection, "docstatus"
        ) != 1:
            frappe.throw(
                _("Quality inspection {0} must be submitted.").format(
                    item.quality_inspection
                )
            )


def create_supplier_evaluation(doc, method=None):
    """Create one pending performance evaluation for each submitted receipt."""
    from ugavi.compliance.doctype.budget_encumbrance.budget_encumbrance import (
        release_for_purchase_receipt,
    )

    release_for_purchase_receipt(doc)
    if frappe.db.exists("Ugavi Supplier Evaluation", {"purchase_receipt": doc.name}):
        return
    frappe.get_doc(
        {
            "doctype": "Ugavi Supplier Evaluation",
            "supplier": doc.supplier,
            "purchase_receipt": doc.name,
            "evaluation_date": frappe.utils.today(),
            "status": "Pending",
        }
    ).insert(ignore_permissions=True)


def create_direct_invoice_evaluation(doc, method=None):
    """Create an evaluation for purchases invoiced without a receipt."""
    if any(item.pr_detail for item in doc.items):
        return
    if frappe.db.exists(
        "Ugavi Supplier Evaluation", {"purchase_invoice": doc.name}
    ):
        return
    frappe.get_doc(
        {
            "doctype": "Ugavi Supplier Evaluation",
            "supplier": doc.supplier,
            "purchase_invoice": doc.name,
            "evaluation_date": frappe.utils.today(),
            "status": "Pending",
        }
    ).insert(ignore_permissions=True)


def validate_supplier_evaluation_before_payment(doc, method=None):
    """Do not pay a supplier until each referenced purchase is evaluated."""
    if doc.payment_type != "Pay" or doc.party_type != "Supplier":
        return
    for reference in doc.references:
        if reference.reference_doctype != "Purchase Invoice":
            continue
        invoice = frappe.get_doc("Purchase Invoice", reference.reference_name)
        receipts = {
            frappe.db.get_value("Purchase Receipt Item", item.pr_detail, "parent")
            for item in invoice.items
            if item.pr_detail
        }
        if receipts:
            for receipt in receipts:
                status = frappe.db.get_value(
                    "Ugavi Supplier Evaluation",
                    {"purchase_receipt": receipt},
                    "status",
                )
                if status != "Completed":
                    frappe.throw(
                        _("Complete supplier evaluation for receipt {0} before payment.").format(
                            receipt
                        )
                    )
        else:
            status = frappe.db.get_value(
                "Ugavi Supplier Evaluation",
                {"purchase_invoice": invoice.name},
                "status",
            )
            if status != "Completed":
                frappe.throw(
                    _("Complete supplier evaluation for invoice {0} before payment.").format(
                        invoice.name
                    )
                )
