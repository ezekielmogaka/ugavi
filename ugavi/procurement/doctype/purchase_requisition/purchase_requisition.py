"""Purchase Requisition — coded PR with DoA, budget check and method determination."""
import frappe
from frappe.model.document import Document
from frappe import _


class PurchaseRequisition(Document):
    """Coded Purchase Requisition with auto-determined procurement method."""

    def validate(self):
        self._calculate_total()
        self._determine_procurement_method()
        self._check_budget()
        self._set_approval_chain()

    def _calculate_total(self):
        total = 0.0
        for item in self.items:
            item.estimated_total = item.quantity * item.estimated_unit_price
            total += item.estimated_total
        self.estimated_value = total

    def _determine_procurement_method(self):
        if self.waiver_reference:
            return  # Manual override via waiver — keep as-is
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
        self.status = "Converted to Tender"
        self.save()
        return tender.name