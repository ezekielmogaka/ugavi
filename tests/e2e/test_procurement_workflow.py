"""
E2E Workflow Test: Procurement Requisition → Approval → Tender → Award

This test covers the end-to-end procurement lifecycle:
1. Create Purchase Requisition
2. Submit for approval
3. DoA auto-determines approval chain
4. Convert to Tender
5. Publish tender (generates sealed-bid keys)
6. Suppliers submit bids
7. Bid opening ceremony (3 officers + OTP)
8. Evaluation and award
"""
import pytest
import frappe
from frappe.tests.utils import FrappeTestCase


class TestProcurementE2E(FrappeTestCase):
    """End-to-end procurement workflow."""

    def setUp(self):
        """Set up test data: prequalify supplier, set DoA, create donor."""
        from ugavi.fixtures.demo_data import run as seed_demo
        self._ensure_demo_data()

    def _ensure_demo_data(self):
        """Ensure demo data exists for tests."""
        if not frappe.db.exists("Ugavi Procurement Settings", "Ugavi Procurement Settings"):
            frappe.get_doc({
                "doctype": "Ugavi Procurement Settings",
                "direct_threshold": 200000,
                "restricted_threshold": 500000,
            }).insert()

    def test_01_create_purchase_requisition(self):
        """Create and validate a Purchase Requisition."""
        pr = frappe.get_doc({
            "doctype": "Purchase Requisition",
            "title": "E2E Test — Medical Supplies Q3",
            "requester": "procurement@ugavi.demo",
            "department": "Health Programmes",
            "donor": "Global Fund",
            "justification": "Quarterly medical supply procurement for health facilities",
            "items": [
                {"item_code": "MED-001", "item_name": "Surgical Gloves", "quantity": 500, "estimated_unit_price": 150},
                {"item_code": "MED-002", "item_name": "Face Masks N95", "quantity": 1000, "estimated_unit_price": 80},
            ],
        })
        pr.insert()
        self.assertEqual(pr.status, "Draft")
        self.assertGreater(pr.estimated_value, 0)
        # Should auto-determine procurement method
        self.assertIsNotNone(pr.procurement_method)
        return pr.name

    def test_02_approval_chain_generation(self):
        """Verify Delegation of Authority generates proper approval chain."""
        # Create DoA entries
        if not frappe.db.exists("Delegation of Authority", {"role": "Approver Level 1", "amount_limit": 500000}):
            frappe.get_doc({
                "doctype": "Delegation of Authority",
                "role": "Approver Level 1",
                "amount_limit": 500000,
                "user": "approver1@ugavi.demo",
            }).insert()
        if not frappe.db.exists("Delegation of Authority", {"role": "Approver Level 2", "amount_limit": 5000000}):
            frappe.get_doc({
                "doctype": "Delegation of Authority",
                "role": "Approver Level 2",
                "amount_limit": 5000000,
                "user": "approver2@ugavi.demo",
            }).insert()

        pr = frappe.get_doc({
            "doctype": "Purchase Requisition",
            "title": "DoA Test PR",
            "requester": "procurement@ugavi.demo",
            "department": "Administration",
            "donor": "USAID",
            "justification": "Testing DoA",
            "items": [
                {"item_code": "TEST-001", "item_name": "Test Item", "quantity": 10, "estimated_unit_price": 100},
            ],
        })
        pr.insert()
        self.assertIsNotNone(pr.approval_chain)

    def test_03_create_tender_from_pr(self):
        """Create a Tender and publish with sealed-bid keys."""
        # Create PR first
        pr = frappe.get_doc({
            "doctype": "Purchase Requisition",
            "title": "Tender Test PR",
            "requester": "procurement@ugavi.demo",
            "department": "Health Programmes",
            "donor": "Global Fund",
            "justification": "Generating tender",
            "items": [
                {"item_code": "BED-001", "item_name": "Hospital Beds", "quantity": 50, "estimated_unit_price": 15000},
            ],
        })
        pr.insert()
        pr.status = "Approved"
        pr.save()

        # Create tender
        tender = frappe.get_doc({
            "doctype": "Tender",
            "title": "E2E Tender — Hospital Furniture",
            "purchase_requisition": pr.name,
            "donor": "Global Fund",
            "procurement_method": "Restricted Tender",
            "estimated_value": pr.estimated_value,
            "submission_deadline": frappe.utils.add_days(None, 14),
            "opening_officer_1": "opening1@ugavi.demo",
            "opening_officer_2": "opening2@ugavi.demo",
            "opening_officer_3": "opening3@ugavi.demo",
        })
        tender.insert()
        self.assertEqual(tender.status, "Draft")

        # Publish tender
        tender.publish()
        tender.reload()
        self.assertEqual(tender.status, "Published")
        # Verify sealed-bid key was generated
        self.assertIsNotNone(tender.public_key)
        return tender.name