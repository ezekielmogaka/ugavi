"""Regression tests for ERPNext-normalized demo scenario keys."""

import unittest
from unittest.mock import MagicMock, patch

from ugavi.scripts import seed_lokado


class TestSeedScenarioKeys(unittest.TestCase):
    def test_stock_entries_reuse_remarks_not_erpnext_purpose(self):
        with patch.object(seed_lokado, "frappe") as frappe:
            frappe.db.exists.return_value = True
            seed_lokado._seed_stock_entries()

            self.assertEqual(frappe.db.exists.call_count, 11)
            for call in frappe.db.exists.call_args_list:
                doctype, filters = call.args
                self.assertEqual(doctype, "Stock Entry")
                self.assertIn("remarks", filters)
                self.assertNotIn("purpose", filters)
                self.assertNotIn("posting_date", filters)
            frappe.get_doc.assert_not_called()

    def test_purchase_invoices_reuse_remarks_not_posting_date(self):
        with patch.object(seed_lokado, "frappe") as frappe:
            frappe.db.exists.return_value = True
            frappe.db.get_value.return_value = "Demo Supplier"
            seed_lokado._seed_purchase_invoices()

            self.assertEqual(frappe.db.exists.call_count, 6)
            for call in frappe.db.exists.call_args_list:
                doctype, filters = call.args
                self.assertEqual(doctype, "Purchase Invoice")
                self.assertIn("supplier", filters)
                self.assertIn("remarks", filters)
                self.assertNotIn("posting_date", filters)
            frappe.get_doc.assert_not_called()

    def test_new_stock_entries_keep_scenario_description_and_posting_date(self):
        with patch.object(seed_lokado, "frappe") as frappe:
            frappe.db.exists.return_value = False
            frappe.get_doc.return_value = MagicMock()
            seed_lokado._seed_stock_entries()

            self.assertEqual(frappe.get_doc.call_count, 11)
            for call in frappe.get_doc.call_args_list:
                data = call.args[0]
                self.assertTrue(data["remarks"])
                self.assertEqual(data["set_posting_time"], 1)
                self.assertNotIn("purpose", data)

    def test_new_purchase_invoices_keep_requested_posting_date(self):
        with patch.object(seed_lokado, "frappe") as frappe:
            frappe.db.exists.return_value = False
            frappe.db.get_value.return_value = "Demo Supplier"
            seed_lokado._seed_purchase_invoices()

            self.assertEqual(frappe.get_doc.call_count, 6)
            for call in frappe.get_doc.call_args_list:
                self.assertEqual(call.args[0]["set_posting_time"], 1)
