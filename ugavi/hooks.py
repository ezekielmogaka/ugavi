# Ugavi - Enterprise SCM for ERPNext
# hooks.py — All supported Frappe extension points

app_name = "ugavi"
app_title = "Ugavi SCM"
app_publisher = "Ugavi Team"
app_description = "Enterprise Supply Chain Management"
app_email = "info@ugavi.dev"
app_license = "MIT"

# ---- DocType Events ----
doc_events = {
    "Purchase Order": {
        "validate": "ugavi.procurement.services.purchase_order.validate_purchase_order",
        "on_submit": "ugavi.procurement.services.purchase_order.on_submit_po",
    },
    "Purchase Receipt": {
        "on_submit": "ugavi.logistics.services.grn.on_submit_grn",
        "validate": "ugavi.logistics.services.grn.validate_donor_stock",
    },
    "Stock Entry": {
        "validate": "ugavi.logistics.services.stock_entry.validate_donor_segregation",
    },
    "Supplier": {
        "validate": "ugavi.procurement.services.supplier.validate_supplier",
        "on_update": "ugavi.procurement.services.supplier.on_update_supplier",
    },
    "Purchase Invoice": {
        "validate": "ugavi.compliance.services.three_way_match.validate_three_way",
    },
}

# ---- Scheduled Tasks ----
scheduler_events = {
    "daily": [
        "ugavi.procurement.services.prequalification.check_expiry",
        "ugavi.fleet.services.vehicle.check_alerts",
    ],
    "monthly": [
        "ugavi.logistics.services.monthly_report.generate_reports",
    ],
}

# ---- Override Doctype Classes ----
override_doctype_class = {
    "Purchase Order": "ugavi.procurement.doctype.purchase_order.purchase_order.CustomPurchaseOrder",
}

# ---- Whitelisted Methods ----
override_whitelisted_methods = {
    "erpnext.stock.doctype.stock_entry.stock_entry.get_warehouse_details": "ugavi.logistics.services.stock_entry.get_donor_warehouse_details",
}

# ---- Fixtures ----
fixtures = [
    {"dt": "Custom Field", "filters": [["module", "in", ["Ugavi"]]]},
    {"dt": "Property Setter", "filters": [["module", "in", ["Ugavi"]]]},
    {"dt": "Role", "filters": [["name", "in", [
        "Procurement Officer", "Bid Opening Officer", "Store Keeper",
        "Fleet Manager", "Auditor", "Supplier Portal User",
        "Program Staff", "Approver Level 1", "Approver Level 2",
        "Evaluation Committee Member"
    ]]]},
    {"dt": "Workflow", "filters": [["name", "in", [
        "Purchase Requisition Approval", "Tender Management",
        "Bid Opening Process", "Bid Evaluation", "Award Approval",
        "Supplier Prequalification", "Contract Approval",
        "Asset Disposal", "Vehicle Allocation"
    ]]]},
]

# ---- Website / Portal ----
website_route_rules = [
    {"from_route": "/supplier-portal", "to_route": "supplier_portal"},
]

# ---- Jinja Environment ----
jinja = {
    "methods": [
        "ugavi.utils.format_kes",
        "ugavi.utils.get_donor_name",
    ],
}