"""Concurrency Tests — verify concurrent bid submissions and stock updates.

FrappeTestCase with threading to simulate race conditions.
"""
import frappe
import unittest
import threading
import time
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime


class TestConcurrencyBidSubmission(FrappeTestCase):
    """Verify that concurrent bid submissions don't corrupt bid count or status."""

    def setUp(self):
        self.tender = "TEST-CONCURRENT-001"
        if not frappe.db.exists("Tender", self.tender):
            frappe.get_doc({
                "doctype": "Tender",
                "tender_title": "Concurrency Test Tender",
                "tender_no": self.tender,
                "status": "Published",
                "submission_deadline": now_datetime(),
                "opening_date_time": now_datetime(),
            }).insert(ignore_permissions=True)
            frappe.db.commit()

    def test_concurrent_bid_submissions_serial(self):
        """10 rapid-fire bid submissions — verify count integrity."""
        for i in range(10):
            bid = frappe.get_doc({
                "doctype": "Bid",
                "tender": self.tender,
                "supplier": f"SUP-CONC-{i % 3}",  # 3 suppliers
                "bid_amount": 10000 + i * 100,
                "bid_currency": "USD",
                "status": "Submitted",
            })
            bid.insert(ignore_permissions=True)

        frappe.db.commit()
        count = frappe.db.count("Bid", {"tender": self.tender})
        self.assertEqual(count, 10, f"Expected 10 bids, got {count}")

    def tearDown(self):
        frappe.db.delete("Bid", {"tender": self.tender})
        frappe.db.delete("Tender", {"tender_no": self.tender})
        frappe.db.commit()


class TestConcurrencyStockUpdate(FrappeTestCase):
    """Verify that concurrent stock movements don't corrupt ledger."""

    def setUp(self):
        self.item = "TEST-STOCK-CONCURRENT"
        self.donor = "TEST-DONOR-CONCURRENT"
        self.warehouse = "TEST-WH-CONCURRENT"

        if not frappe.db.exists("Item", self.item):
            frappe.get_doc({
                "doctype": "Item", "item_code": self.item,
                "item_name": "Concurrency Test Item",
            }).insert(ignore_permissions=True)
            frappe.db.commit()

    def test_concurrent_stock_ledger_entries(self):
        """10 concurrent stock-in entries via threads — verify ledger integrity."""
        errors = []
        lock = threading.Lock()

        def do_stock_in(qty):
            try:
                sle = frappe.get_doc({
                    "doctype": "Stock Ledger",
                    "item_code": self.item,
                    "donor": self.donor,
                    "warehouse": self.warehouse,
                    "voucher_type": "Stock Entry",
                    "incoming_qty": qty,
                    "outgoing_qty": 0,
                })
                sle.insert(ignore_permissions=True)
            except Exception as e:
                with lock:
                    errors.append(str(e))

        threads = [threading.Thread(target=do_stock_in, args=(i + 1,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrency errors: {errors}")

        total_in = frappe.db.get_value("Stock Ledger", {
            "item_code": self.item, "donor": self.donor
        }, "sum(incoming_qty)") or 0
        self.assertEqual(total_in, 55, f"Expected 55 total in, got {total_in}")  # 1+2+...+10 = 55

    def tearDown(self):
        frappe.db.delete("Stock Ledger", {"donor": self.donor})
        frappe.db.delete("Item", {"item_code": self.item})
        frappe.db.commit()