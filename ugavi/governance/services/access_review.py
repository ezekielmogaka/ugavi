"""User access review report (W10).

Quarterly access review with role-permission matrix and change log.
"""
import frappe
from frappe import _
from frappe.utils import today, getdate, add_to_date


@frappe.whitelist()
def generate_access_review():
    """Generate a matrix of users × roles with permission details."""
    users = frappe.get_all("User", filters={"enabled": 1},
                           fields=["name", "full_name", "email",
                                   "last_login", "creation"])
    result = []
    for u in users:
        roles = frappe.get_all("Has Role",
                               filters={"parent": u.name,
                                        "parenttype": "User"},
                               fields=["role", "name"])
        u["roles"] = [r.role for r in roles]
        u["role_count"] = len(roles)
        result.append(u)
    return {
        "generated_at": today(),
        "user_count": len(result),
        "admin_count": sum(1 for u in result
                           if "System Manager" in u.get("roles", [])),
        "users_with_no_login_90d": [
            u for u in result if not u.get("last_login")
            or getdate(u["last_login"])
            < add_to_date(today(), days=-90)
        ],
        "users": result,
    }


@frappe.whitelist()
def check_segregation_of_duties():
    """Return users with conflicting roles (SoD violations)."""
    conflict_pairs = [
        ("Purchase Requisitioner", "Purchase Approver"),
        ("Purchase Order Creator", "Receipt Confirmer"),
        ("Invoice Creator", "Payment Approver"),
    ]
    violations = []
    for role_a, role_b in conflict_pairs:
        users_a = set(frappe.get_all(
            "Has Role", filters={"role": role_a}, pluck="parent"))
        users_b = set(frappe.get_all(
            "Has Role", filters={"role": role_b}, pluck="parent"))
        overlap = users_a & users_b
        if overlap:
            violations.append({
                "roles": [role_a, role_b],
                "users": sorted(overlap),
                "count": len(overlap),
            })
    return {"violations": violations,
            "total_violations": sum(v["count"] for v in violations)}