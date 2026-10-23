import frappe
from frappe.model.document import Document
from frappe import _


class BudgetEncumbrance(Document):
    """Supplement native ERPNext Budget with procurement commitment reporting."""

    def validate(self):
        if self.status == "Active" and self.released_date:
            self.released_date = None
        self._validate_dimensions()

    def release(self):
        if self.status != "Active":
            return
        self.status = "Released"
        self.released_date = frappe.utils.today()
        self.save()
        frappe.msgprint(_("Budget encumbrance released for {0}").format(self.purchase_order))

    def _validate_dimensions(self):
        budget = frappe.db.get_value(
            "Budget",
            self.budget,
            ["fiscal_year", "budget_against", "project", "cost_center", "ugavi_donor"],
            as_dict=True,
        )
        if not budget:
            frappe.throw(_("Budget {0} does not exist.").format(self.budget))
        if budget.ugavi_donor and self.donor != budget.ugavi_donor:
            frappe.throw(_("The purchase order donor does not match the budget donor."))
        if budget.budget_against == "Project" and self.project != budget.project:
            frappe.throw(_("The purchase order project does not match the budget project."))
        if budget.budget_against == "Cost Center" and self.cost_center != budget.cost_center:
            frappe.throw(_("The purchase order activity cost center does not match the budget."))
        self.fiscal_year = budget.fiscal_year


def create_for_purchase_order(doc, method=None):
    """Record an idempotent commitment after ERPNext accepts the PO."""
    budget = doc.get("ugavi_budget")
    if not budget or frappe.db.exists(
        "Budget Encumbrance",
        {"purchase_order": doc.name, "status": "Active"},
    ):
        return
    cost_centers = {row.cost_center for row in doc.items if row.cost_center}
    projects = {row.project for row in doc.items if row.project}
    if len(cost_centers) > 1 or len(projects) > 1:
        frappe.throw(
            _("A budget-tracked purchase order must use one project and one activity cost center.")
        )
    frappe.get_doc(
        {
            "doctype": "Budget Encumbrance",
            "purchase_order": doc.name,
            "budget": budget,
            "encumbered_amount": doc.base_grand_total,
            "donor": doc.get("ugavi_donor"),
            "project": next(iter(projects), doc.get("ugavi_project")),
            "cost_center": next(iter(cost_centers), None),
            "status": "Active",
        }
    ).insert(ignore_permissions=True)


def reverse_for_purchase_order(doc, method=None):
    names = frappe.get_all(
        "Budget Encumbrance",
        filters={"purchase_order": doc.name, "status": "Active"},
        pluck="name",
    )
    for name in names:
        frappe.db.set_value(
            "Budget Encumbrance",
            name,
            {"status": "Reversed", "released_date": frappe.utils.today()},
        )


def release_for_purchase_receipt(doc):
    """Release commitments only when ERPNext reports the PO fully received."""
    purchase_orders = {
        row.purchase_order for row in doc.items if row.purchase_order
    }
    for purchase_order in purchase_orders:
        if float(
            frappe.db.get_value("Purchase Order", purchase_order, "per_received") or 0
        ) < 100:
            continue
        names = frappe.get_all(
            "Budget Encumbrance",
            filters={"purchase_order": purchase_order, "status": "Active"},
            pluck="name",
        )
        for name in names:
            frappe.get_doc("Budget Encumbrance", name).release()