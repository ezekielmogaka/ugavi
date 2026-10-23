"""Integration tests for new DocTypes and services (Batch 4)."""
import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today, add_days
from unittest.mock import patch


class TestBusinessRolePermissions(IntegrationTestCase):
    def setUp(self):
        from ugavi.scripts.setup_config import configure_roles, configure_role_permissions

        configure_roles()
        configure_role_permissions()

    def test_configuration_preserves_upstream_roles_and_is_repeatable(self):
        from ugavi.scripts.setup_config import configure_role_permissions

        before = frappe.db.count("Custom DocPerm")
        configure_role_permissions()
        self.assertEqual(frappe.db.count("Custom DocPerm"), before)
        receipt_permissions = {
            row.role: row for row in frappe.get_meta("Purchase Receipt").permissions
        }
        self.assertTrue(receipt_permissions["Stock User"].submit)
        self.assertTrue(receipt_permissions["Purchase User"].read)

    def test_auditor_and_finance_configuration_is_read_only(self):
        for doctype, role in (
            ("Delegation of Authority", "Auditor"),
            ("Segregation of Duties", "Auditor"),
            ("Budget", "Finance Officer"),
            ("Landed Cost Voucher", "Finance Officer"),
        ):
            permission = next(
                row for row in frappe.get_meta(doctype).permissions if row.role == role
            )
            self.assertTrue(permission.read)
            for capability in ("write", "create", "delete", "submit", "cancel"):
                self.assertFalse(permission.get(capability), (doctype, role, capability))


class TestOpeningCeremonyRuntime(IntegrationTestCase):
    def test_sealed_bid_requires_all_codes_and_creates_private_pdf(self):
        from ugavi.procurement.services import sealed_bid

        officers = [f"_test_opening_{index}@example.com" for index in range(3)]
        for email in officers:
            if not frappe.db.exists("User", email):
                frappe.get_doc({
                    "doctype": "User", "email": email, "first_name": "Opening",
                    "send_welcome_email": 0,
                    "roles": [{"role": "Bid Opening Officer"}],
                }).insert(ignore_permissions=True)
        donor = frappe.get_doc({
            "doctype": "Donor Profile", "donor_name": "_Test Opening Donor",
            "donor_code": "_TEST_OPENING",
        }).insert(ignore_permissions=True)
        _ensure_supplier("_Test Opening Supplier")
        tender = frappe.get_doc({
            "doctype": "Tender", "title": "_Test Opening Ceremony",
            "donor": donor.name, "procurement_method": "Open Tender",
            "estimated_value": 600000, "submission_deadline": add_days(today(), 2),
            **{f"opening_officer_{index + 1}": email for index, email in enumerate(officers)},
        }).insert(ignore_permissions=True)
        tender.publish()
        bid = frappe.get_doc({
            "doctype": "Bid", "tender": tender.name,
            "supplier": "_Test Opening Supplier", "bid_amount": 580000,
        }).insert(ignore_permissions=True)
        bid.submit_bid()
        self.assertEqual(bid.bid_amount, 0)
        self.assertTrue(bid.encrypted_content)
        tender.reload()
        tender.publish_date = add_days(today(), -3)
        tender.submission_deadline = add_days(today(), -1)
        tender.save()
        try:
            with patch.object(sealed_bid, "_send_otp_email") as email:
                for provided_codes in (1, 2, 3):
                    email.reset_mock()
                    sealed_bid.init_opening_ceremony(tender.name)
                    codes = {
                        call.args[0]: call.args[1] for call in email.call_args_list
                    }
                    args = {
                        f"officer_{index + 1}_otp": codes[officers[index]]
                        for index in range(provided_codes)
                    }
                    if provided_codes < 3:
                        with self.assertRaisesRegex(frappe.ValidationError, "Missing OTP"):
                            sealed_bid.open_bids(tender.name, **args)
                        self.assertFalse(
                            frappe.db.exists("Bid Opening Record", {"tender": tender.name})
                        )
                        self.assertEqual(frappe.db.get_value("Bid", bid.name, "bid_amount"), 0)
                    else:
                        result = sealed_bid.open_bids(tender.name, **args)
                        self.assertEqual(result["bids_opened"], 1)
                        self.assertEqual(result["decrypted_bids"][0]["amount"], 580000)
                        record = frappe.get_doc("Bid Opening Record", result["opening_record"])
                        self.assertEqual(record.outcome, "Success")
                        self.assertTrue(record.record_hash)
                        self.assertTrue(record.signed_record.startswith("/private/files/"))
                        self.assertEqual(
                            frappe.db.get_value("Tender", tender.name, "status"), "Under Evaluation"
                        )
                        with self.assertRaisesRegex(frappe.ValidationError, "immutable"):
                            record.save()
        finally:
            for email in officers:
                frappe.cache().delete(f"bid_otp:{tender.name}:{email}")
            record_name = frappe.db.get_value(
                "Bid Opening Record", {"tender": tender.name}, "name"
            )
            if record_name:
                for name in frappe.get_all(
                    "File",
                    filters={"attached_to_doctype": "Bid Opening Record",
                             "attached_to_name": record_name},
                    pluck="name",
                ):
                    frappe.delete_doc("File", name, ignore_permissions=True)


def _ensure_supplier(name):
    if not frappe.db.exists("Supplier", name):
        frappe.get_doc({
            "doctype": "Supplier",
            "supplier_name": name,
            "supplier_group": _ensure_supplier_group(),
        }).insert(ignore_permissions=True)


def _ensure_supplier_group():
    sg = "All Supplier Groups"
    if not frappe.db.exists("Supplier Group", sg):
        frappe.get_doc({"doctype": "Supplier Group", "supplier_group_name": sg}).insert(ignore_permissions=True)
    return sg


class TestContractLifecycle(IntegrationTestCase):
    """CT1-CM4: Contract milestones, retention, and expiry."""

    def setUp(self):
        _ensure_supplier("_Test Supplier")
        self.contract = frappe.get_doc({
            "doctype": "Ugavi Contract", "supplier": "_Test Supplier",
            "start_date": "2025-01-01", "end_date": "2025-12-31",
            "contract_value": 500000, "retention_percentage": 10,
            "expiry_alert_days": 30, "status": "Draft",
        }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.delete("Ugavi Contract", {"name": self.contract.name})

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
        doc = frappe.get_doc("Ugavi Contract", self.contract.name)
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