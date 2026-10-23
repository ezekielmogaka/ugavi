"""Contract Retention & Performance Bonds Controller (GA-009 - CT2).

Manages contract retention amounts (typically 5-10% held until
defects liability period ends) and performance bonds/guarantees.
"""
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import now_datetime, add_to_date, get_datetime
from typing import Optional


class ContractRetention(Document):
    """Contract Retention document — lifecycle hooks fire via this class."""
    pass


def calculate_retention(contract_value: float, retention_pct: float = 5.0,
                        supplier: str = None) -> dict:
    """Calculate retention amount and schedule for a contract.

    Returns dict with retention details and release schedule.
    """
    retention_amount = contract_value * (retention_pct / 100)

    # Default defects liability period: 12 months
    liability_months = frappe.db.get_single_value(
        "Ugavi Procurement Settings", "defects_liability_months") or 12

    release_date = add_to_date(now_datetime(), months=liability_months)

    return {
        "contract_value": contract_value,
        "retention_pct": retention_pct,
        "retention_amount": retention_amount,
        "defects_liability_months": liability_months,
        "retention_release_date": str(release_date),
        "net_payable": contract_value - retention_amount,
    }


def apply_retention(contract_name: str, retention_pct: Optional[float] = None):
    """Apply retention to a contract after award.

    Creates a retention schedule and deducts from payment milestones.
    """
    contract = frappe.get_doc("Contract", contract_name)

    if not contract.contract_value:
        frappe.throw(_("Contract {0} has no contract value.").format(contract_name))

    pct = retention_pct or frappe.db.get_single_value(
        "Ugavi Procurement Settings", "default_retention_pct") or 5.0

    retention = calculate_retention(contract.contract_value, pct)

    # Store retention details on contract
    contract.retention_pct = pct
    contract.retention_amount = retention["retention_amount"]
    contract.retention_release_date = retention["retention_release_date"]
    contract.net_payable = retention["net_payable"]
    contract.status = "Retention Applied"
    contract.save()

    # Create retention schedule
    schedule = frappe.get_doc({
        "doctype": "Retention Schedule",
        "contract": contract_name,
        "contract_value": contract.contract_value,
        "retention_pct": pct,
        "retention_amount": retention["retention_amount"],
        "release_date": retention["retention_release_date"],
        "status": "Held",
    })
    schedule.insert()

    return retention


def register_performance_bond(contract_name: str, bond_type: str,
                              bond_value: float, issuing_bank: str,
                              bond_reference: str, expiry_date: str) -> str:
    """Register a performance bond/guarantee for a contract.

    Bond types: Bid Bond, Performance Bond, Advance Payment Guarantee.
    """
    bond = frappe.get_doc({
        "doctype": "Performance Bond",
        "contract": contract_name,
        "bond_type": bond_type,
        "bond_value": bond_value,
        "issuing_bank": issuing_bank,
        "bond_reference": bond_reference,
        "expiry_date": expiry_date,
        "status": "Active",
        "registered_date": now_datetime(),
    })
    bond.insert()

    return bond.name


def release_retention(contract_name: str) -> dict:
    """Release retention after defects liability period expires.

    Verifies final acceptance certificate exists.
    """
    schedule_name = frappe.db.get_value(
        "Retention Schedule", {"contract": contract_name, "status": "Held"}, "name")

    if not schedule_name:
        frappe.throw(_("No retention held for contract {0}.").format(contract_name))

    schedule = frappe.get_doc("Retention Schedule", schedule_name)

    # Verify defects liability period has passed
    if get_datetime(schedule.release_date) > now_datetime():
        frappe.throw(_("Retention release date ({0}) has not yet passed.").format(
            schedule.release_date))

    # Verify final acceptance exists
    acceptance = frappe.db.exists("Final Acceptance Certificate", {"contract": contract_name})
    if not acceptance:
        frappe.throw(_("Final Acceptance Certificate required before retention release."))

    schedule.status = "Released"
    schedule.released_date = now_datetime()
    schedule.save()

    # Create payment voucher for retention release
    contract_doc = frappe.get_doc("Contract", contract_name)
    frappe.get_doc({
        "doctype": "Payment Request",
        "reference_doctype": "Contract",
        "reference_name": contract_name,
        "supplier": contract_doc.supplier,
        "amount": schedule.retention_amount,
        "description": _("Retention Release — Contract {0}").format(contract_name),
        "status": "Requested",
    }).insert()

    return {"released_amount": schedule.retention_amount, "released_date": str(now_datetime())}


def check_expiring_bonds():
    """Scheduled task: alert for bonds expiring within 30 days."""
    cutoff = add_to_date(now_datetime(), days=30)
    expiring = frappe.get_all("Performance Bond",
        filters={"status": "Active", "expiry_date": ["<", cutoff]},
        fields=["name", "contract", "issuing_bank", "bond_type", "expiry_date"],
    )

    for bond in expiring:
        frappe.log_error(
            title="Performance Bond Expiring",
            message=f"Bond {bond.name} ({bond.bond_type}) for {bond.contract} "
                    f"expires on {bond.expiry_date}. Issuing bank: {bond.issuing_bank}"
        )

    return len(expiring)