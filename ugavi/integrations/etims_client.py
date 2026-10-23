"""eTIMS Integration Service (GA-011).

Kenya Revenue Authority (KRA) electronic Tax Invoice Management System.
This is a scaffold — full integration requires KRA API credentials and
sandbox access for testing.

Integration Flow:
    1. Supplier submits bid → KRA PIN validated
    2. Contract awarded → eTIMS invoice registered
    3. Payment milestone → eTIMS invoice transmitted
    4. Periodic reconciliation → eTIMS vs Ugavi invoice totals
"""
import frappe
from typing import Optional, Dict

ETIMS_SANDBOX_URL = "https://etims-sandbox.kra.go.ke/api/v1"


class ETIMSClient:
    """Configuration boundary for a future verified KRA sandbox contract."""

    def __init__(self):
        if not self._is_sandbox():
            frappe.throw(
                "Production eTIMS transmission is not enabled in this release.",
                frappe.ValidationError,
            )
        self.base_url = ETIMS_SANDBOX_URL
        self.api_key = self._get_api_key()
        self.api_secret = self._get_api_secret()

    def _is_sandbox(self) -> bool:
        return True

    def _get_api_key(self) -> Optional[str]:
        return frappe.db.get_single_value("Ugavi Procurement Settings", "etims_api_key")

    def _get_api_secret(self) -> Optional[str]:
        return frappe.get_single("Ugavi Procurement Settings").get_password(
            "etims_api_secret", raise_exception=False
        )

    def validate_kra_pin(self, pin: str) -> Dict:
        """Validate syntax locally; remote validity requires the KRA contract."""
        if not pin or len(pin) != 11 or not pin.startswith(("A", "P")):
            return {"valid": False, "error": "Invalid KRA PIN format"}
        return {
            "valid": None,
            "format_valid": True,
            "status": "remote_validation_unavailable",
            "mode": "sandbox",
        }

    def generate_invoice(self, contract: str, amount: float,
                         tax_rate: float = 16.0) -> Dict:
        """Reject transmission until the authoritative KRA payload is configured."""
        self._require_verified_contract()

    def submit_invoice(self, invoice_no: str) -> Dict:
        """Reject fake acknowledgements; only KRA may acknowledge submission."""
        self._require_verified_contract()

    def reconcile(self, start_date: str, end_date: str) -> Dict:
        self._require_verified_contract()

    def _require_verified_contract(self):
        frappe.throw(
            "KRA eTIMS sandbox transmission is unavailable until the approved API "
            "contract, credentials, and test certificate are configured.",
            frappe.ValidationError,
        )


def validate_supplier_pin(supplier_name: str) -> Dict:
    """Validate supplier's KRA PIN before registration."""
    pin = frappe.db.get_value("Supplier", supplier_name, "kra_pin")
    if not pin:
        return {"valid": False, "error": "Supplier has no KRA PIN on file"}
    client = ETIMSClient()
    return client.validate_kra_pin(pin)


def generate_contract_invoice(contract_name: str, amount: float) -> Dict:
    """Generate eTIMS invoice for a contract milestone payment."""
    client = ETIMSClient()
    return client.generate_invoice(contract_name, amount)


def check_e_tims_status():
    """Report configuration honestly without simulating KRA connectivity."""
    client = ETIMSClient()
    return {
        "status": "credentials_present_contract_pending"
        if client.api_key and client.api_secret
        else "not_configured",
        "mode": "sandbox",
        "transmission_enabled": False,
    }