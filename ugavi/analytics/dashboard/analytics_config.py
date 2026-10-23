"""Analytics dashboard configuration (W11).

Role-based dashboards with number cards and scheduled reports.
"""
import frappe
from frappe import _


DASHBOARD_CONFIG = {
    "System Manager": {
        "name": "System Overview",
        "cards": [
            {"label": "Open POs", "query": "count_purchase_orders_by_status",
             "args": {"status": "Submitted"}},
            {"label": "Pending Approvals",
             "query": "count_documents_pending_approval"},
            {"label": "Total Suppliers",
             "query": "count_suppliers"},
            {"label": "Active Contracts",
             "query": "count_contracts_by_status",
             "args": {"status": "Active"}},
            {"label": "Overdue Payments",
             "query": "count_overdue_purchase_invoices"},
            {"label": "Open RFQs",
             "query": "count_request_for_quotations_by_status",
             "args": {"status": "Open"}},
            {"label": "Total Items", "query": "count_items"},
            {"label": "Warehouse Stock Value",
             "query": "sum_stock_balance_value"},
            {"label": "Donor Pipeline (KES)",
             "query": "sum_donor_budget_commitments"},
            {"label": "Pending Complaints",
             "query": "count_complaints_by_status",
             "args": {"status": "Open"}},
        ],
        "scheduled_reports": [
            {"label": "Monthly Procurement Summary",
             "frequency": "Monthly",
             "recipients": ["admin@ugavi.org"]},
            {"label": "Weekly Burn-rate Snapshot",
             "frequency": "Weekly",
             "recipients": ["admin@ugavi.org", "finance@ugavi.org"]},
            {"label": "Daily PO Status", "frequency": "Daily",
             "recipients": ["warehouse@ugavi.org"]},
        ],
    },
    "Procurement Manager": {
        "name": "Procurement Dashboard",
        "cards": [
            {"label": "Open POs", "query": "count_purchase_orders_by_status",
             "args": {"status": "Submitted"}},
            {"label": "Open RFQs",
             "query": "count_request_for_quotations_by_status",
             "args": {"status": "Open"}},
            {"label": "Pending Approvals",
             "query": "count_documents_pending_approval"},
            {"label": "Active Contracts",
             "query": "count_contracts_by_status",
             "args": {"status": "Active"}},
            {"label": "Total Suppliers",
             "query": "count_suppliers"},
            {"label": "Overdue Payments",
             "query": "count_overdue_purchase_invoices"},
        ],
        "scheduled_reports": [],
    },
    "Stock User": {
        "name": "Inventory Dashboard",
        "cards": [
            {"label": "Total Items", "query": "count_items"},
            {"label": "Warehouse Stock Value",
             "query": "sum_stock_balance_value"},
            {"label": "Pending Stock Entries",
             "query": "count_stock_entries_by_status",
             "args": {"status": "Draft"}},
            {"label": "Open POs",
             "query": "count_purchase_orders_by_status",
             "args": {"status": "Submitted"}},
        ],
        "scheduled_reports": [],
    },
    "Finance Manager": {
        "name": "Finance Dashboard",
        "cards": [
            {"label": "Overdue Payments",
             "query": "count_overdue_purchase_invoices"},
            {"label": "Donor Pipeline (KES)",
             "query": "sum_donor_budget_commitments"},
            {"label": "Total Budget (KES)",
             "query": "sum_donor_budget_amount"},
            {"label": "Pending Approvals",
             "query": "count_documents_pending_approval"},
            {"label": "Open POs",
             "query": "count_purchase_orders_by_status",
             "args": {"status": "Submitted"}},
        ],
        "scheduled_reports": [
            {"label": "Weekly Burn-rate Snapshot",
             "frequency": "Weekly",
             "recipients": ["finance@ugavi.org"]},
        ],
    },
    "Auditor": {
        "name": "Audit Dashboard",
        "cards": [
            {"label": "Pending Complaints",
             "query": "count_complaints_by_status",
             "args": {"status": "Open"}},
            {"label": "Total Suppliers",
             "query": "count_suppliers"},
            {"label": "Open POs",
             "query": "count_purchase_orders_by_status",
             "args": {"status": "Submitted"}},
            {"label": "Overdue Payments",
             "query": "count_overdue_purchase_invoices"},
        ],
        "scheduled_reports": [],
    },
}


def get_dashboard_config(user_roles=None):
    """Return dashboard config for the given user roles."""
    user_roles = user_roles or frappe.get_roles()
    for role in ["System Manager", "Procurement Manager",
                 "Stock User", "Finance Manager", "Auditor"]:
        if role in user_roles:
            return DASHBOARD_CONFIG.get(role, {})
    return {"name": "Default Dashboard",
            "cards": DASHBOARD_CONFIG["Procurement Manager"]["cards"],
            "scheduled_reports": []}


@frappe.whitelist()
def get_dashboard(user_roles=None):
    return get_dashboard_config(user_roles)