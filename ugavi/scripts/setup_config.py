"""Phase B: Site Configuration.

Run after `bench migrate`: `bench --site ugavi.localhost execute ugavi.scripts.setup_config.run`
"""
import os

import frappe
from frappe.utils import getdate, nowdate


def run():
    """Apply all Phase B configuration — idempotent."""
    configure_custom_fields()
    configure_roles()
    configure_fiscal_years()
    configure_procurement_settings()
    configure_taxes()
    configure_payment_modes()
    configure_stock_settings()
    configure_security()
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
            "fieldname": "ugavi_pr",
            "label": "Purchase Requisition",
            "fieldtype": "Link",
            "options": "Purchase Requisition",
            "insert_after": "ugavi_tender",
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
        {
            "fieldname": "ugavi_budget",
            "label": "Budget",
            "fieldtype": "Link",
            "options": "Budget",
            "insert_after": "ugavi_project",
        },
        {
            "fieldname": "ugavi_supplier_acknowledged",
            "label": "Supplier Acknowledged",
            "fieldtype": "Check",
            "insert_after": "ugavi_procurement_method",
            "read_only": 1,
        },
        {
            "fieldname": "ugavi_acknowledged_at",
            "label": "Acknowledged At",
            "fieldtype": "Datetime",
            "insert_after": "ugavi_supplier_acknowledged",
            "read_only": 1,
        },
    ]
    for f in po_fields:
        create_custom_field("Purchase Order", f)
    create_custom_field("Purchase Invoice", {
        "fieldname": "ugavi_supplier_invoice_file",
        "label": "Supplier Invoice File",
        "fieldtype": "Attach",
        "insert_after": "bill_date",
        "read_only": 1,
    })
    create_custom_field("Purchase Invoice", {
        "fieldname": "ugavi_submitted_from_portal",
        "label": "Submitted from Supplier Portal",
        "fieldtype": "Check",
        "insert_after": "ugavi_supplier_invoice_file",
        "read_only": 1,
    })
    create_custom_field("Payment Entry", {
        "fieldname": "ugavi_mpesa_status",
        "label": "M-Pesa Status",
        "fieldtype": "Select",
        "options": "\nNot Transmitted\nSent\nConfirmed\nFailed",
        "insert_after": "mode_of_payment",
        "read_only": 1,
    })
    create_custom_field("Payment Entry", {
        "fieldname": "ugavi_mpesa_conversation_id",
        "label": "M-Pesa Conversation ID",
        "fieldtype": "Data",
        "insert_after": "ugavi_mpesa_status",
        "read_only": 1,
    })
    create_custom_field("Budget", {
        "fieldname": "ugavi_donor",
        "label": "Donor",
        "fieldtype": "Link",
        "options": "Donor Profile",
        "insert_after": "fiscal_year",
        "in_standard_filter": 1,
    })
    create_custom_field("Purchase Order Item", {
        "fieldname": "ugavi_inspection_required",
        "label": "Quality Inspection Required",
        "fieldtype": "Check",
        "insert_after": "quality_inspection_template",
        "default": "0",
    })

    # Item custom fields for donor tracking
    create_custom_field("Item", {
        "fieldname": "ugavi_donor_funded",
        "label": "Donor Funded",
        "fieldtype": "Check",
        "insert_after": "is_stock_item",
    })
    create_custom_field("Item", {
        "fieldname": "ugavi_fleet_category",
        "label": "Fleet Purchase Category",
        "fieldtype": "Select",
        "options": "\nFuel\nSpare Part",
        "insert_after": "ugavi_donor_funded",
        "description": (
            "Fleet-classified receipt and invoice rows must be reconciled to "
            "vehicle consumption."
        ),
    })
    create_custom_field("Stock Entry", {
        "fieldname": "ugavi_inter_donor_transfer",
        "label": "Inter-Donor Transfer",
        "fieldtype": "Link",
        "options": "Inter Donor Transfer",
        "insert_after": "stock_entry_type",
        "read_only": 1,
    })
    vehicle_fields = [
        {
            "fieldname": "ugavi_donor",
            "label": "Donor",
            "fieldtype": "Link",
            "options": "Donor Profile",
            "insert_after": "company",
        },
        {
            "fieldname": "ugavi_project",
            "label": "Project",
            "fieldtype": "Link",
            "options": "Project",
            "insert_after": "ugavi_donor",
        },
        {
            "fieldname": "ugavi_warehouse",
            "label": "Assigned Warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "insert_after": "ugavi_project",
        },
        {
            "fieldname": "ugavi_total_fuel_litres",
            "label": "Total Fuel (Litres)",
            "fieldtype": "Float",
            "insert_after": "last_odometer",
            "read_only": 1,
        },
        {
            "fieldname": "ugavi_total_fuel_cost",
            "label": "Total Fuel Cost",
            "fieldtype": "Currency",
            "insert_after": "ugavi_total_fuel_litres",
            "read_only": 1,
        },
        {
            "fieldname": "ugavi_status",
            "label": "Fleet Status",
            "fieldtype": "Select",
            "options": "Active\nInactive\nUnder Repair\nDisposed",
            "insert_after": "ugavi_total_fuel_cost",
            "default": "Active",
        },
        {
            "fieldname": "ugavi_next_service_date",
            "label": "Next Service Date",
            "fieldtype": "Date",
            "insert_after": "ugavi_status",
        },
        {
            "fieldname": "ugavi_insurance_expiry",
            "label": "Insurance Expiry",
            "fieldtype": "Date",
            "insert_after": "ugavi_next_service_date",
        },
        {
            "fieldname": "ugavi_inspection_expiry",
            "label": "Inspection Expiry",
            "fieldtype": "Date",
            "insert_after": "ugavi_insurance_expiry",
        },
    ]
    for field in vehicle_fields:
        create_custom_field("Vehicle", field)
    create_custom_field("Stock Entry", {
        "fieldname": "ugavi_vehicle",
        "label": "Vehicle",
        "fieldtype": "Link",
        "options": "Vehicle",
        "insert_after": "ugavi_inter_donor_transfer",
        "read_only": 1,
    })
    create_custom_field("Stock Entry", {
        "fieldname": "ugavi_spare_parts_issue",
        "label": "Spare Parts Issue",
        "fieldtype": "Link",
        "options": "Spare Parts Issue",
        "insert_after": "ugavi_vehicle",
        "read_only": 1,
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
        "Procurement Manager",
        "Programme Manager",
        "Bid Opening Officer",
        "Approver Level 1",
        "Approver Level 2",
        "Evaluation Committee",
        "Store Keeper",
        "Stock Manager",
        "Fleet Manager",
        "Asset Manager",
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


def configure_procurement_settings():
    settings = frappe.get_single("Ugavi Procurement Settings")
    changed = False
    if not settings.standstill_days:
        settings.standstill_days = 14
        changed = True
    if not settings.complaint_response_days:
        settings.complaint_response_days = 7
        changed = True
    if changed:
        settings.save(ignore_permissions=True)
    print("  Procurement policy defaults configured")


def configure_taxes():
    """Create KES tax templates for VAT and withholding tax."""
    company = frappe.defaults.get_user_default("company") or frappe.db.get_value(
        "Company", {}, "name"
    )
    if not company:
        print("  Tax templates skipped until a company is seeded")
        return
    abbreviation = frappe.db.get_value("Company", company, "abbr")
    duties_account = f"Duties and Taxes - {abbreviation}"
    if not frappe.db.exists("Account", duties_account):
        print("  Tax templates skipped until the company chart of accounts exists")
        return

    # Ensure withholding tax account exists
    withholding_account = f"Withholding Tax - {abbreviation}"
    if not frappe.db.exists("Account", withholding_account):
        frappe.get_doc({
            "doctype": "Account",
            "account_name": "Withholding Tax",
            "account_type": "Tax",
            "parent_account": duties_account,
            "company": company,
            "is_group": 0,
        }).insert(ignore_permissions=True)

    vat_account = f"VAT Input - {abbreviation}"
    if not frappe.db.exists("Account", vat_account):
        frappe.get_doc({
            "doctype": "Account",
            "account_name": "VAT Input",
            "account_type": "Tax",
            "parent_account": duties_account,
            "company": company,
            "is_group": 0,
        }).insert(ignore_permissions=True)

    # VAT 16% Purchase Tax Template
    if not frappe.db.exists(
        "Purchase Taxes and Charges Template",
        {"title": "VAT 16% - UG", "company": company},
    ):
        vat = frappe.get_doc({
            "doctype": "Purchase Taxes and Charges Template",
            "title": "VAT 16% - UG",
            "company": company,
            "is_default": 0,
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": vat_account,
                "rate": 16,
                "description": "VAT 16%",
            }],
        })
        vat.insert(ignore_permissions=True)

    # Withholding Tax 5% Purchase Template
    if not frappe.db.exists(
        "Purchase Taxes and Charges Template",
        {"title": "WHT 5% - UG", "company": company},
    ):
        wht = frappe.get_doc({
            "doctype": "Purchase Taxes and Charges Template",
            "title": "WHT 5% - UG",
            "company": company,
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": withholding_account,
                "rate": 5,
                "description": "Withholding Tax 5%",
            }],
        })
        wht.insert(ignore_permissions=True)

    print("  Tax templates configured")


