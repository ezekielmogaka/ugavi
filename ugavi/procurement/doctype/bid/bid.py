"""Bid — supplier bid with encrypted content support."""
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import now_datetime


class Bid(Document):
    """Supplier bid for a tender."""

    def validate(self):
        self._validate_deadline()
        self._check_duplicate()

    def _validate_deadline(self):
        if self.tender:
            tender = frappe.get_cached_doc("Tender", self.tender)
            if tender.submission_deadline and now_datetime() > tender.submission_deadline:
                self.status = "Late"

    def _check_duplicate(self):
        if self.status in ("Draft", "Submitted"):
            existing = frappe.db.exists(
                "Bid",
                {"tender": self.tender, "supplier": self.supplier, "name": ("!=", self.name)},
            )
            if existing:
                frappe.throw(f"Bid already exists for this supplier on tender {self.tender}")

    @frappe.whitelist()
    def submit_bid(self):
        """Submit bid — encrypt if tender uses sealed bids."""
        tender = frappe.get_doc("Tender", self.tender)

        if now_datetime() > tender.submission_deadline:
            self.status = "Late"
            frappe.throw(_("Submission deadline has passed"))

        if tender.public_key:
            # Encrypt bid content
            from ugavi.procurement.services.sealed_bid import encrypt_bid_content
            import json
            content = json.dumps({
                "bidder": self.supplier,
                "amount": getattr(self, "bid_amount", 0),
                "delivery": getattr(self, "delivery_days", 0),
            })
            encrypted = encrypt_bid_content(content, tender.public_key.encode())
            self.encrypted_key = encrypted["encrypted_key"]
            self.nonce = encrypted["nonce"]
            self.encrypted_content = encrypted["ciphertext"]

        self.status = "Submitted"
        self.submission_date = now_datetime()
        self.save()

        # Update tender status
        if tender.status == "Published":
            tender.status = "Bids Received"
            tender.save(ignore_permissions=True)