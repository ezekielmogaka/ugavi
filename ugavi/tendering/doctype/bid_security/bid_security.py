"""Bid Security — bid bond, guarantee, or tender security management."""
import frappe
from frappe.model.document import Document
from frappe import _


class BidSecurity(Document):
    """Bid Security (bid bond/guarantee) tracking for tenders."""

    def validate(self):
        self._validate_bid_identity()
        if self.valid_until and self.received_date:
            if frappe.utils.getdate(self.valid_until) <= frappe.utils.getdate(self.received_date):
                frappe.throw(_("Valid until date must be after received date."))
        if self.verification_status == "Verified" and not self.verified_by:
            frappe.throw(_("Verified bid security must record the verifier."))

    def before_save(self):
        if self.security_amount:
            # Validate against tender requirement
            if self.tender:
                tender = frappe.get_cached_doc("Tender", self.tender)
                req = tender.get("bid_security_required")
                if req and self.security_amount < req:
                    frappe.throw(_("Bid security amount ({0}) is below minimum required ({1})").format(
                        frappe.format_value(self.security_amount, "Currency"),
                        frappe.format_value(req, "Currency"),
                    ))

    @frappe.whitelist()
    def verify(self, verification_notes: str | None = None):
        if self.status != "Held":
            frappe.throw(_("Only held bid security can be verified."))
        if not self.valid_until or frappe.utils.getdate(
            self.valid_until
        ) < frappe.utils.getdate(frappe.utils.today()):
            frappe.throw(_("Expired bid security cannot be verified."))
        self.verification_status = "Verified"
        self.verified_by = frappe.session.user
        self.verified_at = frappe.utils.now_datetime()
        self.verification_notes = verification_notes
        self.save()

    @frappe.whitelist()
    def release(self):
        if self.status != "Held":
            frappe.throw(_("Only held bid security can be released."))
        self.status = "Released"
        self.release_date = frappe.utils.today()
        self.save()

    @frappe.whitelist()
    def forfeit(self):
        if self.status != "Held":
            frappe.throw(_("Only held bid security can be forfeited."))
        self.status = "Forfeited"
        self.forfeit_date = frappe.utils.today()
        self.save()

    def _validate_bid_identity(self):
        if not self.bid:
            return
        bid = frappe.db.get_value(
            "Bid", self.bid, ["tender", "supplier"], as_dict=True
        )
        if not bid or bid.tender != self.tender or bid.supplier != self.supplier:
            frappe.throw(_("Bid security must match the bid's tender and supplier."))
