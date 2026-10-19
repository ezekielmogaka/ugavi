"""Integration tests for new DocTypes and services (Batch 4)."""
import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today, add_days


def _ensure_supplier(name):
    if not frappe.db.exists("Supplier", name):
        frappe.get_doc({
            "doctype": "Supplier", "supplier_name": name,
            "supplier_group": "All Supplier Groups",
        }).insert(ignore_permissions=True)


class TestContractLifecycle(IntegrationTestCase):
    """CT1-CM4: Contract milestones, retention, and expiry."""

    def setUp(self):
        _ensure_supplier("_Test Supplier")
        self.contract = frappe.get_doc({
            "doctype": "Contract", "supplier": "_Test Supplier",
            "start_date": "2025-01-01", "end_date": "2025-12-31",
            "contract_value": 500000, "retention_percentage": 10,
            "expiry_alert_days": 30, "status": "Draft",
        }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.delete("Contract", {"name": self.contract.name})

    def test_end_date_before_start_should_fail(self):
        self.contract.end_date = "2024-12-31"
        with self.assertRaises(frappe.ValidationError):
            self.contract.save()

    def test_retention_cannot_exceed_100(self):
        self.contract.retention_percentage = 150
        with self.assertRaises(frappe.ValidationError):
            self.contract.save()

    def test_expiry_check_within_window(self):
        self.contract.end_date = add_days(today(), 15)
        self.contract.save()
        doc = frappe.get_doc("Contract", self.contract.name)
        self.assertTrue(doc.check_expiry())


class TestScoringEngine(IntegrationTestCase):
    """EV2: Weighted scoring."""

    def test_weighted_scoring_basic(self):
        from ugavi.procurement.services.scoring_engine import compute_weighted_score
        criteria = [{"name": "Price", "weight": 0.40}, {"name": "Technical", "weight": 0.35},
                     {"name": "Delivery", "weight": 0.25}]
        scores = [{"criterion": "Price", "score": 8}, {"criterion": "Technical", "score": 9},
                   {"criterion": "Delivery", "score": 7}]
        result = compute_weighted_score(scores, criteria)
        self.assertEqual(result["total"], 8.1)

    def test_scoring_with_missing_criterion(self):
        from ugavi.procurement.services.scoring_engine import compute_weighted_score
        criteria = [{"name": "Price", "weight": 0.50}, {"name": "Quality", "weight": 0.50}]
        scores = [{"criterion": "Price", "score": 6}]
        self.assertEqual(compute_weighted_score(scores, criteria)["total"], 3.0)


class TestKeyDistribution(IntegrationTestCase):
    """TN13: Verify key generation never stores private key in DB."""

    def test_key_doc_has_no_private_key_field(self):
        meta = frappe.get_meta("Sealed Bid Key")
        fieldnames = [f.fieldname for f in meta.fields]
        self.assertNotIn("private_key_pem", fieldnames)

    def test_key_doc_requires_three_distinct_officers(self):
        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc({
                "doctype": "Sealed Bid Key", "tender": "TEND-001",
                "share_1_user": "user1@test.com", "share_1_data": "d1",
                "share_2_user": "user2@test.com", "share_2_data": "d2",
                "share_3_user": "user1@test.com", "share_3_data": "d3",
                "shares_distributed": 1,
            }).insert(ignore_permissions=True)