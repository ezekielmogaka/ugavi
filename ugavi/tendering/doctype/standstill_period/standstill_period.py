"""Standstill Period Controller (GA-008 - EV6).

After bid opening and evaluation recommendation, a mandatory standstill period
(typically 7-14 days) allows losing bidders to challenge the award decision
before contract signing.
"""
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import add_to_date, get_datetime, now_datetime


OPEN_COMPLAINT_STATUSES = ("Submitted", "Under Review")


class StandstillPeriod(Document):
    """Standstill Period document — lifecycle hooks fire via this class."""
    pass


def initiate_standstill(tender: str, duration_days: int | None = None) -> str:
    """Start the standstill period after bid evaluation.

    During standstill:
    - Contract cannot be signed
    - Losing bidders can submit challenges
    - All evaluators receive notification
    - Countdown timer displayed on tender

    Returns standstill end date.
    """
    if frappe.db.exists(
        "Standstill Period",
        {"tender": tender, "status": ("in", ["Active", "Challenged"])},
    ):
        frappe.throw(_("This tender already has an open standstill period."))

    if duration_days is None:
        duration_days = (
            frappe.db.get_single_value(
                "Ugavi Procurement Settings", "standstill_days"
            )
            or 14
        )
    duration_days = int(duration_days)
    if duration_days < 1:
        frappe.throw(_("Standstill duration must be at least one day."))

    start_date = now_datetime()
    end_date = add_to_date(start_date, days=duration_days)

    standstill = frappe.get_doc({
        "doctype": "Standstill Period",
        "tender": tender,
        "start_date": start_date,
        "end_date": end_date,
        "duration_days": duration_days,
        "status": "Active",
        "challenges_count": 0,
    })
    standstill.insert()

    # Update tender status
    frappe.db.set_value("Tender", tender, "status", "Standstill Period")

    # Notify all bidders
    _notify_losing_bidders(tender, end_date, duration_days)

    return end_date


def _notify_losing_bidders(tender: str, end_date, duration_days: int):
    """Send standstill notification to all bidders."""
    # Get recommended bidder
    best_bid = frappe.db.get_value("Bid",
        {"tender": tender, "status": ["in", ["Submitted", "Opened"]]},
        ["name", "supplier", "bid_amount"],
        order_by="total_score desc",
        as_dict=True,
    )

    # Get all bidders
    all_bids = frappe.get_all("Bid",
        filters={"tender": tender},
        fields=["supplier", "name"],
    )

    for bid in all_bids:
        is_winner = (bid.name == best_bid.name) if best_bid else False
        supplier_email = frappe.db.get_value("Supplier", bid.supplier, "email_id")

        if supplier_email and not is_winner:
            frappe.sendmail(
                recipients=[supplier_email],
                subject=_("Tender {0} — Standstill Period Notification").format(tender),
                message=_("""
                    The evaluation for Tender {tender} is complete. A standstill period of {days} days
                    is now in effect until {end_date}.
                    
                    If you wish to challenge the evaluation outcome, you may submit a challenge
                    through the supplier portal before the standstill period ends.
                    
                    Tender: {tender}
                    Standstill Ends: {end_date}
                """).format(tender=tender, days=duration_days, end_date=end_date),
            )


def submit_challenge(tender: str, supplier: str, grounds: str,
                     supporting_doc: str = None) -> str:
    """Create the app-owned complaint record used by the supplier portal."""
    # Verify standstill is active
    standstill = frappe.db.get_value("Standstill Period",
        {"tender": tender, "status": "Active"}, ["name", "end_date"], as_dict=True)

    if not standstill:
        frappe.throw(_("No active standstill period for this tender."))

    if get_datetime(standstill.end_date) < now_datetime():
        frappe.throw(_("Standstill period has ended. Challenges are no longer accepted."))

    challenge = frappe.get_doc({
        "doctype": "Tender Complaint",
        "tender": tender,
        "standstill_period": standstill.name,
        "supplier": supplier,
        "grounds": grounds,
        "supporting_document": supporting_doc,
        "status": "Submitted",
        "submission_date": now_datetime(),
    })
    challenge.insert()

    # Increment challenge counter
    frappe.db.set_value("Standstill Period", standstill.name,
                        "challenges_count",
                        frappe.db.get_value("Standstill Period", standstill.name, "challenges_count") + 1)
    frappe.db.set_value("Standstill Period", standstill.name, "status", "Challenged")
    return challenge.name


def resolve_standstill(tender: str, resolution: str = "Award Confirmed") -> str:
    """End the standstill period and proceed to contract award."""
    standstill_name = frappe.db.get_value("Standstill Period",
        {"tender": tender, "status": ("in", ["Active", "Challenged"])}, "name")

    if not standstill_name:
        frappe.throw(_("No open standstill period."))
    if resolution == "Award Confirmed" and frappe.db.exists(
        "Tender Complaint",
        {
            "standstill_period": standstill_name,
            "status": ("in", OPEN_COMPLAINT_STATUSES),
        },
    ):
        frappe.throw(
            _("The award cannot be confirmed while a complaint remains unresolved.")
        )

    frappe.db.set_value("Standstill Period", standstill_name, "status", "Resolved")
    frappe.db.set_value("Standstill Period", standstill_name, "resolution", resolution)
    frappe.db.set_value("Standstill Period", standstill_name, "resolved_date", now_datetime())

    # Update tender status
    if resolution == "Award Confirmed":
        frappe.db.set_value("Tender", tender, "status", "Awarded")
    elif resolution == "Re-evaluation Required":
        frappe.db.set_value("Tender", tender, "status", "Under Evaluation")

    return resolution


def check_expired_standstills():
    """Scheduled task: auto-resolve standstills past end date with no challenges."""
    expired = frappe.get_all("Standstill Period",
        filters={"status": "Active", "end_date": ["<", now_datetime()]},
        fields=["name", "tender", "challenges_count"],
    )
    for s in expired:
        if s.challenges_count == 0:
            resolve_standstill(s.tender, "Award Confirmed")