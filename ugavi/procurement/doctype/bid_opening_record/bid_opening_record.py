"""Bid Opening Record — records a 3-officer sealed-bid opening ceremony."""
import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime
import hashlib


class BidOpeningRecord(Document):
    """Immutable record of a bid opening session.

    Created by sealed_bid.open_bids() — stores officer identities,
    OTP verification logs, decrypted bid details, and an optional
    SHA-256 hash for tamper detection.
    """

    def before_insert(self):
        if not getattr(self.flags, "opening_verified", False):
            frappe.throw(
                "Bid Opening Records can only be created by the verified "
                "three-officer opening ceremony."
            )
        self._validate_officers()
        if not all((self.otp_log_1, self.otp_log_2, self.otp_log_3)):
            frappe.throw("All three officer verification logs are required")
        if not self.opening_date:
            self.opening_date = now_datetime()
        self.record_hash = self._compute_hash()

    def before_save(self):
        if not self.is_new():
            frappe.throw("Bid Opening Records are immutable")

    def on_trash(self):
        frappe.throw("Bid Opening Records cannot be deleted")

    def _validate_officers(self):
        officers = [self.officer_1, self.officer_2, self.officer_3]
        if len(set(officers)) != 3:
            frappe.throw("Three distinct bid-opening officers are required")
        configured = frappe.db.get_value(
            "Tender",
            self.tender,
            ["opening_officer_1", "opening_officer_2", "opening_officer_3"],
            as_dict=True,
        )
        if not configured or set(officers) != {
            configured.opening_officer_1,
            configured.opening_officer_2,
            configured.opening_officer_3,
        }:
            frappe.throw("Opening officers must match the Tender ceremony panel")

    def _compute_hash(self):
        opened = "|".join(
            sorted(f"{row.bid}:{row.supplier}" for row in self.bids_opened)
        )
        payload = "|".join(
            [
                self.tender,
                str(self.opening_date),
                self.officer_1,
                self.officer_2,
                self.officer_3,
                self.outcome,
                opened,
            ]
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def after_insert(self):
        from frappe.utils.file_manager import save_file
        from frappe.utils.pdf import get_pdf

        rows = "".join(
            f"<tr><td>{frappe.utils.escape_html(row.bid)}</td>"
            f"<td>{frappe.utils.escape_html(row.supplier)}</td></tr>"
            for row in self.bids_opened
        )
        html = (
            f"<h1>Bid Opening Record {frappe.utils.escape_html(self.name)}</h1>"
            f"<p>Tender: {frappe.utils.escape_html(self.tender)}</p>"
            f"<p>Opened: {self.opening_date}</p>"
            f"<p>Officers: {frappe.utils.escape_html(self.officer_1)}, "
            f"{frappe.utils.escape_html(self.officer_2)}, "
            f"{frappe.utils.escape_html(self.officer_3)}</p>"
            f"<table><tr><th>Bid</th><th>Supplier</th></tr>{rows}</table>"
            f"<p>SHA-256: {self.record_hash}</p>"
        )
        pdf = get_pdf(html)
        file_doc = save_file(
            f"{self.name}.pdf",
            pdf,
            self.doctype,
            self.name,
            is_private=1,
        )
        frappe.db.set_value(self.doctype, self.name, "signed_record", file_doc.file_url)
