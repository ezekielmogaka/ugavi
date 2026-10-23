"""Unit tests for Ugavi procurement rules engine."""
import unittest
from unittest.mock import patch


class TestProcurementRulesEngine(unittest.TestCase):
    """Test the procurement method determination engine."""

    def setUp(self):
        from ugavi.procurement.services.rules_engine import (
            ProcurementRulesEngine,
            ProcurementMethod,
            ThresholdRule,
        )
        self.engine_class = ProcurementRulesEngine
        self.ProcurementMethod = ProcurementMethod
        self.ThresholdRule = ThresholdRule

    def test_threshold_rule_applies_within_range(self):
        rule = self.ThresholdRule(200000, 500000, self.ProcurementMethod.RESTRICTED_TENDER)
        self.assertTrue(rule.applies(200000))
        self.assertTrue(rule.applies(499999))
        self.assertFalse(rule.applies(500000))
        self.assertFalse(rule.applies(199999))

    def test_threshold_rule_no_upper_bound(self):
        rule = self.ThresholdRule(500000, None, self.ProcurementMethod.OPEN_TENDER)
        self.assertTrue(rule.applies(500000))
        self.assertTrue(rule.applies(5000000))
        self.assertFalse(rule.applies(499999))

    def test_engine_defaults(self):
        with patch.object(self.engine_class, '_load_settings', return_value={
            "direct_threshold": 200000, "restricted_threshold": 500000,
            "open_threshold": 500000, "enforce_donor_rules": 0,
            "enforce_category_rules": 0,
        }):
            engine = self.engine_class()
            self.assertEqual(engine.determine_method(100000), self.ProcurementMethod.DIRECT)
            self.assertEqual(engine.determine_method(300000), self.ProcurementMethod.RESTRICTED_TENDER)
            self.assertEqual(engine.determine_method(500000), self.ProcurementMethod.OPEN_TENDER)

    def test_requires_prequalified(self):
        engine = self.engine_class()
        self.assertTrue(engine.requires_prequalified_suppliers(self.ProcurementMethod.RESTRICTED_TENDER))
        self.assertFalse(engine.requires_prequalified_suppliers(self.ProcurementMethod.OPEN_TENDER))

    def test_cannot_override(self):
        engine = self.engine_class()
        self.assertFalse(engine.can_override(self.ProcurementMethod.DIRECT))