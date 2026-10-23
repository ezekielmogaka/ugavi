"""Contract lifecycle, acceptance, retention, and PO integration."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate, today


class UgaviContract(Document):
    def validate(self):
        self._validate_contract()
        self._validate_status_transition()
        if self.end_date and getdate(self.end_date) < getdate(today()):
            if self.status not in ("Completed", "Terminated"):
                self.status = "Expired"

    def _validate_contract(self):
        if self.start_date and self.end_date:
            if getdate(self.end_date) <= getdate(self.start_date):
                frappe.throw(_("End date must be after start date."))
        if self.retention_percentage is not None and not (
            0 <= self.retention_percentage <= 100
        ):
            frappe.throw(_("Retention percentage must be between 0 and 100."))
        total = 0
        for milestone in self.milestones:
            if self.start_date and getdate(milestone.due_date) < getdate(
                self.start_date
            ):
                frappe.throw(_("Milestone dates cannot precede the contract."))
            if self.end_date and getdate(milestone.due_date) > getdate(self.end_date):
                frappe.throw(_("Milestone dates cannot exceed the contract end date."))
            if milestone.status in ("Completed", "Verified"):
                milestone.completed = 1
                milestone.completed_date = milestone.completed_date or today()
            total += milestone.amount or 0
        if self.contract_value and total > self.contract_value + 0.01:
            frappe.throw(_("Milestone amounts cannot exceed the contract value."))

    def _validate_status_transition(self):
        previous = self.get_doc_before_save()
        old_status = previous.status if previous else None
        if self.status == old_status:
            return
        allowed = {
            "Draft": {"Active", "Terminated"},
            "Active": {"Completed", "Terminated", "Expired"},
            "Completed": set(),
            "Terminated": set(),
            "Expired": set(),
        }
        if old_status and self.status not in allowed.get(old_status, set()):
            frappe.throw(
                _("Contract status cannot change from {0} to {1}.").format(
                    old_status, self.status
                )
            )
        if self.status == "Active":
            self._validate_activation()
        elif self.status == "Completed":
            self._validate_completion()
            self.completion_date = today()
        elif self.status == "Terminated" and not self.termination_reason:
            frappe.throw(_("A termination reason is required."))

    def _validate_activation(self):
        if not self.purchase_order:
            frappe.throw(_("An issued Purchase Order is required to activate a contract."))
        if frappe.db.get_value("Purchase Order", self.purchase_order, "docstatus") != 1:
            frappe.throw(_("The linked Purchase Order must be submitted."))
        if not self.milestones:
            frappe.throw(_("At least one delivery milestone is required."))
        if not any(document.attachment for document in self.documents):
            frappe.throw(_("An attached contract document is required."))
        if self.performance_bond_required and not self.bond_amount:
            frappe.throw(_("Performance bond amount is required."))

    def _validate_completion(self):
        if not self.milestones or any(
            milestone.status != "Verified" for milestone in self.milestones
        ):
            frappe.throw(_("Every contract milestone must be verified before completion."))
        receipts = frappe.get_all(
            "Purchase Receipt Item",
            filters={"purchase_order": self.purchase_order, "docstatus": 1},
            pluck="parent",
        )
        for receipt in set(receipts):
            status = frappe.db.get_value(
                "Ugavi Supplier Evaluation",
                {"purchase_receipt": receipt},
                "status",
            )
            if status != "Completed":
                frappe.throw(
                    _("Supplier evaluation for receipt {0} must be completed.").format(
                        receipt
                    )
                )

    @frappe.whitelist()
    def activate(self):
        if self.status != "Draft":
            frappe.throw(_("Only draft contracts can be activated."))
        self.status = "Active"
        self.save()

    @frappe.whitelist()
    def verify_milestone(self, milestone_name, acceptance_notes, evidence=None):
        if self.status != "Active":
            frappe.throw(_("Only active contracts can verify milestones."))
        milestone = next(
            (row for row in self.milestones if row.name == milestone_name), None
        )
        if not milestone:
            frappe.throw(_("Milestone {0} was not found.").format(milestone_name))
        if not acceptance_notes:
            frappe.throw(_("Acceptance notes are required."))
        milestone.status = "Verified"
        milestone.completed = 1
        milestone.completed_date = today()
        milestone.verified_by = frappe.session.user
        milestone.verified_date = today()
        milestone.acceptance_notes = acceptance_notes
        if evidence:
            milestone.acceptance_evidence = evidence
        self.save()

    @frappe.whitelist()
    def complete(self):
        if self.status != "Active":
            frappe.throw(_("Only active contracts can be completed."))
        self.status = "Completed"
        self.save()

    def check_expiry(self):
        if not self.end_date or not self.expiry_alert_days:
            return False
        days_left = (getdate(self.end_date) - getdate(today())).days
        return 0 <= days_left <= self.expiry_alert_days

    def get_retention_release_status(self):
        milestones = list(self.milestones or [])
        completed = sum(1 for row in milestones if row.status == "Verified")
        total = len(milestones)
        release_pct = (completed / total * 100) if total else 0
        retention_amount = (self.contract_value or 0) * (
            (self.retention_percentage or 0) / 100
        )
        return {
            "release_percentage": round(release_pct, 1),
            "eligible_milestones": completed,
            "total_milestones": total,
            "can_release": bool(total and completed == total),
            "retention_amount": retention_amount,
            "releaseable_amount": retention_amount * release_pct / 100,
        }

    @staticmethod
    def get_active_retention_contracts():
        contracts = frappe.get_all(
            "Ugavi Contract",
            filters={
                "status": ("in", ["Active", "Completed"]),
                "retention_percentage": (">", 0),
            },
            fields=[
                "name",
                "supplier",
                "contract_value",
                "retention_percentage",
                "end_date",
                "status",
            ],
            order_by="end_date",
        )
        for contract in contracts:
            doc = frappe.get_doc("Ugavi Contract", contract.name)
            retention = doc.get_retention_release_status()
            contract.update(
                {
                    "retention_amount": retention["retention_amount"],
                    "completed_milestones": retention["eligible_milestones"],
                    "total_milestones": retention["total_milestones"],
                    "release_pct": retention["release_percentage"],
                }
            )
        return contracts


def ensure_contract_for_purchase_order(doc, method=None):
    """Every issued PO enters contract management without bypassing activation."""
    if frappe.db.exists("Ugavi Contract", {"purchase_order": doc.name}):
        return
    frappe.get_doc(
        {
            "doctype": "Ugavi Contract",
            "purchase_order": doc.name,
            "supplier": doc.supplier,
            "status": "Draft",
            "start_date": doc.transaction_date or today(),
            "end_date": add_days(doc.transaction_date or today(), 90),
            "contract_value": doc.grand_total,
            "donor": doc.get("ugavi_donor"),
        }
    ).insert(ignore_permissions=True)
