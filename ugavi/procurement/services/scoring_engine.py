"""Bid Evaluation Scoring Engine — weighted scoring for tender evaluation."""
import frappe
from frappe import _
from typing import List, Dict


def compute_weighted_score(bid_items: List[Dict], criteria: List[Dict]) -> Dict:
    """Compute weighted score for a bid.

    criteria = [{"name": "Price", "weight": 0.40}, {"name": "Technical", "weight": 0.35}, ...]

    Returns: {"total": 85.5, "breakdown": {"Price": 34.0, "Technical": 29.75, ...}}
    """
    if not criteria:
        return {"total": 0, "breakdown": {}}

    total = 0
    breakdown = {}
    weight_map = {c["name"]: c["weight"] for c in criteria}
    score_map = {item.get("criterion"): (item.get("score") or 0) for item in bid_items}

    for name, weight in weight_map.items():
        score = score_map.get(name, 0)
        weighted = score * weight
        breakdown[name] = round(weighted, 2)
        total += weighted

    return {"total": round(total, 2), "breakdown": breakdown}


def rank_bids(tender_id: str) -> List[Dict]:
    """Rank all submitted bids for a tender by weighted score."""
    from frappe.utils import flt

    # Get evaluation criteria from tender
    tender = frappe.get_doc("Tender", tender_id)
    criteria = []
    for criterion in tender.get("evaluation_criteria") or []:
        criteria.append({
            "name": criterion.get("criterion"),
            "weight": flt(criterion.get("weight")) / 100.0,
        })

    if not criteria:
        frappe.throw(_("No evaluation criteria defined for this tender"))

    # Get all submitted bids
    bids = frappe.get_all("Bid", filters={"tender": tender_id, "status": "Submitted"},
                          fields=["name", "supplier"])

    results = []
    for bid_info in bids:
        bid = frappe.get_doc("Bid", bid_info.name)
        items = []
        for child in bid.get("evaluation_scores") or []:
            items.append({
                "criterion": child.get("criterion"),
                "score": flt(child.get("score")),
            })
        score = compute_weighted_score(items, criteria)
        results.append({
            "bid": bid.name,
            "supplier": bid.supplier,
            "total_score": score["total"],
            "breakdown": score["breakdown"],
        })

    results.sort(key=lambda x: x["total_score"], reverse=True)
    return results


def get_bid_comparison_table(tender_id: str) -> List[Dict]:
    """Generate comparative bid summary table (EV4)."""
    ranked = rank_bids(tender_id)
    if not ranked:
        return []

    # Collect all criteria names
    criteria_names = list(ranked[0]["breakdown"].keys())

    rows = []
    for r in ranked:
        row = {
            "bid": r["bid"],
            "supplier": r["supplier"],
            "total_score": r["total_score"],
        }
        for criterion in criteria_names:
            row[criterion] = r["breakdown"].get(criterion, 0)
        rows.append(row)

    return rows