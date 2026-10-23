"""Prometheus metrics endpoint for Ugavi (GA-054).

Exposes application-level metrics at /api/method/ugavi.metrics.get_metrics
for Prometheus scraping.

Metrics exposed:
    ugavi_bids_submitted_total         Counter   Total bid submissions
    ugavi_bids_opened_total            Counter   Total successful bid openings
    ugavi_prs_created_total            Counter   Total purchase requisitions
    ugavi_stock_movements_total        Counter   Total stock ledger entries
    ugavi_rate_limit_hits_total        Counter   Rate limiter rejections
    ugavi_sealed_bid_errors_total      Counter   Crypto operation failures
    ugavi_active_tenders               Gauge     Currently open tenders
    ugavi_suppliers_prequalified       Gauge     Active prequalified suppliers
    ugavi_pending_approvals            Gauge     PRs awaiting approval
"""
from prometheus_client import CollectorRegistry, Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
import frappe

REGISTRY = CollectorRegistry()

bids_submitted = Counter(
    "ugavi_bids_submitted_total", "Total bid submissions", registry=REGISTRY
)
bids_opened = Counter(
    "ugavi_bids_opened_total", "Total successful bid openings", registry=REGISTRY
)
prs_created = Counter(
    "ugavi_prs_created_total", "Total purchase requisitions", registry=REGISTRY
)
stock_movements = Counter(
    "ugavi_stock_movements_total", "Total stock ledger entries", registry=REGISTRY
)
rate_limit_hits = Counter(
    "ugavi_rate_limit_hits_total", "Rate limiter rejections", registry=REGISTRY
)
crypto_errors = Counter(
    "ugavi_sealed_bid_errors_total", "Crypto operation failures", registry=REGISTRY
)

active_tenders = Gauge(
    "ugavi_active_tenders", "Currently open tenders", registry=REGISTRY
)
suppliers_prequalified = Gauge(
    "ugavi_suppliers_prequalified", "Active prequalified suppliers", registry=REGISTRY
)
pending_approvals = Gauge(
    "ugavi_pending_approvals", "PRs awaiting approval", registry=REGISTRY
)


@frappe.whitelist(allow_guest=True)
def get_metrics():
    """Prometheus metrics endpoint — returns text/plain metrics."""
    try:
        active_tenders.set(
            frappe.db.count("Tender", {"status": "Published"})
        )
        suppliers_prequalified.set(
            frappe.db.count("Supplier Prequalification",
                            {"status": "Approved", "docstatus": 1})
        )
        pending_approvals.set(
            frappe.db.count("Purchase Requisition",
                            {"status": "Pending Approval", "docstatus": 1})
        )
    except Exception:
        pass  # DB not available; return counters only

    metrics_data = generate_latest(REGISTRY)
    frappe.local.response.update({
        "http_status_code": 200,
        "content_type": CONTENT_TYPE_LATEST,
        "body": metrics_data,
    })
    return frappe.local.response


def record_bid_submitted():
    """Increment bid submission counter (call from Bid controller)."""
    bids_submitted.inc()


def record_bid_opened():
    """Increment successful bid opening counter (call from BOR controller)."""
    bids_opened.inc()


def record_pr_created():
    """Increment PR creation counter."""
    prs_created.inc()


def record_stock_movement():
    """Increment stock ledger entry counter."""
    stock_movements.inc()


def record_rate_limit_hit():
    """Increment rate limiter rejection counter."""
    rate_limit_hits.inc()


def record_crypto_error():
    """Increment crypto operation failure counter."""
    crypto_errors.inc()