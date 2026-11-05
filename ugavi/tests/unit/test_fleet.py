"""Fleet requirement and upgrade-boundary tests."""

import inspect
import unittest
from unittest.mock import patch

from ugavi.fleet.doctype.fleet_utilization_report.fleet_utilization_report import (
    FleetUtilizationReport,
)
from ugavi.fleet.doctype.fuel_log.fuel_log import FuelLog
from ugavi.fleet.doctype.spare_parts_issue.spare_parts_issue import SparePartsIssue
from ugavi.fleet.services import purchase_reconciliation


class TestFleetControlBoundaries(unittest.TestCase):
    def test_shared_donor_report_regenerates_after_another_vehicle_is_seeded(self):
        from ugavi.scripts import seed_fleet_journey

        with patch.object(seed_fleet_journey, "frappe") as frappe:
            frappe.db.exists.return_value = "FLEET-REPORT-DEMO"
            report = frappe.get_doc.return_value
            seed_fleet_journey._ensure_report("USAID", {})
            frappe.get_doc.assert_called_once_with(
                "Fleet Utilization Report", "FLEET-REPORT-DEMO"
            )
            report.generate.assert_called_once()
            self.assertLess(report.from_date, report.to_date)

    def test_fuel_does_not_mutate_totals_on_draft_insert(self):
        self.assertFalse(hasattr(FuelLog, "after_insert"))
        self.assertTrue(hasattr(FuelLog, "before_submit"))
        self.assertTrue(hasattr(FuelLog, "on_cancel"))

    def test_fleet_purchase_allocation_is_serialized(self):
        source = inspect.getsource(
            purchase_reconciliation.lock_and_validate_allocation
        )
        self.assertIn("FOR UPDATE", source)
        self.assertIn("exceeds purchased quantity", source)

    def test_spare_issue_uses_direct_stock_entry_link(self):
        source = inspect.getsource(SparePartsIssue)
        self.assertIn("self.stock_entry", source)
        self.assertIn("ugavi_spare_parts_issue", source)
        self.assertNotIn('creation": (">", self.creation)', source)

    def test_report_filters_submitted_records_and_donor(self):
        source = inspect.getsource(FleetUtilizationReport.get_report_data)
        self.assertIn('"docstatus": 1', source)
        self.assertIn("docstatus = 1", source)
        self.assertIn("self.donor", source)

    def test_purchase_hooks_cover_receipts_and_invoices(self):
        self.assertTrue(
            callable(purchase_reconciliation.create_for_purchase_receipt)
        )
        self.assertTrue(
            callable(purchase_reconciliation.create_or_link_for_purchase_invoice)
        )
