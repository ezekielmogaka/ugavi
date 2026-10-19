import frappe
from frappe.model.document import Document
from frappe import _


class SealedBidKey(Document):
    """Sealed Bid Key — stores ONLY SSS shares, never the full private key.

    TN13 FIX: private_key_pem is removed from the schema. The RSA private key
    is split into 3 Shamir shares at generation time (in memory only) and
    only the encrypted shares are persisted. Reconstruction requires all 3
    officers to provide their shares, after which the key is used to decrypt
    bids and immediately discarded.
    """

    def validate(self):
        self._validate_distinct_officers()
        self._validate_no_private_key_leak()

    def _validate_distinct_officers(self):
        officers = [
            self.share_1_user,
            self.share_2_user,
            self.share_3_user,
        ]
        if not all(officers):
            frappe.throw(_("All 3 officers must be assigned"))
        if len(set(officers)) != 3:
            frappe.throw(_("Share officers must be 3 distinct users"))

    def _validate_no_private_key_leak(self):
        """Ensure no private key PEM is ever written to this document."""
        if hasattr(self, "private_key_pem") and self.private_key_pem:
            frappe.throw(_("Private key must never be stored in the database"))

    def mark_reconstructed(self, user: str):
        """Record that the key was reconstructed (for audit trail)."""
        from frappe.utils import now_datetime
        self.key_reconstructed = 1
        self.reconstructed_at = now_datetime()
        self.reconstructed_by = user
        self.save(ignore_permissions=True)
        frappe.db.commit()

    @frappe.whitelist()
    def get_share_for_officer(self, officer_user: str) -> dict | None:
        """Return a single share for the given officer (for bid opening)."""
        for i, fld in [("1", self.share_1_user), ("2", self.share_2_user),
                        ("3", self.share_3_user)]:
            if fld == officer_user:
                return {
                    "share_x": i,
                    "share_y": self.get(f"share_{i}_data"),
                }
        return None
