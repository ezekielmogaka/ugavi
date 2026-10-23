"""Bid — supplier bid with encrypted content support."""
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import now_datetime
import hashlib
import json
import base64


class Bid(Document):
    """Supplier bid for a tender."""

    def validate(self):
        self._validate_immutability()
        self._validate_deadline()
        self._check_duplicate()

    def _validate_immutability(self):
        previous = self.get_doc_before_save()
        if previous and previous.status == "Submitted":
            frappe.throw(_("Submitted bids are immutable until the opening ceremony"))

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

        if tender.status not in ("Published", "Bids Received"):
            frappe.throw(_("Tender is not accepting bids"))
        if now_datetime() > tender.submission_deadline:
            self.status = "Late"
            frappe.throw(_("Submission deadline has passed"))

        if tender.procurement_method == "Restricted Tender":
            from ugavi.procurement.doctype.supplier_prequalification.supplier_prequalification import (
                is_prequalified,
            )

            if not is_prequalified(self.supplier, tender.item_category):
                frappe.throw(_("Supplier is not prequalified for this restricted tender category"))

        if tender.procurement_method in ("Restricted Tender", "Open Tender"):
            if not tender.public_key:
                frappe.throw(_("Tender encryption key is unavailable"))
            from ugavi.procurement.services.sealed_bid import encrypt_bid_content

            attachment = None
            if self.technical_proposal:
                file_doc = frappe.get_doc("File", {"file_url": self.technical_proposal})
                attachment = {
                    "name": file_doc.file_name,
                    "content": base64.b64encode(file_doc.get_content()).decode(),
                }
                frappe.delete_doc("File", file_doc.name, ignore_permissions=True)
                self.technical_proposal = None
            content = json.dumps({
                "bidder": self.supplier,
                "amount": getattr(self, "bid_amount", 0),
                "delivery": getattr(self, "delivery_days", 0),
                "technical_proposal": attachment,
            })
            encrypted = encrypt_bid_content(content, tender.public_key.encode())
            self.encrypted_key = encrypted["encrypted_key"]
            self.nonce = encrypted["nonce"]
            self.encrypted_content = encrypted["ciphertext"]
            self.bid_amount = 0
            self.delivery_days = 0

        self.status = "Submitted"
        self.submission_date = now_datetime()
        self.submission_receipt = hashlib.sha256(
            f"{self.name}|{self.tender}|{self.supplier}|{self.submission_date}".encode()
        ).hexdigest()
        self.save()

        # Update tender status
        if tender.status == "Published":
            tender.status = "Bids Received"
            tender.save(ignore_permissions=True)