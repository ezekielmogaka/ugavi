"""Bid Evaluation Summary Controller (GA-008 - EV4).

Generates a bid comparison summary for evaluation committee review.
Compares all submitted bids for a tender side-by-side with scoring.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import fmt_money, now_datetime

APPROVER_ROLES = {"Tender Committee Chair", "System Manager"}


class BidEvaluationSummary(Document):
    """Committee recommendation that authorizes the standstill notice."""

    def validate(self):
        previous = self.get_doc_before_save()
        if previous and previous.status in {"Approved", "Rejected"}:
            frappe.throw(_("An approved or rejected evaluation summary cannot be changed."))
        if self.recommended_bidder:
            self.recommended_bid = frappe.db.get_value(
                "Bid",
                {
                    "tender": self.tender,
                    "supplier": self.recommended_bidder,
                    "status": ("in", ["Opened", "Evaluated", "Accepted"]),
                },
                "name",
            )
            if not self.recommended_bid:
                frappe.throw(
                    _("{0} has no opened bid on tender {1}.").format(
                        self.recommended_bidder, self.tender
                    )
                )
        if self.evaluation_minutes and frappe.db.get_value(
            "Evaluation Minutes", self.evaluation_minutes, "tender"
        ) != self.tender:
            frappe.throw(_("The evaluation minutes belong to a different tender."))

    @frappe.whitelist()
    def approve(self):
        from ugavi.tendering.services.evaluation import (
            approved_minutes,
            assert_recommendation_supported,
        )

        if self.status not in {"Draft", "Submitted"}:
            frappe.throw(_("Only a draft or submitted evaluation summary can be approved."))
        if not APPROVER_ROLES.intersection(frappe.get_roles()):
            frappe.throw(_("Only the Tender Committee Chair can approve the recommendation."))
        if frappe.db.get_value("Tender", self.tender, "status") != "Under Evaluation":
            frappe.throw(_("The tender must be Under Evaluation."))
        if not self.recommended_bidder:
            frappe.throw(_("Select the recommended bidder."))
        assert_recommendation_supported(
            self.tender, self.recommended_bidder, self.recommended_amount
        )
        self.evaluation_minutes = self.evaluation_minutes or approved_minutes(self.tender)
        self.status = "Approved"
        self.approved_by = frappe.session.user
        self.approved_at = now_datetime()
        self.save()

    @frappe.whitelist()
    def reject(self, reason: str):
        if self.status not in {"Draft", "Submitted"}:
            frappe.throw(_("Only a draft or submitted evaluation summary can be rejected."))
        if not APPROVER_ROLES.intersection(frappe.get_roles()):
            frappe.throw(_("Only the Tender Committee Chair can reject the recommendation."))
        if not (reason or "").strip():
            frappe.throw(_("A rejection reason is required."))
        self.status = "Rejected"
        self.rejection_reason = reason.strip()
        self.save()


def generate_bid_summary(tender: str) -> dict:
    """Generate bid evaluation summary for a tender.

    Returns:
        dict with tender info, bid list sorted by total score, and recommendation.
    """
    tender_doc = frappe.db.get_value(
        "Tender",
        tender,
        [
            "name",
            "title",
            "procurement_method",
            "submission_deadline",
            "bid_opening_date",
        ],
        as_dict=True,
    )
    if not tender_doc:
        frappe.throw(_("Tender {0} not found").format(tender))

    bids = frappe.get_all("Bid",
        filters={"tender": tender, "status": ["in", ["Opened", "Evaluated"]]},
        fields=["name", "supplier", "bid_amount",
                "technical_score", "financial_score", "delivery_days"],
        order_by="bid_amount asc",
    )

    if not bids:
        return {
            "tender": tender_doc,
            "total_bids": 0,
            "bids": [],
            "message": _("No bids submitted for this tender."),
        }

    # Compute total score (weighted: 40% technical, 40% financial, 10% delivery, 10% past performance)
    for bid in bids:
        bid["total_score"] = (
            (bid.get("technical_score") or 0) * 0.4 +
            (bid.get("financial_score") or 0) * 0.4 +
            (1 - min(bid.get("delivery_days") or 365, 365) / 365) * 20
        )

    # Sort by total score descending
    bids_sorted = sorted(bids, key=lambda b: b["total_score"], reverse=True)

    # Determine recommendation (lowest responsive bid or highest scored)
    best_bid = bids_sorted[0]

    return {
        "tender": {
            "title": tender_doc.title,
            "number": tender_doc.name,
            "type": tender_doc.procurement_method,
            "method": "Weighted technical and financial scoring",
            "deadline": str(tender_doc.submission_deadline),
            "opening_date": str(tender_doc.bid_opening_date or ""),
        },
        "total_bids": len(bids),
        "bids": [
            {
                "rank": i + 1,
                "bid": b.name,
                "supplier": b.supplier,
                "amount": fmt_money(b.bid_amount, currency="KES"),
                "technical_score": b.get("technical_score") or 0,
                "financial_score": b.get("financial_score") or 0,
                "delivery_days": b.get("delivery_days") or "N/A",
                "total_score": round(b["total_score"], 2),
            }
            for i, b in enumerate(bids_sorted)
        ],
        "recommendation": {
            "recommended_bid": best_bid.name,
            "recommended_supplier": best_bid.supplier,
            "recommended_amount": fmt_money(best_bid.bid_amount, currency="KES"),
            "total_score": round(best_bid["total_score"], 2),
            "justification": _("Highest evaluated score ({0}) with competitive pricing").format(
                round(best_bid["total_score"], 2)
            ),
        },
    }


def flag_abnormally_low_bids(tender: str, threshold_percent: float = 40.0) -> list[str]:
    """Flag bids that are >threshold% below the average bid amount (potential dumping)."""
    bids = frappe.get_all("Bid",
        filters={"tender": tender, "status": ["in", ["Submitted", "Opened"]]},
        fields=["name", "supplier", "bid_amount"],
    )
    if len(bids) < 3:
        return []  # Need at least 3 bids to detect outliers

    amounts = [b.bid_amount for b in bids]
    avg = sum(amounts) / len(amounts)

    flagged = []
    for b in bids:
        deviation = ((avg - b.bid_amount) / avg) * 100
        if deviation > threshold_percent:
            flagged.append(b.name)

            # Log low bid alert
            frappe.log_error(
                title="Abnormally Low Bid Detected",
                message=f"Bid {b.name} from {b.supplier} ({b.bid_amount}) "
                        f"is {deviation:.1f}% below average ({avg:.2f}) for tender {tender}"
            )

    return flagged


def bid_summary_to_html(bid_summary: dict) -> str:
    """Render bid summary as HTML table for email or print."""
    rows = ""
    for bid in bid_summary["bids"]:
        rows += f"""<tr>
            <td>{bid['rank']}</td>
            <td>{bid['supplier']}</td>
            <td>{bid['amount']}</td>
            <td>{bid['technical_score']}</td>
            <td>{bid['financial_score']}</td>
            <td>{bid['total_score']}</td>
        </tr>"""

    return f"""<h2>Bid Evaluation Summary — {bid_summary['tender']['title']}</h2>
    <p>Tender No: {bid_summary['tender']['number']} | Total Bids: {bid_summary['total_bids']}</p>
    <table border="1" cellpadding="5">
        <tr><th>Rank</th><th>Supplier</th><th>Amount</th><th>Tech</th><th>Fin</th><th>Total</th></tr>
        {rows}
    </table>
    <p><strong>Recommendation:</strong> {bid_summary['recommendation']['recommended_supplier']} — {bid_summary['recommendation']['justification']}</p>"""