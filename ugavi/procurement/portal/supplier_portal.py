"""Supplier dashboard context and identity-bound supplier commands."""
import json
from urllib.parse import urlparse

import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime, getdate, now_datetime, today

OPEN_TENDER_STATUSES = ("Published", "Bids Received")
PROFILE_FIELDS = ("supplier_name", "supplier_group", "supplier_type", "country",
                  "tax_id", "website", "mobile_no", "email_id")
PREQUALIFICATION_DOCUMENT_TYPES = {
    "Registration Certificate", "Tax Compliance", "Business Permit", "Bank Reference",
    "Trade Reference", "Insurance", "Other",
}


def _get_supplier_for_user(user=None):
    user = user or frappe.session.user
    contact = frappe.db.get_value("Contact", {"user": user}, "name")
    if contact:
        supplier = frappe.db.get_value(
            "Dynamic Link",
            {
                "parenttype": "Contact",
                "parent": contact,
                "link_doctype": "Supplier",
            },
            "link_name",
        )
        if supplier:
            return supplier
    return frappe.db.get_value(
        "User Permission",
        {"user": user, "allow": "Supplier"},
        "for_value",
    )


def get_home_page(user: str) -> str | None:
    """Send linked supplier users to their app-owned portal after login."""
    return "/supplier/dashboard" if _get_supplier_for_user(user) else None


def _require_supplier():
    supplier = _get_supplier_for_user()
    if not supplier:
        frappe.throw(_("You are not registered as a supplier."))
    return supplier


def _supplier_file(file_url: str | None):
    if not file_url:
        return None
    file_doc = frappe.db.get_value(
        "File",
        {"file_url": file_url},
        ["name", "owner", "is_private"],
        as_dict=True,
    )
    if not file_doc or file_doc.owner != frappe.session.user:
        frappe.throw(_("The attachment is not available to this supplier account."))
    if not file_doc.is_private:
        frappe.throw(_("Supplier documents must be uploaded as private files."))
    return file_url


def _notify_supplier(title: str, description: str, document_type: str | None = None,
                     document_name: str | None = None):
    notification = frappe.get_doc({
        "doctype": "Notification Log",
        "type": "Alert",
        "title": title,
        "description": description,
        "document_type": document_type,
        "document_name": document_name,
        "for_user": frappe.session.user,
        "from_user": "Administrator",
    })
    notification.insert(ignore_permissions=True)
    return notification.name


def notify_supplier_users(supplier: str, title: str, description: str,
                          document_type: str | None = None,
                          document_name: str | None = None):
    """Create identity-scoped portal notifications for users linked to a Supplier."""
    users = set(frappe.get_all(
        "User Permission",
        filters={"allow": "Supplier", "for_value": supplier},
        pluck="user",
    ))
    contacts = frappe.get_all(
        "Dynamic Link",
        filters={
            "link_doctype": "Supplier",
            "link_name": supplier,
            "parenttype": "Contact",
        },
        pluck="parent",
    )
    if contacts:
        users.update(frappe.get_all(
            "Contact",
            filters={"name": ("in", contacts), "user": ("is", "set")},
            pluck="user",
        ))
    for user in users:
        frappe.get_doc({
            "doctype": "Notification Log",
            "type": "Alert",
            "title": title,
            "description": description,
            "document_type": document_type,
            "document_name": document_name,
            "for_user": user,
            "from_user": frappe.session.user,
        }).insert(ignore_permissions=True)


