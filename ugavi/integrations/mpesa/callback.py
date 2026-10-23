"""Safaricom Daraja callback endpoints.

Safaricom posts the authoritative outcome of a B2C request here. These
endpoints only record what Safaricom reports; they never synthesise a result.
"""
import json
import logging

import frappe
from frappe.utils import now_datetime

from ugavi.integrations.mpesa import CONVERSATION_FIELD, STATUS_FIELD

logger = logging.getLogger(__name__)


def _payload():
    if frappe.request and frappe.request.data:
        try:
            return json.loads(frappe.request.data)
        except ValueError:
            logger.warning("Unparseable M-Pesa callback payload")
    return frappe.local.form_dict or {}


def _conversation_id(payload):
    result = payload.get("Result") or {}
    return result.get("ConversationID") or payload.get("ConversationID")


def _record(action, payload, status):
    conversation_id = _conversation_id(payload)
    frappe.get_doc(
        {
            "doctype": "Audit Log",
            "action": action,
            "user": "Administrator",
            "outcome": "Success" if status == "Confirmed" else "Failed",
            "ip_address": getattr(frappe.local, "request_ip", None) or "N/A",
            "timestamp": now_datetime(),
        }
    ).insert(ignore_permissions=True)

    if not conversation_id:
        return
    payment_entry = frappe.db.get_value(
        "Payment Entry", {CONVERSATION_FIELD: conversation_id}, "name"
    )
    if payment_entry:
        frappe.db.set_value(
            "Payment Entry",
            payment_entry,
            STATUS_FIELD,
            status,
            update_modified=False,
        )


@frappe.whitelist(allow_guest=True)
def result():
    payload = _payload()
    code = str(((payload.get("Result") or {}).get("ResultCode")))
    _record("MPESA_B2C_RESULT", payload, "Confirmed" if code == "0" else "Failed")
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


@frappe.whitelist(allow_guest=True)
def timeout():
    _record("MPESA_B2C_TIMEOUT", _payload(), "Failed")
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


@frappe.whitelist(allow_guest=True)
def status_result():
    payload = _payload()
    code = str(((payload.get("Result") or {}).get("ResultCode")))
    _record("MPESA_STATUS_RESULT", payload, "Confirmed" if code == "0" else "Failed")
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


@frappe.whitelist(allow_guest=True)
def status_timeout():
    _record("MPESA_STATUS_TIMEOUT", _payload(), "Failed")
    return {"ResultCode": 0, "ResultDesc": "Accepted"}
