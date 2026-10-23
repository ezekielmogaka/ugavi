"""Regression tests for repeatable LOKADO demo scenario keys."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from ugavi.scripts import seed_lokado

MAKE_INVOICE = "erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_invoice"


def _completed_transfers(doctype, filters=None, fieldname=None, *args, **kwargs):
    if doctype == "Inter Donor Transfer":
        return "IDT-DEMO" if fieldname == "name" else "Completed"
    return None


class TestSeedScenarioKeys(unittest.TestCase):
    def _stock_entry_lookups(self, frappe):
        return [
            call for call in frappe.db.get_value.call_args_list
            if call.args and call.args[0] == "Stock Entry"
        ]

    def test_stock_entries_reuse_remarks_not_erpnext_purpose(self):
        def get_value(doctype, filters=None, fieldname=None, *args, **kwargs):
            if doctype == "Stock Entry":
                return SimpleNamespace(name="MAT-STE-DEMO", docstatus=1)
            return _completed_transfers(doctype, filters, fieldname)

        with patch.object(seed_lokado, "frappe") as frappe:
            frappe.db.get_value.side_effect = get_value
            seed_lokado._seed_stock_entries()

            lookups = self._stock_entry_lookups(frappe)
            self.assertEqual(len(lookups), 12)
            for call in lookups:
                filters = call.args[1]
                self.assertIn("remarks", filters)
                self.assertIn("stock_entry_type", filters)
                self.assertNotIn("purpose", filters)
                self.assertNotIn("posting_date", filters)
            frappe.get_doc.assert_not_called()

    def test_new_stock_entries_keep_scenario_description_and_posting_date(self):
        with patch.object(seed_lokado, "frappe") as frappe:
            frappe.db.get_value.side_effect = _completed_transfers
            frappe.get_doc.return_value = MagicMock()
            seed_lokado._seed_stock_entries()

            self.assertEqual(frappe.get_doc.call_count, 12)
            for call in frappe.get_doc.call_args_list:
                data = call.args[0]
                self.assertTrue(data["remarks"])
                self.assertEqual(data["set_posting_time"], 1)
                self.assertNotIn("purpose", data)
            self.assertEqual(frappe.get_doc.return_value.submit.call_count, 12)
            receipt_rows = [
                call.args[1]
                for call in frappe.get_doc.return_value.append.call_args_list
                if call.args[1].get("t_warehouse") and not call.args[1].get("s_warehouse")
            ]
            self.assertTrue(receipt_rows)
            for row in receipt_rows:
                self.assertGreater(row["basic_rate"], 0)

    def test_purchase_invoices_reuse_bill_no_not_posting_date(self):
        with patch.object(seed_lokado, "frappe") as frappe, patch(MAKE_INVOICE) as make_invoice:
            frappe.db.get_value.return_value = SimpleNamespace(name="ACC-PINV-DEMO", docstatus=1)
            seed_lokado._seed_purchase_invoices()

            calls = frappe.db.get_value.call_args_list
            self.assertEqual(len(calls), len(seed_lokado.RECEIPT_INVOICES))
            for call in calls:
                doctype, filters = call.args[:2]
                self.assertEqual(doctype, "Purchase Invoice")
                self.assertIn("bill_no", filters)
                self.assertNotIn("posting_date", filters)
            make_invoice.assert_not_called()
            frappe.get_doc.assert_not_called()

    def test_new_purchase_invoices_are_receipt_linked_and_back_dated(self):
        def get_value(doctype, filters=None, fieldname=None, *args, **kwargs):
            if doctype == "Purchase Invoice":
                return None
            if doctype == "Purchase Receipt":
                return "2026-01-01" if fieldname == "posting_date" else "MAT-PRE-DEMO"
            return f"{doctype}-DEMO"

        invoice = MagicMock(grand_total=1000)
        with patch.object(seed_lokado, "frappe") as frappe, patch(
            MAKE_INVOICE, return_value=invoice
        ) as make_invoice:
            frappe.db.get_value.side_effect = get_value
            seed_lokado._seed_purchase_invoices()

            self.assertEqual(make_invoice.call_count, len(seed_lokado.RECEIPT_INVOICES))
            make_invoice.assert_called_with("MAT-PRE-DEMO")
            self.assertEqual(invoice.set_posting_time, 1)
            self.assertEqual(str(invoice.posting_date), "2026-01-03")
            self.assertEqual(invoice.payment_schedule, [])
            self.assertEqual(invoice.submit.call_count, len(seed_lokado.RECEIPT_INVOICES))
            frappe.db.rollback.assert_not_called()
