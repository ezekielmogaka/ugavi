"""Delegation of Authority (DoA) Matrix Engine.

Determines the approval workflow for Purchase Requisitions based on:
- Amount
- Department
- Donor/Project
"""
import frappe
from typing import Optional, List, Dict


def get_approval_chain(
    amount: float,
    department: str,
    donor: Optional[str] = None,
    project: Optional[str] = None,
) -> List[Dict]:
    """Return the ordered approval chain for a given PR context.
    
    Returns list of {"role": str, "user": Optional[str], "min_amount": float}
    """
    # Find all applicable DoA rules, ordered by level
    rules = frappe.get_all(
        "Delegation of Authority",
        filters={
            "enabled": 1,
            "min_amount": ("<=", amount),
            "department": department,
        },
        fields=[
            "approval_level",
            "approver_role",
            "approver_user",
            "min_amount",
            "max_amount",
            "donor",
            "project",
            "effective_from",
            "effective_to",
        ],
        order_by="approval_level asc",
    )
    today = frappe.utils.getdate()
    rules = [
        rule
        for rule in rules
        if (not rule.donor or rule.donor == donor)
        and (not rule.project or rule.project == project)
        and (not rule.effective_from or frappe.utils.getdate(rule.effective_from) <= today)
        and (not rule.effective_to or frappe.utils.getdate(rule.effective_to) >= today)
    ]
    
    if not rules:
        # Fallback to default approvers from settings
        settings = frappe.get_single("Ugavi Procurement Settings")
        return [
            {"role": settings.default_approver_role or "Approver Level 1",
             "user": None, "min_amount": 0},
        ]
    
    chain = []
    for rule in rules:
        if rule.max_amount and amount > rule.max_amount:
            continue
        chain.append({
            "role": rule.approver_role,
            "user": rule.approver_user,
            "min_amount": rule.min_amount,
        })
    
    return chain


def validate_approval_chain(chain: List[Dict]) -> bool:
    """Validate chain: at least one approver, no duplicates, ascending."""
    if not chain:
        return False
    roles = [c["role"] for c in chain]
    if len(roles) != len(set(roles)):
        return False
    amounts = [c["min_amount"] for c in chain]
    return amounts == sorted(amounts)


def check_budget(amount: float, donor: str, budget_line: str) -> Dict:
    """Check if sufficient budget exists for the requisition."""
    if not budget_line:
        return {"available": True, "message": "No budget control configured"}
    budget = frappe.get_all(
        "Budget Account",
        filters={"account": budget_line},
        fields=["budget_amount"],
    )

    if not budget:
        return {"available": True, "message": "No budget control configured"}

    total_budget = sum(b.budget_amount or 0 for b in budget)
    return {
        "available": total_budget >= amount,
        "budget_total": total_budget,
        "available_balance": total_budget,
    }