# Ugavi — Enterprise SCM for ERPNext
app_name = "ugavi"
app_title = "Ugavi SCM"
app_publisher = "Ugavi Team"
app_description = "Enterprise Supply Chain Management"
app_email = "info@ugavi.dev"
app_license = "MIT"

# DocTypes registered in this app
doctype_js = {
    "Purchase Requisition": "js/purchase_requisition.js",
    "Supplier Prequalification": "js/supplier_prequalification.js",
    "Tender": "js/tender.js",
    "Bid": "js/bid.js",
    "Bid Opening Record": "js/bid_opening_record.js",
    "Bid Evaluation Summary": "js/bid_evaluation_summary.js",
    "Evaluation Minutes": "js/evaluation_minutes.js",
    "Evaluation Score": "js/evaluation_score.js",
}

# Cross-DocType integrations with ERPNext-owned transactions.
doc_events = {
    "*": {
        "before_trash": "ugavi.governance.services.retention.enforce_record_disposal",
    },
    "Purchase Receipt": {
        "validate": "ugavi.procurement.events.validate_purchase_receipt",
        "before_cancel": "ugavi.fleet.services.purchase_reconciliation.prevent_source_cancellation",
        "on_submit": [
            "ugavi.procurement.events.create_supplier_evaluation",
            "ugavi.fleet.services.purchase_reconciliation.create_for_purchase_receipt",
        ],
        "on_cancel": "ugavi.fleet.services.purchase_reconciliation.cancel_source_reconciliations",
    },
    "Purchase Invoice": {
        "before_cancel": "ugavi.fleet.services.purchase_reconciliation.prevent_source_cancellation",
        "on_submit": [
            "ugavi.compliance.doctype.three_way_match.three_way_match.create_for_purchase_invoice",
            "ugavi.fleet.services.purchase_reconciliation.create_or_link_for_purchase_invoice",
            "ugavi.procurement.events.create_direct_invoice_evaluation",
        ],
        "on_cancel": "ugavi.fleet.services.purchase_reconciliation.cancel_source_reconciliations",
    },
    "Purchase Order": {
        "on_submit": [
            "ugavi.compliance.doctype.budget_encumbrance.budget_encumbrance.create_for_purchase_order",
            "ugavi.procurement.doctype.ugavi_contract.ugavi_contract.ensure_contract_for_purchase_order",
        ],
        "on_cancel": "ugavi.compliance.doctype.budget_encumbrance.budget_encumbrance.reverse_for_purchase_order",
    },
    "Stock Entry": {
        "validate": "ugavi.logistics.services.donor_ledger_integrity.validate_stock_entry",
    },
    "Payment Entry": {
        "validate": "ugavi.procurement.events.validate_supplier_evaluation_before_payment",
        "on_submit": [
            "ugavi.integrations.mpesa.queue_supplier_payment",
        ],
    },
}

# Scheduler events for automated tasks
scheduler_events = {
    "daily": [
        "ugavi.procurement.services.rules_engine.check_expiring_prequalifications",
        "ugavi.scripts.scheduled_tasks.check_contract_expiry",
        "ugavi.scripts.scheduled_tasks.check_vehicle_service_due",
        "ugavi.tendering.doctype.standstill_period.standstill_period.check_expired_standstills",
    ],
    "weekly": [
        "ugavi.scripts.scheduled_tasks.flag_inactive_suppliers",
        "ugavi.compliance.services.donor_report_scheduler.generate_scheduled_donor_reports",
    ],
    "monthly": [
        "ugavi.scripts.scheduled_tasks.generate_monthly_stock_reports",
        "ugavi.scripts.scheduled_tasks.generate_asset_verification_reminder",
        "ugavi.scripts.scheduled_tasks.generate_monthly_fleet_reports",
    ],
    "cron": {
        "0 3 1,15 * *": [
            "ugavi.scripts.scheduled_tasks.check_supplier_suspension",
        ],
    },
}

# Fixtures to install on app install
fixtures = [
    {"doctype": "Role", "filters": [["name", "in", ["Procurement Officer", "Bid Opening Officer", "Approver Level 1", "Approver Level 2", "Evaluation Committee"]]]},
]

website_route_rules = [
    {"from_route": "/supplier/portal", "to_route": "supplier/dashboard"},
]

get_website_user_home_page = (
    "ugavi.procurement.portal.supplier_portal.get_home_page"
)

# CSS theme injection
app_include_css = [
    "/assets/ugavi/css/ugavi-tokens.css",
    "/assets/ugavi/css/ugavi-theme.css",
    "/assets/ugavi/css/ugavi-components.css",
]

web_include_css = [
    "/assets/ugavi/css/ugavi-tokens.css",
    "/assets/ugavi/css/ugavi-components.css",
    "/assets/ugavi/css/ugavi-portal.css",
]