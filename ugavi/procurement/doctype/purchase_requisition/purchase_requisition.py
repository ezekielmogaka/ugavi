"""Purchase Requisition — coded PR with DoA, budget check and method determination."""
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.model.naming import make_autoname
import json


class PurchaseRequisition(Document):
    """Coded Purchase Requisition with auto-determined procurement method."""

    def autoname(self):
        donor_code = frappe.db.get_value("Donor Profile", self.donor, "donor_code") or self.donor
        safe_code = "".join(ch for ch in donor_code.upper() if ch.isalnum())[:12]
        self.name = make_autoname(f"PR-{safe_code}-.YYYY.-.#####")

    def validate(self):
        self._validate_status_transition()
        self._calculate_total()
        self._determine_procurement_method()
        self._check_budget()
        self._set_approval_chain()

    def _validate_status_transition(self):
        previous = self.get_doc_before_save()
        previous_status = previous.status if previous else None
        if not previous and self.status != "Draft" and not self.flags.get("allow_status_transition"):
            frappe.throw(_("New requisitions must start in Draft"))
        if (
            previous
            and previous_status != self.status
            and not self.flags.get("allow_status_transition")
        ):
            frappe.throw(_("Use the requisition workflow actions to change status"))

    def _calculate_total(self):
        total = 0.0
        for item in self.items:
            item.estimated_total = item.quantity * item.estimated_unit_price
            total += item.estimated_total
        self.estimated_value = total

    def _determine_procurement_method(self):
        if self.waiver_reference:
            waiver = frappe.get_doc("Waiver", self.waiver_reference)
            if waiver.status != "Approved":
                frappe.throw(_("The procurement-method waiver is not approved"))
            if waiver.purchase_requisition and waiver.purchase_requisition != self.name:
                frappe.throw(_("The waiver belongs to a different requisition"))
            return
        if self.estimated_value == 0:
            return
        try:
            from ugavi.procurement.services.rules_engine import get_engine
            engine = get_engine()
            method = engine.determine_method(
                estimated_value=self.estimated_value,
                donor=self.donor,
                item_category=self.item_category,
            )
            self.procurement_method = method.value
        except ImportError:
            # Fallback: simple threshold logic
            settings = frappe.get_single("Ugavi Procurement Settings")
            if self.estimated_value < (settings.direct_threshold or 200000):
                self.procurement_method = "Request for Quotation (Direct)"
            elif self.estimated_value < (settings.restricted_threshold or 500000):
                self.procurement_method = "Restricted Tender"
            else:
                self.procurement_method = "Open Tender"

    def _check_budget(self):
        try:
            from ugavi.procurement.services.delegation_of_authority import check_budget
            result = check_budget(
                amount=self.estimated_value,
                donor=self.donor,
                budget_line=getattr(self, "budget_line", ""),
            )
            if not result.get("available", True):
                frappe.throw(_(
                    "Insufficient budget. Available: {0}, Required: {1}"
                ).format(result.get("available_balance", 0), self.estimated_value))
            self.budget_status = f"Available: {result.get('available_balance', 0)}"
        except ImportError:
            self.budget_status = "Budget check unavailable — development mode"

    def _set_approval_chain(self):
        try:
            from ugavi.procurement.services.delegation_of_authority import get_approval_chain
            chain = get_approval_chain(
                amount=self.estimated_value,
                department=self.department,
                donor=self.donor,
                project=self.project,
            )
            self.approval_chain = " → ".join(
                [f"{c['role']} (≥{c['min_amount']:,.0f})" for c in chain]
            ) if chain else "Default Approver"
        except ImportError:
            self.approval_chain = "Default Approver (dev mode)"

    def _approval_steps(self):
        from ugavi.procurement.services.delegation_of_authority import get_approval_chain

        return get_approval_chain(
            amount=self.estimated_value,
            department=self.department,
            donor=self.donor,
            project=self.project,
        )

    @frappe.whitelist()
    def submit_for_approval(self):
        if self.status != "Draft":
            frappe.throw(_("Only draft requisitions can be submitted"))
        self._check_budget()
        if not self._approval_steps():
            frappe.throw(_("No Delegation of Authority rule applies to this requisition"))
        self.flags.allow_status_transition = True
        self.status = "Pending Approval"
        self.save()

    @frappe.whitelist()
    def approve(self, remarks=None):
        if self.status != "Pending Approval":
            frappe.throw(_("Only pending requisitions can be approved"))
        if frappe.session.user == self.requester:
            frappe.throw(_("The requester cannot approve their own requisition"))

        history = json.loads(self.approval_history or "[]")
        approved_roles = {entry["role"] for entry in history if entry["action"] == "Approved"}
        remaining = [step for step in self._approval_steps() if step["role"] not in approved_roles]
        if not remaining:
            frappe.throw(_("This requisition already has all required approvals"))
        required = remaining[0]
        if required.get("user") and required["user"] != frappe.session.user:
            frappe.throw(_("The next approval must be completed by {0}").format(required["user"]))
        if not required.get("user") and required["role"] not in frappe.get_roles():
            frappe.throw(_("The next approval requires role {0}").format(required["role"]))

        history.append(
            {
                "action": "Approved",
                "role": required["role"],
                "user": frappe.session.user,
                "timestamp": str(frappe.utils.now_datetime()),
                "remarks": remarks or "",
            }
        )
        self.approval_history = json.dumps(history)
        self.flags.allow_status_transition = True
        self.status = "Approved" if len(remaining) == 1 else "Pending Approval"
        self.save()

    @frappe.whitelist()
    def reject(self, remarks):
        if self.status != "Pending Approval":
            frappe.throw(_("Only pending requisitions can be rejected"))
        if frappe.session.user == self.requester:
            frappe.throw(_("The requester cannot reject their own requisition"))
        history = json.loads(self.approval_history or "[]")
        history.append(
            {
                "action": "Rejected",
                "user": frappe.session.user,
                "timestamp": str(frappe.utils.now_datetime()),
                "remarks": remarks,
            }
        )
        self.approval_history = json.dumps(history)
        self.flags.allow_status_transition = True
        self.status = "Rejected"
        self.save()

    @frappe.whitelist()
    def create_tender(self) -> str:
        """Create a Tender from this approved requisition."""
        if self.status != "Approved":
            frappe.throw("Only approved requisitions can generate tenders.")
        tender = frappe.get_doc({
            "doctype": "Tender",
            "purchase_requisition": self.name,
            "title": f"Tender for {self.title}",
            "donor": self.donor,
            "procurement_method": self.procurement_method,
            "estimated_value": self.estimated_value,
        })
        tender.insert()
        self.flags.allow_status_transition = True
        self.status = "Converted to Tender"
        self.save()
        return tender.name

    @frappe.whitelist()
    def convert_to_po(self, supplier: str) -> str:
        """Create a Purchase Order directly from an approved PR (direct procurement path).

        Used when no tender is required (e.g. Request for Quotation Direct, Single Source).
        The PR must be Approved and the procurement method must allow direct PO.
        """
        if self.status != "Approved":
            frappe.throw(_("Only approved requisitions can create a Purchase Order"))
        if self.procurement_method not in (
            "Request for Quotation (Direct)", "Single Source"
        ):
            frappe.throw(_(
                "Direct PO only allowed for Direct RFQ or Single Source. "
                "Current method: {0}. Create a Tender instead."
            ).format(self.procurement_method))

        settings = frappe.get_single("Ugavi Procurement Settings")
        schedule_date = frappe.utils.add_days(None, 30)
        po = frappe.get_doc({
            "doctype": "Purchase Order",
            "supplier": supplier,
            "company": settings.default_company,
            "ugavi_pr": self.name,
            "ugavi_donor": self.donor,
            "ugavi_procurement_method": self.procurement_method,
            "transaction_date": frappe.utils.now_datetime().date(),
            "schedule_date": schedule_date,
        })
        for item in self.items:
            po.append("items", {
                "item_code": item.item_code,
                "item_name": getattr(item, "item_name", ""),
                "qty": item.quantity,
                "rate": item.estimated_unit_price,
                "uom": getattr(item, "uom", "Nos"),
                "schedule_date": schedule_date,
            })
        po.insert()
        po.submit()
        contract_name = frappe.db.get_value(
            "Ugavi Contract", {"purchase_order": po.name}, "name"
        )
        self.flags.allow_status_transition = True
        self.status = "Converted to PO"
        self.save()
        frappe.msgprint(
            _("Purchase Order {0} and Contract {1} created").format(
                po.name, contract_name
            )
        )
        return po.name