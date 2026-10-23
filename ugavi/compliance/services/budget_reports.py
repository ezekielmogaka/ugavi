"""Budget burn-rate and variance reporting (W7)."""
import frappe
from frappe import _
from frappe.utils import today, getdate, flt, add_days
from datetime import datetime


@frappe.whitelist()
def get_burn_rate_report(fiscal_year=None, donor=None):
    """Return per-donor, per-fiscal-year budget variance report."""
    fy_filter = fiscal_year or frappe.defaults.get_user_default("fiscal_year")
    result = {"fiscal_year": fy_filter, "donors": [], "summary": {}}
    donors = [donor] if donor else frappe.get_all(
        "Donor Profile", pluck="name"
    )
    total_budget = 0
    total_spent = 0
    for d in donors:
        budgets = frappe.get_all("Budget Account",
                                 filters={"donor": d,
                                          "fiscal_year": fy_filter},
                                 fields=["account", "budget_amount"])
        if not budgets:
            continue
        total = sum(flt(b.budget_amount) for b in budgets)
        spent = _get_actual_spend(d, fy_filter)
        entries = []
        for b in budgets:
            actual = _get_account_spend(b.account, fy_filter)
            variance = flt(b.budget_amount) - flt(actual)
            entries.append({
                "account": b.account,
                "budget": flt(b.budget_amount),
                "actual": actual,
                "variance": variance,
                "burn_pct": round((actual / flt(b.budget_amount) * 100), 1)
                if flt(b.budget_amount) else 0,
            })
        remaining = total - spent
        result["donors"].append({
            "donor": d,
            "total_budget": total,
            "total_spent": spent,
            "remaining": remaining,
            "burn_pct": round((spent / total * 100), 1) if total else 0,
            "entries": entries,
            "over_budget": abs(remaining) if remaining < 0 else 0,
        })
        total_budget += total
        total_spent += spent
    result["summary"] = {
        "total_budget": total_budget,
        "total_spent": total_spent,
        "total_remaining": total_budget - total_spent,
        "overall_burn_pct": round((total_spent / total_budget * 100), 1)
        if total_budget else 0,
        "donor_count": len(result["donors"]),
    }
    return result


def _get_actual_spend(donor, fiscal_year):
    """Sum actual GL spend for a donor in a fiscal year via Budget Accounts."""
    fyd = frappe.get_doc("Fiscal Year", fiscal_year)
    budget_accounts = frappe.get_all(
        "Budget Account",
        filters={"parent": ["like", f"%{donor}%"]},
        pluck="account",
    )
    if not budget_accounts:
        return 0
    result = frappe.db.sql("""
        SELECT SUM(gl.debit) - SUM(gl.credit)
        FROM `tabGL Entry` gl
        WHERE gl.account IN %(accounts)s
          AND gl.posting_date BETWEEN %(start)s AND %(end)s
          AND gl.is_cancelled = 0
    """, {"accounts": tuple(budget_accounts), "start": fyd.year_start_date, "end": fyd.year_end_date})
    return flt(result[0][0]) if result and result[0][0] else 0


def _get_account_spend(account, fiscal_year):
    """Sum actual spend for a budget account in a fiscal year."""
    fyd = frappe.get_doc("Fiscal Year", fiscal_year)
    result = frappe.db.sql("""
        SELECT SUM(gl.debit) - SUM(gl.credit)
        FROM `tabGL Entry` gl
        WHERE gl.account = %s
          AND gl.posting_date BETWEEN %s AND %s
          AND gl.is_cancelled = 0
    """, (account, fyd.year_start_date, fyd.year_end_date))
    return flt(result[0][0]) if result and result[0][0] else 0


@frappe.whitelist()
def get_budget_commitments(donor=None, days=30):
    """Return active budget commitments (PRs/POs pending release)."""
    return frappe.get_list("Budget Account",
                           filters={"donor": donor}
                           if donor else {},
                           fields=["name", "account",
                                   "budget_amount",
                                   "balance_amount"])