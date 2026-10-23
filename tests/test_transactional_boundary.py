"""Transactional Boundary Tests — verify ACID properties.

Tests that multi-doc operations either fully commit or fully rollback.
"""
import frappe
import unittest
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime
from frappe import _


class TestProcurementTransactionBoundary(FrappeTestCase):
    """Verify PR + Approval workflow is atomic."""

    def setUp(self):
        self.pr_name = None
        self.donor = "TEST-TX-DONOR"

    def test_pr_creation_with_failed_approval_rollback(self):
        """If approval fails, entire PR+approval chain rolls back."""
        try:
            with frappe.db.transaction():
                pr = frappe.get_doc({
                    "doctype": "Purchase Requisition",
                    "requisition_title": "Tx Test PR",
                    "donor": self.donor,
                    "requisition_date": now_datetime(),
                    "status": "Draft",
                })
                pr.insert()

                # Simulate an approval that fails
                raise frappe.ValidationError("Simulated approval failure")
        except frappe.ValidationError:
            pass

        # Both PR and approval should NOT exist
        exists = frappe.db.exists("Purchase Requisition", {"donor": self.donor})
        self.assertFalse(exists, "PR should have been rolled back")

    def test_bid_submission_with_stale_tender(self):
        """Bid on closed tender should roll back."""
        tender = frappe.get_doc({
            "doctype": "Tender",
            "tender_title": "Tx Test Tender",
            "tender_no": "TX-TENDER-001",
            "status": "Closed",
            "submission_deadline": now_datetime(),
            "opening_date_time": now_datetime(),
        }).insert(ignore_permissions=True)
        frappe.db.commit()

        bid_count_before = frappe.db.count("Bid", {"tender": tender.name})

        try:
            frappe.get_doc({
                "doctype": "Bid",
                "tender": tender.name,
                "supplier": "SUP-TX",
                "bid_amount": 5000,
                "bid_currency": "USD",
                "status": "Submitted",
            }).insert()
            frappe.db.commit()
        except Exception:
            pass

        bid_count_after = frappe.db.count("Bid", {"tender": tender.name})
        self.assertEqual(bid_count_before, bid_count_after,
                         "Bid on closed tender should not be committed")

    def tearDown(self):
        frappe.db.delete("Purchase Requisition", {"donor": self.donor})
        frappe.db.delete("Bid", {"tender": ["like", "TX-TENDER%"]})
        frappe.db.delete("Tender", {"tender_no": "TX-TENDER-001"})
        frappe.db.commit()


class TestLogisticsTransactionBoundary(FrappeTestCase):
    """Verify inter-donor transfer is atomic."""

    def setUp(self):
        self.source_donor = "TEST-SRC-DONOR"
        self.target_donor = "TEST-TGT-DONOR"
        self.item = "TEST-TX-ITEM"

        if not frappe.db.exists("Item", self.item):
            frappe.get_doc({
                "doctype": "Item", "item_code": self.item,
                "item_name": "Tx Test Item",
            }).insert(ignore_permissions=True)
            frappe.db.commit()

        # Seed stock for source donor
        frappe.get_doc({
            "doctype": "Stock Ledger",
            "item_code": self.item,
            "donor": self.source_donor,
            "warehouse": "MAIN",
            "voucher_type": "Stock Entry",
            "incoming_qty": 100,
            "outgoing_qty": 0,
        }).insert(ignore_permissions=True)
        frappe.db.commit()

    def test_inter_donor_transfer_atomic(self):
        """Transfer 50 units from source to target — both ledgers must update or neither."""
        try:
            with frappe.db.transaction():
                # Deduct from source
                frappe.get_doc({
                    "doctype": "Stock Ledger",
                    "item_code": self.item,
                    "donor": self.source_donor,
                    "warehouse": "MAIN",
                    "voucher_type": "Inter Donor Transfer",
                    "incoming_qty": 0,
                    "outgoing_qty": 50,
                }).insert()

                # Add to target
                frappe.get_doc({
                    "doctype": "Stock Ledger",
                    "item_code": self.item,
                    "donor": self.target_donor,
                    "warehouse": "MAIN",
                    "voucher_type": "Inter Donor Transfer",
                    "incoming_qty": 50,
                    "outgoing_qty": 0,
                }).insert()
        except Exception:
            pass

        source_balance = frappe.db.get_value("Stock Ledger", {
            "item_code": self.item, "donor": self.source_donor
        }, "sum(incoming_qty) - sum(outgoing_qty)") or 0

        target_balance = frappe.db.get_value("Stock Ledger", {
            "item_code": self.item, "donor": self.target_donor
        }, "sum(incoming_qty) - sum(outgoing_qty)") or 0

        # Both should be 50 — atomic transfer
        self.assertEqual(source_balance, target_balance,
                         f"Source={source_balance}, Target={target_balance} — transfer not atomic")

    def tearDown(self):
        frappe.db.delete("Stock Ledger", {"donor": ["in", [self.source_donor, self.target_donor]]})
        frappe.db.delete("Item", {"item_code": self.item})
        frappe.db.commit()