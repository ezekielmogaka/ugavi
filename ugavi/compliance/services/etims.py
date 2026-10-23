"""eTIMS integration stub (W12).

Placeholder for Kenya Revenue Authority eTIMS integration.
Real implementation requires KRA-issued API credentials.
"""
import frappe
from frappe import _


@frappe.whitelist()
def submit_invoice_to_etims(sales_invoice_name):
    """Submit an invoice to eTIMS. Placeholder — real impl requires KRA API."""
    doc = frappe.get_doc("Sales Invoice", sales_invoice_name)
    frappe.msgprint(
        _("eTIMS integration not yet configured. "
          "Invoice {0} saved locally only.").format(doc.name),
        indicator="orange"
    )
    return {"status": "pending", "invoice": doc.name,
            "etims_reference": None, "message": "eTIMS stub — configure KRA credentials"}


@frappe.whitelist()
def check_etims_status(sales_invoice_name):
    """Check eTIMS status for an invoice. Stub."""
    return {"status": "not_configured",
            "invoice": sales_invoice_name,
            "message": "eTIMS integration requires KRA API credentials."}


@frappe.whitelist()
def cancel_etims_invoice(sales_invoice_name, reason=""):
    """Cancel an eTIMS invoice. Stub."""
    return {"status": "not_configured",
            "invoice": sales_invoice_name,
            "message": "eTIMS integration requires KRA API credentials."}


def get_etims_config():
    """Return eTIMS configuration singleton."""
    return frappe.get_single("Ugavi Settings")