def configure_fiscal_years():
    """Ensure an active Fiscal Year covers today.

    ERPNext raises FiscalYearError for any accounting document posted outside a
    Fiscal Year, so a stale seed would block every invoice and payment.
    """
    today = getdate(nowdate())
    existing = frappe.db.sql(
        """SELECT name FROM `tabFiscal Year`
           WHERE disabled = 0 AND year_start_date <= %s AND year_end_date >= %s""",
        (today, today),
    )
    if existing:
        print(f"  Fiscal Year covering {today} already present")
        return

    last_year = frappe.db.get_value(
        "Fiscal Year", {"disabled": 0}, "year_end_date", order_by="year_end_date desc"
    )
    start_year = (getdate(last_year).year + 1) if last_year else today.year

    for year in range(start_year, today.year + 1):
        name = str(year)
        if frappe.db.exists("Fiscal Year", name):
            continue
        frappe.get_doc(
            {
                "doctype": "Fiscal Year",
                "year": name,
                "year_start_date": f"{year}-01-01",
                "year_end_date": f"{year}-12-31",
            }
        ).insert(ignore_permissions=True)
        print(f"  Fiscal Year {name} created")


def configure_payment_modes():
    for name, payment_type in (("Bank Transfer", "Bank"), ("M-Pesa", "Phone")):
        if frappe.db.exists("Mode of Payment", name):
            continue
        frappe.get_doc(
            {
                "doctype": "Mode of Payment",
                "mode_of_payment": name,
                "type": payment_type,
                "enabled": 1,
            }
        ).insert(ignore_permissions=True)
    print("  Bank Transfer and M-Pesa payment modes configured")


