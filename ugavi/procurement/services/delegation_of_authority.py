"""Delegation of Authority (DoA) Matrix Engine.

Determines the approval workflow for Purchase Requisitions based on:
- Amount
- Department
- Donor/Project
"""
import frappe
from frappe import _
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
        or_filters=[
            {"donor": donor} if donor else {},
            {"project": project} if project else {},
        ],
        fields=["approval_level", "approver_role", "approver_user", "min_amount", "max_amount"],
        order_by="approval_level asc",
    )
    
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
    budget = frappe.get_all(
        "Budget Account",
        filters={"parent": budget_line, "donor": donor},
        fields=["budget_amount", "actual_amount", "committed_amount"],
    )
    if not budget:
        return {"available": True, "message": "No budget control configured"}
    
    available = budget[0].budget_amount - budget[0].actual_amount - budget[0].committed_amount
    return {
        "available": available >= amount,
        "budget_total": budget[0].budget_amount,
        "spent": budget[0].actual_amount,
        "committed": budget[0].committed_amount,
        "available_balance": available,
    }