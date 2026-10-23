"""Feature Flags — runtime toggles for safe rollout.

Usage:
    from ugavi.governance.services.feature_flags import is_enabled
    if is_enabled("sealed_bid_v2"):
        use_new_crypto()
"""
import frappe
from frappe import _


# All known feature flags with defaults (off until explicitly enabled)
FLAG_DEFAULTS = {
    "sealed_bid_key_rotation": False,     # GA-046: auto key rotation
    "supplier_portal": False,             # GA-007: supplier self-service
    "evaluation_ai_assist": False,        # ADR-003: declined for MVP
    "mobile_offline": False,              # GA-037: offline mode
    "hash_chain_audit": True,             # GA-045: enabled by default
    "rate_limiting": True,                # GA-010: enabled by default
    "structured_logging": True,           # GA-053: structured JSON logs
    "idempotent_jobs": False,             # GA-013: idempotent scheduled jobs
    "graceful_degradation": False,        # GA-058: circuit breakers
    "dark_mode_support": True,            # Frappe v16 native
}


def is_enabled(flag_name: str) -> bool:
    """Check if a feature flag is enabled.

    Order of precedence:
    1. System Settings override (frappe.db.get_single_value)
    2. Default value from FLAG_DEFAULTS
    """
    default = FLAG_DEFAULTS.get(flag_name, False)
    try:
        from frappe.db import get_single_value
        val = get_single_value("Ugavi Procurement Settings", flag_name)
        if val is not None:
            return bool(val)
    except Exception:
        pass
    return default


def enable(flag_name: str):
    """Enable a feature flag (persists in Ugavi Procurement Settings)."""
    if flag_name not in FLAG_DEFAULTS:
        frappe.throw(_("Unknown feature flag: {0}").format(flag_name))
    frappe.db.set_single_value("Ugavi Procurement Settings", flag_name, 1)
    frappe.db.commit()


def disable(flag_name: str):
    """Disable a feature flag."""
    frappe.db.set_single_value("Ugavi Procurement Settings", flag_name, 0)
    frappe.db.commit()


def list_flags() -> dict:
    """Return all flags with their current state."""
    return {name: is_enabled(name) for name in FLAG_DEFAULTS}