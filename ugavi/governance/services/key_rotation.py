"""Tender-scoped sealed-bid key lifetime enforcement (GA-046)."""
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import add_to_date, get_datetime, now_datetime

from ugavi.governance.services.feature_flags import is_enabled


def get_rotation_policy():
    """Return (enabled, rotation_days, max_key_age_days)."""
    return (
        is_enabled("sealed_bid_key_rotation"),
        frappe.db.get_single_value("Ugavi Procurement Settings", "key_rotation_days") or 90,
        frappe.db.get_single_value("Ugavi Procurement Settings", "max_key_age_days") or 120,
    )


def check_and_rotate(tender_name: str) -> bool:
    """Check if a tender's sealed-bid key needs rotation and rotate if so.

    Returns True if rotated, False if no rotation needed.
    """
    enabled, rotation_days, max_age = get_rotation_policy()
    if not enabled:
        return False

    key_doc_name = frappe.db.get_value(
        "Sealed Bid Key", {"tender": tender_name}, "name"
    )
    if not key_doc_name:
        return False

    key_doc = frappe.get_doc("Sealed Bid Key", key_doc_name)

    # An opened tender's key is evidence and must remain immutable.
    if key_doc.key_reconstructed:
        return False

    key_age = now_datetime() - get_datetime(key_doc.creation)
    if key_age < timedelta(days=rotation_days):
        return False

    # Enforce maximum age — refuse to operate with stale key
    if key_age > timedelta(days=max_age):
        frappe.throw(
            _("Sealed-bid key for {0} has exceeded maximum age of {1} days. "
              "Key rotation is mandatory.").format(tender_name, max_age)
        )

    # Perform rotation: generate new keypair, re-encrypt all unopened bids
    _rotate_keypair(key_doc, tender_name)
    return True


def _rotate_keypair(key_doc, tender_name: str):
    """Replace a key only while no bid has been encrypted with it."""
    if frappe.db.count("Bid", {"tender": tender_name}):
        frappe.throw(
            _(
                "The sealed-bid key for {0} cannot be rotated after bids exist. "
                "Cancel and reissue the tender so suppliers can encrypt against a new key."
            ).format(tender_name)
        )

    officers = [
        key_doc.share_1_user,
        key_doc.share_2_user,
        key_doc.share_3_user,
    ]
    frappe.delete_doc(
        "Sealed Bid Key", key_doc.name, ignore_permissions=True, force=True
    )
    from ugavi.procurement.services.sealed_bid import generate_and_distribute_keys

    result = generate_and_distribute_keys(tender_name, officers)
    frappe.db.set_value("Tender", tender_name, "public_key", result["public_key_pem"])
    frappe.logger("ugavi").info(
        "Rotated unused sealed-bid key for tender %s", tender_name
    )


def flag_stale_keys():
    """Scheduled task: flag any sealed-bid keys nearing max age."""
    enabled, _, max_age = get_rotation_policy()
    if not enabled:
        return

    stale_threshold = max_age - 10  # warn 10 days before max age
    cutoff = add_to_date(now_datetime(), days=-stale_threshold)

    stale_keys = frappe.get_all(
        "Sealed Bid Key",
        filters={"key_reconstructed": 0, "creation": ["<", cutoff]},
        fields=["name", "tender", "creation"],
    )
    for key in stale_keys:
        frappe.log_error(
            title="Key Rotation Required",
            message=f"Tender {key.tender}: key is {key.creation} (stale)"
        )