"""Tender — lifecycle management with sealed-bid support."""
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import now_datetime


class Tender(Document):
    """Tender with publishing, sealed bids, and award workflow."""

    def validate(self):
        self._validate_officers()
        self._validate_deadline()

    def _validate_officers(self):
        officers = [
            self.opening_officer_1,
            self.opening_officer_2,
            self.opening_officer_3,
        ]
        # Only validate if all officers are set
        if any(officers) and not all(officers):
            if self.procurement_method in ("Restricted Tender", "Open Tender"):
                frappe.throw("All 3 Bid Opening Officers must be assigned for sealed-bid tenders")
        if all(officers):
            if len(set(officers)) != 3:
                frappe.throw("Bid Opening Officers must be 3 distinct users")

    def _validate_deadline(self):
        if self.submission_deadline and self.publish_date:
            if self.submission_deadline <= self.publish_date:
                frappe.throw("Submission deadline must be after publish date")

    @frappe.whitelist()
    def publish(self):
        """Publish the tender and generate encryption keys if needed."""
        if self.status != "Draft":
            frappe.throw("Only draft tenders can be published")

        self.publish_date = now_datetime()

        # Generate sealed-bid keypair for restricted/open tenders
        if self.procurement_method in ("Restricted Tender", "Open Tender"):
            self._generate_keys()

        self.status = "Published"
        self.save()

    def _generate_keys(self):
        from ugavi.procurement.services.sealed_bid import generate_and_distribute_keys
        result = generate_and_distribute_keys(
            tender=self.name,
            officers=[
                self.opening_officer_1,
                self.opening_officer_2,
                self.opening_officer_3,
            ],
        )
        self.public_key = result["public_key_pem"]
        self.key_generated_at = now_datetime()

    def _store_private_key(self, private_pem):
        """DEPRECATED — key is now split at generation, never stored in DB."""
        frappe.throw(
            "Private keys must never be stored in the database. "
            "Use generate_and_distribute_keys instead."
        )

    @frappe.whitelist()
    def award(self, supplier: str, amount: float):
        """Award tender to supplier and create Purchase Order."""
        if self.status != "Under Evaluation":
            frappe.throw("Tender must be under evaluation to award")

        self.awarded_supplier = supplier
        self.award_amount = amount
        self.status = "Awarded"
        self.save()

        # Create Purchase Order
        try:
            from frappe import get_doc
            po = get_doc({
                "doctype": "Purchase Order",
                "supplier": supplier,
                "ugavi_tender": self.name,
                "ugavi_donor": self.donor,
                "transaction_date": now_datetime().date(),
            })
            po.insert()
            self.purchase_order = po.name
            self.save()
            frappe.msgprint(_("Purchase Order {0} created").format(po.name))
        except Exception as e:
            frappe.log_error(f"PO creation: {e}", "Tender Award")

    @frappe.whitelist()
    def close(self):
        """Close the tender."""
        self.status = "Closed"
        self.save()