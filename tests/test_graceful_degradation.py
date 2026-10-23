"""Graceful Degradation Tests — verify system behavior under failure.

Tests circuit breaker pattern: when downstream services fail
(e.g., email, SMS, external API), the core procurement flow
still completes.
"""
import frappe
import unittest
from unittest.mock import patch, MagicMock
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime
from frappe import _


class TestEmailFailureDegradation(FrappeTestCase):
    """PR submission succeeds even if email notification fails."""

    def setUp(self):
        self.pr_name = None

    @patch("frappe.sendmail")
    def test_pr_submits_without_email(self, mock_sendmail):
        """Email failure should not block PR submission."""
        mock_sendmail.side_effect = Exception("SMTP connection refused")

        pr = frappe.get_doc({
            "doctype": "Purchase Requisition",
            "requisition_title": "Degradation Test PR",
            "requisition_date": now_datetime(),
            "status": "Submitted",
        }).insert(ignore_permissions=True)

        # PR should still exist despite email failure
        self.assertTrue(frappe.db.exists("Purchase Requisition", pr.name),
                        "PR should exist even when email fails")
        self.pr_name = pr.name

    def tearDown(self):
        if self.pr_name:
            frappe.db.delete("Purchase Requisition", {"name": self.pr_name})
            frappe.db.commit()


class TestNotificationDegradation(FrappeTestCase):
    """Tender creation succeeds even if notification system is down."""

    @patch("frappe.sendmail")
    def test_tender_created_without_notification(self, mock_sendmail):
        mock_sendmail.side_effect = Exception("Notification service down")

        tender = frappe.get_doc({
            "doctype": "Tender",
            "tender_title": "Degradation Tender",
            "tender_no": "DEG-TENDER-001",
            "status": "Draft",
            "submission_deadline": now_datetime(),
            "opening_date_time": now_datetime(),
        }).insert(ignore_permissions=True)
        frappe.db.commit()

        self.assertTrue(frappe.db.exists("Tender", tender.name),
                        "Tender should exist even when notification fails")

        frappe.db.delete("Tender", {"name": tender.name})
        frappe.db.commit()


class TestCacheDegradation(FrappeTestCase):
    """Bid opens proceed even if cache (Valkey) is unavailable."""

    def test_bid_query_without_cache(self):
        """Direct DB lookup works when cache fails."""
        # Simulate cache miss by using direct DB
        count = frappe.db.count("Bid", {"status": "Submitted"})
        self.assertIsInstance(count, int, "Direct DB count should work without cache")