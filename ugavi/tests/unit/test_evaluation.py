"""Tests for Evaluation Score, Minutes, and Regret Notice workflows."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch


class TestSupplierEvaluationHistory(unittest.TestCase):
    def test_pending_zero_scorecards_do_not_dilute_completed_rating(self):
        from ugavi.procurement.doctype.ugavi_supplier_evaluation.ugavi_supplier_evaluation import (
            UgaviSupplierEvaluation,
        )

        evaluation = SimpleNamespace(supplier="DEMO", name="EVAL-NEW", total_score=90)

        def history(_doctype, filters, **_kwargs):
            if filters.get("status") == "Completed":
                return [SimpleNamespace(total_score=80)]
            return [SimpleNamespace(total_score=80), SimpleNamespace(total_score=0)]

        with patch(
            "ugavi.procurement.doctype.ugavi_supplier_evaluation.ugavi_supplier_evaluation.frappe.get_all",
            side_effect=history,
        ):
            UgaviSupplierEvaluation._compute_cumulative_rating(evaluation)
        self.assertEqual(evaluation.cumulative_rating, 85)


class TestEvaluationScore(unittest.TestCase):
    """Test evaluation scoring workflow."""

    def test_score_submission(self):
        from ugavi.tendering.doctype.evaluation_score.evaluation_score import (
            EvaluationScore,
        )
        self.assertTrue(hasattr(EvaluationScore, "submit_score"))
        self.assertTrue(hasattr(EvaluationScore, "review_score"))

    def test_validate_method_exists(self):
        from ugavi.tendering.doctype.evaluation_score.evaluation_score import (
            EvaluationScore,
        )
        self.assertTrue(hasattr(EvaluationScore, "validate"))
        self.assertTrue(hasattr(EvaluationScore, "_calculate_scores"))


class TestEvaluationMinutes(unittest.TestCase):
    """Test evaluation minutes workflow."""

    def test_approve_reject_methods(self):
        from ugavi.tendering.doctype.evaluation_minutes.evaluation_minutes import (
            EvaluationMinutes,
        )
        self.assertTrue(hasattr(EvaluationMinutes, "approve"))
        self.assertTrue(hasattr(EvaluationMinutes, "reject"))

    def test_quorum_validation(self):
        from ugavi.tendering.doctype.evaluation_minutes.evaluation_minutes import (
            EvaluationMinutes,
        )
        self.assertTrue(hasattr(EvaluationMinutes, "_validate_quorum"))


class TestRegretNotice(unittest.TestCase):
    """Test regret notice workflow."""

    def test_send_method(self):
        from ugavi.tendering.doctype.regret_notice.regret_notice import (
            RegretNotice,
        )
        self.assertTrue(hasattr(RegretNotice, "send"))


class TestBudgetReports(unittest.TestCase):
    """Test budget burn-rate reporting (W7)."""

    def test_whitelist_endpoints(self):
        from ugavi.compliance.services import budget_reports
        self.assertTrue(hasattr(budget_reports, "get_burn_rate_report"))
        self.assertTrue(hasattr(budget_reports, "get_budget_commitments"))


class TestMpesaAdapter(unittest.TestCase):
    """Test M-Pesa adapter (W6)."""

    def test_adapter_instantiation(self):
        from ugavi.integrations.mpesa import (
            MpesaAdapter,
            DarajaMpesaAdapter,
            get_adapter,
            send_supplier_payment,
        )
        adapter = get_adapter()
        self.assertIsInstance(adapter, DarajaMpesaAdapter)
        self.assertTrue(issubclass(DarajaMpesaAdapter, MpesaAdapter))
        self.assertTrue(callable(send_supplier_payment))

    def test_no_fabricated_gateway_success(self):
        """Without Safaricom credentials the adapter must refuse, not pretend."""
        import frappe
        from ugavi.integrations.mpesa import get_adapter

        adapter = get_adapter()
        if adapter.is_configured():
            self.skipTest("Live M-Pesa credentials configured")
        with self.assertRaises(frappe.ValidationError):
            adapter.send_b2c(1000, "254712345678", "Test")

    def test_msisdn_normalisation(self):
        import frappe
        from ugavi.integrations.mpesa import normalize_msisdn

        self.assertEqual(normalize_msisdn("0712345678"), "254712345678")
        self.assertEqual(normalize_msisdn("+254 712 345 678"), "254712345678")
        self.assertEqual(normalize_msisdn("712345678"), "254712345678")
        with self.assertRaises(frappe.ValidationError):
            normalize_msisdn("12345")

    def test_submission_is_not_blocked_for_other_payment_modes(self):
        """The Payment Entry hook must ignore non-M-Pesa disbursements."""
        import frappe
        from ugavi.integrations.mpesa import queue_supplier_payment

        doc = frappe._dict(
            name="PE-TEST", payment_type="Pay", mode_of_payment="Bank Transfer"
        )
        self.assertIsNone(queue_supplier_payment(doc, "on_submit"))


class TestAnalyticsConfig(unittest.TestCase):
    """Test analytics dashboard config (W11)."""

    def test_system_manager_config(self):
        from ugavi.analytics.dashboard.analytics_config import (
            DASHBOARD_CONFIG,
            get_dashboard_config,
        )
        sm = get_dashboard_config(["System Manager"])
        self.assertEqual(sm["name"], "System Overview")
        self.assertEqual(len(sm["cards"]), 10)
        self.assertEqual(len(sm["scheduled_reports"]), 3)

    def test_all_roles_have_config(self):
        from ugavi.analytics.dashboard.analytics_config import DASHBOARD_CONFIG
        roles = ["System Manager", "Procurement Manager",
                 "Stock User", "Finance Manager", "Auditor"]
        for role in roles:
            self.assertIn(role, DASHBOARD_CONFIG)
            self.assertTrue(DASHBOARD_CONFIG[role]["cards"])

    def test_default_fallback(self):
        from ugavi.analytics.dashboard.analytics_config import get_dashboard_config
        cfg = get_dashboard_config(["Guest"])
        self.assertEqual(cfg["name"], "Default Dashboard")


class TestDonorReportScheduler(unittest.TestCase):
    """Test scheduled donor report generation (W8)."""

    def test_entry_point(self):
        from ugavi.compliance.services.donor_report_scheduler import (
            generate_scheduled_donor_reports,
            _should_generate,
        )
        self.assertTrue(callable(generate_scheduled_donor_reports))
        self.assertTrue(callable(_should_generate))