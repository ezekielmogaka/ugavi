# Ugavi — Enterprise SCM for ERPNext
app_name = "ugavi"
app_title = "Ugavi SCM"
app_publisher = "Ugavi Team"
app_description = "Enterprise Supply Chain Management"
app_email = "info@ugavi.dev"
app_license = "MIT"

# DocTypes registered in this app
doctype_js = {
    "Purchase Requisition": "procurement/doctype/purchase_requisition/purchase_requisition.js",
    "Supplier Prequalification": "procurement/doctype/supplier_prequalification/supplier_prequalification.js",
    "Tender": "tendering/doctype/tender/tender.js",
    "Bid": "procurement/doctype/bid/bid.js",
    "Bid Opening Record": "procurement/doctype/bid_opening_record/bid_opening_record.js",
}

# DocType event hooks
doc_events = {
    "Purchase Requisition": {
        "validate": "ugavi.procurement.doctype.purchase_requisition.purchase_requisition.validate",
    },
    "Supplier Prequalification": {
        "validate": "ugavi.procurement.doctype.supplier_prequalification.supplier_prequalification.validate",
    },
    "Tender": {
        "validate": "ugavi.tendering.doctype.tender.tender.validate",
    },
    "Bid": {
        "validate": "ugavi.procurement.doctype.bid.bid.validate",
    },
}

# Scheduler events for automated tasks
scheduler_events = {
    "daily": [
        "ugavi.procurement.services.rules_engine.check_expiring_prequalifications",
    ],
    "monthly": [
        "ugavi.logistics.services.stock_report.generate_monthly_reports",
    ],
}

# Fixtures to install on app install
fixtures = [
    {"doctype": "Role", "filters": [["name", "in", ["Procurement Officer", "Bid Opening Officer", "Approver Level 1", "Approver Level 2", "Evaluation Committee"]]]},
]

website_route_rules = []

# Override standard ERPNext hooks
override_doctype_class = {
    "Purchase Requisition": "ugavi.procurement.doctype.purchase_requisition.purchase_requisition.PurchaseRequisition",
}