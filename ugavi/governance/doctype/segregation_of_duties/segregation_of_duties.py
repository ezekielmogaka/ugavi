import frappe
from frappe.model.document import Document
from frappe import _


class SegregationofDuties(Document):
    """Define incompatible duties for SoD enforcement."""

    def validate(self):
        if self.role_1 == self.role_2:
            frappe.throw(_("Cannot segregate the same role from itself"))

    @staticmethod
    def check_conflict(user: str, doc_type: str, action: str) -> bool:
        """Check if the user's roles create a SoD conflict for this action."""
        user_roles = frappe.get_roles(user)
        for sod in frappe.get_all("Segregation of Duties", fields=["*"]):
            if sod.role_1 in user_roles and sod.role_2 in user_roles:
                if sod.enforcement == "Block":
                    frappe.throw(
                        _("Segregation of Duties conflict: {0} and {1}").format(
                            sod.role_1, sod.role_2
                        )
                    )
                elif sod.enforcement == "Warning Only":
                    frappe.msgprint(
                        _("SoD Warning: User holds both {0} and {1}").format(
                            sod.role_1, sod.role_2
                        )
                    )
        return False