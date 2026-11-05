"""Evaluation evidence used to authorize standstill and award decisions."""

import frappe
from frappe import _

SCORED_STATUSES = ("Submitted", "Reviewed")
OPENED_BID_STATUSES = ("Opened", "Evaluated", "Accepted")


def last_reevaluation(tender: str):
    """Datetime of the latest standstill resolved for re-evaluation, if any."""
    rows = frappe.get_all(
        "Standstill Period",
        filters={"tender": tender, "status": "Resolved", "resolution": "Re-evaluation Required"},
        fields=["resolved_date"],
        order_by="resolved_date desc",
        limit=1,
    )
    return rows[0].resolved_date if rows else None


def _since_reevaluation(tender: str) -> dict:
    since = last_reevaluation(tender)
    return {"creation": (">", since)} if since else {}


def score_ranking(tender: str) -> list[dict]:
    """Average submitted committee scores per opened bid, best first.

    Each row carries ``complete`` (every committee member scored the bid).
    """
    members = {
        row.user for row in frappe.get_doc("Tender", tender).evaluation_committee if row.user
    }
    bids = frappe.get_all(
        "Bid",
        filters={"tender": tender, "status": ("in", OPENED_BID_STATUSES)},
        fields=["name", "supplier", "bid_amount"],
    )
    scores = frappe.get_all(
        "Evaluation Score",
        filters={"tender": tender, "status": ("in", SCORED_STATUSES), **_since_reevaluation(tender)},
        fields=["bid", "evaluator", "weighted_total"],
    )
    ranking = []
    for bid in bids:
        rows = [row for row in scores if row.bid == bid.name and row.evaluator in members]
        evaluators = {row.evaluator for row in rows}
        ranking.append({
            "bid": bid.name,
            "supplier": bid.supplier,
            "bid_amount": bid.bid_amount,
            "average": round(sum(row.weighted_total or 0 for row in rows) / len(rows), 2) if rows else 0,
            "complete": bool(members) and members <= evaluators,
        })
    return sorted(ranking, key=lambda row: (-row["average"], row["bid_amount"]))


def approved_minutes(tender: str) -> str | None:
    return frappe.db.get_value(
        "Evaluation Minutes",
        {"tender": tender, "status": "Approved", **_since_reevaluation(tender)},
        "name",
        order_by="approved_at desc",
    )


def approved_recommendation(tender: str) -> dict | None:
    """Latest approved Bid Evaluation Summary after any re-evaluation."""
    return frappe.db.get_value(
        "Bid Evaluation Summary",
        {"tender": tender, "status": "Approved", **_since_reevaluation(tender)},
        ["name", "recommended_bidder", "recommended_bid", "recommended_amount"],
        as_dict=True,
        order_by="approved_at desc",
    )


def assert_recommendation_supported(tender: str, supplier: str, amount: float) -> dict:
    """Validate a recommendation against governance and committee scoring evidence."""
    from ugavi.tendering.doctype.coi_declaration.coi_declaration import check_coi_compliance

    compliance = check_coi_compliance(tender)
    if not compliance["compliant"]:
        frappe.throw(
            _("Evaluation governance is incomplete. Pending declarations: {0}; conflicted members: {1}.").format(
                ", ".join(compliance["pending"]) or _("None"),
                ", ".join(compliance["conflicted"]) or _("None"),
            )
        )
    if not approved_minutes(tender):
        frappe.throw(_("Approved evaluation minutes are required for tender {0}.").format(tender))

    ranking = score_ranking(tender)
    if not ranking:
        frappe.throw(_("Tender {0} has no opened bids to recommend.").format(tender))
    incomplete = [row["bid"] for row in ranking if not row["complete"]]
    if incomplete:
        frappe.throw(
            _("Every committee member must submit a score for each opened bid. Missing: {0}").format(
                ", ".join(incomplete)
            )
        )
    selected = next((row for row in ranking if row["supplier"] == supplier), None)
    if not selected:
        frappe.throw(_("{0} has no opened bid on tender {1}.").format(supplier, tender))
    if abs(float(amount or 0) - float(selected["bid_amount"] or 0)) > 0.01:
        frappe.throw(_("The recommended amount must equal the opened bid amount."))
    if selected["bid"] != ranking[0]["bid"]:
        frappe.throw(
            _("{0} is not the highest-ranked bid by committee scores ({1}).").format(
                supplier, ranking[0]["supplier"]
            )
        )
    return selected
