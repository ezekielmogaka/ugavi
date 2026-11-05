"""Standstill Period Controller (GA-008 - EV6).

After an approved evaluation recommendation, a mandatory standstill period
(typically 7-14 days) allows unsuccessful bidders to challenge the intended
award before a purchase order or contract is issued.

Lifecycle: Active -> Challenged (complaint received) -> Resolved.
``Award Confirmed`` keeps the tender in "Standstill Period" so that the award
itself remains an explicit, separately authorized ``Tender.award`` action.
"""
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate, now_datetime, today

from ugavi.procurement.portal.supplier_portal import notify_supplier_users

OPEN_STANDSTILL_STATUSES = ("Active", "Challenged")
OPEN_COMPLAINT_STATUSES = ("Submitted", "Under Review")


class StandstillPeriod(Document):
    def validate(self):
        if self.start_date and self.end_date and getdate(self.end_date) <= getdate(self.start_date):
            frappe.throw(_("Standstill end date must be after its start date."))


def get_open_standstill(tender: str) -> str | None:
    return frappe.db.get_value(
        "Standstill Period",
        {"tender": tender, "status": ("in", OPEN_STANDSTILL_STATUSES)},
        "name",
    )


def initiate_standstill(tender: str, recommended_supplier: str,
                        duration_days: int | None = None) -> str:
    """Create the standstill record and notify unsuccessful bidders.

    The caller (``Tender.start_standstill``) owns tender status changes and the
    evaluation-governance checks. Returns the Standstill Period name.
    """
    if get_open_standstill(tender):
        frappe.throw(_("This tender already has an open standstill period."))

    if duration_days is None:
        duration_days = (
            frappe.db.get_single_value("Ugavi Procurement Settings", "standstill_days")
            or 14
        )
    duration_days = int(duration_days)
    if duration_days < 1:
        frappe.throw(_("Standstill duration must be at least one day."))

    start_date = today()
    end_date = add_days(start_date, duration_days)
    standstill = frappe.get_doc({
        "doctype": "Standstill Period",
        "tender": tender,
        "start_date": start_date,
        "end_date": end_date,
        "status": "Active",
        "challenges_count": 0,
    })
    standstill.insert(ignore_permissions=True)
    _notify_bidders(tender, recommended_supplier, end_date, duration_days)
    return standstill.name


def _notify_bidders(tender: str, recommended_supplier: str, end_date, duration_days: int):
    suppliers = set(frappe.get_all("Bid", filters={"tender": tender}, pluck="supplier"))
    for supplier in suppliers:
        if supplier == recommended_supplier:
            title = _("Intended award notice")
            message = _(
                "Your bid for tender {0} is recommended for award. No contract may be "
                "issued before the standstill period ends on {1}."
            ).format(tender, end_date)
        else:
            title = _("Standstill period started")
            message = _(
                "The evaluation of tender {0} is complete and a {1}-day standstill period "
                "runs until {2}. You may submit a complaint from the supplier portal "
                "before it ends."
            ).format(tender, duration_days, end_date)
        notify_supplier_users(supplier, title, message, "Tender", tender)
        supplier_email = frappe.db.get_value("Supplier", supplier, "email_id")
        if supplier_email:
            frappe.sendmail(
                recipients=[supplier_email], subject=title, message=message,
                reference_doctype="Tender", reference_name=tender,
            )


def resolve_standstill(tender: str, resolution: str = "Award Confirmed") -> str:
    """Close the open standstill with the given resolution."""
    standstill_name = get_open_standstill(tender)
    if not standstill_name:
        frappe.throw(_("No open standstill period."))
    standstill = frappe.get_doc("Standstill Period", standstill_name)

    if resolution == "Award Confirmed":
        if getdate(today()) <= getdate(standstill.end_date):
            frappe.throw(
                _("The award can only be confirmed after the standstill ends on {0}.").format(
                    standstill.end_date
                )
            )
        if frappe.db.exists(
            "Tender Complaint",
            {"standstill_period": standstill_name, "status": ("in", OPEN_COMPLAINT_STATUSES)},
        ):
            frappe.throw(_("The award cannot be confirmed while a complaint remains unresolved."))
    elif resolution != "Re-evaluation Required":
        frappe.throw(_("Unsupported standstill resolution {0}.").format(resolution))

    standstill.status = "Resolved"
    standstill.resolution = resolution
    standstill.resolved_date = now_datetime()
    standstill.save(ignore_permissions=True)

    if resolution == "Re-evaluation Required":
        frappe.get_doc("Tender", tender).db_set("status", "Under Evaluation")
    return resolution


def check_expired_standstills():
    """Daily: confirm unchallenged standstills whose period has ended.

    Confirmation does not award the tender; ``Tender.award`` remains a
    separate, permission-checked action.
    """
    expired = frappe.get_all(
        "Standstill Period",
        filters={"status": "Active", "end_date": ("<", today())},
        fields=["tender"],
    )
    for row in expired:
        try:
            resolve_standstill(row.tender, "Award Confirmed")
        except frappe.ValidationError:
            frappe.log_error(title=f"Standstill confirmation failed for {row.tender}")
