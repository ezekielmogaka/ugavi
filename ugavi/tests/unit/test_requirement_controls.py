"""Cross-requirement control-boundary tests."""

import inspect
import unittest
from unittest.mock import MagicMock, patch

import frappe

from ugavi.procurement.doctype.bid_opening_record.bid_opening_record import (
    BidOpeningRecord,
)
from ugavi.procurement.doctype.ugavi_contract.ugavi_contract import (
    UgaviContract,
    ensure_contract_for_purchase_order,
)
from ugavi.ugavi_assets.doctype.asset_disposal.asset_disposal import AssetDisposal
from ugavi.ugavi_assets.doctype.ugavi_asset_movement.ugavi_asset_movement import (
    UgaviAssetMovement,
)
from ugavi.procurement import events


class TestRequirementControlBoundaries(unittest.TestCase):
    def test_stock_report_uses_posted_value_not_highest_historical_rate(self):
        from ugavi.logistics.doctype.monthly_stock_report.monthly_stock_report import (
            MonthlyStockReport,
        )

        report = MagicMock(
            donor="TEST-DONOR", warehouse="TEST-WAREHOUSE", report_month="2026-10-01",
        )
        ledger_row = frappe._dict(
            item_code="TEST-ITEM", opening_qty=5, receipts_qty=10, issues_qty=2,
            transfer_in_qty=1, transfer_out_qty=3, adjustment_qty=-1,
            closing_value=1210,
        )
        with (
            patch.object(frappe.db, "get_value", return_value="TEST-DONOR"),
            patch.object(frappe.db, "sql", return_value=[ledger_row]) as sql,
        ):
            MonthlyStockReport.generate(report)
        row = report.append.call_args.args[1]
        self.assertEqual(row["closing_qty"], 10)
        self.assertEqual(row["total_value"], 1210)
        report.save.assert_called_once()
        self.assertIn("SUM(sle.stock_value_difference)", sql.call_args.args[0])

    def test_bid_opening_record_requires_verified_ceremony(self):
        source = inspect.getsource(BidOpeningRecord)
        self.assertIn("opening_verified", source)
        self.assertIn("immutable", source)
        self.assertIn("Three distinct", source)

    def test_asset_movement_locks_and_compares_source_state(self):
        source = inspect.getsource(UgaviAssetMovement.confirm)
        self.assertIn("FOR UPDATE", source)
        self.assertIn("asset.location != self.from_location", source)
        self.assertIn("asset.condition != self.from_condition", source)

    def test_asset_disposal_requires_independent_authorizer(self):
        source = inspect.getsource(AssetDisposal.approve)
        self.assertIn("self.authorized_by == self.owner", source)

    def test_every_submitted_po_enters_contract_management(self):
        source = inspect.getsource(ensure_contract_for_purchase_order)
        self.assertIn('"status": "Draft"', source)
        self.assertIn('"purchase_order": doc.name', source)

    def test_contract_completion_requires_verified_milestones(self):
        source = inspect.getsource(UgaviContract._validate_completion)
        self.assertIn('milestone.status != "Verified"', source)
        self.assertIn("Ugavi Supplier Evaluation", source)

    def test_supplier_payment_requires_completed_evaluation(self):
        source = inspect.getsource(
            events.validate_supplier_evaluation_before_payment
        )
        self.assertIn('status != "Completed"', source)
        self.assertIn("Purchase Invoice", source)
