import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime
import hashlib


class AuditLog(Document):
    """Immutable audit log. Records are append-only with hash chaining."""

    def before_insert(self):
        self.timestamp = now_datetime()
        if not self.ip_address and hasattr(frappe.local, "request_ip"):
            self.ip_address = frappe.local.request_ip
        self._compute_hash()

    def _compute_hash(self):
        """Hash this entry linked to the previous entry for tamper evidence."""
        prev = frappe.get_all(
            "Audit Log",
            filters={"tender": self.tender},
            fields=["record_hash"],
            order_by="creation desc",
            limit=1,
        )
        prev_hash = prev[0].record_hash if prev else "genesis"
        raw = f"{prev_hash}|{self.tender}|{self.user}|{self.action}|{self.outcome}|{self.timestamp}"
        self.record_hash = hashlib.sha256(raw.encode()).hexdigest()

    def validate(self):
        # Audit Log is append-only — no updates allowed after insert
        if self.get_doc_before_save():
            frappe.throw("Audit Log records cannot be modified")