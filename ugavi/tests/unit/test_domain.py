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


class TestWaiverWorkflow(IntegrationTestCase):
    """PR5: Waiver approval workflow."""

    def setUp(self):
        self.waiver = frappe.get_doc({
            "doctype": "Waiver",
            "requested_by": "Administrator",
            "reason": "Emergency procurement",
            "rule_to_override": "THRESHOLD_200K",
            "status": "Draft",
        }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.delete("Waiver", {"name": self.waiver.name})

    def test_approve_waiver(self):
        self.waiver.approve("Administrator", "Approved")
        doc = frappe.get_doc("Waiver", self.waiver.name)
        self.assertEqual(doc.status, "Approved")

    def test_reject_waiver(self):
        self.waiver.reject("Administrator", "Rejected")
        doc = frappe.get_doc("Waiver", self.waiver.name)
        self.assertEqual(doc.status, "Rejected")

    def test_approve_without_approver_fails(self):
        self.waiver.status = "Approved"
        with self.assertRaises(frappe.ValidationError):
            self.waiver.save()


class TestSegregationOfDuties(IntegrationTestCase):
    """GV1: SoD rule validation."""

    def test_same_role_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc({
                "doctype": "Segregation of Duties",
                "role_1": "System Manager",
                "role_2": "System Manager",
                "conflict_type": "Create + Approve Same Doc",
            }).insert(ignore_permissions=True)


class TestApprovalDelegation(IntegrationTestCase):
    """GV6: Delegation validity."""

    def test_cannot_delegate_to_self(self):
        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc({
                "doctype": "Approval Delegation",
                "delegated_from": "user@test.com",
                "delegated_to": "user@test.com",
                "delegation_type": "All Procurement",
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            }).insert(ignore_permissions=True)


class TestAuditLog(IntegrationTestCase):
    """TN11-GV5: Immutable audit log with hash chain."""

    def setUp(self):
        frappe.db.delete("Audit Log", {"tender": "TEST-001"})
        self.log = frappe.get_doc({
            "doctype": "Audit Log",
            "tender": "TEST-001",
            "user": "admin@test.com",
            "action": "BID_OPENED",
            "outcome": "Success",
        }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.delete("Audit Log", {"tender": "TEST-001"})

    def test_hash_computed_on_insert(self):
        self.assertIsNotNone(self.log.record_hash)
        self.assertEqual(len(self.log.record_hash), 64)

    def test_cannot_modify_audit_log(self):
        log = frappe.get_doc("Audit Log", self.log.name)
        log.action = "TAMPERED"
        with self.assertRaises(frappe.ValidationError):
            log.save()
                "shares_distributed": 1,
            }).insert(ignore_permissions=True)