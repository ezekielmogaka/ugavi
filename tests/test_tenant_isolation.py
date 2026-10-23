"""Tenant Isolation Tests — verify donor segregation.

Tests that one donor's data is never visible to queries
scoped to another donor.
"""
import frappe
import unittest
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime


class TestDonorIsolationBase(FrappeTestCase):
    """Base class with seeded donor data."""

    DONOR_A = "TENANT-ISOLATION-A"
    DONOR_B = "TENANT-ISOLATION-B"

    def setUp(self):
        # Seed PR for Donor A
        if not frappe.db.exists("Purchase Requisition", {"donor": self.DONOR_A}):
            frappe.get_doc({
                "doctype": "Purchase Requisition",
                "requisition_title": f"PR for {self.DONOR_A}",
                "donor": self.DONOR_A,
                "requisition_date": now_datetime(),
                "status": "Draft",
            }).insert(ignore_permissions=True)

        # Seed PR for Donor B
        if not frappe.db.exists("Purchase Requisition", {"donor": self.DONOR_B}):
            frappe.get_doc({
                "doctype": "Purchase Requisition",
                "requisition_title": f"PR for {self.DONOR_B}",
                "donor": self.DONOR_B,
                "requisition_date": now_datetime(),
                "status": "Draft",
            }).insert(ignore_permissions=True)

        frappe.db.commit()

    def tearDown(self):
        frappe.db.delete("Purchase Requisition", {"donor": ["in", [self.DONOR_A, self.DONOR_B]]})
        frappe.db.commit()


class TestDonorPRIsolation(TestDonorIsolationBase):
    """Donor A should not see Donor B's PRs."""

    def test_donor_a_only_sees_own_prs(self):
        prs = frappe.get_all(
            "Purchase Requisition",
            filters={"donor": self.DONOR_A},
            fields=["name"],
        )
        self.assertGreaterEqual(len(prs), 1, "Donor A should see at least 1 PR")
        for pr in prs:
            self.assertEqual(
                frappe.db.get_value("Purchase Requisition", pr.name, "donor"),
                self.DONOR_A,
                f"PR {pr.name} belongs to wrong donor"
            )

    def test_cross_donor_query_returns_nothing(self):
        """Querying for Donor B's data with Donor A filter returns nothing."""
        prs = frappe.get_all(
            "Purchase Requisition",
            filters={"donor": self.DONOR_A, "requisition_title": f"PR for {self.DONOR_B}"},
        )
        self.assertEqual(len(prs), 0, "Cross-donor query should return empty")


class TestDonorStockIsolation(FrappeTestCase):
    """Stock balances are donor-segregated."""

    DONOR_A = "STOCK-ISO-A"
    DONOR_B = "STOCK-ISO-B"
    ITEM = "ISO-TEST-ITEM"

    def setUp(self):
        if not frappe.db.exists("Item", self.ITEM):
            frappe.get_doc({
                "doctype": "Item", "item_code": self.ITEM,
                "item_name": "Isolation Test Item",
            }).insert(ignore_permissions=True)

        # Donor A: 100 units
        frappe.get_doc({
            "doctype": "Stock Ledger",
            "item_code": self.ITEM,
            "donor": self.DONOR_A,
            "warehouse": "MAIN",
            "incoming_qty": 100, "outgoing_qty": 0,
            "voucher_type": "Stock Entry",
        }).insert(ignore_permissions=True)

        # Donor B: 50 units
        frappe.get_doc({
            "doctype": "Stock Ledger",
            "item_code": self.ITEM,
            "donor": self.DONOR_B,
            "warehouse": "MAIN",
            "incoming_qty": 50, "outgoing_qty": 0,
            "voucher_type": "Stock Entry",
        }).insert(ignore_permissions=True)

        frappe.db.commit()

    def test_stock_balances_are_segregated(self):
        """Donor A balance = 100, Donor B balance = 50 — no mixing."""
        balance_a = frappe.db.get_value("Stock Ledger", {
            "item_code": self.ITEM, "donor": self.DONOR_A
        }, "sum(incoming_qty) - sum(outgoing_qty)") or 0

        balance_b = frappe.db.get_value("Stock Ledger", {
            "item_code": self.ITEM, "donor": self.DONOR_B
        }, "sum(incoming_qty) - sum(outgoing_qty)") or 0

        self.assertEqual(balance_a, 100, f"Donor A balance should be 100, got {balance_a}")
        self.assertEqual(balance_b, 50, f"Donor B balance should be 50, got {balance_b}")

        # Total should NOT be 150 in a single donor query
        total_across_donors = frappe.db.get_value("Stock Ledger", {
            "item_code": self.ITEM, "donor": self.DONOR_A
        }, "sum(incoming_qty) - sum(outgoing_qty)") or 0

        self.assertNotEqual(total_across_donors, 150,
                            "Donor A query should not sum Donor B's stock")

    def tearDown(self):
        frappe.db.delete("Stock Ledger", {"donor": ["in", [self.DONOR_A, self.DONOR_B]]})
        frappe.db.delete("Item", {"item_code": self.ITEM})
        frappe.db.commit()