"""Procurement Rules Engine — Strategy Pattern.

Determines the procurement method based on configurable rules.
Methods: DIRECT (RFQ), RESTRICTED_TENDER, OPEN_TENDER, SINGLE_SOURCE

Rule evaluation order:
1. Value-based thresholds (from Procurement Settings)
2. Donor-specific rules
3. Category-specific rules
4. Manual override (requires Waiver)
"""

import frappe
from frappe import _
from typing import Optional, Dict, Any
from enum import Enum


class ProcurementMethod(str, Enum):
    DIRECT = "Request for Quotation (Direct)"
    RESTRICTED_TENDER = "Restricted Tender"
    OPEN_TENDER = "Open Tender"
    SINGLE_SOURCE = "Single Source"


class ThresholdRule:
    """A single threshold rule: min_value, max_value, method."""
    
    def __init__(self, min_value: float, max_value: Optional[float], method: ProcurementMethod):
        self.min_value = min_value
        self.max_value = max_value  # None = no upper bound
        self.method = method
    
    def applies(self, value: float) -> bool:
        if self.max_value is None:
            return value >= self.min_value
        return self.min_value <= value < self.max_value
class ProcurementRulesEngine:
    """Evaluates procurement rules to determine the required method.
    
    Default thresholds (configurable in Procurement Settings):
    - < 200,000 KES: RFQ/Direct
    - 200,000 - 499,999 KES: Restricted Tender
    - >= 500,000 KES: Open Tender
    """
    
    def __init__(self):
        self.settings = self._load_settings()
        self._thresholds = self._build_thresholds()
    
    def _load_settings(self) -> Dict[str, Any]:
        doc = frappe.get_single("Ugavi Procurement Settings")
        return {
            "direct_threshold": doc.direct_threshold or 200000,
            "restricted_threshold": doc.restricted_threshold or 500000,
            "open_threshold": doc.open_threshold or 500000,
            "enforce_donor_rules": doc.enforce_donor_rules or 0,
        }
    
    def _build_thresholds(self) -> list:
        return [
            ThresholdRule(0, self.settings["direct_threshold"], ProcurementMethod.DIRECT),
            ThresholdRule(
                self.settings["direct_threshold"],
                self.settings["restricted_threshold"],
                ProcurementMethod.RESTRICTED_TENDER,
            ),
            ThresholdRule(self.settings["open_threshold"], None, ProcurementMethod.OPEN_TENDER),
        ]
    
    def determine_method(
        self, estimated_value: float,
        donor: Optional[str] = None, item_category: Optional[str] = None,
    ) -> ProcurementMethod:
        if donor and self.settings.get("enforce_donor_rules"):
            donor_method = self._check_donor_rules(estimated_value, donor)
            if donor_method:
                return donor_method
        for rule in self._thresholds:
            if rule.applies(estimated_value):
                return rule.method
        frappe.throw(_("Could not determine procurement method for value {0}").format(estimated_value))
    
    def _check_donor_rules(self, value: float, donor: str) -> Optional[ProcurementMethod]:
        rules = frappe.get_all(
            "Donor Rule",
            filters={"parent": donor, "parenttype": "Donor Profile", "enabled": 1},
            fields=[
                "min_value",
                "max_value",
                "procurement_method",
                "effective_from",
                "effective_to",
            ],
            order_by="min_value asc",
        )
        today = frappe.utils.getdate()
        for rd in rules:
            if rd.effective_from and frappe.utils.getdate(rd.effective_from) > today:
                continue
            if rd.effective_to and frappe.utils.getdate(rd.effective_to) < today:
                continue
            r = ThresholdRule(rd.min_value, rd.max_value, ProcurementMethod(rd.procurement_method))
            if r.applies(value):
                return r.method
        return None
    
    def requires_prequalified_suppliers(self, method: ProcurementMethod) -> bool:
        return method in (ProcurementMethod.RESTRICTED_TENDER, ProcurementMethod.SINGLE_SOURCE)
    
    def can_override(self, method: ProcurementMethod) -> bool:
        return False  # All overrides require Waiver workflow


def get_engine() -> ProcurementRulesEngine:
    if not hasattr(frappe.local, "_ugavi_rules_engine"):
        frappe.local._ugavi_rules_engine = ProcurementRulesEngine()
    return frappe.local._ugavi_rules_engine


@frappe.whitelist()
def determine_procurement_method(estimated_value: float, donor: str = None, item_category: str = None) -> Dict[str, Any]:
    engine = get_engine()
    method = engine.determine_method(estimated_value, donor, item_category)
    return {
        "method": method.value,
        "requires_prequalified": engine.requires_prequalified_suppliers(method),
        "can_override": engine.can_override(method),
    }


def check_expiring_prequalifications():
    """Scheduled job: check for supplier prequalifications expiring within 30 days."""
    from frappe.utils import add_days, nowdate

    expiring = frappe.get_all(
        "Supplier Prequalification",
        filters={
            "status": "Prequalified",
            "expiry_date": ["between", [nowdate(), add_days(nowdate(), 30)]],
        },
        fields=["name", "supplier", "expiry_date"],
    )
    for e in expiring:
        frappe.log_error(
            title="Prequalification Expiring",
            message=f"Supplier {e.supplier} prequalification {e.name} expires on {e.expiry_date}"
        )
    return expiring