def get_context(context):
    """Supplier dashboard context."""
    context.no_cache = 1
    context.title = _("Supplier Portal")
    context.supplier = _get_supplier_for_user()
    context.open_tenders = []
    context.bids = []
    context.prequalifications = []
    context.profile = None
    context.categories = []
    context.clarifications = []
    context.awards = []
    context.contracts = []
    context.purchase_orders = []
    context.deliveries = []
    context.purchase_invoices = []
    context.evaluations = []
    context.notifications = []
    context.complaints = []
    context.complaint_windows = []
    context.journey_progress = 0
    context.next_action = None

    if context.supplier:
        context.profile = frappe.db.get_value(
            "Supplier", context.supplier, PROFILE_FIELDS, as_dict=True
        )
        context.categories = frappe.get_all(
            "Item Group",
            filters={"is_group": 0},
            pluck="name",
            order_by="name asc",
            limit=100,
        )
        context.bids = frappe.get_all(
            "Bid",
            filters={"supplier": context.supplier},
            fields=[
                "name", "tender", "bid_amount", "bid_currency", "status",
                "submission_date", "submission_receipt", "creation",
            ],
            order_by="creation desc",
            limit=20,
        )
        context.prequalifications = frappe.get_all(
            "Supplier Prequalification",
            filters={"supplier": context.supplier},
            fields=["name", "status", "expiry_date"],
            order_by="creation desc",
            limit=5,
        )
        open_tenders = frappe.get_all(
            "Tender",
            filters={
                "status": ("in", OPEN_TENDER_STATUSES),
                "submission_deadline": (">=", now_datetime()),
            },
            fields=[
                "name", "title", "submission_deadline", "procurement_method",
                "item_category", "estimated_value", "bid_security_required",
            ],
            order_by="submission_deadline asc",
            limit=10,
        )
        from ugavi.procurement.doctype.supplier_prequalification.supplier_prequalification import (
            is_prequalified,
        )

        context.open_tenders = [
            tender
            for tender in open_tenders
            if tender.procurement_method != "Restricted Tender"
            or is_prequalified(context.supplier, tender.item_category)
        ]
        context.clarifications = frappe.get_all(
            "Clarification",
            filters={"supplier": context.supplier},
            fields=["name", "tender", "question", "answer", "status", "creation", "answered_date"],
            order_by="creation desc",
            limit=20,
        )
        context.awards = frappe.get_all(
            "Tender",
            filters={"awarded_supplier": context.supplier, "status": ("in", ["Awarded", "Closed"])},
            fields=["name", "title", "award_amount", "purchase_order", "status", "modified"],
            order_by="modified desc",
            limit=20,
        )
        context.contracts = frappe.get_all(
            "Ugavi Contract",
            filters={"supplier": context.supplier},
            fields=[
                "name", "tender", "purchase_order", "status", "start_date",
                "end_date", "contract_value",
            ],
            order_by="creation desc",
            limit=20,
        )
        context.purchase_orders = frappe.get_all(
            "Purchase Order",
            filters={"supplier": context.supplier, "docstatus": ("<", 2)},
            fields=[
                "name", "transaction_date", "schedule_date", "status", "currency",
                "grand_total", "per_received", "ugavi_supplier_acknowledged",
            ],
            order_by="transaction_date desc",
            limit=20,
        )
        context.deliveries = frappe.get_all(
            "Purchase Receipt",
            filters={"supplier": context.supplier, "docstatus": ("<", 2)},
            fields=["name", "posting_date", "status", "currency", "grand_total", "docstatus"],
            order_by="posting_date desc",
            limit=20,
        )
        context.purchase_invoices = frappe.get_all(
            "Purchase Invoice",
            filters={"supplier": context.supplier, "docstatus": ("<", 2)},
            fields=[
                "name", "bill_no", "bill_date", "posting_date", "status",
                "currency", "grand_total", "outstanding_amount",
            ],
            order_by="posting_date desc",
            limit=20,
        )
        context.evaluations = frappe.get_all(
            "Ugavi Supplier Evaluation",
            filters={"supplier": context.supplier},
            fields=[
                "name", "purchase_receipt", "status", "evaluation_date", "total_score",
                "cumulative_rating", "remarks",
            ],
            order_by="evaluation_date desc",
            limit=20,
        )
        context.notifications = frappe.get_all(
            "Notification Log",
            filters={"for_user": frappe.session.user},
            fields=[
                "name", "title", "description", "document_type", "document_name",
                "link", "read", "creation",
            ],
            order_by="creation desc",
            limit=20,
        )
        context.complaints = frappe.get_all(
            "Tender Complaint",
            filters={"supplier": context.supplier},
            fields=[
                "name", "tender", "status", "grounds", "outcome",
                "submission_date", "resolution_date",
            ],
            order_by="submission_date desc",
            limit=20,
        )
        bid_tenders = sorted({bid.tender for bid in context.bids if bid.tender})
        if bid_tenders:
            context.complaint_windows = frappe.get_all(
                "Standstill Period",
                filters={
                    "tender": ("in", bid_tenders),
                    "status": ("in", ["Active", "Challenged"]),
                    "end_date": (">=", today()),
                },
                fields=["name", "tender", "end_date", "status"],
                order_by="end_date asc",
                limit=20,
            )
        context.active_prequalifications = sum(
            item.status == "Prequalified" and (
                not item.expiry_date or getdate(item.expiry_date) >= getdate(today())
            )
            for item in context.prequalifications
        )
        context.pending_bids = sum(
            bid.status in {"Draft", "Submitted"} for bid in context.bids
        )
        context.unread_notifications = sum(not item.read for item in context.notifications)
        completed_stages = (
            bool(context.profile and context.profile.email_id),
            bool(context.active_prequalifications),
            bool(context.bids),
            bool(context.awards),
            bool(context.purchase_orders),
            bool(context.deliveries),
            bool(context.evaluations),
        )
        context.journey_progress = round(
            sum(completed_stages) * 100 / len(completed_stages)
        )
        if not completed_stages[0]:
            context.next_action = {
                "label": _("Complete your supplier profile"),
                "href": "#profile",
            }
        elif not completed_stages[1]:
            context.next_action = {
                "label": _("Apply for a supplier category"),
                "href": "#prequalification",
            }
        elif context.open_tenders and not completed_stages[2]:
            context.next_action = {
                "label": _("Review open opportunities"),
                "href": "#opportunities",
            }
        elif context.complaint_windows:
            context.next_action = {
                "label": _("Review an active standstill window"),
                "href": "#complaints",
            }
        elif context.unread_notifications:
            context.next_action = {
                "label": _("Read your latest notifications"),
                "href": "#notifications",
            }


