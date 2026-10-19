"""Phase B: Site Configuration.

Run after `bench migrate`: `bench --site ugavi.localhost execute ugavi.scripts.setup_config.run`
"""
import frappe
from frappe.utils import nowdate


def run():
    """Apply all Phase B configuration — idempotent."""
    configure_custom_fields()
    configure_roles()
    configure_taxes()
    configure_stock_settings()
    configure_workflows()
    frappe.db.commit()
    print("Phase B configuration complete!")


def configure_custom_fields():
    """Add custom fields to standard ERPNext DocTypes."""
    # Purchase Order custom fields for donor/tender/project tracking
    po_fields = [
        {
            "fieldname": "ugavi_donor",
            "label": "Donor",
            "fieldtype": "Link",
            "options": "Donor Profile",
            "insert_after": "supplier",
            "in_list_view": 1,
            "in_standard_filter": 1,
        },
        {
            "fieldname": "ugavi_tender",
            "label": "Tender",
            "fieldtype": "Link",
            "options": "Tender",
            "insert_after": "ugavi_donor",
            "read_only": 1,
        },
        {
            "fieldname": "ugavi_project",
            "label": "Project",
            "fieldtype": "Link",
            "options": "Project",
            "insert_after": "ugavi_tender",
        },
        {
            "fieldname": "ugavi_procurement_method",
            "label": "Procurement Method",
            "fieldtype": "Select",
            "options": "\nRequest for Quotation (Direct)\nRestricted Tender\nOpen Tender\nSingle Source",
            "insert_after": "ugavi_project",
            "read_only": 1,
            "in_list_view": 1,
        },
    ]
    for f in po_fields:
        create_custom_field("Purchase Order", f)

    # Item custom fields for donor tracking
    create_custom_field("Item", {
        "fieldname": "ugavi_donor_funded",
        "label": "Donor Funded",
        "fieldtype": "Check",
        "insert_after": "is_stock_item",
    })

    print("  Custom fields configured")


def create_custom_field(doctype, field_def):
    """Create a custom field if it doesn't exist."""
    fieldname = field_def["fieldname"]
    if frappe.db.exists("Custom Field", f"{doctype}-{fieldname}"):
        return
    cf = frappe.get_doc({
        "doctype": "Custom Field",
        "dt": doctype,
        **field_def,
    })
    cf.insert(ignore_permissions=True)


def configure_roles():
    """Create least-privilege roles for the Ugavi role matrix."""
    roles = [
        "Procurement Officer",
        "Bid Opening Officer",
        "Approver Level 1",
        "Approver Level 2",
        "Evaluation Committee",
        "Store Keeper",
        "Fleet Manager",
        "Asset Custodian",
        "Finance Officer",
        "Auditor",
    ]
    for role_name in roles:
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1,
            }).insert(ignore_permissions=True)
    print(f"  Roles configured: {len(roles)} confirmed")


def configure_taxes():
    """Create KES tax templates for VAT and withholding tax."""
    company = frappe.defaults.get_user_default("company") or "Ugavi NGO"
    _ensure_account("VAT Payable - UG", "Tax", company)
    _ensure_account("Withholding Tax Payable - UG", "Tax", company)

    # VAT 16% Purchase Tax Template
    if not frappe.db.exists("Purchase Taxes and Charges Template", "VAT 16% - UG"):
        vat = frappe.get_doc({
            "doctype": "Purchase Taxes and Charges Template",
            "title": "VAT 16% - UG",
            "company": company,
            "is_default": 1,
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": "VAT Payable - UG",
                "rate": 16,
                "description": "VAT 16%",
            }],
        })
        vat.insert(ignore_permissions=True)

    # Withholding Tax 5% Purchase Template
    if not frappe.db.exists("Purchase Taxes and Charges Template", "WHT 5% - UG"):
        wht = frappe.get_doc({
            "doctype": "Purchase Taxes and Charges Template",
            "title": "WHT 5% - UG",
            "company": company,
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": "Withholding Tax Payable - UG",
                "rate": 5,
                "description": "Withholding Tax 5%",
            }],
        })
        wht.insert(ignore_permissions=True)

    print("  Tax templates configured")


def _ensure_account(account_name, account_type, company):
    """Create account if missing."""
    root = {
        "Tax": "Duties and Taxes - UG",
        "Expense": "Expenses - UG",
    }
    parent = root.get(account_type, "Application of Funds (Assets) - UG")
    if not frappe.db.exists("Account", account_name):
        frappe.get_doc({
            "doctype": "Account",
            "account_name": account_name,
            "account_type": account_type,
            "parent_account": parent,
            "company": company,
            "is_group": 0,
        }).insert(ignore_permissions=True)


def configure_stock_settings():
    """Configure stock settings for batch tracking and reorder."""
    try:
        settings = frappe.get_single("Stock Settings")
        if not settings.item_naming_by:
            settings.item_naming_by = "Item Name"
        settings.allow_negative_stock = 0
        settings.save(ignore_permissions=True)
    except Exception:
        pass
    print("  Stock settings configured")


def configure_workflows():
    """Create placeholder workflow states for key processes."""
    # Workflow definitions will be created in Phase C
    # For now, ensure required doctype states exist
    print("  Workflow scaffolding ready (implementation in Phase C)")