def configure_stock_settings():
    """Configure stock settings for batch tracking and reorder."""
    settings = frappe.get_single("Stock Settings")
    if not settings.item_naming_by:
        settings.item_naming_by = "Item Name"
    settings.allow_negative_stock = 0
    settings.save(ignore_permissions=True)
    print("  Stock settings configured")


def configure_security():
    """Enable Frappe-native TOTP only when explicitly requested by deployment."""
    if os.environ.get("UGAVI_ENFORCE_2FA") != "1":
        print("  TOTP enforcement not enabled (set UGAVI_ENFORCE_2FA=1 in production)")
        return
    settings = frappe.get_single("System Settings")
    settings.enable_two_factor_auth = 1
    settings.two_factor_method = "OTP App"
    settings.otp_issuer_name = "Ugavi SCM"
    settings.deny_multiple_sessions = 1
    settings.enable_password_policy = 1
    settings.minimum_password_score = "3"
    settings.logout_on_password_reset = 1
    settings.save(ignore_permissions=True)
    print("  Frappe TOTP and hardened session policy configured")


def configure_workflows():
    """Confirm the PR DocType is ready for its dynamic DoA state machine."""
    required_fields = {"status", "approval_history"}
    available_fields = {
        field.fieldname for field in frappe.get_meta("Purchase Requisition").fields
    }
    missing_fields = required_fields - available_fields
    if missing_fields:
        frappe.throw(
            "Purchase Requisition workflow fields are missing: "
            + ", ".join(sorted(missing_fields))
        )
    print("  Dynamic delegation-of-authority workflow configured")