@frappe.whitelist(allow_guest=False)
def update_supplier_profile(mobile_no: str = "", email_id: str = "", website: str = "",
                            tax_id: str = ""):
    """Update the limited set of Supplier fields owned by the portal account."""
    supplier = _require_supplier()
    email_id = email_id.strip()
    website = website.strip()
    mobile_no = mobile_no.strip()
    tax_id = tax_id.strip()
    if email_id:
        frappe.utils.validate_email_address(email_id, throw=True)
    if website and urlparse(website).scheme not in {"http", "https"}:
        frappe.throw(_("Website must start with http:// or https://"))
    if len(mobile_no) > 50 or len(tax_id) > 140:
        frappe.throw(_("Profile field is longer than allowed."))

    frappe.db.set_value("Supplier", supplier, {
        "mobile_no": mobile_no,
        "email_id": email_id,
        "website": website,
        "tax_id": tax_id,
    })
    return {"supplier": supplier, "updated": True}


@frappe.whitelist(allow_guest=False)
def submit_prequalification(category: str, expiry_date: str, documents: str | None = None):
    """Supplier submits a prequalification application."""
    supplier = _require_supplier()
    if not frappe.db.exists("Item Group", category):
        frappe.throw(_("Unknown supplier category"))
    if getdate(expiry_date) <= getdate(today()):
        frappe.throw(_("Expiry date must be in the future"))
    if frappe.db.exists(
        "Supplier Prequalification",
        {
            "supplier": supplier,
            "category": category,
            "status": ("in", ["Under Review", "Prequalified"]),
        },
    ):
        frappe.throw(_("An active application already exists for this category"))

    doc = frappe.get_doc({
        "doctype": "Supplier Prequalification",
        "supplier": supplier,
        "category": category,
        "expiry_date": expiry_date,
        "status": "Under Review",
    })
    for item in json.loads(documents or "[]"):
        document_type = item.get("document_type")
        if document_type not in PREQUALIFICATION_DOCUMENT_TYPES:
            frappe.throw(_("Unknown prequalification document type."))
        doc.append("documents", {
            "document_type": document_type,
            "attachment": _supplier_file(item.get("attachment")),
            "expiry_date": item.get("expiry_date"),
        })
    # Portal users are intentionally not granted broad DocType create access.
    # This command is the narrow, identity-bound write boundary.
    doc.insert(ignore_permissions=True)
    _notify_supplier(
        _("Prequalification application received"),
        _("Application {0} is under review.").format(doc.name),
        "Supplier Prequalification",
        doc.name,
    )
    return doc.name


