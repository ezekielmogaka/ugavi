"""Conflict of Interest (COI) Declaration Controller (GA-008 - EV3).

Tender Evaluation COI: evaluators must declare conflicts before
accessing bids. If conflicted, they are excluded from the evaluation
committee.
"""
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class COIDeclaration(Document):
    def validate(self):
        if not self.tender:
            frappe.throw(_("Tender is required."))
        if self.is_new() and self.declarant != frappe.session.user and "System Manager" not in frappe.get_roles():
            frappe.throw(_("Committee members must submit their own declaration."))
        if self.has_conflict == "Yes" and not self.conflict_description:
            frappe.throw(_("Conflict details are required."))
        tender = frappe.get_doc("Tender", self.tender)
        members = {row.user for row in tender.evaluation_committee}
        if self.declarant not in members:
            frappe.throw(_("Only an assigned evaluation committee member may declare."))
        duplicate = frappe.db.exists(
            "COI Declaration",
            {
                "tender": self.tender,
                "declarant": self.declarant,
                "name": ("!=", self.name),
            },
        )
        if duplicate:
            frappe.throw(_("This evaluator has already submitted a declaration."))


def create_coi_declaration(
    tender: str,
    evaluator: str,
    declaration: str,
    has_conflict: bool = False,
    conflict_detail: str | None = None,
):
    """Record a COI declaration for a tender evaluator.

    Args:
        tender: Tender name
        evaluator: User/employee declaring
        declaration: "No conflict" or "Conflict declared"
        has_conflict: True if evaluator has a conflict of interest
        conflict_detail: Description of the conflict (if any)
    """
    if frappe.db.exists(
        "COI Declaration", {"tender": tender, "declarant": evaluator}
    ):
        frappe.throw(_("COI declaration already exists for this evaluator."))

    doc = frappe.get_doc({
        "doctype": "COI Declaration",
        "tender": tender,
        "declarant": evaluator,
        "has_conflict": "Yes" if has_conflict else "No",
        "conflict_description": conflict_detail or declaration,
        "declaration_date": now_datetime(),
        "status": "Submitted",
    })
    doc.insert()

    if has_conflict:
        _notify_conflict(tender, evaluator, conflict_detail or declaration)

    return doc.name


def _notify_conflict(tender: str, evaluator: str, reason: str):
    procurement_users = frappe.get_all(
        "Has Role",
        filters={"role": "Procurement Manager", "parenttype": "User"},
        pluck="parent",
    )
    for user in procurement_users:
        frappe.get_doc(
            {
                "doctype": "Notification Log",
                "type": "Alert",
                "for_user": user,
                "from_user": frappe.session.user,
                "title": _("Evaluation conflict declared"),
                "description": _(
                    "{0} declared a conflict for tender {1}: {2}"
                ).format(evaluator, tender, reason),
                "document_type": "Tender",
                "document_name": tender,
            }
        ).insert(ignore_permissions=True)


def check_coi_compliance(tender: str) -> dict:
    """Verify all evaluation committee members have submitted COI declarations.

    Returns dict with compliant/uncompliant evaluators.
    """
    tender_doc = frappe.get_doc("Tender", tender)
    evaluators = [row.user for row in tender_doc.evaluation_committee]

    declarations = frappe.get_all(
        "COI Declaration",
        filters={"tender": tender, "status": ("in", ["Submitted", "Reviewed"])},
        fields=["declarant", "has_conflict", "declaration_date"],
    )

    declared = {d.declarant for d in declarations}
    conflicted = {d.declarant for d in declarations if d.has_conflict == "Yes"}

    result = {
        "tender": tender,
        "total_evaluators": len(evaluators),
        "declared": len(declared),
        "pending": [user for user in evaluators if user not in declared],
        "conflicted": list(conflicted),
        "compliant": bool(evaluators)
        and len(declared) == len(evaluators)
        and not conflicted,
    }

    return result