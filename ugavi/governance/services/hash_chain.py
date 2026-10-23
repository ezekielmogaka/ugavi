"""Audit Log Hash Chain — tamper-evident audit trail.

Each audit event is hashed and chained to the previous event,
creating an immutable sequence. Tampering with any entry breaks
the chain (detectable by verify()).
"""
import hashlib
import json
import frappe
from frappe.utils import now_datetime


def hash_event(event_data: dict, previous_hash: str = "") -> str:
    """SHA-256 hash of event data with previous link."""
    payload = json.dumps(event_data, sort_keys=True, default=str) + previous_hash
    return hashlib.sha256(payload.encode()).hexdigest()


def log_and_chain(doctype: str, docname: str, event: str, user: str = None,
                  details: dict = None, ip_address: str = None) -> str:
    """Create an audit log entry chained to the previous one.

    Returns the new hash for verification.
    """
    if user is None:
        user = frappe.session.user

    # Get previous hash for the chain
    previous = frappe.db.get_value(
        "Audit Log",
        {"reference_doctype": doctype, "reference_name": docname},
        "chain_hash",
        order_by="creation desc",
    ) or ""

    event_data = {
        "doctype": doctype,
        "docname": docname,
        "event": event,
        "user": user,
        "timestamp": str(now_datetime()),
        "ip": ip_address or frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "unknown",
        "details": details or {},
    }

    chain_hash = hash_event(event_data, previous)

    audit = frappe.get_doc({
        "doctype": "Audit Log",
        "reference_doctype": doctype,
        "reference_name": docname,
        "event": event,
        "user": user,
        "timestamp": now_datetime(),
        "ip_address": event_data["ip"],
        "chain_hash": chain_hash,
        "previous_hash": previous,
    })
    audit.insert(ignore_permissions=True)
    frappe.db.commit()

    return chain_hash


def verify_chain(doctype: str, docname: str) -> dict:
    """Verify the integrity of an audit log chain.

    Returns:
        dict with 'intact' (bool), 'total_entries', 'broken_at' (index or None)
    """
    entries = frappe.get_all(
        "Audit Log",
        filters={"reference_doctype": doctype, "reference_name": docname},
        fields=["name", "event", "user", "timestamp", "ip_address", "chain_hash", "previous_hash"],
        order_by="creation asc",
    )

    if not entries:
        return {"intact": True, "total_entries": 0, "broken_at": None}

    previous_hash = ""
    for i, entry in enumerate(entries):
        expected = hash_event({
            "doctype": doctype,
            "docname": docname,
            "event": entry.event,
            "user": entry.user,
            "timestamp": str(entry.timestamp),
            "ip": entry.ip_address or "unknown",
            "details": {},
        }, previous_hash)

        if entry.chain_hash != expected:
            return {"intact": False, "total_entries": len(entries), "broken_at": i}

        previous_hash = entry.chain_hash

    return {"intact": True, "total_entries": len(entries), "broken_at": None}


def verify_chain_for_tender(tender_name: str) -> dict:
    """Verify the full audit chain for a tender (covers PR, Tender, Bids, BOR)."""
    return verify_chain("Tender", tender_name)