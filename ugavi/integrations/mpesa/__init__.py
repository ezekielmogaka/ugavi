"""M-Pesa (Daraja B2C) payment adapter for supplier disbursements.

This module is a configuration boundary, not a simulator. When Safaricom
credentials are absent the adapter refuses to act and the Payment Entry is
marked as not transmitted, so the ledger never records a disbursement that
Safaricom did not actually accept.
"""
import base64
import logging
import os

import frappe
from frappe import _
from frappe.utils import now_datetime

logger = logging.getLogger(__name__)

SANDBOX_HOST = "https://sandbox.safaricom.co.ke"
PRODUCTION_HOST = "https://api.safaricom.co.ke"

MPESA_MODE_OF_PAYMENT = "M-Pesa"

STATUS_FIELD = "ugavi_mpesa_status"
CONVERSATION_FIELD = "ugavi_mpesa_conversation_id"


def normalize_msisdn(phone):
    """Return a Safaricom MSISDN (2547XXXXXXXX) or raise for an unusable value."""
    digits = "".join(ch for ch in str(phone or "") if ch.isdigit())
    if digits.startswith("254"):
        pass
    elif digits.startswith("0"):
        digits = "254" + digits[1:]
    elif len(digits) == 9:
        digits = "254" + digits
    if len(digits) != 12:
        frappe.throw(
            _("{0} is not a valid Kenyan mobile number for M-Pesa.").format(phone),
            frappe.ValidationError,
        )
    return digits


class MpesaAdapter:
    """Abstract M-Pesa adapter interface."""

    def send_b2c(self, amount, phone, remarks="", occasion=""):
        raise NotImplementedError

    def check_transaction_status(self, transaction_id):
        raise NotImplementedError

    def get_access_token(self):
        raise NotImplementedError