@frappe.whitelist(allow_guest=False)
def submit_bid(tender: str, bid_amount: float, bid_currency: str = "USD",
               delivery_days: int = 0, technical_proposal: str | None = None):
    """Supplier submits a bid for a tender."""
    supplier = _require_supplier()

    tender_doc = frappe.db.get_value(
        "Tender", tender, ["status", "submission_deadline"], as_dict=True
    )
    if not tender_doc or tender_doc.status not in OPEN_TENDER_STATUSES:
        frappe.throw(_("Tender is not accepting bids."))
    if get_datetime(tender_doc.submission_deadline) < now_datetime():
        frappe.throw(_("Submission deadline has passed."))
    if flt(bid_amount) <= 0 or cint(delivery_days) < 0:
        frappe.throw(_("Bid amount must be positive and delivery days cannot be negative."))
    if not frappe.db.exists("Currency", bid_currency):
        frappe.throw(_("Unknown bid currency."))

    doc = frappe.get_doc({
        "doctype": "Bid",
        "tender": tender,
        "supplier": supplier,
        "bid_amount": flt(bid_amount),
        "bid_currency": bid_currency,
        "delivery_days": cint(delivery_days),
        "technical_proposal": _supplier_file(technical_proposal),
        "status": "Draft",
    })
    # Supplier identity and tender eligibility are validated above and again
    # by Bid.submit_bid(); portal users do not receive general Bid write access.
    doc.insert(ignore_permissions=True)
    doc.submit_bid()
    _notify_supplier(
        _("Bid submitted securely"),
        _("Bid {0} was received. Receipt: {1}").format(doc.name, doc.submission_receipt),
        "Bid",
        doc.name,
    )
    return {
        "bid": doc.name,
        "status": doc.status,
        "submission_receipt": doc.submission_receipt,
    }


@frappe.whitelist(allow_guest=False)
def submit_clarification(tender: str, question: str):
    """Submit a question against an opportunity without granting broad DocType access."""
    supplier = _require_supplier()
    question = question.strip()
    if not question or len(question) > 4000:
        frappe.throw(_("Clarification question must contain between 1 and 4,000 characters."))
    tender_doc = frappe.db.get_value(
        "Tender", tender, ["status", "submission_deadline"], as_dict=True
    )
    if not tender_doc or tender_doc.status not in OPEN_TENDER_STATUSES:
        frappe.throw(_("Tender is not accepting clarifications."))
    if get_datetime(tender_doc.submission_deadline) < now_datetime():
        frappe.throw(_("The clarification period has closed."))

    doc = frappe.get_doc({
        "doctype": "Clarification",
        "tender": tender,
        "supplier": supplier,
        "asked_by": frappe.session.user,
        "question": frappe.utils.escape_html(question),
        "status": "Open",
    })
    doc.insert(ignore_permissions=True)
    _notify_supplier(
        _("Clarification submitted"),
        _("Question {0} was sent to the procurement team.").format(doc.name),
        "Clarification",
        doc.name,
    )
    return {"clarification": doc.name, "status": doc.status}


@frappe.whitelist(allow_guest=False)
def submit_tender_complaint(tender: str, grounds: str,
                            supporting_document: str | None = None):
    """Submit a supplier-bound complaint during an active standstill window."""
    supplier = _require_supplier()
    grounds = grounds.strip()
    if not grounds or len(grounds) > 8000:
        frappe.throw(
            _("Complaint grounds must contain between 1 and 8,000 characters.")
        )
    if not frappe.db.exists("Bid", {"tender": tender, "supplier": supplier}):
        frappe.throw(_("Only a bidder on this tender may submit a complaint."))
    standstill = frappe.db.get_value(
        "Standstill Period",
        {
            "tender": tender,
            "status": ("in", ["Active", "Challenged"]),
            "end_date": (">=", today()),
        },
        ["name", "end_date"],
        as_dict=True,
    )
    if not standstill:
        frappe.throw(_("No active standstill complaint window exists for this tender."))
    if frappe.db.exists(
        "Tender Complaint",
        {
            "tender": tender,
            "supplier": supplier,
            "status": ("in", ["Submitted", "Under Review"]),
        },
    ):
        frappe.throw(_("An unresolved complaint already exists for this tender."))

    complaint = frappe.get_doc({
        "doctype": "Tender Complaint",
        "tender": tender,
        "standstill_period": standstill.name,
        "supplier": supplier,
        "submitted_by": frappe.session.user,
        "submission_date": now_datetime(),
        "grounds": frappe.utils.escape_html(grounds),
        "supporting_document": _supplier_file(supporting_document),
        "status": "Submitted",
    })
    complaint.insert(ignore_permissions=True)
    frappe.db.set_value(
        "Standstill Period",
        standstill.name,
        {
            "status": "Challenged",
            "challenges_count": (
                frappe.db.get_value(
                    "Standstill Period", standstill.name, "challenges_count"
                )
                or 0
            ) + 1,
        },
    )
    _notify_supplier(
        _("Tender complaint received"),
        _("Complaint {0} is awaiting review.").format(complaint.name),
        "Tender Complaint",
        complaint.name,
    )
    return {"complaint": complaint.name, "status": complaint.status}


