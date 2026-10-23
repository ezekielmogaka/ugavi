"""Regret Notice — Notification to unsuccessful bidders.

Sent after standstill period when award is confirmed.
Published on supplier portal and emailed to the bidder.
"""

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import now_datetime

from ugavi.procurement.portal.supplier_portal import notify_supplier_users


class RegretNotice(Document):
    """Formal regret notification to unsuccessful bidders."""

    def validate(self):
        if self.awarded_supplier == self.supplier:
            frappe.throw(
                _("A regret notice cannot be issued to the awarded supplier.")
            )
        self._validate_standstill_concluded()

    def _validate_standstill_concluded(self):
        standstills = frappe.get_all(
            "Standstill Period",
            filters={"tender": self.tender, "status": "Resolved"},
            pluck="name",
        )
        if not standstills:
            frappe.throw(
                _("No concluded standstill period found for this tender. "
                  "Regret notices require a completed standstill.")
            )

    @frappe.whitelist()
    def send(self):
        """Send regret notice via email and publish on portal."""
        if self.status != "Draft":
            frappe.throw(_("This regret notice has already been sent."))

        # Notify via email and portal
        notify_supplier_users(
            self.supplier,
            _("Tender Award Notice — {0}").format(self.tender),
            (
                f"Thank you for your bid for {self.tender}. "
                f"We regret to inform you that your bid was not successful. "
                f"The contract was awarded to {self.awarded_supplier} "
                f"for KES {frappe.utils.fmt_money(self.award_amount)}. "
                f"Reason: {self.rejection_reason}\n\n"
                f"{self.detailed_reason or ''}"
            ),
            "Tender",
            self.tender,
        )

        self.sent_via_email = 1
        self.sent_via_portal = 1
        self.sent_at = now_datetime()
        self.status = "Sent"
        self.save()
        frappe.msgprint(
            _("Regret notice sent to {0}.").format(self.supplier)
        )


def send_regret_notices_for_tender(tender: str) -> int:
    """Send regret notices to all non-awarded bidders on a tender.

    Returns count of notices created.
    """
    award = frappe.db.get_value("Tender", tender, ["awarded_supplier", "award_amount"],
                                as_dict=True)
    if not award or not award.awarded_supplier:
        frappe.throw(_("Tender has not been awarded yet."))

    bids = frappe.get_all(
        "Bid",
        filters={"tender": tender, "status": ("!=", "Withdrawn")},
        fields=["name", "supplier", "bid_amount",
                "technical_score", "financial_score"],
    )

    count = 0
    for bid in bids:
        if bid.supplier == award.awarded_supplier:
            continue
        if frappe.db.exists("Regret Notice", {"tender": tender, "bid": bid.name}):
            continue
        notice = frappe.get_doc({
            "doctype": "Regret Notice",
            "tender": tender,
            "supplier": bid.supplier,
            "bid": bid.name,
            "awarded_supplier": award.awarded_supplier,
            "award_amount": award.award_amount,
            "bid_amount": bid.bid_amount,
            "bid_technical_score": bid.technical_score,
            "bid_financial_score": bid.financial_score,
            "rejection_reason": "Price Not Competitive",
            "detailed_reason": (
                f"Your bid scored {bid.technical_score or 0}% technical "
                f"and {bid.financial_score or 0}% financial."
            ),
            "status": "Draft",
        })
        notice.insert(ignore_permissions=True)
        try:
            notice.send()
        except Exception as e:
            frappe.log_error(title="Regret Notice Send Failed",
                             message=str(e))
        count += 1
    return count