class DarajaMpesaAdapter(MpesaAdapter):
    """Safaricom Daraja API implementation."""

    def __init__(self):
        self.consumer_key = os.getenv("MPESA_CONSUMER_KEY", "")
        self.consumer_secret = os.getenv("MPESA_CONSUMER_SECRET", "")
        self.security_credential = os.getenv("MPESA_SECURITY_CREDENTIAL", "")
        self.initiator = os.getenv("MPESA_INITIATOR_NAME", "")
        self.shortcode = os.getenv("MPESA_SHORTCODE", "")
        self.production = os.getenv("MPESA_ENVIRONMENT") == "production"
        self.host = PRODUCTION_HOST if self.production else SANDBOX_HOST

    @property
    def auth_url(self):
        return f"{self.host}/oauth/v1/generate?grant_type=client_credentials"

    @property
    def b2c_url(self):
        return f"{self.host}/mpesa/b2c/v3/paymentrequest"

    @property
    def status_url(self):
        return f"{self.host}/mpesa/transactionstatus/v1/query"

    def is_configured(self):
        return bool(
            self.consumer_key
            and self.consumer_secret
            and self.security_credential
            and self.initiator
            and self.shortcode
        )

    def _require_configuration(self):
        if not self.is_configured():
            frappe.throw(
                _(
                    "M-Pesa disbursement is not configured. Set MPESA_CONSUMER_KEY, "
                    "MPESA_CONSUMER_SECRET, MPESA_SECURITY_CREDENTIAL, "
                    "MPESA_INITIATOR_NAME and MPESA_SHORTCODE before transmitting."
                ),
                frappe.ValidationError,
            )

    def get_access_token(self):
        self._require_configuration()
        import requests

        credential = base64.b64encode(
            f"{self.consumer_key}:{self.consumer_secret}".encode()
        ).decode()
        response = requests.get(
            self.auth_url,
            headers={"Authorization": f"Basic {credential}"},
            timeout=15,
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        if not token:
            frappe.throw(
                _("Safaricom did not return an access token."), frappe.ValidationError
            )
        return token

    def send_b2c(self, amount, phone, remarks="Supplier Payment", occasion=""):
        self._require_configuration()
        import requests

        token = self.get_access_token()
        payload = {
            "OriginatorConversationID": frappe.generate_hash(length=20),
            "InitiatorName": self.initiator,
            "SecurityCredential": self.security_credential,
            "CommandID": "BusinessPayment",
            "Amount": int(amount),
            "PartyA": self.shortcode,
            "PartyB": normalize_msisdn(phone),
            "Remarks": (remarks or "")[:100],
            "QueueTimeOutURL": frappe.utils.get_url(
                "/api/method/ugavi.integrations.mpesa.callback.timeout"
            ),
            "ResultURL": frappe.utils.get_url(
                "/api/method/ugavi.integrations.mpesa.callback.result"
            ),
            "Occasion": (occasion or "")[:100],
        }
        response = requests.post(
            self.b2c_url,
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        result = response.json()
        self._log("MPESA_B2C", result)
        return result

    def check_transaction_status(self, transaction_id):
        self._require_configuration()
        import requests

        token = self.get_access_token()
        payload = {
            "Initiator": self.initiator,
            "SecurityCredential": self.security_credential,
            "CommandID": "TransactionStatusQuery",
            "TransactionID": transaction_id,
            "PartyA": self.shortcode,
            "IdentifierType": "4",
            "ResultURL": frappe.utils.get_url(
                "/api/method/ugavi.integrations.mpesa.callback.status_result"
            ),
            "QueueTimeOutURL": frappe.utils.get_url(
                "/api/method/ugavi.integrations.mpesa.callback.status_timeout"
            ),
            "Remarks": "Status check",
            "Occasion": "Supplier payment verification",
        }
        response = requests.post(
            self.status_url,
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        result = response.json()
        self._log("MPESA_STATUS", result)
        return result

    def _log(self, action, response):
        frappe.get_doc(
            {
                "doctype": "Audit Log",
                "action": action,
                "user": frappe.session.user,
                "outcome": "Success"
                if str(response.get("ResponseCode")) == "0"
                else "Failed",
                "ip_address": getattr(frappe.local, "request_ip", None) or "N/A",
                "timestamp": now_datetime(),
            }
        ).insert(ignore_permissions=True)


def get_adapter():
    return DarajaMpesaAdapter()


def queue_supplier_payment(doc, method=None):
    """`Payment Entry.on_submit` handler.

    Only outgoing M-Pesa disbursements are considered. Submission is never
    blocked: when the gateway is unconfigured the entry is flagged for manual
    disbursement instead.
    """
    if doc.payment_type != "Pay" or doc.mode_of_payment != MPESA_MODE_OF_PAYMENT:
        return

    adapter = get_adapter()
    if not adapter.is_configured():
        _set_status(doc, "Not Transmitted")
        logger.info(
            "M-Pesa not configured; %s flagged for manual disbursement", doc.name
        )
        return

    try:
        response = _disburse(doc, adapter=adapter)
    except Exception:
        logger.exception("M-Pesa disbursement failed for %s", doc.name)
        _set_status(doc, "Failed")
        return

    _apply_response(doc, response)


@frappe.whitelist()
def send_supplier_payment(payment_entry, phone_number=None):
    """Manually transmit a submitted M-Pesa Payment Entry to Safaricom."""
    doc = frappe.get_doc("Payment Entry", payment_entry)
    if doc.docstatus != 1:
        frappe.throw(_("Payment Entry must be submitted."))
    if doc.mode_of_payment != MPESA_MODE_OF_PAYMENT:
        frappe.throw(_("Payment mode must be {0}.").format(MPESA_MODE_OF_PAYMENT))

    response = _disburse(doc, phone_number=phone_number)
    _apply_response(doc, response)
    return response


def _disburse(doc, phone_number=None, adapter=None):
    adapter = adapter or get_adapter()
    adapter._require_configuration()
    if not phone_number:
        phone_number = frappe.db.get_value("Supplier", doc.party, "mobile_no")
    if not phone_number:
        frappe.throw(_("No phone number for supplier {0}.").format(doc.party))
    return adapter.send_b2c(
        amount=doc.paid_amount,
        phone=phone_number,
        remarks=f"Payment for {doc.name}",
        occasion=f"Supplier: {doc.party}",
    )


def _apply_response(doc, response):
    accepted = str(response.get("ResponseCode")) == "0"
    _set_status(doc, "Sent" if accepted else "Failed")
    if accepted and response.get("ConversationID"):
        frappe.db.set_value(
            "Payment Entry",
            doc.name,
            CONVERSATION_FIELD,
            response["ConversationID"],
            update_modified=False,
        )


def _set_status(doc, status):
    if not frappe.get_meta("Payment Entry").has_field(STATUS_FIELD):
        return
    frappe.db.set_value(
        "Payment Entry", doc.name, STATUS_FIELD, status, update_modified=False
    )