@frappe.whitelist(allow_guest=False)
def acknowledge_purchase_order(purchase_order: str):
    supplier = _require_supplier()
    order_supplier = frappe.db.get_value("Purchase Order", purchase_order, "supplier")
    if order_supplier != supplier:
        frappe.throw(_("This purchase order does not belong to your supplier account"))
    frappe.db.set_value(
        "Purchase Order",
        purchase_order,
        {
            "ugavi_supplier_acknowledged": 1,
            "ugavi_acknowledged_at": frappe.utils.now_datetime(),
        },
    )
    _notify_supplier(
        _("Purchase order acknowledged"),
        _("You acknowledged purchase order {0}.").format(purchase_order),
        "Purchase Order",
        purchase_order,
    )
    return {"purchase_order": purchase_order, "acknowledged": True}


@frappe.whitelist(allow_guest=False)
def submit_supplier_invoice(
    purchase_receipt: str,
    supplier_invoice_number: str,
    supplier_invoice_date: str,
    invoice_file: str,
):
    """Create a reviewable ERPNext invoice from a submitted supplier receipt."""
    supplier = _require_supplier()
    receipt = frappe.db.get_value(
        "Purchase Receipt",
        purchase_receipt,
        ["supplier", "docstatus"],
        as_dict=True,
    )
    if not receipt or receipt.supplier != supplier or receipt.docstatus != 1:
        frappe.throw(_("Select one of your submitted purchase receipts."))
    supplier_invoice_number = supplier_invoice_number.strip()
    if not supplier_invoice_number or len(supplier_invoice_number) > 140:
        frappe.throw(_("A valid supplier invoice number is required."))
    invoice_date = getdate(supplier_invoice_date)
    if invoice_date > getdate(today()):
        frappe.throw(_("Supplier invoice date cannot be in the future."))
    if frappe.db.exists(
        "Purchase Invoice",
        {
            "supplier": supplier,
            "bill_no": supplier_invoice_number,
            "docstatus": ("<", 2),
        },
    ):
        frappe.throw(_("This supplier invoice number has already been submitted."))

    from erpnext.stock.doctype.purchase_receipt.purchase_receipt import (
        make_purchase_invoice,
    )

    invoice = make_purchase_invoice(purchase_receipt)
    invoice.bill_no = supplier_invoice_number
    invoice.bill_date = invoice_date
    invoice.ugavi_supplier_invoice_file = _supplier_file(invoice_file)
    invoice.ugavi_submitted_from_portal = 1
    invoice.insert(ignore_permissions=True)
    _notify_supplier(
        _("Supplier invoice received"),
        _("Invoice {0} was created for finance review.").format(invoice.name),
        "Purchase Invoice",
        invoice.name,
    )
    return {"purchase_invoice": invoice.name, "status": invoice.status}


@frappe.whitelist(allow_guest=False)
def mark_notification_read(notification: str):
    owner = frappe.db.get_value("Notification Log", notification, "for_user")
    if owner != frappe.session.user:
        frappe.throw(_("This notification does not belong to your account."))
    frappe.db.set_value("Notification Log", notification, "read", 1)
    return {"notification": notification, "read": True}