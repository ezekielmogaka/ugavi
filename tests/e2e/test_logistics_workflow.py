"""
E2E Workflow Test: Logistics — Stock Receipt → Donor Warehouse → Monthly Report

Covers the logistics lifecycle:
1. Stock receipt into donor-segregated warehouse
2. Inter-donor stock transfer with approval
3. Monthly stock report generation
"""
import frappe
from frappe.tests.utils import FrappeTestCase


class TestLogisticsE2E(FrappeTestCase):
    """End-to-end logistics workflow."""

    def setUp(self):
        self._ensure_warehouses()

    def _ensure_warehouses(self):
        """Create test donor warehouses."""
        donors = ["USAID", "Global Fund"]
        for donor in donors:
            if not frappe.db.exists("Donor Profile", donor):
                frappe.get_doc({
                    "doctype": "Donor Profile",
                    "donor_name": donor,
                    "status": "Active",
                }).insert()

            warehouse = f"Test {donor} WH - SB"
            if not frappe.db.exists("Warehouse", warehouse):
                frappe.get_doc({
                    "doctype": "Warehouse",
                    "warehouse_name": warehouse,
                    "parent_warehouse": "Stores - SB",
                }).insert()

            if not frappe.db.exists("Donor Warehouse", {"warehouse": warehouse}):
                frappe.get_doc({
                    "doctype": "Donor Warehouse",
                    "warehouse": warehouse,
                    "donor": donor,
                }).insert()

    def test_01_receive_stock_into_donor_warehouse(self):
        """Receive stock into a donor-segregated warehouse."""
        ste = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "to_warehouse": "Test USAID WH - SB",
            "items": [
                {"item_code": "MED-001", "item_name": "Surgical Gloves", "qty": 100, "basic_rate": 150},
            ],
        })
        ste.insert()
        ste.submit()
        self.assertEqual(ste.docstatus, 1)

    def test_02_inter_donor_transfer(self):
        """Transfer stock between donor-segregated warehouses."""
        transfer = frappe.get_doc({
            "doctype": "Inter Donor Transfer",
            "from_warehouse": "Test USAID WH - SB",
            "to_warehouse": "Test Global Fund WH - SB",
            "items": [
                {"item_code": "MED-001", "item_name": "Surgical Gloves", "qty": 10},
            ],
        })
        transfer.insert()
        self.assertEqual(transfer.from_donor, "USAID")
        self.assertEqual(transfer.to_donor, "Global Fund")
        self.assertNotEqual(transfer.from_donor, transfer.to_donor)

    def test_03_monthly_stock_report(self):
        """Generate monthly stock report."""
        report = frappe.get_doc({
            "doctype": "Monthly Stock Report",
            "report_month": frappe.utils.today()[:7] + "-01",
            "donor": "USAID",
        })
        report.insert()
        report.generate()
        self.assertIsNotNone(report.generated_at)